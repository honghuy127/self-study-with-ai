# Experiment plan: logit variance under the sqrt(d_k) scale

Frozen before the claim-eligible runs, as audited assurance requires. Nothing
below was changed after seeing results; the record of what actually ran is in
`.research/runs/`.

## Hypothesis

Under the derivation's own assumptions (query and key components independent,
mean 0, variance 1), the variance of the unscaled dot product equals `d_k`,
and dividing by `sqrt(d_k)` yields variance 1 at every `d_k`.

## Design

- `d_k` in 8, 32, 128, 512. Four points spanning two orders of magnitude is
  enough to distinguish linear growth from anything else the eye would confuse
  it with.
- 20000 independent query and key pairs per dimension for the variance
  measurement.
- 2000 softmax rows of 64 competing keys per dimension for the concentration
  measurement.
- Inputs drawn from `random.gauss(0, 1)`, which imposes the assumption rather
  than testing it. That is the point: the claim under test is conditional on
  the assumption.

## Metrics

- Population variance of the unscaled logits, and of the logits after dividing
  by `sqrt(d_k)`.
- Mean of the largest softmax probability per row, with and without the scale,
  against the uniform baseline of 1/64 = 0.0156.
- Mean and maximum absolute logit, as a sanity check on the sampler.

## Controls

- The scaled and unscaled figures come from the same sampled dot products, so
  the comparison is not confounded by sampling differences.
- One code path, one seed per run. The seed fully determines the output, so
  the JSON artifact is reproducible byte for byte.

## Failure criteria

- Unscaled variance not tracking `d_k` within sampling error would contradict
  the hypothesis outright.
- Scaled variance drifting systematically with `d_k` would mean the scale is
  not the right normalizer.
- Either outcome gets reported as measured. No rerun-until-it-looks-right.

## Cheapest decisive falsifier

The `d_k = 8` against `d_k = 512` contrast on unscaled variance. If the ratio
is not near 64, nothing else in the design matters.

## Independent check

A second full run at a different seed (`run-replication-20260902`), used as the
verification run for every reported claim. Agreement between two seeds is a
weak check by design: it catches sampling flukes and nondeterminism, not a
mistake in the design itself, which is what the human review is for.

## What this cannot support

Any statement about trained attention, about gradients, or about downstream
quality. The generator imposes the independence the derivation assumes, so the
measurement is a check on the algebra, not on a model.
