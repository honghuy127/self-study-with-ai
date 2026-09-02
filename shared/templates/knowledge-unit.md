---
id: topic.concept
question: What single question does this page answer?
prerequisites: []
source_ids: []
misconceptions: []
tags: []
studies: []
mastery:
  last_assessed: ""
  level: ""
  help: ""
review:
  next_due: ""
superseded_by: ""
---

# Title

Distilled understanding from finished studies. Agents search this base with
`python3 tools/knowledge.py search "<question>"` before gathering, so
established results are reused rather than re-derived.

Structure the page so retrieval practice works: `python3 tools/review.py run
<id>` withholds any section whose heading starts with Answer, Claim,
Explanation, Derivation, Evidence, or Worked, and shows the rest as context.
So put the thing to be recalled under one of those headings.

## Answer

State the claim in the smallest number of sentences that survive scrutiny.

## Evidence

What backs the claim, with the same anchoring discipline as a source note:
registry key plus page, section, or file:line.

## Evidential limits

What this does not establish, and what would change it. Link related units
with [[other-id]].
