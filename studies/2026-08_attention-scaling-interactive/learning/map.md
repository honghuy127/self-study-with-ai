# Concept map

<!--
Tutor-authored, updated as the session progresses. The route the learning
takes, not a transcript of it.

SIMULATION: authored during the 2026-08-22 simulated-learner pipeline
validation. The baseline it plans from is the human's real attempt; the
downstream teaching, practice, and mastery records appended in this run are
simulated, not a genuine human performance.
-->

## Target capability

Derive the sqrt(d_k) attention-logit scale from explicit variance
assumptions, explain its connection to softmax saturation, distinguish the
paper's stated motivation from later interpretation, and adapt the scale when
the assumptions change.

## Prerequisites

- Dot product as a sum of coordinate products: shaky (needed the completed
  chain twice in the scaffolded session).
- Variance of a sum of independent terms: shaky -> landed with scaffolding.
- Independence split E[XY] = E[X]E[Y] for zero-mean coordinates: shaky; the
  learner could not explain it back unaided.
- Softmax concentration and derivative behavior: shaky; underestimated how
  fast the softmax concentrates ("half the mass").

## Concept path

1. Dot product q . k is a sum of d_k coordinate products q_i k_i.
2. For independent zero-mean unit-variance coordinates, Var(q_i k_i) = 1.
3. Variance of the sum is d_k, so std(q . k) = sqrt(d_k).
4. Dividing by sqrt(d_k) pins the logit variance to 1, independent of d_k.
5. Large-magnitude logits concentrate the softmax (max-prob toward 1, entropy
   toward 0) and shrink its gradients; normalization keeps logits in a usable
   range.
6. Separate what Vaswani et al. state (an analytical suspicion) from what the
   derivation adds (the variance mechanism) from what remains empirically
   unverified (trained-model behavior).

## Likely misconceptions

- "No big logits" treated as an assumption rather than a consequence: the
  small-logit behavior follows from the normalization, it is not assumed.
  Surfaced in the scaffolded session; corrected there.
- Normalization controls the distribution, not every realized value: dividing
  by sqrt(d_k) sets the spread of the logit distribution; an individual
  realized logit can still be large. Needs practice.
- Softmax concentration underestimated: the learner expected a gentler effect
  ("half the mass"); the concentration is sharp once logit spread exceeds a
  few units.

## Transfer task

With query coordinate variance sigma_q^2 and key coordinate variance sigma_k^2
(independence and zero means retained), derive a scale that gives the dot
product unit variance, and state why a learned model may violate the
assumptions even if 1/sqrt(d_k) remains useful.
