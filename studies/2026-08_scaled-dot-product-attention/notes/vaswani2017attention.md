---
source_key: "vaswani2017attention"
read_date: "2026-08-19"
confidence: "high"
relevance: 3
---

# Notes: Attention Is All You Need

## Source identification

- Key: vaswani2017attention
- Authors, year, venue: Vaswani et al., 2017, NeurIPS
- Tier: peer-reviewed
- URL / DOI: https://arxiv.org/abs/1706.03762

## Problem and motivation

The paper proposes the Transformer, a sequence-to-sequence architecture that
removes recurrence and convolution in favor of attention mechanisms alone
(Section~1). The motivation is parallelization: recurrence limits the
computation that can run in parallel across sequence positions (Section~1).

## Method or core idea

Attention maps a query and a set of key-value pairs to an output as a weighted
sum of values, with weights from a compatibility function of query and key
(Section~3.2). The Transformer uses scaled dot-product attention:

Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V (Section~3.2.1).

Multi-head attention runs h = 8 parallel attention functions over projected
queries, keys, and values with d_k = d_v = d_model / h = 64, d_model = 512
(Section~3.2.2).

## Key claims with anchors

- Claim 1 (Section~3.2.1): for large d_k, dot products grow large in magnitude,
  pushing softmax into regions of extremely small gradients; dividing by
  sqrt(d_k) counteracts this effect.
- Claim 2 (Section~3.2.1): the two common attention functions are additive
  attention and dot-product (multiplicative) attention; the paper adopts the
  multiplicative form because it is faster and more space-efficient in
  practice, with highly optimized matrix multiplication code.
- Claim 3 (Section~3.2.1): additive attention computes the compatibility
  function with a single-hidden-layer feedforward network, and the two forms
  are theoretically similar in complexity, but dot-product attention needs the
  scaling factor at large d_k to remain competitive with additive attention.

## Evaluation and evidence

Machine translation experiments on WMT 2014 English-to-German and
English-to-French (Section~5 and Table~2) report the Transformer achieving
competitive BLEU scores at lower training cost than prior recurrent and
convolutional models. The gradient argument for scaling (Claim 1) is stated
as an analytical motivation, not validated by an ablation in the paper itself.

## Limitations

The 1/sqrt(d_k) justification is asserted from softmax behavior rather than
demonstrated empirically; the paper provides no controlled comparison of
scaled versus unscaled dot-product attention (Section~3.2.1). The remark that
dot-product attention outperforms additive attention only with scaling is
likewise not accompanied by full numeric support in the paper.

## Relevance to the brief

Directly answers the primary question: the division by sqrt(d_k) exists to
keep dot-product magnitudes in a range where softmax retains usable gradients
(Claim 1). Claim 3 frames the motivation as making the cheaper multiplicative
form viable at large key dimensionality. Left open by the source: empirical
confirmation, which later work would need to supply.

## Quotables for the report

- "We suspect that for large values of d_k, the dot products grow large in
  magnitude, pushing the softmax function into regions where it has extremely
  small gradients." (Section~3.2.1): usable when stating the motivation as the
  authors' stated suspicion, not an established measurement.
