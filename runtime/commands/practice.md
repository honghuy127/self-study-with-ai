---
name: practice
description: "Administer a practice item from an interactive study without exposing hints or solutions. Usage: /practice studies/<slug> [item-name]"
---

Administer practice for: $ARGUMENTS

1. Read `study.yaml`. Refuse unless the mode is `interactive`.
2. With no item named, run `python3 tools/study.py practice <id>` to list the
   available items and ask the learner which to attempt.
3. With an item named, run
   `python3 tools/study.py practice <id> --item <name>`. It prints the
   `## Problem` section and withholds `## Hints` and `## Solution`. Show the
   learner exactly what that command printed. Do not open the item file
   yourself first: reading the solution and then administering the problem is
   how a practice session turns into a guided walkthrough.
4. Let the learner attempt it. Offer help only when asked, one level at a
   time, in order: 0 restate the question, 1 name the prerequisite, 2 give an
   intermediate step or counterexample, 3 show the step and ask them to
   explain it back. Say which level you are giving.
5. Append the attempt to the item's `## Attempt record`: date, highest help
   level used, what the learner produced in their own words, and the verdict
   (solved unaided, solved with hints, not solved). Never edit an earlier
   attempt block.
6. Report whether the learner is ready for assessment. Solved-with-hints is
   not ready; it means one more item targeting the same capability.
