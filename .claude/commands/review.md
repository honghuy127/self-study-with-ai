---
description: >-
  Run the reviewer agent on a study draft and record findings. Usage: /review
  studies/<slug>
---

<!-- Generated from runtime/commands/review.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Run the review stage for: $ARGUMENTS

1. Read `brief.md` and `study.yaml`. For delegated mode, refuse unless
   `gates.draft_approved` is true and move `drafting` to `review`. For
   paper-reading mode, refuse unless `gates.deck_approved` is true and move
   `presenting` to `review`. Interactive mode does not use this command.
2. Load the `conduct-cs-ai-research` skill.
3. Dispatch the `reviewer` subagent with the study directory.
4. When it returns, read the review report in `reviews/` and summarize:
   per-gate verdicts, the numbered findings, and every blocked item.
5. Remind the user: findings go back to the writer only after the user
   decides what stands. Sign off the review gate (`python3 tools/study.py
   approve <study-id> review --note "..."`) only when satisfied, then move
   the study to done (`python3 tools/study.py status-set <study-id> done
   --note "..."`; the CLI refuses until the review gate is signed off).
6. Never edit the draft yourself during review; the writer fixes
   post-decision.
