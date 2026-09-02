# Review round 1

Independent pass over `report/main.tex` against `notes/`,
`sources/registry.yaml`, and the brief. Not required at grounded assurance;
run because the study's whole value is the distinction between what the
source establishes and what it conjectures, and that is exactly the kind of
distinction a draft erodes.

## Verdicts

| Gate | Verdict | Evidence |
|---|---|---|
| Claim traceability | PASS | Every substantive claim in Findings carries a Section or footnote locator resolving to `notes/vaswani2017attention.md`. |
| Citation honesty | PASS | One cited key, present in `report/refs.bib` and in the registry with matching metadata. No rejected source cited. |
| Methodology match | PASS | Source-only study, no experimental claim, no `[RESULT PENDING]` marker, no implied measurement. |
| Numbers | NOT_ASSESSED | The report states no measured value, correctly: the source reports no ablation for this choice. |
| Style | PASS | Lint clean: no em-dashes, citations tied with `~`, American spellings. |

## Findings

1. **Resolved, suggestion.** The first draft of the abstract stated that
   unscaled logits "push the softmax into a region of vanishing gradients",
   without a hedge. That strengthens the source: Section~3.2.1 says the
   authors *suspect* this. Rewritten to attribute the conjecture. This was the
   single most likely way for this report to become subtly false, and it is
   worth noting that it happened on the first attempt.

2. **Accepted, not a defect.** The study rests on one source. For a question
   about a choice made in one paper, a wider survey would add citations
   without adding evidence. The brief fixed a source budget of 2 and the
   registry documents the exclusion reason, so the narrowness is a recorded
   decision rather than an oversight.

3. **Carried forward.** Two questions remain open and cannot be closed by any
   source-only study: whether the gradient conjecture holds, and how the scale
   behaves once the independence assumption fails in a trained model. Both are
   recorded in Limitations and belong to a follow-up study with an
   `experimental` methodology.

## Next decisive action

Sign off. The report answers the brief at the supported scope and does not
overstate its single source.
