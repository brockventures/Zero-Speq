#!/usr/bin/env python3
"""Activity-Renewed Turn Lease & Runaway Loop Detector for Speq's Google Chat Bridge.

Replaces brittle static wall-clock turn timeouts (e.g. killing an active Argon Medium
turn at 15 or 30 minutes while subagents or tests are actively progressing).

Monitors 4 activity signals every heartbeat interval:
  1. Stream stdout byte counter growth (`stdout_bytes`).
  2. Active child/descendant process PIDs in `/proc/<pid>/task/*/children`.
  3. Background task log modification timestamps (`bg_log_mtime`).
  4. Subagent transcript modification timestamps (`subagent_mtime`).

Also enforces a 3-Strike Identical Error Circuit Breaker so genuinely wedged tool loops
terminate early instead of burning lease extensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time


@dataclass
class LeaseConfig:
    initial_lease_seconds: float = 300.0
    renewal_extension_seconds: float = 300.0
    max_silence_seconds: float = 300.0
    hard_safety_ceiling_seconds: float = 7200.0
    max_identical_error_strikes: int = 3


@dataclass
class ProgressSnapshot:
    stdout_bytes: int = 0
    active_child_pids: tuple[int, ...] = ()
    latest_bg_log_mtime: float = 0.0
    latest_subagent_mtime: float = 0.0


@dataclass
class TurnLeaseMonitor:
    config: LeaseConfig = field(default_factory=LeaseConfig)
    started_at: float = field(default_factory=time.time)
    last_activity_at: float = field(default_factory=time.time)
    lease_expires_at: float = field(init=False)
    last_snapshot: ProgressSnapshot = field(default_factory=ProgressSnapshot)
    recent_error_signatures: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.lease_expires_at = self.started_at + self.config.initial_lease_seconds

    def record_error_signature(self, signature: str) -> bool:
        """Record a tool error signature. Returns True if 3-strike circuit breaker tripped."""
        if not signature:
            return False
        self.recent_error_signatures.append(signature)
        n = self.config.max_identical_error_strikes
        if len(self.recent_error_signatures) >= n:
            tail = self.recent_error_signatures[-n:]
            if len(set(tail)) == 1:
                return True
        return False

    def evaluate(
        self, snapshot: ProgressSnapshot, now: float | None = None
    ) -> dict[str, object]:
        """Evaluate whether to renew the lease or terminate the turn."""
        now_ts = time.time() if now is None else now
        elapsed = now_ts - self.started_at

        if elapsed >= self.config.hard_safety_ceiling_seconds:
            return {
                "status": "expired",
                "reason": f"Hard safety ceiling reached ({int(elapsed)}s)",
                "lease_expires_at": self.lease_expires_at,
            }

        n = self.config.max_identical_error_strikes
        if len(self.recent_error_signatures) >= n and len(set(self.recent_error_signatures[-n:])) == 1:
            return {
                "status": "circuit_breaker",
                "reason": f"3-strike identical tool error loop detected: {self.recent_error_signatures[-1]}",
                "lease_expires_at": self.lease_expires_at,
            }

        progressed = (
            snapshot.stdout_bytes > self.last_snapshot.stdout_bytes
            or bool(snapshot.active_child_pids)
            or snapshot.latest_bg_log_mtime > self.last_snapshot.latest_bg_log_mtime
            or snapshot.latest_subagent_mtime > self.last_snapshot.latest_subagent_mtime
        )

        if progressed:
            self.last_activity_at = now_ts
            self.last_snapshot = snapshot
            self.lease_expires_at = max(
                self.lease_expires_at,
                now_ts + self.config.renewal_extension_seconds,
            )
            return {
                "status": "renewed",
                "reason": "Forward progress detected",
                "lease_expires_at": self.lease_expires_at,
            }

        silence = now_ts - self.last_activity_at
        if now_ts >= self.lease_expires_at or silence >= self.config.max_silence_seconds:
            return {
                "status": "expired",
                "reason": f"No progress signals for {int(silence)}s",
                "lease_expires_at": self.lease_expires_at,
            }

        return {
            "status": "active",
            "reason": f"Within active lease ({int(self.lease_expires_at - now_ts)}s remaining)",
            "lease_expires_at": self.lease_expires_at,
        }


def collect_proc_children(root_pid: int) -> tuple[int, ...]:
    """Inspect `/proc/<pid>/task/*/children` to find active child processes."""
    children: set[int] = set()
    task_dir = Path(f"/proc/{root_pid}/task")
    if not task_dir.exists():
        return ()
    for ch_file in task_dir.glob("*/children"):
        try:
            for tok in ch_file.read_text(encoding="utf-8").split():
                pid = int(tok)
                if pid != root_pid:
                    children.add(pid)
        except Exception:
            continue
    return tuple(sorted(children))
