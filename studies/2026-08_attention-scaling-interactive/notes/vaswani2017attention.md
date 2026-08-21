---
source_key: "vaswani2017attention"
read_date: "2026-08-22"
confidence: "high"
relevance: 3
---

# Notes: Attention Is All You Need

<!--
SIMULATION: written during the 2026-08-22 simulated-learner pipeline
validation, reusing anchors already verified against arXiv:1706.03762 in the
companion concept and mechanism studies.
-->

## Source identification

- Key: vaswani2017attention
- Authors, year, venue: Vaswani et al., 2017, NeurIPS
- Tier: peer-reviewed
- URL / DOI: https://arxiv.org/abs/1706.03762

## Method or core idea

Scaled dot-product attention maps a query and a set of key-value pairs to an
output as a weighted sum of values, with weights from a softmax over scaled
query-key dot products (Section~3.2.1):

Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V.

Here d_k is the dimensionality of the query and key vectors.

## Key claims with anchors

- Claim 1 (Section~3.2.1): for large d_k the dot products grow large in
  magnitude, pushing the softmax into regions of extremely small gradients;
  dividing by sqrt(d_k) counteracts this effect. Stated as the authors'
  suspicion ("We suspect that for large values of d_k ..."), not demonstrated
  by an ablation.

## Derivation the learner reconstructs (not stated as a proof in the paper)

The paper's footnote supplies the variance sketch: with independent zero-mean
unit-variance query and key coordinates, q . k is a sum of d_k terms each with
variance 1, so Var(q . k) = d_k and std(q . k) = sqrt(d_k); dividing by
sqrt(d_k) gives unit variance. This is the mechanism the learner derives. It
is a derivation under idealized assumptions, distinct from the paper's stated
motivation and from trained-model behavior.

## Boundary for the learner to keep straight

- What the source states: the scaling motivation, as an analytical suspicion
  (Section~3.2.1); no ablation isolates the scale.
- What the derivation adds: the variance mechanism under independent,
  zero-mean, unit-variance coordinates.
- What remains empirically unverified here: the behavior of trained
  Transformers; the companion mechanism study checks the mechanism on
  synthetic vectors only.

## Relevance to the brief

Anchors every link of the concept path: the equation, the variance
derivation, the softmax connection, and the stated-versus-derived-versus-
unverified distinction.

## Quotables

- "We suspect that for large values of d_k, the dot products grow large in
  magnitude, pushing the softmax function into regions where it has extremely
  small gradients." (Section~3.2.1). Cite as the authors' stated suspicion.
