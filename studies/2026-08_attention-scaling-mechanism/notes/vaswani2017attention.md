---
source_key: "vaswani2017attention"
read_date: "2026-08-21"
confidence: "high"
relevance: 3
---

# Notes: Attention Is All You Need

## Source identification

- Key: vaswani2017attention
- Authors, year, venue: Vaswani et al., 2017, NeurIPS
- Tier: peer-reviewed
- URL / DOI: https://arxiv.org/abs/1706.03762

## Method or core idea

Scaled dot-product attention maps queries and key-value pairs to an output as
a weighted sum of values, with weights from a softmax over scaled query-key
dot products (Section~3.2.1):

Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V.

## Key claims with anchors

- Claim 1 (Section~3.2.1): for large d_k, the dot products grow large in
  magnitude, pushing the softmax into regions of extremely small gradients;
  dividing by sqrt(d_k) counteracts this effect. This is the stated
  motivation this study checks under controlled synthetic sampling.

## Evaluation and evidence

The scaling argument (Claim 1) is stated as an analytical motivation in
Section~3.2.1. The paper provides no controlled comparison of scaled versus
unscaled dot-product attention and no ablation isolating the scale factor, so
the mechanism is asserted rather than measured in the source.

## Relevance to the brief

Supplies the framing claim: the authors motivate 1/sqrt(d_k) by the
expectation that unscaled dot products grow with d_k and saturate the softmax.
This study tests exactly that expectation on synthetic query and key vectors.
The note establishes what the paper states so the report can keep the
paper's stated motivation distinct from what the synthetic runs measure.

## Quotables for the report

- "We suspect that for large values of d_k, the dot products grow large in
  magnitude, pushing the softmax function into regions where it has extremely
  small gradients." (Section~3.2.1). Cite as the authors' stated suspicion,
  not as an established measurement.
