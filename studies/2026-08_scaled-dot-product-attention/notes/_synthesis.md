# Synthesis: Why scaled dot-product attention divides by sqrt(d_k)

Cross-note synthesis for the study. Built only from the per-source notes in
`notes/`; every claim below carries a note reference. This study has one
primary source, so there are no cross-source agreements or conflicts to
resolve.

## Primary question: why scale by 1/sqrt(d_k)?

- The Transformer's attention is softmax(QK^T / sqrt(d_k)) V; the division by
  sqrt(d_k) is the mechanism under study (notes/vaswani2017attention.md,
  Method).
- The source's stated motivation: for large d_k, raw dot products grow large in
  magnitude, pushing softmax into regions of extremely small gradients; dividing
  by sqrt(d_k) counteracts that (notes/vaswani2017attention.md, Claim 1). This
  is asserted by the authors, not demonstrated by an ablation in the paper.
- A secondary motivation: dot-product attention is faster and more
  space-efficient than additive attention via optimized matrix multiplication;
  the scaling is what keeps the cheaper multiplicative form competitive with
  additive attention at large d_k (notes/vaswani2017attention.md, Claims 2-3).

## Secondary question: softmax gradients without scaling

- The note records the paper's gradient argument only as an analytical claim
  (Claim 1); it is labeled the authors' "stated suspicion," not a measurement
  (notes/vaswani2017attention.md, Quotables).
- The source provides no controlled scaled-vs-unscaled comparison and no numeric
  support for unscaled underperformance at large d_k
  (notes/vaswani2017attention.md, Limitations). Empirical confirmation is
  [EVIDENCE NEEDED] and was out of this briefing's search scope.

## Interpretation (flagged, not from the source)

- The standard-deviation reading (a logit sums d_k roughly unit-scale products,
  so dividing by sqrt(d_k) normalizes the growth) is a common interpretation of
  the stated motivation. The note attributes it as an inference, not a sentence
  from the paper (notes/vaswani2017attention.md, Relevance). The report must
  label it as interpretation.

## Gaps

- No ablation of scaled vs. unscaled attention in the primary source
  [EVIDENCE NEEDED].
- Later empirical work confirming or refining the factor is outside the single-
  source scope [CITATION NEEDED].
