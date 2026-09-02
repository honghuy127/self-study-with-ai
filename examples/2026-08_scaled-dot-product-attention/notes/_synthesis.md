# Synthesis

Cross-note synthesis for the report. One source, so this is less about
reconciling disagreement than about separating what the source establishes
from what it conjectures, which is the whole substance of this study.

## Q1: why divide by the square root of the key dimension?

Because that is the factor that normalizes the variance of the logits. Under
the source's stated assumptions, independent query and key components with
mean 0 and variance 1, the dot product of two `d_k`-dimensional vectors has
mean 0 and variance `d_k` (vaswani2017attention, Section~3.2.1 footnote 4).
Variance scales linearly in the number of summed terms, so the standard
deviation scales with the square root of `d_k`, and dividing by that returns
the logits to unit variance. No other function of `d_k` does that.

This is a derivation, and it holds only under its assumptions. It is not a
claim about trained models, whose queries and keys are neither independent nor
unit variance.

## Q2: what does the source claim versus conjecture?

- Established in the source: the definition (Equation~1), the variance
  calculation (footnote 4), and the observation that additive attention
  outperforms unscaled dot-product attention at larger `d_k` (Section~3.2.1).
- Conjectured in the source: that large dot products push the softmax into a
  small-gradient region, which is the causal story usually repeated as fact.
  The paper writes that it *suspects* this (Section~3.2.1).
- Absent from the source: any measurement isolating the scaling factor. There
  is no ablation, no gradient-magnitude figure, no effect size.

The gap between the second and third points is the finding worth carrying
forward. The popular explanation of this constant is more confident than its
primary source.

## Q3: what the report must not do

Not state the softmax-saturation mechanism as established. Not present the
variance result as a property of trained attention. Not imply this study
measured anything: the methodology is `source-only` and there is no
experiment behind any number here.

## Gaps

No `[CITATION NEEDED]` markers: every claim carried into the report has a
locator in the single source. The open questions (is the gradient story
right, does the scale hold once independence fails) are recorded as
limitations and as the next study, not as gaps in this one.
