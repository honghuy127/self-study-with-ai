# Brief: Attention logit scaling, a controlled empirical mechanism check

## Mode and dimensions

- Mode: `delegated`
- Intent: `understand`
- Assurance: `audited`
- Methodology: `experimental`
- Deliverables: `report`

## Purpose

The concept study `2026-08_scaled-dot-product-attention` established what
Vaswani et al. state about the `1/sqrt(d_k)` factor and when the derivation
holds, but it deliberately left empirical behavior unverified. This study runs
controlled synthetic experiments to check the proposed mechanism (logit
variance normalization, softmax saturation, gradient magnitude) and states
precisely what the results do and do not establish about trained Transformers.

## Questions

- Primary question: Under controlled sampling of query and key vectors, does
  dividing by `sqrt(d_k)` normalize the variance of attention logits and
  reduce softmax concentration and gradient attenuation, as the standard
  derivation predicts?
- Secondary questions:
  - How closely do measured logit standard deviations match the theoretical
    `sqrt(d_k) * sigma_q * sigma_k` across `d_k` values?
  - How sensitive are softmax concentration and gradient magnitude to the
    scale factor at fixed `d_k`?
  - How does violating the unit-variance, zero-mean assumptions shift the
    scale that normalizes the logits?

## Scope

- In scope: synthetic sampling experiments (numpy, CPU). Independent
  zero-mean Gaussian query and key coordinates at controlled variance.
  `d_k` across a small grid (for example 8, 64, 512). Measurements of logit
  variance and standard deviation, softmax concentration (entropy and max
  probability), and softmax gradient magnitude, each scaled versus unscaled
  and compared against the closed-form prediction.
- Out of scope: training neural networks, loading real model checkpoints,
  end-task accuracy claims, alternative attention variants (linear, sparse),
  and any literature survey beyond the reused primary source.
- Audience: my future self, and anyone reusing
  `shared/knowledge/attention-scaling.md`.

## Budget and stop rules

- Time budget: two agent sessions for experiments plus drafting.
- Source budget: 2 sources. Reuse `vaswani2017attention` from the concept
  study; add at most one new source if the independent review requires a
  named precedent for the mechanism check.
- Compute or spend budget: CPU-only numpy runs, single run under ten minutes
  wall time, no GPU and no external API calls.
- Stop rule: if the synthetic setup cannot separate scaled from unscaled
  behavior cleanly, or if answering the primary question appears to require
  training a real model, stop and re-scope with the human rather than
  expanding the study.

## Human decision points

Between gates the agent may register sources, write anchored notes, run the
approved experiment protocol, and draft the report. Fresh approval is always
required for: changing the questions or scope, exceeding the source or
compute budget, adding any system or dependency, and any claim about trained
Transformer models.

## Prior understanding

- What you already know: the derivation of `Var(q . k) = d_k` under
  independent unit-variance coordinates; the Vaswani stated motivation; the
  distinction between the paper's stated motivation and later interpretation.
  Agents will not re-derive or re-teach this.
- Repos, notes, glossary pages to reuse:
  `studies/2026-08_scaled-dot-product-attention` (registry record
  `vaswani2017attention` and its anchored note),
  `shared/knowledge/attention-scaling.md`, and `shared/glossary.md`.

## Mode-specific contract

### Delegated: research contract

- Report audience: my future self; the audited record is the mechanism-check
  evidence behind the attention-scaling knowledge page.
- Coverage dimensions: (1) logit variance and standard deviation versus
  `d_k`, scaled versus unscaled, versus the closed-form prediction; (2)
  softmax concentration (entropy, max probability) versus scale; (3) softmax
  gradient magnitude versus scale; (4) robustness when the unit-variance or
  zero-mean assumptions are relaxed.
- Required comparisons: a scaled-versus-unscaled column for every measured
  dimension, and a theory-versus-measured row for the logit statistics.
- Source cutoff: reuse the existing 2026-08-20 evidence cutoff; no new web
  sources beyond the declared budget.
- Independent review: required at audited assurance; the reviewer agent
  audits the central claims with fresh context against the run manifests.
- Uncertainty to keep visible: synthetic results do not establish behavior of
  trained Transformers; the assumption-violation regime is explored over a
  bounded grid only.

## Definition of done

Delegated:

- [ ] Every declared deliverable builds clean and passes lint
- [ ] Every material claim traces to an eligible note, evidence record, or run
- [ ] Independent review findings resolved or explicitly accepted
- [ ] Glossary and library.bib merged on completion
