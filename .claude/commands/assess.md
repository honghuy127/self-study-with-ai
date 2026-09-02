---
description: >-
  Administer the unaided mastery assessment for an interactive study through the
  independent assessor agent. Usage: /assess studies/<slug>
---

<!-- Generated from runtime/commands/assess.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Run the mastery assessment for: $ARGUMENTS

1. Read `brief.md` and `study.yaml`. Refuse unless the mode is `interactive`.
   Refuse if `learning/baseline.md` is still templated: without the
   pre-teaching attempt there is nothing for a mastery verdict to mean.
2. Move the status to `assessing` if it is not there already
   (`python3 tools/study.py status-set <id> assessing --note "..."`).
3. Run `python3 tools/study.py assess <id>`. It opens a timestamped attempt
   record under `learning/attempts/` and prints the mastery task with its
   grading notes withheld.
4. Dispatch the `assessor` subagent, not the tutor. Pass it only the study
   directory. Do not summarize the tutoring history for it, do not tell it
   what the learner struggled with, and do not offer your own view of whether
   the learner knows this. Its independence is the entire point: it must see
   the performance, not your expectation of the performance.
5. When it returns, surface the verdict, the per-capability judgments with the
   learner's quoted words, and the weakest capability.
6. On `needs-practice`: move back to `practicing`
   (`python3 tools/study.py status-set <id> practicing --note "..."`) and tell
   the human which capability the next practice item should target.
7. On `pass`: remind the human to approve the mastery gate
   (`python3 tools/study.py approve <id> mastery --note "..."`), then move to
   `retained`, distill `outputs/learning-note.md`, write or update a knowledge
   unit (`python3 tools/knowledge.py new <id> --question "..."`), and schedule
   the first delayed review
   (`python3 tools/review.py schedule <id> --in 7d`).

Never approve the mastery gate yourself, and never soften a `needs-practice`
into a pass because the session went well.
