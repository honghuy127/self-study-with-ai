---
source_key: "vaswani2017attention"
read_date: "2026-08-04"
confidence: "high"
relevance: "3"
---

# Notes: Attention Is All You Need

## Source identification

- Key: vaswani2017attention
- Authors, year, venue: Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez,
  Kaiser, Polosukhin, 2017, Advances in Neural Information Processing Systems
  30
- Tier: peer-reviewed
- URL / DOI: https://arxiv.org/abs/1706.03762

## Problem and motivation

The paper introduces an architecture built entirely from attention, removing
recurrence and convolution (Section~1). The scaling factor is a small
implementation detail inside that architecture, introduced in the definition
of the attention operation itself (Section~3.2.1), not as a contribution the
paper foregrounds.

## Method or core idea

Scaled dot-product attention computes the compatibility of a query with every
key as a dot product, divides each result by the square root of the key
dimension, and passes the result through a softmax to weight the values
(Section~3.2.1, Equation~1). The divisor is the square root of `d_k`, the
dimension of the keys, which for multi-head attention is the per-head
dimension rather than the full model width (Section~3.2.2).

The paper distinguishes its variant from two established forms of attention
(Section~3.2.1): additive attention, which computes compatibility with a
feed-forward network with a single hidden layer, and unscaled dot-product
attention. It states that the two are similar in theoretical complexity,
while dot-product attention is faster and more space-efficient in practice
because it can be implemented with highly optimized matrix multiplication
code.

## Key claims with anchors

- Claim 1 (Section~3.2.1, Equation~1): attention is defined with the logits
  divided by the square root of `d_k` before the softmax.
- Claim 2 (Section~3.2.1): for small values of `d_k` the two mechanisms
  perform similarly, but additive attention outperforms dot-product attention
  without scaling for larger values of `d_k`. This is the empirical
  observation the scaling is introduced to address.
- Claim 3 (Section~3.2.1, footnote 4, p. 4): the variance argument. If the
  components of the query and the key are independent random variables with
  mean 0 and variance 1, their dot product has mean 0 and variance `d_k`.
  Dividing by the square root of `d_k` returns that variance to 1.
- Claim 4 (Section~3.2.1): the paper *suspects* that for large `d_k` the dot
  products grow large in magnitude, pushing the softmax into regions where it
  has extremely small gradients, and it scales the logits to counteract this.
  The hedge is the paper's own word, not this note's softening.

## Evaluation and evidence

The paper reports no ablation isolating the scaling factor. There is no table,
figure, or number in it that measures the scaled variant against the unscaled
one; the support offered is the variance calculation in footnote 4 plus the
qualitative statement in Claim 2 about additive attention outperforming
unscaled dot-product attention at larger `d_k`. Anyone wanting a measured
effect size for this specific choice will not find one here.

## Limitations

- The gradient consequence is a stated suspicion, not a demonstrated result
  (Section~3.2.1). The paper offers no measurement of softmax gradient
  magnitude at any `d_k`.
- The variance argument assumes independent components with mean 0 and
  variance 1 (footnote 4). Learned queries and keys are not independent and
  are not unit variance, so the argument establishes a scale, not a guarantee
  about trained models.
- `d_k` in the formula is the per-head key dimension (Section~3.2.2), which is
  easy to conflate with the model dimension when reading the equation alone.

## Relevance to the brief

This settles the primary question at the level the brief asked for: the
divisor is the square root of `d_k` because that is exactly what normalizes
the variance of a sum of `d_k` independent unit-variance products back to 1,
which is Claim 3. It also settles the secondary question, and the answer is
uncomfortable: the causal story everyone repeats, saturated softmax and
vanishing gradients, is Claim 4, which the paper marks as a suspicion. The
distinction between the derivation (solid, under stated assumptions) and the
mechanism story (conjectured) is the most valuable thing in this note.

What it leaves open: whether the softmax gradient story is actually correct,
and how the scale behaves once the independence assumption fails in a trained
model. Answering either needs a study with an `experimental` methodology.

## Quotables for the report

- Footnote 4's assumption and conclusion, paraphrased with its locator, for
  the derivation section. Frame it as "under the paper's stated assumptions",
  never as a property of trained attention.
- The "we suspect" hedge in Section~3.2.1, quoted as a hedge. If the report
  states the gradient mechanism without that framing, it strengthens the
  source, which the reviewer should catch.
