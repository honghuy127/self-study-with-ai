---
id: attention.logit-scaling
question: Why divide attention logits by sqrt(d_k)?
prerequisites: []
source_ids: [vaswani2017attention]
misconceptions:
  - "The factor was measured by the primary paper rather than asserted analytically"
  - "A synthetic mechanism check establishes the behavior of trained Transformers"
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
primary source (as a suspicion, "We suspect that for large values of d_k ..."),
not measured by it; the paper gives no ablation isolating the scale factor.

Source: studies/2026-08_scaled-dot-product-attention (vaswani2017attention,
Section 3.2.1).

## Empirical mechanism check

A controlled synthetic mechanism check confirms the stated mechanism under
idealized sampling. With independent zero-mean Gaussian query and key
coordinates, dividing by sqrt(d_k) holds the logit standard deviation near one
(unscaled grows as sqrt(d_k)), keeps softmax entropy and max-probability
roughly constant as d_k grows (unscaled saturates), and prevents the softmax
Jacobian norm from decaying toward zero (unscaled decays). When the
unit-variance assumption is relaxed to coordinate standard deviation sigma, the
unscaled logit standard deviation is sqrt(d_k) sigma^2 and the scale that
yields unit-variance logits generalizes to sqrt(d_k) sigma_q sigma_k.

Boundary: these results hold on idealized synthetic coordinates and do not
establish the behavior of trained Transformers, which remains an open empirical
question.

Source: studies/2026-08_attention-scaling-mechanism (audited, experimental;
run RUN-001-full, seed 0).
