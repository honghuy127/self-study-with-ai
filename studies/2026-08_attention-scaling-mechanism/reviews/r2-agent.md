# r2-agent: focused re-review of 2026-08_attention-scaling-mechanism

Reviewer: agent (fresh context, adversarial posture). Date: 2026-08-22.
Scope: verify the writer's fixes against r1 findings F1-F6 and check for
regressions in `report/main.tex`, `sources/registry.yaml`,
`.research/evidence.jsonl`, and the new snapshot
`sources/docs/vaswani2017attention.txt`. This is a delta review; items not
touched since r1 (notes fidelity, run manifest integrity, math derivations)
were spot-rechecked via artifact hashes rather than fully re-derived.

## Tool outputs

- `python3 tools/lint_report.py studies/2026-08_attention-scaling-mechanism`
  printed `lint clean`, exit 0.
- `python3 tools/research/audit_research.py --root studies/2026-08_attention-scaling-mechanism`
  printed `errors=0 warnings=0`, exit 0. As in r1, the audit certifies
  structural traceability only; the checks below are independent of it.

## F1 (was blocking): RESOLVED

- Draft now reads (main.tex:124-127): "the Frobenius norm of the softmax
  Jacobian, computed in closed form as the square root of
  $\sum_i p_i^2(1-p_i)^2 + (\sum_i p_i^2)^2 - \sum_i p_i^4$ and averaged
  over rows."
- The script computes exactly this: `jacobian_frobenius`
  (run_mechanism_check.py:41-47) forms
  `diag_term = sum_i p_i^2(1-p_i)^2`, `off_term = (sum_i p_i^2)^2 - sum_i
  p_i^4`, and returns `sqrt(diag_term + off_term)` per row; the reported
  metric is the row mean of that norm (run_mechanism_check.py:104).
- The radicand in the draft and the radicand in the code are term-for-term
  identical, and the square root and row-averaging order both match. The
  fix is correct and complete: this Metrics paragraph is the only place the
  metric is defined, and Table 3's caption ("Mean Frobenius norm",
  main.tex:190-191) and Findings 4.3 prose are consistent with it. The
  script's `np.maximum(..., 0.0)` clamp is a floating-point guard against a
  tiny negative radicand under saturation; it does not change the defined
  quantity and needs no mention.
- No numbers changed and none needed to: the tabulated values were always
  mean norms; only the definition sentence was wrong in r1.

## Dispositions for F2-F6

### F2 (hedging): RESOLVED

- Abstract (main.tex:22-26): "motivate the factor by the suspicion that
  large dot products push the softmax into regions of small gradients, but
  the paper provides no ablation isolating the scale."
- Introduction (main.tex:43-49): "The source offers this as an analytical
  suspicion rather than a measured result, and reports no controlled
  comparison of scaled versus unscaled attention, so the mechanism is stated
  rather than measured in the primary source (dossier claim CLM-001)."
- Both match the verified source text "We suspect that for large values of
  d_k, ..." (snapshot lines 192-194) and the note's instruction "Cite as the
  authors' stated suspicion, not as an established measurement"
  (notes/vaswani2017attention.md:49-52). No new overclaim: the remaining
  "states"/"asserts" uses (main.tex:98, 184-185, 233-234, 237) all appear in
  "stated, not measured" framings and echo the note's own phrase "asserted
  rather than measured". Abstract and introduction are mutually consistent.

### F3 (registry status): RESOLVED

- `sources/registry.yaml:21` is now `status: noted`, matching the contract
  for an entry with a completed note and an approved notes gate.

### F4 (local snapshot): RESOLVED

- Snapshot exists at `sources/docs/vaswani2017attention.txt` (1312 lines),
  header `arXiv:1706.03762v7 [cs.CL] 2 Aug 2023`, title and author block
  confirm it is the Vaswani et al. paper. It is a pdftotext extraction,
  committable text.
- Registry carries `snapshot: "sources/docs/vaswani2017attention.txt"`
  (registry.yaml:23), and SRC-001's locator now reads "Sec. 3.2.1 (snapshot
  sources/docs/vaswani2017attention.txt line 192)" with a note recording the
  F4 addition.
- Locator verified: Section 3.2.1 begins at snapshot lines 167-169; the
  anchored passage "We suspect that for large values of dk, the dot products
  grow large in magnitude, pushing the softmax function into regions where
  it has extremely small gradients" starts at line 192, and "To counteract
  this effect, we scale the dot products by 1/sqrt(dk)" appears at line 194.
  The full-text check is now reproducible from the tree alone.
- No PDF binary committed or present: `git ls-files '*.pdf'` is empty,
  `sources/pdfs/` is empty, and the only `*.pdf` on disk is
  `report/build/main.pdf`, the report's own build artifact, which is
  gitignored via `**/build/`. Note the whole study directory is still
  untracked (`git status`: `?? studies/2026-08_attention-scaling-mechanism/`),
  consistent with the repo rule that agents commit only on human request;
  there is no paper PDF anywhere to commit.

### F5 (single seed and 1.2% bound): RESOLVED

- Protocol (main.tex:118-120): "All reported results are for the single
  seed $0$ with no error bars; sampling-noise deviations from the closed
  form are at most about $1.2\%$." Findings 4.1 (main.tex:135-136):
  "matches the closed form to within about $1.2$ percent."
- Recomputed all theory-vs-measured relative deviations from summary.json:
  unscaled/scaled logit std gives 1.1707% (d_k=8, both, since scaling by a
  constant preserves relative deviation), 0.2934% (d_k=64), 0.2528%
  (d_k=512). Including every relaxation-arm slice (including the d_k=8 and
  d_k=512 slices not in Table 4), the maximum is still 1.1707%. So 1.2% is
  a correct upper bound, worst case ~1.17% at d_k=8 as r1 stated, and the
  two draft phrasings are consistent with each other.

### F6 (symmetric-only relaxation arm): RESOLVED

- Section 4.4 (main.tex:210-213): "The relaxation arm sets
  $\sigma_q = \sigma_k = \sigma$; the asymmetric form follows from the
  derivation in the Background and reduces to the symmetric instance that is
  actually measured."
- Accurate: the Background derives std = sqrt(d_k) sigma_q sigma_k for
  general sigmas (Equation 2, main.tex:84-92), and the script's relaxation
  arm draws both q and k with `scale=sigma` (run_mechanism_check.py:111-112),
  so only the symmetric instance is measured, exactly as disclosed.

## Regression checks

- **Numbers unchanged and correct.** `summary.json` sha256 is still
  `809a305ddc91...3590`, and `run_mechanism_check.py` (`4702c4481cbd...`)
  and `config_full.json` (`2460b0c4c3a3...`) still match the RUN-001-full
  manifest `dirty_file_hashes` records, so the artifact is byte-identical to
  the captured run. Re-audited all four tables against summary.json:
  Table 1 (main.tex:148-150) 2.862/8.023/22.570, 2.828/8.000/22.627,
  1.012/1.003/0.997; Table 2 (main.tex:172-174) 0.428/0.785/0.923,
  2.053/0.597/0.193, 0.106/0.107/0.107, 3.689/3.687/3.684; Table 3
  (main.tex:197-199) 0.2946/0.2185/0.0972, 0.1820/0.1833/0.1837; Table 4
  (main.tex:224-226) 2.001/7.998/32.217, 2.000/8.000/32.000,
  0.250/1.000/4.027, 0.250/1.000/4.000. Every value rounds correctly from
  the JSON. No drift.
- **Citations tied.** All 8 `\citep` uses and all 4 `Table~\ref` uses carry
  `~` (grep-verified; lint confirms). No untied cite or ref.
- **No fabrication markers.** No `[CITATION NEEDED]`, `[EVIDENCE NEEDED]`,
  or `[RESULT PENDING]` anywhere in the study (the only grep hit is r1's own
  prose quoting the marker names).
- **refs.bib** remains a faithful copy of the registry `bibtex` block plus
  the `gen_bib.py` header comments; metadata was verified against the
  canonical arXiv page in r1 and is unchanged.
- **Claim states unchanged and consistent.** CLM-002..CLM-005 at `analyzed`
  with RUN-001-full, CLM-001 at `proposed` on SRC-001; the draft does not
  overstate lifecycle. SRC-001's locator update is the only dossier change
  and it is accurate.

## New findings

### F8 (suggestion). Filler adverb "actually" in Section 4.4

- Location: main.tex:213, "reduces to the symmetric instance that is
  actually measured".
- Evidence: the house style rule drops filler adverbs including "actually";
  the sentence reads identically without it ("...that is measured").
- Impact: cosmetic; lint does not police this.
- Next decisive action: optional one-word deletion; human decides.

### Observation (not a finding). Study tree still untracked

- `git status` shows the entire study directory as untracked, and the
  RUN-001-full manifest recorded the same state at capture time. This is the
  expected state under the rule that agents commit only on human request.
  F4's reproducibility holds in the working tree now and will hold in the
  commit whenever the human chooses to commit.

## Carried item

### F7 (from r1, deferred). Promote claim lifecycle at sign-off

- Unchanged and correctly so: the audit tooling requires a verification
  record before empirical claims move to `verified`, and `analyzed` with
  `candidate_pending_verification` is the correct pre-sign-off state.
- Next decisive action: at sign-off, promote CLM-002..CLM-005 to `verified`
  then `reported` recording the verification evidence (r1's byte-identical
  re-run plus this re-review's hash re-verification), and CLM-001 to
  `verified` on SRC-001, then approve `review_signed_off`.

## Verdicts per gate

Vocabulary: PASS, CONDITIONAL, FAIL, BLOCKED, NOT_ASSESSED.

- **Sources: PASS.** r1's residuals are cleared: registry status is `noted`
  (F3), a committable pdftotext snapshot exists, is registered, is referenced
  by SRC-001 with a verified line locator, and contains the anchored passage
  (F4). No PDF binary in the tree or the index. Citation metadata verified
  in r1 and unchanged.
- **Notes: PASS.** Note unchanged since r1; its quotable matches the
  snapshot verbatim (line 192-194 passage), and the draft now follows the
  note's "stated suspicion" instruction (F2).
- **Experiments: PASS.** RUN-001-full artifacts are byte-identical to the
  manifest hashes; the smoke run remains uncited and labeled
  non-evidentiary; claim-run links intact.
- **Draft: PASS.** The blocking F1 metric-definition error is fixed and
  verified against the script; F2, F5, F6 fixes are accurate and introduce
  no new overclaim or inconsistency; all numbers, citation ties, and
  no-marker checks pass. Only residual is the cosmetic F8.
- **Review sign-off: PASS (recommend approval).** No blocking finding
  remains. The F7 lifecycle promotion is the documented administrative step
  that accompanies the human's sign-off approval, not a draft defect.

Overall verdict: **PASS**. F1 is resolved; F2-F6 are resolved as specified;
no regressions; no fabrication; no new or remaining blocking findings. The
draft is ready for the human to promote the claim lifecycle (F7) and approve
`review_signed_off`.

## What I did not do

- I did not edit the draft, registry, dossier, or study.yaml; fixes are the
  writer's and human's.
- I did not re-fetch the arXiv page; r1 verified the metadata and passage
  against the canonical page, and the new in-tree snapshot now carries the
  passage verbatim at the recorded locator, which I verified directly.
- I did not re-run the experiment; hash equality with the RUN-001-full
  manifest plus r1's byte-identical re-run establishes the artifact is
  unchanged.
