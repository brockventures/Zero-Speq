#!/usr/bin/env python3
"""Lightweight Detached Background Job Runner for Speq (>90s Commands).

Spawns long-running builds, test sweeps, or migrations completely detached from
the interactive Google Chat turn (`start_new_session=True`), tracks state in SQLite,
and writes logs to disk so interactive turns never block.

Usage:
  python3 tools/detached_runner.py start --name "full-test-sweep" --cmd "pytest -q"
  python3 tools/detached_runner.py status [<job_id>]
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path

DEFAULT_DB = Path(os.environ.get("SPEQ_JOBS_DB", "/workspace/data/speq_jobs.db"))
DEFAULT_LOG_DIR = Path(os.environ.get("SPEQ_JOBS_LOG_DIR", "/workspace/data/detached_jobs"))


def _connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS detached_jobs (
            job_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            pid INTEGER,
            status TEXT NOT NULL,
            exit_code INTEGER,
            log_path TEXT NOT NULL,
            started_at REAL NOT NULL,
            finished_at REAL
        );
        """
    )
    return conn


def start_job(
    name: str,
    command: str,
    db_path: Path = DEFAULT_DB,
    log_dir: Path = DEFAULT_LOG_DIR,
) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    job_id = f"job-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    log_path = log_dir / f"{job_id}.log"

    conn = _connect(db_path)
    now = time.time()
    conn.execute(
        """
        INSERT INTO detached_jobs (job_id, name, command, pid, status, log_path, started_at)
        VALUES (?, ?, ?, ?, 'running', ?, ?)
        """,
        (job_id, name, command, 0, str(log_path), now),
    )
    conn.commit()

    wrapper_code = (
        "import sqlite3, subprocess, sys, time\n"
        f"db_path = {str(db_path)!r}\n"
        f"job_id = {job_id!r}\n"
        f"cmd = {command!r}\n"
        f"log_path = {str(log_path)!r}\n"
        "with open(log_path, 'wb') as lf:\n"
        "    proc = subprocess.Popen(cmd, shell=True, stdout=lf, stderr=subprocess.STDOUT)\n"
        "    conn = sqlite3.connect(db_path, timeout=10.0)\n"
        "    conn.execute('UPDATE detached_jobs SET pid = ? WHERE job_id = ?', (proc.pid, job_id))\n"
        "    conn.commit()\n"
        "    conn.close()\n"
        "    rc = proc.wait()\n"
        "conn = sqlite3.connect(db_path, timeout=10.0)\n"
        "status = 'completed' if rc == 0 else 'failed'\n"
        "conn.execute('UPDATE detached_jobs SET status = ?, exit_code = ?, finished_at = ? WHERE job_id = ?', (status, rc, time.time(), job_id))\n"
        "conn.commit()\n"
        "conn.close()\n"
    )

    proc = subprocess.Popen(
        [os.environ.get("PYTHON", "python3"), "-c", wrapper_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    conn.close()
    return {
        "job_id": job_id,
        "name": name,
        "wrapper_pid": proc.pid,
        "status": "running",
        "log_path": str(log_path),
    }


def list_jobs(job_id: str | None = None, db_path: Path = DEFAULT_DB) -> list[dict]:
    conn = _connect(db_path)
    if job_id:
        rows = conn.execute(
            """
            SELECT job_id, name, command, pid, status, exit_code, log_path, started_at, finished_at
            FROM detached_jobs WHERE job_id = ? LIMIT 1
            """,
            (job_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT job_id, name, command, pid, status, exit_code, log_path, started_at, finished_at
            FROM detached_jobs ORDER BY started_at DESC LIMIT 20
            """
        ).fetchall()
    conn.close()
    return [
        {
            "job_id": r[0],
            "name": r[1],
            "command": r[2],
            "pid": r[3],
            "status": r[4],
            "exit_code": r[5],
            "log_path": r[6],
            "started_at": r[7],
            "finished_at": r[8],
        }
        for r in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Speq Detached Job Runner")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="subcmd", required=True)

    p_start = sub.add_parser("start", help="Launch a detached background command")
    p_start.add_argument("--name", required=True)
    p_start.add_argument("--cmd", required=True)

    p_status = sub.add_parser("status", help="Inspect detached job status")
    p_status.add_argument("job_id", nargs="?")

    args = parser.parse_args()
    if args.subcmd == "start":
        info = start_job(args.name, args.cmd, db_path=args.db)
        print(json.dumps(info, indent=2))
        return 0
    if args.subcmd == "status":
        jobs = list_jobs(args.job_id, db_path=args.db)
        print(json.dumps(jobs, indent=2))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
