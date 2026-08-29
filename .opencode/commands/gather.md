---
description: Run the gathering stage for a study via the researcher agent. Usage: /gather studies/<slug>
agent: build
---

Run the gathering stage for: $ARGUMENTS

1. Read the study's `brief.md` and `study.yaml`. Refuse to proceed if the
   brief's required fields (purpose, questions, scope, budgets, stop rules,
   and the mode-specific contract) are still blank or templated.
2. If the study status is `proposed`, move it first:
   `python3 tools/study.py status-set <study-id> gathering --note "..."`.
3. Load the `conduct-cs-ai-research` skill at
   `.opencode/skills/conduct-cs-ai-research/`.
4. Dispatch the `researcher` subagent with the study directory and any extra
   instructions from the user argument.
5. When it returns, summarize: sources found, tiers, coverage limits, and
   the gate verdict. In delegated mode, remind the user to approve the
   sources gate before `/draft`. In paper-reading mode, require exactly one
   `role: target-paper` entry and remind the user to approve the paper gate
   before `/read-paper` continues.
