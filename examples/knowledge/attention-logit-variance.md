---
id: attention.logit-variance
question: What does the sqrt(d_k) scale actually do to logit variance and softmax
  concentration, measured rather than derived?
prerequisites:
- attention.scale
source_ids: []
misconceptions:
- 'Scaled attention is roughly uniform: measured mean largest probability over 64
  keys is about 0.106, roughly seven times the uniform 0.0156.'
- 'Measuring concentration settles the gradient story: no gradient was measured, so
  the source''s suspicion is exactly as untested as before.'
- 'The measurement says something about trained attention: the generator imposes the
  independence a trained model violates.'
tags:
- transformers
- attention
- normalization
- measurement
studies:
- 2026-08_attention-logit-variance
mastery:
  last_assessed: ''
  level: ''
  help: ''
review:
  next_due: ''
superseded_by: ''
---

# Measured behavior of the sqrt(d_k) scale

Distilled from `2026-08_attention-logit-variance`, the audited experimental
study that measured what [[attention.scale]] derives. Read that unit first:
this one adds calibration, not the mechanism.

## Answer

Under the derivation's own assumptions, the algebra holds and the measurement
adds three things it could not tell you.

Unscaled logit variance tracks `d_k`: measured 8.02, 32.27, 126.70, 506.55 at
`d_k` = 8, 32, 128, 512, ratios of 4.03, 15.80, 63.18 against the predicted 4,
16, 64. Scaling holds variance near unity: 1.0021, 1.0085, 0.9899, 0.9894,
within 1.1 percent, though an independent replication at a different seed
spread to 3.1 percent. "Approximately 1" is the honest phrasing; "exactly 1"
is contradicted by the second run.

Softmax concentration over 64 competing keys is where the interesting result
sits. Without the scale the mean largest probability climbs 0.4215, 0.7083,
0.8497, 0.9290 as `d_k` grows. With it, the value is flat near 0.106 at every
dimension. So the scale stops concentration growing with dimension; it does
not make attention diffuse, since 0.106 is about seven times the uniform
0.0156.

## Evidence

- `.research/claims.jsonl` in `2026-08_attention-logit-variance`:
  `claim-variance-linear`, `claim-scale-normalizes`,
  `claim-softmax-concentration`, all `reported` and `supported`.
- `experiments/logit-variance/results/main.json` (run `run-main-20260902`,
  seed 20260901) and `results/replication.json` (run
  `run-replication-20260902`, seed 771244), both content-hashed in their run
  manifests.

## Evidential limits

The generator imposes the independence and unit variance the derivation
assumes, so nothing here transfers to trained attention. Sampling error shows
in the third significant figure and the two runs differ by up to 2.4 percent
on unscaled variance. No gradient was measured, so the mechanism the original
source suspects, that unscaled logits push the softmax into a small-gradient
region, is still untested. Concentration rising with `d_k` is consistent with
that story without establishing it.

The replication is a second seed, not an independent implementation. It
catches sampling flukes, not a design error.
