# Research Decisions

Append material decisions with evidence, alternatives, rationale, owner, and revisit condition.

## DEC-20260820T213337Z-90dd3d2b: Initialize research dossier (2026-08-20T21:33:37+00:00)

- Evidence:
  - Project root inspected: /Users/hong.huy.nguyen/Work/Code/self-study-with-ai/studies/2026-08_coding-agents-harnesses-and-open-models
- Alternatives considered:
  - Continue without a dossier
- Rationale: Start traceable project state without overwriting project artifacts.
- Consequences:
  - Canonical research state will be indexed under .research/
- Owner: Huy H. Nguyen
- Revisit condition: Reconcile or retire the dossier if it no longer reflects the project artifacts.

## 2026-08-21 Retroactive dossier backfill (repo audit)

- Decision: initialize this dossier after the fact and backfill evidence.jsonl
  from the 44 registry entries, one record each (EVD-001..EVD-044 in registry
  order).
- Evidence: sources/registry.yaml; sources/repos.yaml pins (claude-code
  c3d2e35, codex af70018, opencode d545d8f); repo audit of 2026-08-21 found a
  depth: full study with no dossier, so the audit gate skipped it.
- Alternatives: downgrade depth to briefing; or a human audit_waiver. The
  human chose retroactive creation.
- Rationale: restores structural traceability for the gathering stage without
  fabricating any analysis state. claims.jsonl and experiments.jsonl stay
  empty: this study ran no experiments, and report claims were never ledgered;
  claim traceability for the draft remains the /review stage's job.
- Id scheme: fresh EVD-001.. numbering. Historical EVD-* references in notes
  (e.g. EVD-022 in notes/codexDocsSandboxing.md) and in registry snapshot
  fields point at the pre-merge dossiers, recoverable from git history of
  2026-08_coding-agent-harnesses and 2026-08_open-source-model-compat.
- Owner: Huy H. Nguyen (human decision at audit; recorded by the audit agent).
- Revisit condition: if the /review stage ledgers report claims, link them to
  these evidence ids.

## 2026-08-21 refs.bib to registry key alignment (repo audit, item 1)

- Decision: rename 11 drifted bib keys to their registry keys
  (word-order and short renames, e.g. claudeCodeHooksDocs to
  claudeCodeDocsHooks, claudeCodeSurface to claudeCodePluginSurface), and
  register the three deliberate aggregate citation keys (codexRepo,
  opencodeRepo, lmstudioApiDocs) as explicit aggregate entries in
  sources/registry.yaml, EVD-045..EVD-047.
- Evidence: refs.bib note fields already listed the constituent note keys;
  the registry had no matching entries, leaving bib keys untraceable.
- Alternatives: re-point every aggregate cite (48 sites) to component keys.
  Rejected for this pass: per-cite attribution is writer-stage semantic work
  on a gated draft; the aggregate entries preserve the report as written.
- Revisit condition: at /review, the reviewer may still re-point individual
  aggregate cites to component keys where a claim is subsystem-specific.
- Owner: Huy H. Nguyen (human directed the revision at audit).

## 2026-08-21 Human waiver of residual note-level markers (repo audit)

- Decision: accept the ~23 remaining [CITATION NEEDED] / [EVIDENCE NEEDED]
  markers in notes/ as documented gaps. They are statically unresolvable:
  server-side production values (Codex models catalog and ModelInfo fields,
  remotely-managed feature overrides), closed-core behavior (Claude Code
  loader and gateway wire shape), live-service content (models.opencode.ai
  catalog), and sources whose snapshots were dropped at the pre-merge
  cleanup (Toolformer paper figures, minusX teardown metadata, Claude Code
  plugins-reference deferrals).
- Evidence: each marker records what was searched; the report asserts none
  of the marked facts (report lint clean); seven sibling markers were
  resolved the same day (stream:true proof, absence conversions,
  compaction-path wiring).
- Alternatives: runtime compatibility tests or web re-fetching, both out of
  the brief's static-trace scope.
- Owner: Huy H. Nguyen (human disposition at repo audit, recorded by the
  audit agent).
- Revisit condition: waiver stands unless /review surfaces a report claim
  that depends on a marked gap.

## 2026-08-21 Human sign-off overruling review r2 blocker

- Decision: treat the r2 review as PASS and sign off. The human overrules
  F-r2-1 (validation apparatus never committed to git) on the ground that
  the study was carefully reviewed before the pre-merge cleanup, when the
  artifacts existed in the working tree. F-r2-2 (note count 12 vs 11) is
  likewise accepted as is.
- Evidence: reviews/r2-agent.md (verdict FAIL, one blocker; system findings
  independently re-verified at the pinned checkouts and held); this file's
  2026-08-21 marker waiver; the pre-merge round r1-agent.md and the
  merged_from record in study.yaml (original study done and cleaned with
  all gates passed).
- Consequence: the report's validation narrative (EXP-PLAN-2026-08-19-v1,
  300/300 anchor counts, CLM ledger "preserved in its git history") stands
  as reviewed-and-accepted content even though the underlying artifacts are
  not recoverable from this repository. Any future claim relying on those
  artifacts must re-derive them.
- Owner: Huy H. Nguyen (human disposition; recorded by the audit agent).
- Revisit condition: if the study is reopened or the narrative is ever
  corrected, supersede this entry.
