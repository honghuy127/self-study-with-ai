# Brief: Derive and transfer the sqrt(d_k) attention scale

Drafted from the study contract in the since-removed SELF_STUDY_REDESIGN.md
(recoverable from git history). Human-owned: edit any field before approving
the scope gate.

## Mode and dimensions

- Mode: `interactive`
- Intent: `understand`
- Assurance: `grounded`
- Methodology: `source-only`
- Deliverables: `learning-note`

## Purpose

Understand, personally and durably, why scaled dot-product attention
divides by sqrt(d_k): being able to derive it, explain it, and adapt it
when assumptions change, rather than having read a report about it.

## Questions

- Primary question: why does attention scale the query-key dot product by
  1/sqrt(d_k)?

## Scope

- In scope: the variance derivation under the simplified assumptions, the
  softmax saturation connection, and the boundary between what the primary
  source states and what the derivation adds.
- Out of scope: surveying attention-scaling variants, trained-model
  empirical behavior, implementation benchmarks.
- Audience: the learner.

## Budget and stop rules

- Time budget: 75 minutes of tutoring, plus one delayed review.
- Source budget: 2 sources.
- Compute or spend budget: n_a.
- Stop rule: mastery passed, or two consecutive needs-practice verdicts
  prompt a human re-scoping decision.

## Human decision points

The tutor may teach, pose practice, and record attempts between
checkpoints. Fresh approval is needed to: add a second source, change the
mastery criterion, or change the review schedule.

## Prior understanding

- What you already know: baseline attempt recorded 2026-08-21 was fuzzy;
  the learner could not reproduce the equation or the derivation unaided.
- Repos, notes, glossary pages to reuse: the existing
  vaswani2017attention registry record and anchored note from
  studies/2026-08_scaled-dot-product-attention, and
  shared/knowledge/attention-scaling.md. The existing two-page report is
  optional reading only AFTER the baseline, never before.

## Mode-specific contract

### Interactive: learning contract

- Target capability: derive the sqrt(d_k) attention-logit scale from
  explicit variance assumptions, explain its connection to softmax
  saturation, distinguish the paper's stated motivation from later
  interpretation, and adapt the scale when the assumptions change.
- Baseline task: walk through, unaided, why scaled dot-product attention
  divides by sqrt(d_k), flagging fuzzy spots.
- Mastery task: unaided, (1) reconstruct the attention equation and define
  d_k; (2) derive Var(q dot k) and the normalization under unit-variance
  assumptions; (3) explain how logit scale affects softmax concentration
  and gradient magnitude without claiming the paper provides an ablation;
  (4) separate what the paper states, what follows from the simplified
  assumptions, and what remains empirically unverified; (5) solve the
  changed-variance transfer problem.
- Mastery criterion: every capability demonstrated unaided at help level
  none; on any capability not demonstrated, the verdict is needs-practice.
  Fixed before assessment.
- Transfer task: with query coordinate variance sigma_q^2 and key
  coordinate variance sigma_k^2 (independence and zero means retained),
  derive a scale that gives the dot product unit variance, and state why a
  learned model may violate the assumptions even if 1/sqrt(d_k) remains
  useful.
- Review schedule: delayed retrieval 7 days after mastery.

## Definition of done

- [ ] Baseline attempt recorded before any teaching
- [ ] Mastery task completed unaided at help level none and the criterion met
- [ ] Transfer task attempted and recorded
- [ ] Learning note distilled after mastery
- [ ] Delayed review scheduled or explicitly declined
