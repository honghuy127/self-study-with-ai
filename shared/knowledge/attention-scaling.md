---
id: attention.logit-scaling
question: Why divide attention logits by sqrt(d_k)?
prerequisites: []
source_ids: [vaswani2017attention]
misconceptions:
  - "The factor was measured experimentally rather than asserted analytically"
mastery:
  last_assessed: ""
  level: ""
  help: ""
review:
  next_due: ""
superseded_by: ""
---

# Attention scaling

Distilled understanding from finished studies. Agents read relevant pages
here before gathering, to avoid re-learning established results.

## The 1/sqrt(d_k) factor

The Transformer's attention logits are query-key dot products divided by
sqrt(d_k). The primary source's stated motivation: unscaled dot products grow
in magnitude with d_k, pushing softmax toward regions of extremely small
gradients. A standard reading: a logit sums d_k products of roughly unit-scale
quantities, so its standard deviation grows as sqrt(d_k); dividing by
sqrt(d_k) normalizes that growth.

Known evidential status: the motivation is asserted analytically by the
primary source, not measured by it. Later empirical confirmation was outside
the seeding study's scope.

Source: studies/2026-08_scaled-dot-product-attention (vaswani2017attention,
Section 3.2.1).
