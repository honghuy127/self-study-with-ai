---
description: >-
  Answer one small question with verified sources into shared/inbox/, without
  scaffolding a study. Usage: /ask "<question>"
---

<!-- Generated from runtime/commands/ask.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Answer this question, with sources: $ARGUMENTS

This is the cheap path. A full study is right for a week of work and absurd
for a five-minute question, and a question with nowhere cheap to go gets asked
in a chat window and lost. An inbox note keeps the property that matters,
every claim traceable to something checked, at a fraction of the ceremony.

1. Run `python3 tools/knowledge.py search "<question>"` first. If a unit
   already answers it, show that unit and stop. Answering it again is how a
   knowledge base rots into duplicates.
2. Create the note: `python3 tools/inbox.py new "<question>"`.
3. Gather three to five sources at most, then stop. Verify each against a
   canonical page, DOI, or repository before citing it: exact title, authors,
   year, venue, or remote URL and commit. Never write a citation from memory.
   Prefer primary sources; a third-party summary backs only a hedged claim and
   must say so.
4. Fill the note:
   - **Answer**: two to five sentences. Every factual sentence must be
     attributable to an Evidence line.
   - **Evidence**: one line per source with an exact anchor, the same
     discipline a study note uses (page, section, or `file:line`).
   - **Not verified**: what you could not check, what the sources disagree
     about, and what would settle it. An empty Not verified section is almost
     always a lie; if the question was genuinely closed by one authoritative
     source, say that explicitly instead of leaving it blank.
   Set `status: answered` and list the source keys or URLs in `sources`.
5. Report the answer, then name the honest next step:
   - it stands on its own: leave it, no further action;
   - it deserves to be remembered:
     `python3 tools/inbox.py distill <note> --id <unit-id>`, then
     `python3 tools/review.py schedule <unit-id> --in 7d`;
   - it turned out to be a real investigation:
     `python3 tools/inbox.py promote <note> --mode delegated`, and say plainly
     that the inbox answer is not the study's answer.

Never let this path turn into a study by accretion. Three to five sources,
then either finish or promote.
