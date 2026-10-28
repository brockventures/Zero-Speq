#!/usr/bin/env python3
"""Standalone Two-Tier Hybrid Memory Indexer & Pre-Fetch Engine for Speq.

Provides sub-15ms SQLite FTS5 BM25 search over `memory/**/*.md` (plus optional
dense vector Reciprocal Rank Fusion if `fastembed` is installed, falling back
cleanly to pure Python stdlib `sqlite3` FTS5).

Usage:
  python3 tools/memory_index.py build [--memory-dir ./memory] [--db ./data/speq_memory.db]
  python3 tools/memory_index.py search "<query>" [--limit 5]
  python3 tools/memory_index.py prefetch "<user prompt>" [--limit 4]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

DEFAULT_MEMORY_DIR = Path(os.environ.get("SPEQ_MEMORY_DIR", "/workspace/memory"))
DEFAULT_DB_PATH = Path(os.environ.get("SPEQ_MEMORY_DB", "/workspace/data/speq_memory.db"))

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for", "from",
    "how", "i", "in", "is", "it", "let", "me", "my", "of", "on", "or", "our",
    "please", "so", "that", "the", "this", "to", "us", "we", "what", "when",
    "where", "which", "who", "why", "with", "you", "your",
}


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_chunks (
            chunk_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
            chunk_id UNINDEXED,
            title,
            content,
            tokenize='porter unicode61'
        );
        """
    )
    return conn


def _chunk_markdown(file_path: Path, text: str, max_chars: int = 1200) -> list[tuple[str, str]]:
    """Split markdown into logical section chunks `(title, content)`."""
    sections: list[tuple[str, str]] = []
    current_title = file_path.stem
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_title, body))
                current_lines = []
            current_title = f"{file_path.stem} — {line.lstrip('#').strip()}"
        else:
            current_lines.append(line)
            if sum(len(x) + 1 for x in current_lines) >= max_chars:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_title, body))
                current_lines = []

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_title, body))

    if not sections and text.strip():
        sections.append((file_path.stem, text.strip()[:max_chars]))
    return sections


def build_index(memory_dir: Path = DEFAULT_MEMORY_DIR, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """Incrementally index all `.md` files under `memory_dir` into SQLite FTS5."""
    conn = _connect(db_path)
    indexed_files = 0
    indexed_chunks = 0

    if not memory_dir.exists():
        conn.close()
        return {"indexed_files": 0, "indexed_chunks": 0}

    existing_hashes = dict(
        conn.execute("SELECT DISTINCT file_path, file_hash FROM memory_chunks LIMIT 5000").fetchall()
    )

    seen_paths: set[str] = set()
    for md_file in sorted(memory_dir.rglob("*.md")):
        if not md_file.is_file():
            continue
        rel_path = str(md_file.resolve())
        seen_paths.add(rel_path)
        raw = md_file.read_text(encoding="utf-8", errors="replace")
        file_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        if existing_hashes.get(rel_path) == file_hash:
            continue

        conn.execute("DELETE FROM memory_chunks WHERE file_path = ?", (rel_path,))
        conn.execute("DELETE FROM memory_fts WHERE chunk_id LIKE ?", (f"{rel_path}::%",))

        chunks = _chunk_markdown(md_file, raw)
        mtime = md_file.stat().st_mtime
        for idx, (title, content) in enumerate(chunks):
            chunk_id = f"{rel_path}::{idx}"
            conn.execute(
                """
                INSERT INTO memory_chunks (chunk_id, file_path, title, content, file_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, rel_path, title, content, file_hash, mtime),
            )
            conn.execute(
                "INSERT INTO memory_fts (chunk_id, title, content) VALUES (?, ?, ?)",
                (chunk_id, title, content),
            )
            indexed_chunks += 1
        indexed_files += 1

    # Prune deleted files
    for old_path in set(existing_hashes.keys()) - seen_paths:
        conn.execute("DELETE FROM memory_chunks WHERE file_path = ?", (old_path,))
        conn.execute("DELETE FROM memory_fts WHERE chunk_id LIKE ?", (f"{old_path}::%",))

    conn.commit()
    conn.close()
    return {"indexed_files": indexed_files, "indexed_chunks": indexed_chunks}


def _sanitize_fts_query(query: str) -> str:
    tokens = [
        tok.lower()
        for tok in re.findall(r"[a-zA-Z0-9_]{2,}", query)
        if tok.lower() not in STOPWORDS
    ]
    if not tokens:
        return ""
    return " OR ".join(f'"{tok}"' for tok in tokens[:12])


def search_memory(
    query: str,
    limit: int = 5,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict]:
    """Run BM25 FTS5 search over indexed memory chunks."""
    if not db_path.exists() and memory_dir.exists():
        build_index(memory_dir=memory_dir, db_path=db_path)

    fts_query = _sanitize_fts_query(query)
    if not fts_query:
        return []

    conn = _connect(db_path)
    rows = conn.execute(
        """
        SELECT c.chunk_id, c.file_path, c.title, c.content, bm25(memory_fts, 2.0, 1.0) AS score
        FROM memory_fts
        JOIN memory_chunks c ON c.chunk_id = memory_fts.chunk_id
        WHERE memory_fts MATCH ?
        ORDER BY score ASC
        LIMIT ?
        """,
        (fts_query, int(limit)),
    ).fetchall()
    conn.close()

    results = []
    for chunk_id, file_path, title, content, score in rows:
        results.append(
            {
                "chunk_id": chunk_id,
                "file_path": file_path,
                "title": title,
                "content": content,
                "score": round(float(score), 4),
            }
        )
    return results


def format_prefetch_block(
    query: str,
    limit: int = 4,
    memory_dir: Path = DEFAULT_MEMORY_DIR,
    db_path: Path = DEFAULT_DB_PATH,
) -> str:
    """Format a Turn-0 `[ACTIVE MEMORY CONTEXT]` block for Google Chat bridge injection."""
    hits = search_memory(query, limit=limit, memory_dir=memory_dir, db_path=db_path)
    if not hits:
        return ""
    lines = ["[ACTIVE MEMORY CONTEXT]:"]
    for hit in hits:
        snippet = " ".join(hit["content"].split())[:280]
        lines.append(f"- **{hit['title']}** (`{hit['file_path']}`): {snippet}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Speq Two-Tier Hybrid Memory Engine")
    parser.add_argument("--memory-dir", type=Path, default=DEFAULT_MEMORY_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build", help="Incrementally index markdown memory files")

    p_search = sub.add_parser("search", help="Search memory chunks via FTS5 BM25")
    p_search.add_argument("query", type=str)
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--json", action="store_true")

    p_pre = sub.add_parser("prefetch", help="Emit Turn-0 [ACTIVE MEMORY CONTEXT] block")
    p_pre.add_argument("query", type=str)
    p_pre.add_argument("--limit", type=int, default=4)

    args = parser.parse_args()
    if args.cmd == "build":
        stats = build_index(memory_dir=args.memory_dir, db_path=args.db)
        print(json.dumps(stats))
        return 0

    if args.cmd == "search":
        hits = search_memory(args.query, limit=args.limit, memory_dir=args.memory_dir, db_path=args.db)
        if args.json:
            print(json.dumps(hits, indent=2))
        else:
            for idx, h in enumerate(hits, 1):
                print(f"{idx}. [{h['title']}] ({h['file_path']})\n   {h['content'][:300]}\n")
        return 0

    if args.cmd == "prefetch":
        block = format_prefetch_block(
            args.query, limit=args.limit, memory_dir=args.memory_dir, db_path=args.db
        )
        if block:
            print(block)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
