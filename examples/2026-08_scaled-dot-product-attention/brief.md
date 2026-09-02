# Brief: scaled dot-product attention

## Mode and dimensions

- Mode: `delegated`
- Intent: `understand`
- Assurance: `grounded`
- Methodology: `source-only`
- Deliverables: `report`

## Purpose

The `1/sqrt(d_k)` factor in scaled dot-product attention is one of those
constants everyone reproduces and few can justify. This study fixes the
justification in a form that can be checked against the source rather than
recalled from a blog post.

## Questions

<!-- intent: understand. explain a mechanism from first principles; the answer is a derivation or causal account. -->
- Primary question: why does dot-product attention divide the logits by the
  square root of the key dimension rather than by some other function of it?
- What would count as understanding it: being able to derive the variance of
  an unscaled dot product from stated assumptions, and to say what goes wrong
  in the softmax when that variance grows.
- Secondary questions: what the paper actually claims versus what it
  conjectures, and what it compares the scaled variant against.

## Scope

- In scope: the scaling factor in the transformer's attention, as introduced
  by the source paper, and the argument the authors give for it.
- Out of scope: later variants (QK normalization, entropy-based scaling,
  learned temperatures), empirical reproduction, and anything about training
  dynamics beyond what the source states.
- Audience: my future self, and anyone who has to explain this in an
  interview or a reading group.

## Budget and stop rules

- Time budget: one session
- Source budget: 2
- Compute or spend budget: n_a
- Stop rule: stop once the primary source's own argument is reconstructed
  with locators. This question does not need a literature survey; if the
  source's argument turns out to be incomplete, record that as a limitation
  rather than gathering more sources to paper over it.

## Human decision points

Agents may gather, note, and draft between checkpoints. Adding a second
source, widening scope to later variants, or making any empirical claim
requires fresh approval, because a source-only study cannot support one.

## Prior understanding

- What you already know: the shape of the attention operation and that
  softmax saturates. Nothing about where the specific exponent comes from.
- Repos, notes, glossary pages to reuse: none; this was the first study in
  the base.

## Mode-specific contract

### Delegated: research contract

- Report audience: myself, six months from now
- Coverage dimensions: the variance argument, the softmax consequence, and
  the paper's own comparison against additive attention
- Required comparisons: none
- Source cutoff: the published version of the source paper
- Independent review: not required at grounded assurance; run anyway
- Uncertainty to keep visible: the paper suspects rather than proves the
  gradient consequence, and this study runs no experiment of its own. Both
  must survive into the report.

## Definition of done

Delegated:

- [x] Every declared deliverable builds clean and passes lint
- [x] Every material claim traces to an eligible note, evidence record, or run
- [x] Independent review findings resolved or explicitly accepted
- [x] Glossary and library.bib merged on completion
