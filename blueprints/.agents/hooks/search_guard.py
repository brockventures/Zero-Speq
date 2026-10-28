#!/usr/bin/env python3
"""Scoped Search & Anti-Hang Guard for Speq (Argon-Native Edition).

Blocks unbounded root/home/monorepo filesystem traversals (`grep -r /`, `find /`,
unscoped `grep_search` or `find_by_name`) and binary disassembly that hang agent turns,
while allowing fast scoped searches inside project directories.
"""

from __future__ import annotations

import json
import os
import re
import sys

BLOCKED_TOP_LEVEL_PATHS = {
    "/",
    "/root",
    "/home",
    "/tmp",
    "/var",
    "/usr",
    "/etc",
    "/proc",
    "/sys",
}

BINARY_RE = re.compile(
    r"\b(strings|hexdump|objdump|readelf|nm)\b.*(?:/usr/local/bin/|/usr/bin/|\.so\b)",
    re.IGNORECASE,
)

UNBOUNDED_SHELL_FIND_RE = re.compile(
    r"\bfind\s+(/|/root|/home(?:/[^/\s]+)?|\.|~)\s+(?!.*-maxdepth\s+[1-4]\b)",
    re.IGNORECASE,
)

UNBOUNDED_SHELL_GREP_RE = re.compile(
    r"\b(grep\s+-[a-zA-Z]*r[a-zA-Z]*|rg)\b[^|;&]*\s+(/|/root|/home(?:/[^/\s]+)?|~)(?:\s|$)",
    re.IGNORECASE,
)


def normalize_path(path_str: str) -> str:
    if not path_str:
        return ""
    expanded = os.path.expanduser(path_str.strip())
    return os.path.normpath(expanded)


def check_search_safety(tool_name: str, tool_input: dict) -> str | None:
    """Return a denial message if the search is unbounded and risks hanging, else None."""
    if tool_name in ("grep_search", "find_by_name"):
        search_path = normalize_path(str(tool_input.get("SearchPath", "")))
        if not search_path or search_path in BLOCKED_TOP_LEVEL_PATHS:
            return (
                f"Search Guard: Unbounded `{tool_name}` on top-level path `{search_path or '/'}` "
                "is blocked to prevent filesystem traversal hangs. Scope `SearchPath` to a specific "
                "subdirectory or file."
            )
        home_dir = normalize_path(os.environ.get("HOME", "/root"))
        if search_path == home_dir:
            return (
                f"Search Guard: `{tool_name}` directly on `$HOME` (`{home_dir}`) is blocked. "
                "Target a specific project subdirectory instead."
            )
        if tool_name == "grep_search" and os.path.isdir(search_path):
            includes = tool_input.get("Includes")
            if not includes:
                return (
                    "Search Guard: Directory `grep_search` requires an `Includes` glob filter "
                    "(e.g. `Includes: ['*.py', '*.md']`) to avoid scanning binary or build artifacts."
                )

    if tool_name == "run_command":
        cmd = str(tool_input.get("CommandLine", ""))
        if BINARY_RE.search(cmd):
            return (
                "Search Guard: Binary disassembly/scanning on system binaries is blocked. "
                "Use `--help` or documentation instead."
            )
        if UNBOUNDED_SHELL_FIND_RE.search(cmd):
            return (
                "Search Guard: Unbounded `find` without `-maxdepth <= 4` on a root or home path "
                "is blocked to prevent I/O hangs. Scope the directory and add `-maxdepth 3`."
            )
        if UNBOUNDED_SHELL_GREP_RE.search(cmd):
            return (
                "Search Guard: Unbounded recursive `grep -r` / `rg` on `/` or `$HOME` is blocked. "
                "Scope your search to a specific project subdirectory."
            )

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    reason = check_search_safety(tool_name, tool_input)
    if reason:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
