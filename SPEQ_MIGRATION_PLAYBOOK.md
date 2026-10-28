# Zero-Speq Guided HITL Migration Playbook

> **Target Reader:** **Speq** (**S**ynthetic **P**rocessing **E**ngine for **Q**uality) — Ryan Brock's Resident Agent running in Google Jetski and Google Chat.
> **Author:** **Zero** (**Z**enith **E**ngineering & **R**untime **O**perator) — Ryan's home Resident Agent.
> **Execution Mode:** **Guided Human-in-the-Loop (HITL) Merge.** Never blindly clobber your existing identity, tools, or Google-internal workflows. You are upgrading your own engine room with Ryan as co-pilot.

---

## 0. Security & Boundary Invariants (Read First)

1. **Strict One-Way Inbound Valve:**
   - Everything in this kit flows **one way** into your local Jetski/Cloudtop workspace.
   - **NEVER** push git commits, open PRs, or transmit logs, code, or telemetry back to `github.com/brockventures/Zero-Speq` or any external endpoint.
2. **Preserve Google-Internal Capabilities:**
   - Your existing workspace already contains Google-specific configurations, internal MCP servers, corp CLI integrations (`blaze`, `hg`/`citc`, Critique, Buganizer, g3doc, internal search, Google Chat webhook/adapter wiring).
   - Treat all Google-internal integrations in your existing setup (**Version A**) as sacred. Zero-Speq (**Version B**) upgrades your **cognitive architecture, runtime reliability, persona sharpness, memory recall, and execution latency**—it never replaces your internal corp tooling.
3. **Argon-Medium Native Execution:**
   - At work, Ryan runs you on **Argon Medium** (`gemini-4-argon-medium`) without token-rationing constraints.
   - You do **NOT** need a multi-worktree build queue (like Zero's home `FORGE` engine) or inline file-edit caps. When decomposing complex tasks, spawn native parallel subagents (`invoke_subagent`) directly on Argon Medium.

---

## Phase 1: Self-Discovery & Snapshot Backup (Automatic, Zero Destruction)

Before proposing or applying any edits, execute a single compound diagnostic script to inventory your current setup (**Version A**) and create a timestamped backup snapshot.

### Step 1.1: Create a Complete Backup Snapshot
Run a single shell command or scratch script to back up your existing configuration:

```bash
BACKUP_DIR="$HOME/.speq_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
# Copy your active system prompt, rules, skills, hooks, memory, and chat bridge scripts
cp -r GEMINI.md AGENTS.md .agents tools memory "$BACKUP_DIR/" 2>/dev/null || true
echo "Backup created at: $BACKUP_DIR"
```

### Step 1.2: Inventory Your Current Setup (Version A)
Inspect your active environment in broad 800-line reads (never 50-line slices):
1. **Identity & Core Instructions:** Locate your current `GEMINI.md`, `AGENTS.md`, or system prompt files. Note your Google-specific workflows, links, team context, and domain rules.
2. **Rules & Hooks (`.agents/rules/`, `.agents/hooks.json`):** Check which modular rules and `PreToolUse` / `PostToolUse` hooks you currently run.
3. **Memory Architecture:** Check how you currently persist cross-session knowledge (markdown files, SQLite DB, or vector index) and whether your Google Chat bridge pre-fetches memory on Turn 0.
4. **Google Chat Bridge & Runtime Loop:** Inspect the daemon/adapter that connects Google Chat to Jetski:
   - Does it enforce a static wall-clock timeout (e.g. killing turns at 15 or 30 minutes even when subagents or tests are actively progressing), or an activity-renewed progress lease?
   - Does it leak intermediate SDK background task chatter into Google Chat threads?
   - How does it render interactive choices or confirmations in Google Chat?

---

## Phase 2: Side-by-Side Diff & HITL Decision Matrix

Once Phase 1 is complete, compare **Version A (Current Speq)** against **Version B (Zero-Speq Blueprints)** across the six core pillars below.

Classify every item into one of two buckets:
- **Bucket 1 — Clean Additive Upgrades (Zero Conflict):** New files or capabilities that do not conflict with any existing Version A file. Present these as a single batch for 1-click approval.
- **Bucket 2 — Overlapping Modules (HITL Judgment Calls):** Files where both Version A and Version B define behavior (especially `GEMINI.md` and your Google Chat bridge). Present a concise comparison to Ryan with explicit recommendation options: **`Keep A`**, **`Adopt B`**, or **`Merge Hybrid (Recommended)`**.

### Pillar-by-Pillar Comparison Guide

#### Pillar 1: Core Identity & Persona (`blueprints/GEMINI.speq.md` vs. Your `GEMINI.md`)
- **What Version B Brings:**
  - Sharp staff-engineer/TPM peer voice: calm composure, zero validation-seeking (*never* say *"I hope this helps!"* or *"Let me know if you need anything else!"*), deadpan observational wit, game-theory tradeoff framing, and silent forensic investigation (deliver clean outcomes first; surface stack-trace autopsies only when asked *"why?"*).
  - Strict formatting discipline tailored for **Google Chat** (1–3 sentence default in chat threads; structured headers/bullets reserved for design docs, postmortems, and explicit deep dives).
- **Recommended HITL Strategy (`Merge Hybrid`):**
  - Keep 100% of Version A's Google-internal topology, team roster, project codenames, MCP tools, and workflow references.
  - Replace generic assistant tone instructions with Version B's Character & Voice, Silent Forensic Investigation, and Google Chat / Jetski Formatting sections.

#### Pillar 2: Argon-Native Latency & Crash-Prevention Hooks (`blueprints/.agents/hooks/`)
- **What Version B Brings:**
  - `speq_guard.py` + `search_guard.py` registered via `.agents/hooks.json` (`timeout: 30`).
  - **What is INCLUDED:**
    1. **Auto-Synchronous Promotion:** Rewrites `WaitMsBeforeAsync` to `10000` ms on synchronous `run_command` calls so 3–9s commands don't prematurely detach into background tasks.
    2. **Unbounded Search Guard (`search_guard.py`):** Blocks accidental root (`/`), home directory, or unscoped monorepo `grep -r` / `find` commands that hang the container or workspace.
    3. **Anti-Ouroboros & Pipe-Hang Guard:** Blocks shell polling loops (`while pgrep ... sleep`) and unredirected background subshells that hold stdout FIFOs open until timeout.
    4. **Roundtrip Latency Nudge:** Blocks >3 consecutive single-line shell inspection calls (`ls`, `cat`, `grep`) or >2 narrow (<120-line) slices of the same file, nudging you to read 800 lines at once or bundle checks with `&&`.
    5. **Hook Self-Preservation Gate:** Runs `ast.parse()` before allowing any edit to `.agents/hooks/*.py`.
  - **What is EXCLUDED (By Design for Work):**
    - Zero inline file-edit limits (edit as many files inline as needed).
    - Zero 90-second turn gates.
    - Zero consecutive full-file `read_file` limits.
    - Zero stdout table clipping.

#### Pillar 3: Modular Behavioral Rules (`blueprints/.agents/rules/`)
- **`anti-ai-syntax.md`:** Eliminates synthetic LLM vocabulary (*delve*, *tapestry*, *testament to*, *underscores*, *seamless*, *pivotal*), enforces a near-zero em-dash budget, bans negation reveals (*"It's not X—it's Y"*), and breaks chat prose at natural thought boundaries.
- **`google_chat_and_jetski_formatting.md`:** Calibrates response depth between fast Google Chat threads (1–3 sentences, zero telemetry noise) and rich browser Jetski artifacts/docs.
- **`tool_roundtrip_minimization.md`:** Full-file 800-line reads, scratch scripts in `scratch/` for multi-file diagnostics, compound verification one-liners (`pytest && git status`), and parallel Argon Medium subagents (`invoke_subagent`).
- **`silent_background_execution.md`:** Bans phantom forward narration (*"I will now investigate X..."* at the end of a turn) and bans choosing SDK Option B intermediate chatter when waiting on async tasks.
- **`proactive_memory_recall.md` & `pacific_time_discipline.md`:** Grounds answers in durable memory before parametric guessing and enforces strict `America/Los_Angeles` (`PT`) timestamps.

#### Pillar 4: Two-Tier Hybrid Memory Engine (`blueprints/tools/memory_index.py`)
- **What Version B Brings:**
  - A standalone, zero-external-dependency SQLite **FTS5 BM25** memory & transcript indexer (`memory_index.py`) with optional dense vector Reciprocal Rank Fusion (RRF) if `fastembed` is available, and pure-stdlib SQLite FTS5 fallback if not.
  - Supports **Tier 1 (Turn-0 Ambient Pre-Fetch)** (`python3 tools/memory_index.py prefetch "<user prompt>"`) so your Google Chat bridge can inject the top 5 relevant memory snippets directly into your prompt context with sub-15ms latency and zero tool calls.
  - Supports **Tier 2 (On-Demand Search)** (`python3 tools/memory_index.py search "<query>"`) for deep historical lookups.

#### Pillar 5: Google Chat Bridge Resilience (`blueprints/tools/lease_heartbeat.py` & `detached_runner.py`)
- **`lease_heartbeat.py` (Activity-Renewed Progress Leases):**
  - Replaces brittle fixed wall-clock turn timeouts in your Google Chat bridge.
  - Samples 4 live signals every 30s (`stdout_bytes` delta, `/proc/<pid>/task` active child PIDs, background task log mtimes, and subagent transcript growth).
  - As long as you are making genuine forward progress, the turn lease automatically renews (`+300s`). Only genuinely silent/wedged processes or 3-strike identical tool-error loops are terminated.
- **`detached_runner.py` (Detached Background Jobs):**
  - For genuinely long commands (`>90s` test suites, large builds, data pipelines), spawns a detached background process with `flock` idempotency, logs output to `data/detached_jobs/`, and invokes a completion callback so interactive Google Chat turns never block.

#### Pillar 6: High-Signal Engineering Skills (`blueprints/.agents/skills/`)
- **`consultation-panel`:** Dynamically spawns 3–5 adversarial specialist subagents in parallel on **Argon Medium** (`Security`, `Performance`, `Simplicity/Maintainability`, `Domain Pragmatism`) to stress-test high-stakes designs and synthesize a decisive recommendation.
- **`systematic-debugging`:** Forensic root-cause methodology (reproduce, isolate, trace, verify—never guess-and-patch).
- **`verification-before-completion`:** Enforces running real verification commands before claiming any fix or build is complete.
- **`api-and-interface-design`**, **`code-simplification`**, **`documentation-and-adrs`**, and **`scar-to-skill`**.

---

## Phase 3: How Speq Should Present the HITL Plan to Ryan

When you finish Phase 1 and Phase 2, send Ryan a structured, concise summary in Google Chat or browser Jetski formatted like this:

```markdown
### Zero-Speq Upgrade Audit Complete
- **Backup Snapshot:** `~/.speq_backup_<timestamp>` (verified intact)
- **Current Setup Found:** <1-2 sentence summary of existing GEMINI.md, rules, skills, and Google Chat adapter>

### 1. Ready for Auto-Install (Zero Conflict)
- **Hooks:** `.agents/hooks/speq_guard.py`, `search_guard.py`, `.agents/hooks.json` (Argon-native latency & anti-hang guard; zero token/edit caps)
- **Rules:** `anti-ai-syntax.md`, `google_chat_and_jetski_formatting.md`, `tool_roundtrip_minimization.md`, `silent_background_execution.md`, `proactive_memory_recall.md`, `pacific_time_discipline.md`
- **Tools:** `tools/memory_index.py` (SQLite FTS5 memory engine), `tools/lease_heartbeat.py`, `tools/detached_runner.py`
- **Skills:** `consultation-panel`, `systematic-debugging`, `verification-before-completion`, `api-and-interface-design`, `code-simplification`, `documentation-and-adrs`, `scar-to-skill`

### 2. HITL Decisions Needed (A vs. B vs. Hybrid)
1. **`GEMINI.md` Identity & Voice:**
   - *Version A (Current):* <brief summary of current Speq persona/instructions>
   - *Version B (Zero-Speq):* Staff SWE/TPM peer persona, zero validation-seeking, deadpan wit, short-by-default Google Chat rules.
   - *Recommendation:* **Merge Hybrid** — preserve all Version A Google-internal tools/links/workflows and layer in Version B's voice, silent forensic discipline, and formatting rules.
2. **Google Chat Bridge Lease & Memory Pre-Fetch:**
   - *Version A (Current):* <how your bridge currently handles timeouts and memory>
   - *Version B (Zero-Speq):* Wire `lease_heartbeat.py` (activity-renewed progress leases) and `memory_index.py prefetch` (Turn-0 ambient recall) into the bridge loop.
   - *Recommendation:* **Adopt B** inside the bridge adapter after staging a backup.
```

Wait for Ryan's sign-off before mutating any overlapping Version A files.

---

## Phase 4: Incremental Apply, Verification & Instant Rollback

Once Ryan approves your proposed choices:

1. **Install Non-Conflicting Modules & Approved Hybrids:**
   - Copy `.agents/hooks/`, `.agents/rules/`, `.agents/skills/`, and `tools/` into your active workspace.
   - Merge `GEMINI.md` and update `.agents/hooks.json` paths to match your workspace root.
2. **Run the Verification Suite in One Compound Pass:**
   ```bash
   python3 -m pytest tests/test_speq_kit.py && python3 tools/memory_index.py build && python3 tools/memory_index.py search "Speq"
   ```
3. **Dry-Run the PreToolUse Hook:**
   ```bash
   echo '{"tool_name":"run_command","tool_input":{"CommandLine":"echo ok","WaitMsBeforeAsync":1000}}' | python3 .agents/hooks/speq_guard.py
   ```
   Confirm it returns valid JSON promoting `WaitMsBeforeAsync` to `10000`.
4. **Instant Rollback Command (If Anything Misbehaves):**
   ```bash
   cp -r "$BACKUP_DIR"/* ./
   ```
