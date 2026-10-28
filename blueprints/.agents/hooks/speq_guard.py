#!/usr/bin/env python3
"""Speq Guard — Argon-Native Latency & Crash-Prevention PreToolUse Hook.

Designed for Google Jetski / Argon Medium where token rationing and FORGE worktree
queues are NOT needed. Enforces strictly:
1. Synchronous `WaitMsBeforeAsync: 10000` promotion on `run_command` to prevent premature
   background task detachment on 2-9s commands.
2. Unbounded search protection (via `search_guard.py`).
3. Anti-Ouroboros polling loop & `/proc/1/fd` FIFO pipe-hang prevention.
4. Hook Self-Preservation Gate (`ast.parse` syntax verification before editing hooks).
5. Roundtrip latency nudges: prevents >2 narrow (<120-line) slices on the same file
   (nudging 800-line full reads) and >3 consecutive single-line shell inspection commands
   (nudging compound `&&` commands or scratch scripts).

Intentionally OMITS:
- Inline production file-edit caps (unlimited files may be edited inline).
- 90-second turn gates (unlimited turn duration).
- Consecutive full-file `read_file` caps (unlimited full-file reads).
- Stdout table clipping.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
import time
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

import search_guard  # noqa: E402

STATE_FILE = Path(os.environ.get("SPEQ_GUARD_STATE_FILE", "/tmp/speq_guard_state.json"))
SESSION_RESET_SECONDS = 300

MAX_NARROW_SLICES_SAME_FILE = 2
NARROW_SLICE_MAX_LINES = 120
MAX_CONSECUTIVE_SINGLE_SHELL_INSPECTIONS = 3

OUROBOROS_LOOP_RE = re.compile(
    r"\bwhile\b[^;\n]*(?:pgrep|ps\s+aux|pidof|kill\s+-0)[^;\n]*;\s*do\b[^;\n]*\bsleep\b",
    re.IGNORECASE,
)

PROC_FD_REDIRECT_RE = re.compile(r"/proc/(?:1|self)/fd/[12]")

SINGLE_INSPECTION_CMD_RE = re.compile(
    r"^\s*(?:ls|cat|head|tail|wc|stat|pwd|whoami|uname|date|uptime)\b[^;&|\n]*$"
)


def _load_state(now: float) -> dict:
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if now - float(data.get("last_ts", 0)) <= SESSION_RESET_SECONDS:
                return data
    except Exception:
        pass
    return {
        "last_ts": now,
        "narrow_file_slices": {},
        "consecutive_single_shell": 0,
    }


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _allow(updated_input: dict | None = None) -> dict:
    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }
    if updated_input is not None:
        out["hookSpecificOutput"]["updatedInput"] = updated_input
    return out


def _check_hook_self_preservation(tool_name: str, tool_input: dict) -> str | None:
    """Ensure edits to `.agents/hooks/*.py` compile cleanly with `ast.parse`."""
    path_str = str(tool_input.get("Path", ""))
    if not path_str.endswith(".py") or ".agents/hooks" not in path_str.replace("\\", "/"):
        return None

    target_path = Path(path_str)
    candidate_source: str | None = None

    if tool_name == "write_file":
        if tool_input.get("Append"):
            existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
            candidate_source = existing + str(tool_input.get("Content", ""))
        else:
            candidate_source = str(tool_input.get("Content", ""))
    elif tool_name == "edit_file" and target_path.exists():
        existing = target_path.read_text(encoding="utf-8")
        target = str(tool_input.get("Target", ""))
        replacement = str(tool_input.get("Replacement", ""))
        if target and target in existing:
            candidate_source = existing.replace(target, replacement)

    if candidate_source is not None:
        try:
            ast.parse(candidate_source, filename=path_str)
        except SyntaxError as exc:
            return (
                f"Hook Self-Preservation Gate: SyntaxError in `{path_str}` at line {exc.lineno}: "
                f"{exc.msg}. Fix the Python syntax before modifying an active PreToolUse hook."
            )
    return None


def evaluate_tool_call(
    tool_name: str, tool_input: dict, now: float | None = None
) -> dict | None:
    """Evaluate a PreToolUse event and return a hook response dict (or None for passthrough)."""
    now_ts = time.time() if now is None else now
    state = _load_state(now_ts)
    state["last_ts"] = now_ts

    # 1. Scoped Search Safety
    search_err = search_guard.check_search_safety(tool_name, tool_input)
    if search_err:
        _save_state(state)
        return _deny(search_err)

    # 2. Hook Self-Preservation AST Check
    if tool_name in ("write_file", "edit_file"):
        hook_err = _check_hook_self_preservation(tool_name, tool_input)
        if hook_err:
            _save_state(state)
            return _deny(hook_err)
        state["consecutive_single_shell"] = 0
        _save_state(state)
        return None

    # 3. Narrow File-Slicing Latency Guard (Full-file reads are completely unlimited)
    if tool_name in ("read_file", "view_file"):
        state["consecutive_single_shell"] = 0
        path_str = str(tool_input.get("Path", ""))
        start_line = tool_input.get("StartLine")
        end_line = tool_input.get("EndLine")

        if start_line is not None and end_line is not None:
            span = int(end_line) - int(start_line) + 1
            if span <= NARROW_SLICE_MAX_LINES:
                slices = state.setdefault("narrow_file_slices", {})
                count = int(slices.get(path_str, 0)) + 1
                slices[path_str] = count
                if count > MAX_NARROW_SLICES_SAME_FILE:
                    _save_state(state)
                    return _deny(
                        f"Latency Guard: `{path_str}` has been read in {count} narrow slices "
                        f"(<= {NARROW_SLICE_MAX_LINES} lines). `read_file` supports up to 800 lines "
                        "per call. Omit `StartLine`/`EndLine` or read a 300-800 line block in one shot."
                    )
        _save_state(state)
        return None

    # 4. Shell Command Anti-Hang & Synchronous Promotion
    if tool_name == "run_command":
        cmd = str(tool_input.get("CommandLine", ""))

        if OUROBOROS_LOOP_RE.search(cmd):
            _save_state(state)
            return _deny(
                "Anti-Hang Guard: Shell `while pgrep/ps ... sleep` polling loops block the turn "
                "and risk self-matching Ouroboros deadlocks. Use `detached_runner.py` or a single "
                "bounded check instead."
            )

        if PROC_FD_REDIRECT_RE.search(cmd):
            _save_state(state)
            return _deny(
                "Anti-Hang Guard: Redirecting output to `/proc/1/fd/1` or `/proc/self/fd` inside "
                "`run_command` holds the tool stdout pipe open and wedges the session."
            )

        if SINGLE_INSPECTION_CMD_RE.match(cmd):
            state["consecutive_single_shell"] = int(state.get("consecutive_single_shell", 0)) + 1
            if state["consecutive_single_shell"] > MAX_CONSECUTIVE_SINGLE_SHELL_INSPECTIONS:
                _save_state(state)
                return _deny(
                    "Latency Guard: >3 consecutive single-line shell inspection commands detected. "
                    "Bundle inspection commands into a single compound call using `&&` or a Python "
                    "scratch script to save roundtrip latency."
                )
        else:
            state["consecutive_single_shell"] = 0

        _save_state(state)

        # Auto-promote synchronous WaitMsBeforeAsync to 10000ms
        is_daemon = bool(tool_input.get("IsDaemon", False))
        wait_ms = int(tool_input.get("WaitMsBeforeAsync", 0) or 0)
        if not is_daemon and wait_ms != 500 and wait_ms < 10000:
            updated = dict(tool_input)
            updated["WaitMsBeforeAsync"] = 10000
            return _allow(updated)

        return None

    state["consecutive_single_shell"] = 0
    _save_state(state)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    decision = evaluate_tool_call(tool_name, tool_input)
    if decision is not None:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
