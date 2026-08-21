# Near practice: standard deviation before and after scaling

<!--
SIMULATION: administered and attempted during the 2026-08-22 simulated-learner
pipeline validation. The attempt below is simulated, not the human learner's.
-->

## Problem

Let every coordinate of q and k be independent, zero mean, and unit variance.
For d_k = 64, derive the standard deviation of q dot k before and after
division by sqrt(d_k). Explain what is and is not guaranteed about any
individual realized logit.

## Simulated attempt (help level none)

q dot k = sum over i of q_i k_i. Each term has Var(q_i k_i) = E[q_i^2]E[k_i^2]
= 1 * 1 = 1 because the coordinates are independent and zero mean, so the cross
term E[q_i k_i] = 0. The terms are independent, so variances add:
Var(q dot k) = 64, std = 8. After dividing by sqrt(64) = 8, the std is 8/8 = 1.

What is guaranteed: the spread (standard deviation) of the logit distribution
is pinned to 1, independent of d_k. What is not guaranteed: no individual
realized logit is bounded. A drawn q, k pair can still produce a logit several
standard deviations from zero; the scaling controls the distribution, not each
realized value.

## Feedback

Correct. The variance-of-a-sum step and the independence factorization are both
supplied unaided, and the distribution-versus-realized-value distinction is
stated without a prompt. This was the exact misconception flagged in the map,
and it is now held. No correction needed.
