# r2: agent review of `report/main.tex` and `slides/main.tex`

Reviewer: adversarial agent (read-only except this file). Date: 2026-08-21.
Basis: full read of `report/main.tex` (1420 lines) and grep-level read of
`slides/main.tex`; 47 notes including `_synthesis-harnesses.md`;
`sources/registry.yaml`, `sources/repos.yaml`, `report/refs.bib`;
`.research/` (state.json, decisions.md, ledgers); `brief.md`;
`reviews/r1-agent.md` and `reviews/r1-response.md`; skill playbooks
(`paper-review-and-rebuttal.md`, `ethics-integrity-and-policy.md`);
full git history search of this repository.

Tool runs (this round):

- `python3 tools/lint_report.py .../report/main.tex` -> `lint clean`
  (exit 0; note: the tool itself emits a SyntaxWarning at
  `tools/lint_report.py:8`, a repo-hygiene nit, not a draft defect).
- `python3 tools/research/audit_research.py --root ...` -> errors=0 warnings=0.
- `python3 tools/verify_pins.py ...` -> PASS x3 (codex af70018, opencode
  d545d8fb dev, claude-code c3d2e35).
- Marker sweep: zero `[CITATION NEEDED]`/`[EVIDENCE NEEDED]`/`[RESULT PENDING]`
  in `report/main.tex` or `slides/main.tex`.

## Verdict: FAIL

Plain statement: the draft and the slides assert, as established fact, a
verification apparatus that does not exist in this repository, in any commit
of its git history, in any stash, or in the working tree. Four
"pre-registered trace experiments" (EXP-PLAN-2026-08-19-v1) with
"59/59 ... 131/131 ... 75/75 ... 35/35 (300 total)" anchor checks, their
"markdown and JSON artifacts", a validation script, a gate report, and a
twelve-claim ANALYZED ledger (`CLM-E1-1a` through `CLM-E4-3a`, with
`CLM-E2-1b` supersession) are all cited as if they exist and as if the
ledger is "preserved in its git history". None of these artifacts has ever
been committed. The only validation artifact that was ever committed
(`studies/2026-08_coding-agent-harnesses/validation-output.txt`, visible at
commit `f1b4fd1`) records the validation script failing to run:
`can't open file '.../validate_anchors.py': [Errno 2] No such file or
directory`. Under the repo's no-fabrication rule, a report that presents
nonexistent verification results in its abstract, contributions, and
Methods is a FAIL. I am not proposing wording to make these claims sound
plausible; they must either be evidenced with real artifacts or removed.

This finding is scoped precisely so the human can judge the remedy. I did
NOT find the system-level findings fabricated: the extraction notes are
detailed and anchored, and every anchor I independently re-verified at the
pinned checkouts held (log below). What is unsupported is the
process-and-validation narrative layered on top of them.

Verdicts per gate (skill vocabulary):

| Gate | Verdict | Basis |
|---|---|---|
| Fabrication check | FAIL | F-r2-1: nonexistent experiments, anchor-check counts, and claim ledger asserted as fact in main.tex and slides; only committed validation artifact records a failed run |
| Claim traceability | FAIL | Same block: abstract (main.tex:53-54), contributions (144-147), Methods (214-229), Table 1 caption and cells (314-327), Limitations (1326-1331), slides frames all cite E1-E4/CLM artifacts that do not exist. Sampled system-level claims trace cleanly to notes (see verified log) |
| Number fidelity | CONDITIONAL | Sampled numbers char-exact against notes and pinned code (log below); F-r2-2 minor miscount of Part II notes |
| Citation honesty | PASS | All 23 cited keys exist in refs.bib; 25 bib entries match registry 1:1 on title/author/year/url/tier; no `rejected` source exists or is cited; aggregate keys codexRepo/opencodeRepo/lmstudioApiDocs registered per the 2026-08-21 decision; codebase entries carry repo key + pinned commit |
| Citation ties and style | PASS | `lint clean` (untied cites, em-dashes, table spacing all checked by tool); spot-reads consistent with American spellings |
| Scope vs brief | PASS | Both parts, three surfaces, three servers, closed-core protocol all covered; vLLM exclusion and LM Studio mirror provenance disclosed |
| r1 fixes | PASS | All 13 r1 dispositions verified in place (log below); F-min-10 resolved by the human-approved dossier backfill |
| Dossier audit | PASS | audit errors=0 warnings=0; 47 evidence records; empty claims/experiments ledgers documented in decisions.md |
| Pin verification | PASS | verify_pins PASS x3 |
| Waiver revisit condition | NOT_ASSESSED (partial) | decisions.md waiver stands unless a report claim depends on a marked gap; Limitations "Open cells" paragraph mirrors the gap register, but a full marker-by-marker sweep was not completed this round because the FAIL supersedes it |
| Deep re-read of remaining ~30 notes | NOT_ASSESSED | Stopped at the FAIL per the no-fabrication rule; sampled dimensions (literature, turn loops, tools, synthesis cross-check) verified |

## Findings

Severity: `blocker` must be fixed before sign-off, `major` should be fixed,
`minor` at writer's discretion.

| id | sev | location | issue | next decisive action |
|---|---|---|---|---|
| F-r2-1 | blocker | report/main.tex:53-54 (abstract "300 anchors re-verified"), 144-147 (contributions "four pre-registered static-trace extractions ... whose anchors all re-verify"), 214-229 (Methods "Part I trace experiments": EXP-PLAN-2026-08-19-v1, "59/59 ... 300 total", "all three HEADs matched the pins at every validation", "Twelve claims advanced to ANALYZED ... CLM-E2-1b ... The claim ledger lived in the Part I study's dossier and is preserved in its git history"), 314-316 (Table 1 caption "E1 to E4 are the trace experiment artifacts"), 324-327 (summary-table anchor cites "(E1, ...)" ... "(E4, ...)"), 478 ("outside E2 scope"), 1326-1331 (Limitations "The validation runs re-check anchors"); slides/main.tex:160-175 ("Trace experiments and anchors" frame with the 59/59, 131/131, 75/75, 35/35, 300/300 table), 211, 247, 269, 302 (frame titles tagged E1/E2/E4/E3), 596-597 (CLM ledger claim) | The cited apparatus does not exist. Git history search across all refs: `studies/2026-08_coding-agent-harnesses/` first appears at commit f1b4fd1 already in cleaned knowledge-core form (brief, notes, report, slides, sources, study.yaml, validation-output.txt only). No `.research/`, no `experiments/`, no `gate-report.md`, no `validate_anchors.py`, no claims ledger, no reviews/ were ever committed for that study; `git stash list` empty; `git fsck --dangling` empty; working tree contains no such files; `.gitignore` does not exclude them. `CLM-E2-1b` appears in history only inside the post-merge prose that cites it (_synthesis-harnesses.md, main.tex, slides). The committed validation-output.txt records a failed run. The harness study.yaml at f1b4fd1 likewise asserts `dossier: .research/`, `experiments_approved: true`, `review_signed_off: true`, `last_gate_verdict: PASS (review stage, reviews/r2-agent.md, 2026-08-20)` while no such review or dossier was ever committed, so the "done + cleaned, all gates passed" provenance in this study's merged_from note is itself unverifiable. Additionally, this study's own `.research/decisions.md` (2026-08-21 backfill) states "claims.jsonl and experiments.jsonl stay empty: this study ran no experiments, and report claims were never ledgered", which directly contradicts main.tex:223-228. | HUMAN DECISION, then writer. (1) If the E1-E4 plan, artifacts, gate report, and claim ledger genuinely exist outside this repo, the human must commit them where the draft says they are and the false "preserved in its git history" sentence must be corrected to the true location; review resumes after. (2) If they do not exist, the writer must delete or rewrite every location above to state only what is evidenced: per-component extraction notes whose claims carry file:line anchors, with re-verification evidence limited to what actually exists (this r2 review's independent anchor spot checks at the pinned commits, logged below, are real and can be cited as such). Do not flip `review_signed_off` either way until (1) or (2) is done. |
| F-r2-2 | minor | report/main.tex:243 ("its 12 notes (3 codebase, 8 documentation, 1 context)") | Count disagrees with the registry: Part II has 3 codebase notes (codexOssProviders, opencodeOssProviders, opencodeModelGating), 7 distinct documentation notes (claudeCodeModelDocs, claudeCodeBedrockDocs, ollamaCompatDocs, lmstudioServerDocs, lmstudioCompatToolsDocs, lmstudioCompatResponsesDocs, llamaCppServerDocs; lmstudioApiDocs is the aggregate entry pointing at lmstudioServerDocs, not an eighth note), and 1 context note (claudeCodeRouterContext): 11. r1 verified "3 codebase, 7 documentation, 1 context" as exact at the same Methods location. | Writer: restore "11 notes (3 codebase, 7 documentation, 1 context)" or register the intended eighth documentation note. |

## Verified-clean log (so the human can scope the remedy)

Independent anchor re-verification at the pinned checkouts
(`/Users/hong.huy.nguyen/Work/Code/references/coding-agents/{codex,opencode,claude-code}`,
verify_pins PASS x3):

1. codex `protocol/src/protocol.rs:543`: `pub enum Op` with exactly 27
   variants (enumerated). Matches main.tex:353, 396, 411-412 and
   _synthesis-harnesses.md line 20.
2. codex `protocol/src/turn_input.rs:182`: `pub enum NotSubmittedReason`.
   Matches main.tex:400 ("turn_input.rs:182-208").
3. codexTurnLoop note cross-check: `needs_follow_up` expression
   (session/turn.rs:405), 4 `TurnAbortReason` variants, 3 `TaskKind`
   variants, spawn preemption with `Replaced` (tasks/mod.rs:279-288),
   8-variant rejection taxonomy, rollover mid-turn compaction
   (ContextLimit, MidTurn), stream retry defaults (5/4, 200 ms, factor 2).
   All match draft Table 1, Table 2, and Section "Turn loops" prose.
4. opencodeSessionLoop note cross-check: `while (true)` at prompt.ts:1088;
   exit condition prompt.ts:1106-1130; verdict `compact|stop|continue` at
   processor.ts:30; `DOOM_LOOP_THRESHOLD = 3` at processor.ts:29 with
   default action `ask`; `RETRY_MAX_RETRIES = 5`, initial 2000 ms, factor 2
   at retry.ts:26-31; `continue_loop_on_deny` escape; soft `steps` cap.
   All match draft Table 2 and Figure 2.
5. codexToolsPatch note cross-check: shell defaults 10 s / 1 MiB / 10,000
   deltas (exec.rs:61,75-83); unified exec yield 10 s clamped 250-30_000,
   300 s background, 64 processes (unified_exec/mod.rs:66-75); 19-line
   apply_patch.lark; apply_patch gated on `apply_patch_tool_type.is_some()`
   (spec_plan.rs:1112-1116). All match draft Table 3 shell-defaults row
   and Section "Tool surfaces" prose.
6. Literature numbers against notes: SWE-bench Lite 11.0 -> 18.0 (shell-only
   vs SWE-agent, GPT-4 Turbo); ablation drops 7.7 (no edit) and 3.0 (no
   lint); iterative search 12.0 < no search 15.7; 51.7% instances with a
   failed edit; edit-success 90.5% -> 57.2% (yang2024sweagent note Claims
   2, 4, 5). ReAct hallucination 56% (CoT) vs 0% (ReAct) of failures on
   HotpotQA (yao2023react note Claim 6). Toolformer at-most-one-API-call
   decoding restriction (schick2023toolformer note, decoding paragraph).
   All char-exact against the notes' page anchors.
7. Compaction numbers in draft Table 4 cross-checked against
   _synthesis-harnesses.md line 22 and the two compaction notes' anchor
   lists (9/10 of 95% window; 20,000 user-message cap; 64,000/10,000/2
   remote; min(20,000, maxOutputTokens) reserve; PRUNE_PROTECT 40,000;
   PRUNE_MINIMUM 20,000; 2,000 chars; clamp(25%, 2,000..15,000); chars/4).
   Consistent.

r1 disposition check (all 13 verified present in the current draft):
F-maj-1 hedge at main.tex:976-981 plus Limitations paragraph 1364-1375;
F-min-1 pin-date fix at main.tex:195-196 and refs.bib note fields
("pinned 2026-08-19, re-pinned 2026-08-20"); F-min-2 version-gate
exceptions at 961-966 and matrix cell 1090; F-min-3 at 980-982; F-min-4 at
1024-1027; F-min-5 at 973-974; F-min-6 at matrix cell 1091; F-min-7 at
1029-1034; F-min-8 at 882; F-min-9 at 62-67 vs 944-946 (now consistent);
F-min-11 quote exact at 1055-1056; F-min-12 full condition at 1056-1059
plus v1-path attribution 1020-1023 and Limitations 1372-1375; F-min-13 at
1044-1046; F-min-10 resolved by the human-approved dossier backfill
(decisions.md 2026-08-21, audit now clean).

Citation check: 23 distinct keys cited; all present in refs.bib; bib
entries match registry entries 1:1 on metadata; aggregate keys registered
(EVD-045..EVD-047 per decisions.md); no rejected sources anywhere in the
registry; blog-tier sources (minusXClaudeCodeTeardown, tenguDecoded,
agiflowClaudeCodeInternals, claudeCodeRouterContext) used only in hedged
context positions (main.tex:211-212, 252, 524-526, 1070-1072, 1307-1315,
1348-1352), never filling a matrix cell.

## Next decisive action

1. Human decides F-r2-1 branch (1) produce and commit the real artifacts,
   or (2) they do not exist and the writer strips the validation narrative.
2. If branch (2): writer removes/rewrites the abstract clause, the
   contributions bullet, the Methods "Part I trace experiments" paragraph,
   the E1-E4 anchor citations in Table 1, the "outside E2 scope" cell, the
   Limitations sentence about validation runs, and slides frames
   "Trace experiments and anchors" plus the E1-E4 frame tags and the CLM
   sentence; F-r2-2 note count fixed in the same pass; re-run
   `tools/lint_report.py`.
3. Either branch: `review_signed_off` stays false; no sign-off until the
   human has seen the corrected draft (or the produced artifacts) and a
   follow-up review pass.
