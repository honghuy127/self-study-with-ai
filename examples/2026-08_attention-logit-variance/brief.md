# Brief: attention logit variance

## Mode and dimensions

- Mode: `delegated`
- Intent: `understand`
- Assurance: `audited`
- Methodology: `experimental`
- Deliverables: `report`

## Purpose

The companion study `2026-08_scaled-dot-product-attention` established, from
the source's own argument, that `1/sqrt(d_k)` is the variance normalizer for a
dot product of independent unit-variance components. That is a derivation
under stated assumptions and the source measures none of it. This study
measures it, so the repository holds one worked example of the audited,
experimental path rather than only source-grounded ones.

## Questions

<!-- intent: understand. explain a mechanism from first principles; the answer is a derivation or causal account. -->
- Primary question: under the assumptions the derivation makes, does the
  variance of unscaled attention logits actually grow linearly in `d_k`, and
  does dividing by `sqrt(d_k)` actually hold it at 1?
- What would count as understanding it: being able to say what the scale
  fixes, what it does not fix, and how far the measured numbers sit from the
  idealized ones.
- Secondary questions: what happens to softmax concentration across `d_k` with
  and without the scale, and whether the concentration story the source
  suspects is settled by this kind of measurement.

## Scope

- In scope: synthetic queries and keys with independent standard-normal
  components, at `d_k` in 8, 32, 128, 512; logit variance and softmax
  concentration over a fixed number of competing keys.
- Out of scope: trained models, gradient magnitudes, alternative
  normalizations, and any claim about downstream task quality. The
  independence assumption is imposed here, so nothing measured transfers to a
  trained attention layer without further work.
- Audience: my future self, and anyone who wants to see what the audited
  experimental path looks like end to end.

## Budget and stop rules

- Time budget: one session
- Source budget: 0, deliberately. See the registry's provenance note.
- Compute or spend budget: CPU only, minutes, no paid services
- Stop rule: stop once one full measurement run and one independent
  replication at a different seed agree on the direction and rough magnitude.
  Chasing tighter error bars would not change any conclusion the brief asks
  for.

## Human decision points

Agents may implement, run, and draft between checkpoints. Adding a dimension
beyond the declared set, changing the sampling design after seeing results, or
making any claim about trained models requires fresh approval. Selecting a
favorable seed after the fact is out of bounds and would invalidate the study.

## Prior understanding

- What you already know: the derivation and its assumptions, recorded in
  `examples/knowledge/attention-scale.md`. This study does not re-derive it.
- Repos, notes, glossary pages to reuse: `attention.scale` in the shipped
  knowledge base.

## Mode-specific contract

### Delegated: research contract

- Report audience: myself, and readers of this repository
- Coverage dimensions: measured variance with and without the scale, softmax
  concentration with and without it, and the gap between the measured and
  idealized values
- Required comparisons: unscaled against scaled at each `d_k`
- Source cutoff: n_a, this study cites no external sources
- Independent review: required at audited assurance
- Uncertainty to keep visible: sampling error between the two runs, the fact
  that the scaled softmax is not uniform, and the fact that no gradient was
  measured so the source's suspicion remains untested

## Definition of done

Delegated:

- [x] Every declared deliverable builds clean and passes lint
- [x] Every material claim traces to an eligible note, evidence record, or run
- [x] Independent review findings resolved or explicitly accepted
- [x] Glossary and library.bib merged on completion
