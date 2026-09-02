# Synthesis

This study has no source notes: its evidence is its own runs, recorded in
`.research/`. The synthesis therefore reconciles the two runs against the
derivation the companion study established, and fixes what the report may and
may not say.

## Q1: does unscaled logit variance grow linearly in d_k?

Yes, within sampling error, and the ratios are what linear growth predicts.

| d_k | var, main | var, replication | d_k ratio | measured ratio (main) |
|---|---|---|---|---|
| 8 | 8.0171 | 8.2071 | 1 | 1 |
| 32 | 32.273 | 31.7668 | 4 | 4.03 |
| 128 | 126.703 | 124.0589 | 16 | 15.80 |
| 512 | 506.554 | 511.4883 | 64 | 63.18 |

Claim `claim-variance-linear`, `reported`, backed by `ev-main-results` with
`run-replication-20260902` as the independent check.

## Q2: does the scale hold variance at 1?

Yes, within about 1 percent in the main run and about 3 percent in the
replication. Measured scaled variance: 1.0021, 1.0085, 0.9899, 0.9894 (main);
1.0259, 0.9927, 0.9692, 0.999 (replication). Claim
`claim-scale-normalizes`.

The spread between runs is the honest resolution of this design. Reporting
"exactly 1" would be a fabrication that the second run already contradicts.

## Q3: what happens to the softmax?

Unscaled, concentration climbs sharply with `d_k`: mean largest probability
over 64 keys goes 0.4215, 0.7083, 0.8497, 0.9290. Scaled, it stays near 0.106
at every dimension. Claim `claim-softmax-concentration`.

The nuance the report must keep: 0.106 is not uniform. Uniform over 64 keys is
0.0156, so scaled attention still concentrates roughly seven times more than
chance. The scale stops concentration from growing with dimension; it does not
flatten the distribution.

## What the report must not do

- Not say the gradient story is settled. No gradient was measured. The
  source's suspicion is exactly as untested after this study as before it,
  and `claim-softmax-concentration` carries that caveat.
- Not generalize to trained attention. The generator imposes the independence
  the derivation assumes; a trained model violates it.
- Not report a single run's numbers as if they were exact. Every figure in the
  report comes from `results/main.json`, with the replication cited as the
  spread.

## Gaps

No `[RESULT PENDING]` markers: every number the report states exists in a
committed artifact. The open question, whether the scale matters for the
reason the source suspects, needs a gradient measurement and is out of this
study's declared scope.
