---
description: "Run today's retrieval practice across every knowledge unit and interactive mastery record. Usage: /review-due [--on YYYY-MM-DD]"
agent: build
---

<!-- Generated from runtime/commands/review-due.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Run the review queue: $ARGUMENTS

Retrieval is the part of studying that survives the study. This command is the
daily loop; without it the knowledge base is a filing cabinet.

1. Run `python3 tools/review.py due`, passing through any `--on` argument.
2. If nothing is due, say so and stop. Do not invent extra practice.
3. For each due knowledge unit, in order:
   a. Run `python3 tools/review.py run <id>`. It prints the question and
      withholds every answering section. Show exactly that to the learner.
   b. Do not open the unit file first, and do not hint. Ask the question, wait
      for the answer, and stay quiet while they think.
   c. Compare their answer to the unit only after they have committed to one.
      Then record it: `python3 tools/review.py record <id> --result
      recalled|partial|missed --note "<what was missing, in their words>"`.
      Grade honestly. A generous `recalled` schedules the next review too far
      out and quietly loses the item.
   d. On `partial` or `missed`, show the unit's answering sections
      immediately, while the gap is still open, and say what the learner
      actually got wrong rather than reassuring them.
4. For each due interactive mastery review, run
   `python3 tools/study.py revisit <study-id>` and administer the original
   mastery task at help level none, then append the result to the Reviews
   section of `learning/mastery.md`. Never rewrite the original mastery record.
5. Finish with `python3 tools/knowledge.py index` so the index reflects the
   new schedule, and report what moved out, what came back, and what is now
   due next.
