---
id: attention.scale
question: Why are dot-product attention logits divided by the square root of the key
  dimension?
prerequisites: []
source_ids:
- vaswani2017attention
misconceptions:
- 'The saturated-softmax story is established: the source marks it as a suspicion
  and measures nothing.'
- '`d_k` is the model width: in multi-head attention it is the per-head key dimension.'
- 'The variance argument describes trained attention: it assumes independent unit-variance
  components, which learned queries and keys are not.'
tags:
- transformers
- attention
- normalization
studies:
- 2026-08_scaled-dot-product-attention
mastery:
  last_assessed: ''
  level: ''
  help: ''
review:
  next_due: ''
superseded_by: ''
---

# The sqrt(d_k) scale in dot-product attention

Distilled from the delegated study `2026-08_scaled-dot-product-attention`.
This is what a finished study leaves behind: the study's evidence chain was
packed away at cleanup, and this page is what stays reachable.

## Answer

Dividing by `sqrt(d_k)` is the factor that normalizes the variance of the
logits. Under the assumptions the source states, a dot product of two
`d_k`-dimensional vectors whose components are independent with mean 0 and
variance 1 has mean 0 and variance `d_k`. Variance grows linearly in the
number of summed terms, so the standard deviation grows as `sqrt(d_k)`, and
dividing by it returns the logits to unit variance. No other function of
`d_k` does that.

The causal story usually told alongside it, that unscaled logits saturate the
softmax into a region of vanishing gradients, is a conjecture in the source,
not a result. Knowing which half is derived and which half is suspected is
the whole point of this page.

## Evidence

- `vaswani2017attention`, Section 3.2.1, Equation 1: the definition, with the
  logits divided by `sqrt(d_k)` before the softmax.
- `vaswani2017attention`, Section 3.2.1, footnote 4 (p. 4): the variance
  calculation, with its independence and unit-variance assumptions stated.
- `vaswani2017attention`, Section 3.2.1: additive attention outperforms
  unscaled dot-product attention for larger `d_k`, which is the comparative
  observation motivating the scale, and the authors write that they *suspect*
  the small-gradient mechanism behind it.
- `vaswani2017attention`, Section 3.2.2: `d_k` is the per-head key dimension.

## Evidential limits

One source, no experiment. The paper reports no ablation isolating the
scaling factor, no gradient-magnitude measurement, and no effect size, so
nothing here supports a quantitative claim about what unscaled attention does
in practice. The variance argument holds only under its assumptions, which
trained queries and keys violate: it fixes a scale, it does not guarantee a
property of a trained model.

Two questions stay open and need an `experimental` study to close: whether the
gradient conjecture is correct, and how the scale behaves once independence
fails.
