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
