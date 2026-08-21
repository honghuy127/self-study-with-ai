---
description: Run the reviewer agent on a study draft and record findings. Usage: /review studies/<slug>
agent: build
---

Run the review stage for: $ARGUMENTS

1. Read `brief.md` and `study.yaml`. Refuse if `gates.draft_approved` is not
   `true`.
2. Load the `conduct-cs-ai-research` skill.
3. Dispatch the `reviewer` subagent with the study directory.
4. When it returns, read the review report in `reviews/` and summarize:
   per-gate verdicts, the numbered findings, and every blocked item.
5. Remind the user: findings go back to the writer only after the user
   decides what stands. Sign off the review gate (`python3 tools/study.py
   approve <study-id> review --note "..."`) only when satisfied.
6. Never edit the draft yourself during review; the writer fixes
   post-decision.
