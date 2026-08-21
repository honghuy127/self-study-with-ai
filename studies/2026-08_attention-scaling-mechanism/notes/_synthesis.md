# Synthesis: attention logit scaling mechanism check

Cross-note synthesis for `2026-08_attention-scaling-mechanism`. Combines the
reused primary-source framing with the synthetic run outputs. Every claim is
tied to the source note, a run artifact, or a ledgered dossier claim.

## Framing (what the source states)

Vaswani et al. state, without an ablation, that for large `d_k` the dot
products grow large in magnitude and push the softmax into regions of
extremely small gradients, and that dividing by `sqrt(d_k)` counteracts this
(Sec. 3.2.1; `notes/vaswani2017attention.md`, Claim 1; dossier `CLM-001`,
`descriptive`). This study checks that stated mechanism under controlled
synthetic sampling.

## Q1: does scaling normalize logit variance?

Yes, under the stated assumptions. With independent zero-mean unit-variance
coordinates, the unscaled logit standard deviation grows as `sqrt(d_k)`
(measured 2.862, 8.023, 22.570 at `d_k` = 8, 64, 512; theory 2.828, 8.000,
22.627), and dividing by `sqrt(d_k)` holds it near 1 (1.012, 1.003, 0.997).
`CLM-002`, run `RUN-001-full`, `experiments/results/full/summary.json`.

## Q2: does scaling reduce softmax concentration?

Yes. Over 64 keys, unscaled mean max-probability rises with `d_k` (0.428,
0.785, 0.923) and mean entropy falls (2.053, 0.597, 0.193 nats); the scaled
softmax is near constant (max-probability about 0.107, entropy about 3.69
nats). `CLM-003`, run `RUN-001-full`.

## Q3: does scaling prevent gradient attenuation?

Yes, as measured by the softmax Jacobian. The mean Frobenius norm of the
softmax Jacobian for unscaled logits falls with `d_k` (0.2946, 0.2185,
0.0972), toward the saturated limit of 0, while the scaled norm is near
constant (0.1820, 0.1833, 0.1837). `CLM-004`, run `RUN-001-full`. The
Jacobian norm is a proxy for gradient magnitude, not a training gradient.

## Q4: how do relaxed assumptions shift the normalizing scale?

With coordinate standard deviation `sigma`, the unscaled logit standard
deviation is `sqrt(d_k) * sigma^2` (measured at `d_k`=64: 2.001, 7.998,
32.217 for sigma = 0.5, 1.0, 2.0; theory 2.000, 8.000, 32.000), so dividing by
`sqrt(d_k)` alone leaves `sigma^2` (0.250, 1.000, 4.027). The unit-variance
scale is `sqrt(d_k) * sigma_q * sigma_k`. `CLM-005`, run `RUN-001-full`.

## Gaps and boundaries

- All results are on idealized independent Gaussian coordinates. They do not
  establish the behavior of trained Transformers (kept visible per the brief).
- The relaxation arm explores a bounded `sigma` grid and does not model
  learned query/key distributions, which may violate independence and zero
  mean in ways not covered here.
- The primary source provides no ablation; this study supplies a controlled
  synthetic check but not a trained-model ablation.
