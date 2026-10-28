#!/usr/bin/env python3
"""Verification test suite for the Zero-Speq Lean Argon-Native HITL Migration Kit."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, rel_path: str):
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_speq_guard_argon_native_behavior(tmp_path: Path, monkeypatch) -> None:
    state_file = tmp_path / "guard_state.json"
    monkeypatch.setenv("SPEQ_GUARD_STATE_FILE", str(state_file))

    hooks_dir = str(REPO_ROOT / "blueprints/.agents/hooks")
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)

    speq_guard = _load_module("speq_guard", "blueprints/.agents/hooks/speq_guard.py")

    # 1. Auto-promotes synchronous WaitMsBeforeAsync < 10000 to 10000
    res = speq_guard.evaluate_tool_call(
        "run_command",
        {"CommandLine": "pytest tests/test_speq_kit.py", "WaitMsBeforeAsync": 1000},
        now=1000.0,
    )
    assert res is not None
    assert res["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert res["hookSpecificOutput"]["updatedInput"]["WaitMsBeforeAsync"] == 10000

    # 2. Allows unlimited full-file read_file calls (no consecutive read cap)
    for i in range(10):
        res_read = speq_guard.evaluate_tool_call(
            "read_file",
            {"Path": f"/workspace/file_{i}.py"},
            now=1001.0 + i,
        )
        assert res_read is None

    # 3. Allows unlimited inline production file edits (no 3-file FORGE gate)
    for i in range(8):
        res_edit = speq_guard.evaluate_tool_call(
            "write_file",
            {"Path": f"/workspace/src/module_{i}.py", "Content": "x = 1\n"},
            now=1020.0 + i,
        )
        assert res_edit is None

    # 4. Blocks >2 narrow (<120-line) slices on the same file
    for i in range(2):
        assert (
            speq_guard.evaluate_tool_call(
                "read_file",
                {"Path": "/workspace/big.py", "StartLine": 1, "EndLine": 50},
                now=1040.0 + i,
            )
            is None
        )
    denied_slice = speq_guard.evaluate_tool_call(
        "read_file",
        {"Path": "/workspace/big.py", "StartLine": 51, "EndLine": 100},
        now=1045.0,
    )
    assert denied_slice is not None
    assert denied_slice["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "800 lines" in denied_slice["hookSpecificOutput"]["permissionDecisionReason"]

    # 5. Blocks Ouroboros shell polling loop
    denied_loop = speq_guard.evaluate_tool_call(
        "run_command",
        {"CommandLine": "while pgrep -f worker; do sleep 2; done", "WaitMsBeforeAsync": 10000},
        now=1050.0,
    )
    assert denied_loop is not None
    assert denied_loop["hookSpecificOutput"]["permissionDecision"] == "deny"

    # 6. Blocks unbounded root grep_search
    denied_grep = speq_guard.evaluate_tool_call(
        "grep_search",
        {"SearchPath": "/", "Query": "secret"},
        now=1060.0,
    )
    assert denied_grep is not None
    assert denied_grep["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_memory_index_fts5_search_and_prefetch(tmp_path: Path) -> None:
    mem_mod = _load_module("memory_index", "blueprints/tools/memory_index.py")
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    db_path = tmp_path / "speq_memory.db"

    (mem_dir / "architecture_decisions.md").write_text(
        "# Argon Medium Migration\nSpeq runs on Argon Medium with activity-renewed progress leases and FTS5 recall.\n",
        encoding="utf-8",
    )
    (mem_dir / "team_preferences.md").write_text(
        "# Communication Cadence\nLead with the outcome on sentence one in Google Chat threads.\n",
        encoding="utf-8",
    )

    stats = mem_mod.build_index(memory_dir=mem_dir, db_path=db_path)
    assert stats["indexed_files"] == 2
    assert stats["indexed_chunks"] >= 2

    hits = mem_mod.search_memory("Argon Medium progress leases", memory_dir=mem_dir, db_path=db_path)
    assert len(hits) >= 1
    assert "Argon Medium" in hits[0]["content"]

    prefetch = mem_mod.format_prefetch_block("How does Google Chat communication cadence work?", memory_dir=mem_dir, db_path=db_path)
    assert "[ACTIVE MEMORY CONTEXT]:" in prefetch
    assert "sentence one" in prefetch


def test_lease_heartbeat_renewal_and_circuit_breaker() -> None:
    lease_mod = _load_module("lease_heartbeat", "blueprints/tools/lease_heartbeat.py")
    cfg = lease_mod.LeaseConfig(
        initial_lease_seconds=300.0,
        renewal_extension_seconds=300.0,
        max_silence_seconds=300.0,
        max_identical_error_strikes=3,
    )
    mon = lease_mod.TurnLeaseMonitor(config=cfg, started_at=1000.0, last_activity_at=1000.0)

    # Progress renews lease past initial 1300.0 deadline
    snap1 = lease_mod.ProgressSnapshot(stdout_bytes=512)
    res1 = mon.evaluate(snap1, now=1250.0)
    assert res1["status"] == "renewed"
    assert float(res1["lease_expires_at"]) == 1550.0

    # Silence past max_silence_seconds expires lease
    res2 = mon.evaluate(snap1, now=1560.0)
    assert res2["status"] == "expired"

    # 3 identical errors trip circuit breaker
    assert not mon.record_error_signature("KeyError: 'foo'")
    assert not mon.record_error_signature("KeyError: 'foo'")
    assert mon.record_error_signature("KeyError: 'foo'")
    res3 = mon.evaluate(lease_mod.ProgressSnapshot(stdout_bytes=1024), now=1260.0)
    assert res3["status"] == "circuit_breaker"


def test_bundle_integrity_and_zero_homelab_pii() -> None:
    bundle_path = REPO_ROOT / "ZERO_SPEQ_BUNDLE.md"
    assert bundle_path.exists(), "ZERO_SPEQ_BUNDLE.md must exist"
    bundle_text = bundle_path.read_text(encoding="utf-8")

    m = re.search(
        r"^<!-- ZERO_SPEQ_MANIFEST_START\n(.*?)\nZERO_SPEQ_MANIFEST_END -->",
        bundle_text,
        re.M | re.S,
    )
    assert m is not None, "Manifest block missing in ZERO_SPEQ_BUNDLE.md"
    manifest = json.loads(m.group(1))
    assert "SPEQ_MIGRATION_PLAYBOOK.md" in manifest
    assert "blueprints/GEMINI.speq.md" in manifest
    assert "blueprints/.agents/hooks/speq_guard.py" in manifest

    for rel, b64_payload in manifest.items():
        decoded = base64.b64decode(b64_payload).decode("utf-8")
        assert len(decoded) > 20, f"Empty decoded file in bundle: {rel}"

    # Verify zero hardcoded RFC 1918 LAN IPs or Discord channel snowflakes across repo
    lan_ip_re = re.compile(r"\b192\.168\.\d+\.\d+\b")
    snowflake_re = re.compile(r"\b1[45]\d{17}\b")
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix not in {".md", ".py", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert not lan_ip_re.search(text), f"Private LAN IP found in {path}"
        assert not snowflake_re.search(text), f"Discord snowflake found in {path}"
