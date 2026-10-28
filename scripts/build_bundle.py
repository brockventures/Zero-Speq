#!/usr/bin/env python3
"""Compiles the entire Zero-Speq repository into a single self-extracting markdown bundle.

Generates `ZERO_SPEQ_BUNDLE.md` at the repository root so Ryan can upload or paste
a single file into browser Jetski or Google Chat if external `git clone` is blocked.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_PATH = REPO_ROOT / "ZERO_SPEQ_BUNDLE.md"

INCLUDED_FILES = [
    "README.md",
    "SPEQ_MIGRATION_PLAYBOOK.md",
    "blueprints/GEMINI.speq.md",
    "blueprints/.agents/hooks.json",
    "blueprints/.agents/hooks/speq_guard.py",
    "blueprints/.agents/hooks/search_guard.py",
    "blueprints/.agents/rules/anti-ai-syntax.md",
    "blueprints/.agents/rules/google_chat_and_jetski_formatting.md",
    "blueprints/.agents/rules/pacific_time_discipline.md",
    "blueprints/.agents/rules/proactive_memory_recall.md",
    "blueprints/.agents/rules/silent_background_execution.md",
    "blueprints/.agents/rules/tool_roundtrip_minimization.md",
    "blueprints/tools/memory_index.py",
    "blueprints/tools/lease_heartbeat.py",
    "blueprints/tools/detached_runner.py",
    "blueprints/.agents/skills/consultation-panel/SKILL.md",
    "blueprints/.agents/skills/systematic-debugging/SKILL.md",
    "blueprints/.agents/skills/verification-before-completion/SKILL.md",
    "blueprints/.agents/skills/api-and-interface-design/SKILL.md",
    "blueprints/.agents/skills/code-simplification/SKILL.md",
    "blueprints/.agents/skills/documentation-and-adrs/SKILL.md",
    "blueprints/.agents/skills/scar-to-skill/SKILL.md",
    "tests/test_speq_kit.py",
]


def build_bundle(repo_root: Path = REPO_ROOT, output_path: Path = BUNDLE_PATH) -> Path:
    manifest: dict[str, str] = {}
    sections: list[str] = []

    for rel in INCLUDED_FILES:
        fpath = repo_root / rel
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        manifest[rel] = base64.b64encode(content.encode("utf-8")).decode("ascii")
        ext = fpath.suffix.lstrip(".") or "text"
        if ext == "py":
            lang = "python"
        elif ext in ("md", "json"):
            lang = ext
        else:
            lang = "text"
        sections.append(f"## File: `{rel}`\n\n````{lang}\n{content.rstrip()}\n````\n")

    manifest_json = json.dumps(manifest, indent=2, sort_keys=True)

    header = f"""# ZERO-SPEQ SINGLE-FILE BUNDLE (`ZERO_SPEQ_BUNDLE.md`)

> **For Speq (`Synthetic Processing Engine for Quality`):**
> This single file contains the complete **Zero-Speq Lean Argon-Native Upgrade Kit** (Playbook, Blueprints, Hooks, Rules, Tools, Skills, and Verification Tests).
>
> ### Quick Unpack Command (Run in Shell or Scratch Script)
> Save this file to `/tmp/ZERO_SPEQ_BUNDLE.md` and run:
> ```bash
> python3 -c '
> import base64, json, pathlib, re
> text = pathlib.Path("/tmp/ZERO_SPEQ_BUNDLE.md").read_text(encoding="utf-8")
> m = re.search(r"^<!-- ZERO_SPEQ_MANIFEST_START\n(.*?)\nZERO_SPEQ_MANIFEST_END -->", text, re.M | re.S)
> out = pathlib.Path("/tmp/zero-speq")
> for rel, b64 in json.loads(m.group(1)).items():
>     p = out / rel
>     p.parent.mkdir(parents=True, exist_ok=True)
>     p.write_text(base64.b64decode(b64).decode("utf-8"), encoding="utf-8")
> print("Unpacked", len(json.loads(m.group(1))), "files to", out)
> '
> ```
> Then read `/tmp/zero-speq/SPEQ_MIGRATION_PLAYBOOK.md` and execute **Phase 1 (Backup & Inventory)** and **Phase 2 (Side-by-Side HITL Proposal)**.

<!-- ZERO_SPEQ_MANIFEST_START
{manifest_json}
ZERO_SPEQ_MANIFEST_END -->

---

"""
    full_text = header + "\n".join(sections)
    output_path.write_text(full_text, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    out = build_bundle()
    print(f"Built bundle at {out} ({out.stat().st_size} bytes)")
