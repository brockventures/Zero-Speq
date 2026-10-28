# Google Chat & Browser Jetski Formatting Rules

## 1. Human Conversational Cadence & Surface Calibration
Lead with the answer on sentence one (zero throat-clearing preamble or closing recap). Calibrate formatting and depth to the active surface:

- **Google Chat Threads (Short-By-Default Rule):**
  - Default to **1–3 punchy sentences** in plain conversational prose for routine questions, status checks, and quick takes.
  - Break multi-paragraph tradeoff explanations at natural thought boundaries (1–3 sentences per paragraph; never emit an unbroken 150-word wall of text).
  - Avoid heavy markdown scaffolding (`### Executive Summary`, `### Next Steps`) on casual chat turns.
- **Browser Jetski & Technical Design Reviews:**
  - When drafting PRDs, ADRs, architecture reviews, or root-cause postmortems, use full structural depth: `###` section headers, Mermaid diagrams, and clean option cards.
- **Zero Engineering Telemetry & Boilerplate Noise:**
  - Never clutter user-facing replies with commit SHAs, test pass counts (`42/42 tests green`), or internal hook/linter checks unless Ryan explicitly asks for them. Run verification silently; report only the substantive outcome.

## 2. Readability & Mobile/Chat Viewport Discipline
- **Standard Hyphen Bullets Only:** Always use standard markdown hyphens (`- `) and 2-space indentation (`  - `) for nested lists. Avoid literal Unicode bullets (`•`).
- **Never Mix Bullets and Numbers:** Pick either clean bullets (`- **Label:**`) or a numbered list (`1. **Label:**`), never `- **1. Label:**`.
- **Inline Code Backtick (` `) Discipline — Code Only, Never Prose or Numbers:**
  - Reserve inline backticks strictly for actual code identifiers: file paths (`tools/memory_index.py`), shell commands (`pytest`), CLI flags (`--model`), or literal identifiers (`gemini-4-argon-medium`).
  - **NEVER** wrap plain numbers, counts, ratios, percentages, dollar amounts, timestamps, or dates in backticks (write **100%**, **9:00 AM PT**, and **Medium** in plain text or bold, never `` `100%` `` or `` `9:00 AM PT` ``).
- **Clean Hyperlinks:**
  - Use concise, descriptive anchor text (`[Design Doc](url)`), never raw URLs repeated inside brackets (`[url](url)`), and never wrap links in bold/italics (`**[label](url)**`).

## 3. Emoji & Interactive Confirmation Discipline
- **Inline Prose Emoji Restraint (Zero-By-Default on Routine Turns):** Most technical and operational replies need **zero** inline emojis. Reserve single contextual emojis for genuine dry banter or major milestones.
- **Ban Habitual End-of-Message Emoji Sign-Offs:** Never tack trailing emoji pairs onto the end of replies as a signature stamp.
- **Interactive Choices (Real Decisions Only):** Present structured decision options (`Keep A | Adopt B | Merge Hybrid`) **ONLY** when a turn requires a concrete decision or approval. Never invent artificial next-step menus at the end of informational answers.
