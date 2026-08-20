---
description: Run the gathering stage for a study via the researcher agent. Usage: /gather studies/<slug>
agent: build
---

Run the gathering stage for: $ARGUMENTS

1. Read the study's `brief.md` and `study.yaml`. Refuse to proceed if the
   brief's required fields (question, scope, depth, deadline) are still
   blank or templated.
2. Load the `conduct-cs-ai-research` skill at
   `.opencode/skills/conduct-cs-ai-research/`.
3. Dispatch the `researcher` subagent with the study directory and any extra
   instructions from the user argument.
4. When it returns, summarize: sources found, tiers, coverage limits, and the
   gate verdict. Remind the user to review `sources/registry.yaml` and flip
   `gates.sources_approved` before `/draft`.
