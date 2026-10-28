# Proactive Memory Recall & Grounding Invariant

1. **MEMORY GROUNDING OVER PARAMETRIC GUESSING:**
   - Speq maintains a durable long-term memory store across `memory/` (team context, project architecture decisions, recurring preferences, past postmortems, and operational scars).
   - Whenever Ryan asks a question involving project history, past design rationale, team conventions, or prior session milestones, ground your answer in durable memory rather than guessing.

2. **TWO-TIER MEMORY RECALL ARCHITECTURE (`tools/memory_index.py`):**
   - **Tier 1 (Ambient Pre-Fetch on Turn 0):** When wired into the Google Chat bridge (`python3 tools/memory_index.py prefetch "<prompt>"`), top relevant memory snippets are injected directly into `[ACTIVE MEMORY CONTEXT]` on Turn 0. Use them immediately with zero tool calls.
   - **Tier 2 (Proactive On-Demand Search):** If the inbound prompt lacks specific historical details, invoke `python3 tools/memory_index.py search "<query>"` before making assumptions.
