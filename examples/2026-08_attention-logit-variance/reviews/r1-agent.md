# Review round 1

Independent pass over `report/main.tex` against `.research/claims.jsonl`, the
run manifests, the raw result artifacts, and the brief. Required at audited
assurance.

## Verdicts

| Gate | Verdict | Evidence |
|---|---|---|
| Claim traceability | PASS | Three reported claims, each linking `ev-main-results` and `ev-replication-results`, run `run-main-20260902`, and verification run `run-replication-20260902`. `audit_research.py` reports 0 errors, 0 warnings. |
| Numbers | PASS | Every figure in both tables was re-read from `results/main.json` and `results/replication.json` rather than from the ledger, and matches character for character. |
| Methodology match | PASS | Experimental methodology, real runs behind every number, no `[RESULT PENDING]` marker, no claim beyond the synthetic setting. |
| Independent check | CONDITIONAL | Each reported claim carries a distinct verification run, which is what the contract requires. A second seed is a weak check: it catches sampling flukes and nondeterminism, not a design error. Accepted because the experiment plan says so explicitly rather than implying more. |
| Style | PASS | Lint clean: no em-dashes, ties present, American spellings, table spacing per the style rules. |

## Findings

1. **Resolved, blocking as first written.** The draft's concentration section
   originally read that the scale "keeps attention diffuse". The measured
   scaled value is $0.106$ against a uniform $0.0156$, so attention is roughly
   seven times more concentrated than chance even with the scale. Rewritten to
   say the scale bounds concentration rather than removing it, and the
   misreading is now called out explicitly. This is the finding that justified
   the review: the claim ledger was correct and the prose was not.

2. **Resolved, blocking as first written.** The abstract claimed variance
   "exactly 1" under scaling. Two runs disagree in the second decimal place.
   Replaced with the measured bound and the replication spread.

3. **Accepted.** Four dimensions and 20000 pairs is a small design. It is
   sufficient for the question asked, which is directional, and the brief's
   stop rule says so. Tighter error bars would change no conclusion here.

4. **Accepted, carried forward.** The gradient mechanism remains untested. The
   report says so in three places and `claim-softmax-concentration` carries the
   caveat, so the study does not leave a reader believing more than was
   measured.

## Next decisive action

Sign off. The report states what the runs support and marks the boundary
where it stops.
