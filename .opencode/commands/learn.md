---
description: "Advance an interactive study one gated step: diagnose the baseline, plan the concept path, then tutor. Idempotent; stops at each human gate. Usage: /learn studies/<slug>"
agent: build
---

<!-- Generated from runtime/commands/learn.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Advance the tutoring loop for: $ARGUMENTS

This command drives `mode: interactive` studies only. For delegated studies
use `/draft`; for paper-reading use `/read-paper`.

The command is idempotent: read the current state, do the next ungated step,
and stop at the next human gate. A later `/learn` continues where this one
stopped.

1. Read `brief.md` and `study.yaml`. Refuse if the mode is not `interactive`,
   or if the brief's learning contract (target capability, baseline task,
   mastery task, mastery criterion, transfer task, review schedule) is still
   blank or templated. The brief is human-owned; do not fill it yourself.
2. Run `python3 tools/knowledge.py search "<the brief's primary question>"`
   and report what the repo already holds. If a unit already answers this,
   ask the human whether this should be a review
   (`python3 tools/review.py run <id>`) rather than a new study.
3. If `gates.scope_approved` is not true: dispatch the `tutor` subagent to
   administer the baseline task and record the unaided attempt in
   `learning/baseline.md`. Then stop and ask the human to approve the scope
   gate (`python3 tools/study.py approve <id> scope --note "..."`).
4. With scope approved and status `scoped`, move to `diagnosing`
   (`python3 tools/study.py status-set <id> diagnosing --note "..."`) and have
   the tutor plan `learning/map.md` from the baseline.
5. If the study needs sources the learner does not already have, run `/gather`
   for the minimum evidence packet, then stop for the evidence gate
   (`python3 tools/study.py approve <id> evidence --note "..."`).
6. With the evidence gate approved, move to `learning` and tutor one link at a
   time through the `tutor` subagent, journalling every exchange with its help
   level. Require learner production before showing any polished synthesis.
7. When the map is covered, move to `practicing` and have the tutor write a
   near problem and a transfer problem under `learning/practice/`. Administer
   them with `python3 tools/study.py practice <id> --item <name>`, which shows
   the problem and withholds the hints and solution.
8. Stop and tell the human that assessment is next, via `/assess`. Do not
   assess in this command: the tutor must not administer the test it holds the
   answers to.
