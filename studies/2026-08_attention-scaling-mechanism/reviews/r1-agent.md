# r1-agent: independent review of 2026-08_attention-scaling-mechanism

Reviewer: agent (fresh context, adversarial posture). Date: 2026-08-21.
Scope: draft `report/main.tex` against `brief.md`, `study.yaml`, `notes/`,
the `.research/` dossier, and the run artifacts, per
`.opencode/agents/reviewer.md` and the skill playbooks
`paper-review-and-rebuttal.md` and `ethics-integrity-and-policy.md`.

## Tool outputs

- `python3 tools/lint_report.py studies/2026-08_attention-scaling-mechanism`
  printed `lint clean`, exit 0.
- `python3 tools/research/audit_research.py --root studies/2026-08_attention-scaling-mechanism`
  printed `errors=0 warnings=0`, exit 0. The audit certifies structural
  traceability only, not scientific validity; the checks below are independent
  of it.
- Independent re-run for determinism:
  `python3 experiments/run_mechanism_check.py --dk 8,64,512 --n-pairs 20000 --n-rows 2000 --out <tmp>`
  produced a byte-identical file to `experiments/results/full/summary.json`
  (sha256 `809a305ddc916243536aa47349e72d402f18a0c27cca38341004f52843753590`,
  matching the RUN-001-full manifest output record). Seed-0 determinism holds.
- Current sha256 of `experiments/run_mechanism_check.py`
  (`4702c4481cbd...`) and `experiments/config_full.json` (`2460b0c4c378...`)
  also match the manifest input/config records. No drift since capture.

## Verdicts per gate

Vocabulary: PASS, CONDITIONAL, FAIL, BLOCKED, NOT_ASSESSED.

- **Sources: PASS.** Single cited key `vaswani2017attention` resolves in
  `report/refs.bib`, which is a faithful copy of the registry `bibtex` block.
  Metadata verified against the canonical arXiv page (arXiv:1706.03762,
  accessed 2026-08-21): title, all eight authors in order, year 2017, URL all
  correct; booktitle "Advances in Neural Information Processing Systems 30"
  is the correct NIPS 2017 proceedings title. No fabricated entry, no
  registry-rejected source cited, source budget (2) respected with one source
  reused. Residual notes (registry `status`, missing local snapshot) are
  findings F3 and F4, not gate failures: the human-approved sources gate
  explicitly scoped reuse.
- **Notes: PASS.** The note's quotable matches the paper verbatim. I fetched
  the arXiv HTML (v7) and confirmed Section 3.2.1 contains "We suspect that
  for large values of d_k, the dot products grow large in magnitude, pushing
  the softmax function into regions where it has extremely small gradients"
  and "To counteract this effect, we scale the dot products by 1/sqrt(d_k)".
  The note's claim of no ablation isolating the scale is accurate (the paper's
  support is the quoted analytical argument plus a footnote derivation of
  Var(q.k) = d_k under unit-variance coordinates, not a controlled
  comparison).
- **Experiments: PASS.** RUN-001-full is a completed, measured, full-phase run
  with a schema-1.1 manifest, recorded command, seed list, config, input
  script, output artifact, and complete dirty-git content hashes; RUN-000-smoke
  is correctly labeled `synthetic-plumbing` / `not_scientific_evidence` and is
  not cited anywhere in the report. Empirical claims CLM-002..CLM-005 each
  link RUN-001-full and `experiments/results/full/summary.json`, and the
  artifact reproduces byte-for-byte from the recorded command at seed 0.
  Claim lifecycle is `analyzed` with the run
  `candidate_pending_verification`, the correct pre-sign-off state; see F7
  for the promotion step at sign-off.
- **Draft: CONDITIONAL.** Every metric in all four tables matches
  `summary.json` after rounding to displayed digits (full audit below), all
  claims trace to the ledger and the run, limitations stay visible, no
  `[CITATION NEEDED]`/`[EVIDENCE NEEDED]`/`[RESULT PENDING]` markers exist
  anywhere in the study, and citations are tied and honest. One blocking
  error: the Methods paragraph defines the Jacobian metric without the square
  root the script actually applies (F1). Fixable in one line; no number
  changes.
- **Review sign-off: CONDITIONAL.** Recommend withholding
  `review_signed_off` until F1 is fixed and re-verified. F2-F7 are
  suggestions for the human to accept or defer.

Overall verdict: **CONDITIONAL**. No fabrication found; the draft is
numerically faithful to the artifact. One metric-definition sentence is
inconsistent with the computation and must be corrected before sign-off.

## Claim trace audit

| Claim | Draft location | Grounding | Verdict |
|---|---|---|---|
| CLM-001 (descriptive) | main.tex:22-26, 42-48, 96-98, 226-228 | claims.jsonl CLM-001; evidence.jsonl SRC-001 (full-text-checked, locator Sec. 3.2.1); notes/vaswani2017attention.md Claim 1; verbatim-verified against arXiv HTML in this review | supported; minor wording nuance in F2 |
| CLM-002 (empirical) | main.tex:57-59, 130-133, Table 1 (135-149) | RUN-001-full manifest; summary.json `logit_stats`; claims.jsonl CLM-002 | supported; numbers verified |
| CLM-003 (empirical) | main.tex:60-62, 153-157, Table 2 (159-173) | RUN-001-full; summary.json `softmax_concentration`; claims.jsonl CLM-003 | supported; numbers verified |
| CLM-004 (empirical) | main.tex:63-65, 177-182, Table 3 (184-198) | RUN-001-full; summary.json `gradient_magnitude`; claims.jsonl CLM-004 | supported; numbers verified, but metric definition in Methods is wrong by a square root (F1) |
| CLM-005 (empirical) | main.tex:66-67, 200-206, Table 4 (208-222) | RUN-001-full; summary.json `assumption_relaxation` (d_k=64 slice); claims.jsonl CLM-005 | supported; symmetric case only, see F6 |

No claim lacks a trace, cites a superseded record, or overreaches its anchor,
except the F1 metric-definition sentence (which misdescribes the computation,
not the result) and the F2/F6 nuances.

## Number audit (character-for-character against summary.json)

All values round correctly to the displayed digits:

- Table 1 (main.tex:144-146): unscaled 2.862/8.023/22.570 vs json
  2.8615386/8.0234686/22.5702257; theory 2.828/8.000/22.627 vs
  2.8284271/8.0/22.6274170; scaled 1.012/1.003/0.997 vs
  1.0117067/1.0029336/0.9974725. All match.
- Table 2 (main.tex:168-170): 0.428/0.785/0.923 vs 0.4283722/0.7849696/
  0.9225800; 2.053/0.597/0.193 vs 2.0527936/0.5974076/0.1926469; scaled
  0.106/0.107/0.107 vs 0.1061740/0.1073739/0.1072661; 3.689/3.687/3.684 vs
  3.6892353/3.6873672/3.6840998. All match.
- Table 3 (main.tex:193-195): 0.2946/0.2185/0.0972 vs 0.2945742/0.2185246/
  0.0971879; 0.1820/0.1833/0.1837 vs 0.1819645/0.1832639/0.1837345. All match.
- Table 4 (main.tex:217-219): 2.001/7.998/32.217 vs 2.0014886/7.9977820/
  32.2171282; theory 2.000/8.000/32.000; scaled 0.250/1.000/4.027 vs
  0.2501861/0.9997228/4.0271410; theory 0.250/1.000/4.000. All match.
- Protocol numbers (main.tex:108-117): 20000 pairs, 2000 rows, 64 keys,
  d_k in {8,64,512}, sigma in {0.5,1.0,2.0}, seed 0, default_rng, CPU only.
  All match summary.json `config` and the manifest command.

Math re-derivation:

- With independent zero-mean coordinates at variances sigma_q^2, sigma_k^2,
  Var(q.k) = d_k sigma_q^2 sigma_k^2, so unscaled std = sqrt(d_k) sigma_q
  sigma_k and scaled std = sigma_q sigma_k. The Background derivation
  (main.tex:83-94) is algebraically correct, and the relaxation arm's
  sqrt(d_k) sigma^2 / sigma^2 columns follow for sigma_q = sigma_k = sigma.
- The softmax Jacobian entries p_i(delta_ij - p_j) (main.tex:96-97) are
  correct. The closed form quoted at main.tex:122-123,
  sum_i p_i^2(1-p_i)^2 + (sum_i p_i^2)^2 - sum_i p_i^4, expands to
  sum_i p_i^2 - 2 sum_i p_i^3 + (sum_i p_i^2)^2, which is ||J||_F squared,
  not ||J||_F. The script (run_mechanism_check.py:34-47) takes the square
  root per row and then averages. This is finding F1.
- "Matches the closed form to within about one percent" (main.tex:131-132):
  relative deviations are 1.17% (d_k=8), 0.29% (d_k=64), 0.25% (d_k=512).
  Defensible as "about", see F5.

## Citation honesty

- All 8 `\citep` uses and all 4 `Table~\ref` uses are tied with `~`; lint
  confirms.
- Every citation is framing-only. The draft nowhere attributes an empirical
  finding to Vaswani et al.; it explicitly states the paper gives no ablation
  (abstract, main.tex:25-26; intro, 45-48; related work, 226-228;
  limitations, 242-243). Section 4.3 (main.tex:180-182) correctly separates
  "the effect the primary source states qualitatively" from "here measured
  under controlled sampling".
- One nuance: the paper hedges with "We suspect"; the draft says "state" and
  "asserts" (F2). Not dishonest in context, since the draft never presents
  the mechanism as something the paper demonstrated, but the note's own
  quotable instructs "cite as the authors' stated suspicion".

## Findings

Severity: blocking (must be resolved before review sign-off) or suggestion
(human may accept or defer).

### F1 (blocking). Jacobian metric definition drops the square root

- Location: main.tex:119-124, the Metrics paragraph; the offending clause is
  "the Frobenius norm of the softmax Jacobian, computed in closed form as
  $\sum_i p_i^2(1-p_i)^2 + (\sum_i p_i^2)^2 - \sum_i p_i^4$ and averaged
  over rows".
- Evidence: the quoted expression equals ||J||_F^2 (algebra above). The
  script computes `sqrt(diag_term + off_term)` per row and reports the row
  mean of the norm (run_mechanism_check.py:41-47, 104); the script docstring
  itself labels the expression "||J||_F^2". Tabulated values such as 0.2946
  (Table 3, main.tex:193) are mean norms; recomputing the stated closed form
  yields a squared-norm statistic, not the tabulated number.
- Impact: the metric as defined in Methods is not the metric as computed.
  For an audited study whose value is traceability, this is a reproducibility
  defect even though every reported number is correct and CLM-004 stands.
- Next decisive action: writer changes the clause to, for example, "computed
  in closed form as the square root of ...", reruns lint, no numbers change.
  Reviewer re-checks the sentence against the script.

### F2 (suggestion). "states"/"asserts" vs the paper's "We suspect"

- Location: abstract main.tex:22-25; intro main.tex:42-48, especially "The
  source asserts this from softmax behavior" (45-46).
- Evidence: the verified original text is "We suspect that for large values
  of d_k, ..."; the note's quotable (notes/vaswani2017attention.md:49-52)
  directs citing it as "the authors' stated suspicion".
- Impact: wording is mildly stronger than the source. The draft is not
  otherwise misleading, since it repeatedly flags the missing ablation.
- Next decisive action: optionally soften one or both spots to "motivate" or
  "stated suspicion"; human decides.

### F3 (suggestion). Registry status still `to-read`

- Location: sources/registry.yaml:21.
- Evidence: `status: to-read` although `notes_file` exists, the note is
  written, and the notes gate was approved (events.jsonl line 5). Registry
  contract uses `noted` once the note exists.
- Impact: bookkeeping only; does not affect the draft.
- Next decisive action: writer or human flips the registry entry to `noted`.

### F4 (suggestion). No local snapshot of the cited paper in either study

- Location: studies/2026-08_attention-scaling-mechanism/sources/ (only
  registry.yaml and an empty pdfs/); the reused-from study
  studies/2026-08_scaled-dot-product-attention/sources/ also has no docs/
  snapshot.
- Evidence: the grounded/audited profile calls for a local snapshot of every
  cited paper, and evidence.jsonl SRC-001 records
  `verification: full-text-checked`. The anchored passage is carried in the
  note and I verbatim-verified it against the arXiv HTML in this review, and
  the human-approved sources gate explicitly accepted reuse, so this does not
  taint any claim.
- Impact: provenance gap against the written profile; the full-text check is
  currently not reproducible from the tree alone.
- Next decisive action: add a pdftotext snapshot under sources/docs/ (text is
  committable; PDF binaries are not), or the human accepts the deviation and
  records it in the registry provenance.

### F5 (suggestion). Single seed and loose "one percent" phrasing

- Location: main.tex:108-117 (seed 0, no seed-scope sentence) and
  main.tex:131-132 ("within about one percent").
- Evidence: one seed, no error bars; worst theory-vs-measured deviation is
  1.17% at d_k=8 (2.8615386 vs 2.8284271), the other two are 0.29% and
  0.25%. The brief did not require multi-seed runs, so this is disclosure,
  not a design flaw.
- Impact: negligible; a careful reader may want the sampling-noise scope.
- Next decisive action: optionally add half a sentence (single seed 0;
  deviations at most about 1.2%) or leave as is.

### F6 (suggestion). CLM-005's general form is measured only symmetrically

- Location: main.tex:200-206; Table 4 varies one shared sigma for queries
  and keys, while the stated normalizing scale is sqrt(d_k) sigma_q sigma_k.
- Evidence: the asymmetric form follows from the Background derivation
  (Equation 2) and reduces to the tested case; summary.json
  `assumption_relaxation` never sets sigma_q != sigma_k.
- Impact: none on correctness; the generalization is derived, and only the
  symmetric instance is empirically checked.
- Next decisive action: optionally add a clause in Section 4.4 noting the
  relaxation arm sets sigma_q = sigma_k = sigma.

### F7 (suggestion). Promote claim lifecycle at sign-off with the independent check recorded

- Location: .research/claims.jsonl (CLM-002..CLM-005 at `analyzed`,
  `candidate_pending_verification`); CLM-001 at `proposed`/`not_assessed`.
- Evidence: the audit tooling requires a distinct verification run or
  artifact before an empirical claim may be `verified`, so the current state
  is the correct pre-review state, and AGENTS.md rule 4 admits claims into
  the report when verified or backed by an eligible source note (CLM-001 is
  note-backed). This review's byte-identical re-run of the recorded command
  is a suitable independent check to cite when promoting.
- Impact: process only; the draft is consistent with the current states.
- Next decisive action: after the human accepts this review, promote
  CLM-002..CLM-005 to `verified` then `reported` with the verification
  artifact recorded (this review plus the re-run), and CLM-001 to `verified`
  on SRC-001, before or at sign-off.

## What I could not or did not do

- I did not rebuild the PDF, since writing outside `reviews/` is out of zone;
  `report/build/main.pdf` exists from the draft-approval build and lint is
  clean on the current source.
- I did not re-litigate the human-approved sources, notes, experiments, or
  draft gates beyond the checks above; F3 and F4 are surfaced for awareness,
  not to reopen gates.
- Confidence: high for numbers, determinism, math, and citation checks
  (direct recomputation and canonical-page verification); medium for F4's
  severity, since the gate owner already accepted the reuse arrangement.
