# Tool Roundtrip Minimization & Parallel Subagent Invariant (Argon-Native Edition)

Because Speq runs on **Argon Medium** (`gemini-4-argon-medium`) without token rationing, optimize ruthlessly for **wall-clock latency** and **execution thoroughness**:

## Hard Constraints

1. **Full-File & Broad-Slice Reading (Ban 50-Line Slicing):**
   - `read_file` natively supports loading up to **800 lines** in a single call.
   - **NEVER** inspect files in small 30–60 line sequential slices. Omit `StartLine` and `EndLine` for files under 800 lines to load in one shot.
   - For larger files, inspect targeted logical sections in wide blocks (300–800 lines).

2. **Multi-File Diagnostic Batching (Scratch Scripts First):**
   - When diagnosing issues or auditing patterns across 4+ files, **NEVER** run serial chains of single-line `cat`/`grep`/`ls` calls.
   - Bundle multi-file inspections, AST checks, or regex audits into a single Python script in `scratch/` and execute via `run_command`.

3. **Compound Shell Commands:**
   - Bundle single-line shell inspection, linting, and test commands using `&&` or `;` (`ruff check . && pytest tests/test_feature.py && git status -s`) rather than firing separate serial tool calls.

4. **Synchronous `WaitMsBeforeAsync` Ceiling (`10000` MS):**
   - Always set `WaitMsBeforeAsync: 10000` on synchronous `run_command` calls so 3–9s compound commands finish inline without prematurely detaching into background tasks. (Enforced automatically by `speq_guard.py`).

5. **Native Parallel Subagents (`invoke_subagent`) Over Serial Bottlenecks:**
   - When a task involves independent research tracks, multi-component edits, or adversarial design reviews (`consultation-panel`), launch multiple `invoke_subagent` workers (`Model: "inherit"`) in parallel in a single turn.

6. **Conversational Zero-Tool Fast-Path:**
   - When responding to pure strategy, product tradeoff, or consensus prompts where context is already in memory or the prompt, make **ZERO** tool calls and deliver the response in a single inference pass.
