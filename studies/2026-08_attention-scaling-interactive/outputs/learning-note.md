# Learning note: why attention divides by sqrt(d_k)

<!--
Distilled AFTER mastery, from the learner's final explanation plus the
evidence packet. Compact, sourced, in the learner's words where possible.

SIMULATION: distilled during the 2026-08-22 simulated-learner pipeline
validation. It reflects the simulated learner's demonstration, not the
human's real mastery.
-->

## The idea, in my own words

Attention scores are query-key dot products. With d_k independent, zero-mean,
unit-variance coordinates, that dot product is a sum of d_k terms each with
variance 1, so its spread grows as sqrt(d_k). Big spreads push the softmax
toward one-hot, where gradients nearly vanish. Dividing by sqrt(d_k) pins the
spread back to 1 so the softmax stays in a region where it can still learn.

## The compact derivation or argument

1. q . k = sum_i q_i k_i.
2. Independence and zero means give Var(q_i k_i) = E[q_i^2]E[k_i^2] = 1.
3. Independent terms add: Var(q . k) = d_k, so std = sqrt(d_k).
4. Divide by sqrt(d_k): variance 1, independent of d_k.
5. Unit-spread logits keep the softmax from saturating, so its gradients stay
   usable (anchored to notes/vaswani2017attention.md, Section 3.2.1).

## Boundary of the source

- The paper states: the scaling motivation, as an analytical suspicion
  ("We suspect that for large values of d_k ..."). It gives no ablation.
- The derivation adds: the variance mechanism under independent, zero-mean,
  unit-variance coordinates.
- Still unverified here: trained-model behavior. The companion mechanism study
  checked the mechanism on synthetic vectors only.

## Misconception to keep in check

Normalization controls the distribution, not every realized value. Dividing by
sqrt(d_k) sets the spread of the logits to 1; a single drawn q, k pair can
still give a logit several sigma from zero. Related: "no big logits" is a
consequence of the scaling, not an assumption going in.

## Transfer rule

With coordinate variances sigma_q^2 and sigma_k^2, the dot-product std is
sqrt(d_k) sigma_q sigma_k, so the unit-variance scale is
1 / (sqrt(d_k) sigma_q sigma_k), reducing to 1/sqrt(d_k) at unit variance.
Learned models can break the unit-variance, independence, and zero-mean
assumptions, but 1/sqrt(d_k) still removes the growth with d_k.

## Links

- Source notes: notes/vaswani2017attention.md
- Mastery record: learning/mastery.md
- Concept map: learning/map.md
