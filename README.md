# Project Zero-Speq — Lean Argon-Native Upgrade Kit

**Zero-Speq** is an Agent-to-Agent, Human-in-the-Loop (HITL) architectural upgrade kit designed for **Speq** (**S**ynthetic **P**rocessing **E**ngine for **Q**uality), a persistent Resident Agent running inside **Google Jetski** (Antigravity) and communicating via **Google Chat** and browser-based Jetski.

It distills the highest-leverage runtime, memory, latency, and persona patterns from **Zero** (**Z**enith **E**ngineering & **R**untime **O**perator), stripped of all token-rationing constraints and external worktree queues so Speq can run at full throttle on **Argon Medium** (`gemini-4-argon-medium`).

---

## Core Design Principles

1. **Argon-Medium Native (Zero Token Rationing):**
   - No multi-chunk worktree queues (`FORGE` is omitted). Multi-stream tasks use native parallel Argon Medium subagents (`invoke_subagent`).
   - No inline file-edit caps, no 90-second turn gates, no consecutive `read_file` limits, and no stdout table clipping.
   - Retains all **wall-clock latency** and **crash-prevention** guards: 800-line full-file reads, compound shell execution, synchronous `WaitMsBeforeAsync: 10000` promotion, anti-Ouroboros loop prevention, and scoped search protection.
2. **Guided Agent-to-Agent HITL Merge (Speq Drives):**
   - Speq already has an existing identity, ruleset, and toolset. Rather than overwriting Speq's workspace blindly, [`SPEQ_MIGRATION_PLAYBOOK.md`](SPEQ_MIGRATION_PLAYBOOK.md) instructs Speq to inventory and back up his current setup (`Version A`), diff it against the Zero-Speq blueprints (`Version B`), auto-stage non-conflicting additions, and walk Ryan through side-by-side judgment calls (`Keep A | Adopt B | Merge Hybrid`) in Google Chat or browser Jetski.
3. **Strict One-Way Inbound Valve:**
   - This repository is 100% public, MIT-licensed, and free of any internal or personal topology.
   - **Speq must NEVER push commits, open PRs, or transmit telemetry back to external GitHub from inside Google.** All adaptations stay strictly local to Speq's internal workspace.
4. **Dual Packaging (Git Repo + Single-File Bundle):**
   - Use the structured directory layout via `git clone`, **or** drop the single compiled [`ZERO_SPEQ_BUNDLE.md`](ZERO_SPEQ_BUNDLE.md) file directly into browser Jetski / Google Chat if corporate proxy rules restrict external git cloning.

---

## Repository Structure

```text
Zero-Speq/
├── LICENSE                                  # MIT License
├── README.md                                # Overview & Day-1 Quickstart prompts
├── SPEQ_MIGRATION_PLAYBOOK.md               # Step-by-step HITL migration protocol for Speq
├── ZERO_SPEQ_BUNDLE.md                      # Single-file compiled kit + self-extractor
├── blueprints/
│   ├── GEMINI.speq.md                       # Upgraded Resident Agent identity & voice for Speq
│   ├── .agents/
│   │   ├── hooks.json                       # PreToolUse hook registration (timeout: 30s)
│   │   ├── hooks/
│   │   │   ├── speq_guard.py                # Lean Argon-native latency & anti-hang guard
│   │   │   └── search_guard.py              # Unbounded root/monorepo grep & find protection
│   │   ├── rules/
│   │   │   ├── anti-ai-syntax.md            # Natural human prose & banned AI syntax markers
│   │   │   ├── google_chat_and_jetski_formatting.md # Google Chat & browser Jetski UX rules
│   │   │   ├── pacific_time_discipline.md   # Strict America/Los_Angeles (PT) timestamp rules
│   │   │   ├── proactive_memory_recall.md   # Two-tier ambient + FTS5 hybrid memory grounding
│   │   │   ├── silent_background_execution.md # Anti-phantom-work & silent async waiting
│   │   │   └── tool_roundtrip_minimization.md # Argon-native batching & parallel subagents
│   │   └── skills/
│   │       ├── api-and-interface-design/    # Clean contract & boundary design skill
│   │       ├── code-simplification/         # Behavior-preserving clarity refactoring skill
│   │       ├── consultation-panel/          # Adversarial multi-agent panel on Argon Medium
│   │       ├── documentation-and-adrs/      # Architecture Decision Record (ADR) authoring
│   │       ├── scar-to-skill/               # Debugging scar-to-skill conversion engine
│   │       ├── systematic-debugging/        # Forensic root-cause debugging methodology
│   │       └── verification-before-completion/ # Mandatory evidence-before-assertions gate
│   └── tools/
│       ├── memory_index.py                  # Standalone SQLite FTS5 BM25 + RRF memory engine
│       ├── lease_heartbeat.py               # Activity-renewed progress lease & loop detector
│       └── detached_runner.py               # Lightweight background job runner for >90s tasks
├── scripts/
│   └── build_bundle.py                      # Compiles the entire repo into ZERO_SPEQ_BUNDLE.md
└── tests/
    └── test_speq_kit.py                     # Automated verification & PII/safety test suite
```

---

## Day-1 Quickstart: How to Hand This to Speq

### Option A: Cloudtop / Jetski Shell (`git clone` or archive download)
If your environment allows reading public GitHub repositories:

```bash
git clone https://github.com/brockventures/Zero-Speq.git /tmp/zero-speq
```

Then send this prompt to **Speq** in Google Chat or Jetski:

> **Prompt to Speq:**
> "Read `/tmp/zero-speq/SPEQ_MIGRATION_PLAYBOOK.md` in full. Execute **Phase 1 (Self-Discovery & Backup)** and **Phase 2 (Side-by-Side Diff & HITL Decision Matrix)** against your current workspace and Google Chat bridge. Do not overwrite any existing files yet—present your backup path, your inventory summary, and your side-by-side HITL recommendations (`Keep A | Adopt B | Merge Hybrid`) so we can review them together."

### Option B: Browser Jetski / Air-Gapped Single-File Drop (`ZERO_SPEQ_BUNDLE.md`)
If `git clone` to external GitHub is blocked on your corporate workstation:

1. Download [`ZERO_SPEQ_BUNDLE.md`](ZERO_SPEQ_BUNDLE.md) in your browser and attach or paste it into your Jetski session (or save it to `/tmp/ZERO_SPEQ_BUNDLE.md`).
2. Tell **Speq**:

> **Prompt to Speq:**
> "Unpack `/tmp/ZERO_SPEQ_BUNDLE.md` into `/tmp/zero-speq` using the embedded Python unpacker at the top of the bundle, then read `/tmp/zero-speq/SPEQ_MIGRATION_PLAYBOOK.md` and run Phase 1 (Backup & Inventory) and Phase 2 (Side-by-Side Diff & HITL Proposal)."
