# Transfer practice: changed variances

<!--
SIMULATION: administered and attempted during the 2026-08-22 simulated-learner
pipeline validation. The attempt below is simulated, not the human learner's.
-->

## Problem

Suppose each query coordinate has variance sigma_q^2 and each key coordinate
has variance sigma_k^2, with independence and zero means retained. Derive a
scale that gives the dot product unit variance. Then state why a learned model
may violate the assumptions even if 1/sqrt(d_k) remains useful.

## Simulated attempt (help level none)

Each term q_i k_i has variance E[q_i^2]E[k_i^2] = sigma_q^2 sigma_k^2, since
the coordinates are independent and zero mean (the cross term vanishes). The
d_k terms are independent, so Var(q dot k) = d_k sigma_q^2 sigma_k^2 and
std(q dot k) = sqrt(d_k) sigma_q sigma_k. To get unit variance, divide by
sqrt(d_k) sigma_q sigma_k. The scale that generalizes 1/sqrt(d_k) is therefore
1 / (sqrt(d_k) sigma_q sigma_k), which reduces to 1/sqrt(d_k) when
sigma_q = sigma_k = 1.

Why a learned model may violate the assumptions: learned query and key
coordinates need not have unit variance (initialization, LayerNorm, and
embedding scale set their spread), need not be independent (training can
introduce correlations across coordinates and between q and k), and need not be
exactly zero mean. Even so, 1/sqrt(d_k) stays useful because it removes the
growth with d_k regardless of the constant factor, and common initializations
keep the coordinate variance near a constant, so the leftover sigma_q sigma_k
factor is often close to one.

## Feedback

Correct. The transfer scaling is reconstructed, not recalled, and it correctly
reduces to the familiar form. The assumption-violation answer names variance,
independence, and zero-mean separately and gives the right reason the default
survives. This is the changed-assumptions capability the brief targets. No
correction needed.
