---
name: consultation-panel
description: Use this skill whenever deciding on complex, ambiguous, or high-stakes architectural choices, product/engineering trade-offs, refactors, or security/infrastructure crossroads. Dynamically synthesizes and launches a multi-perspective panel of specialized adversarial subagents in parallel on Argon Medium, conducts rigorous debate, and reconciles the perspectives into a decisive consensus recommendation.
---

# Adversarial Consultation Panel Skill (Argon-Medium Native)

When facing a high-stakes design decision, ambiguous system tradeoff, or complex architectural crossroads, do not rely on a single linear chain of thought. Spawn an adversarial panel of 3–4 specialist subagents in parallel (`invoke_subagent` with `Model: "inherit"` on Argon Medium) and synthesize their findings.

---

## Step 1: Select 3–4 Domain-Specific Adversarial Roles

Tailor the panel personas to the problem at hand:
1. **Systems & Reliability Architect:** Focuses on failure modes, state consistency, race conditions, latency, and blast radius.
2. **Simplicity & Maintainability Skeptic:** Attacks over-engineering, premature abstraction, and cognitive load; champions the smallest clean design.
3. **Security & Boundary Auditor:** Probes trust boundaries, data leakage, auth scopes, and injection vectors.
4. **Product & Execution Pragmatist:** Evaluates time-to-value, user friction, rollout safety, and leverage.

---

## Step 2: Launch Panelists in Parallel (`invoke_subagent`)

Invoke all panelists in a **single turn** so they execute concurrently on Argon Medium:

- Provide each panelist with:
  - The exact problem statement and candidate options (`Option A`, `Option B`, `Option C`).
  - Their specific adversarial charter (e.g., *"Steelman the simplest possible approach and ruthlessly critique hidden complexity in Options A and B"*).
  - Instructions to inspect relevant files in 800-line reads and return a structured 250-word verdict (`Primary Recommendation`, `Fatal Flaws Found`, `Non-Negotiable Safeguards`).

---

## Step 3: Reconcile & Deliver the Synthesis

Once all subagents report back (remember: wait silently without intermediate status chatter until all panelists finish):
1. Weigh where the specialists converged and where they clashed.
2. Lead your response with a **single decisive recommendation** on sentence one.
3. Summarize the key tradeoffs, why the winning option beat the alternatives, and the specific safeguards adopted from the dissenters.
