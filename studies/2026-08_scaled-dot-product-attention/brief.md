# Brief: Why scaled dot-product attention divides by sqrt(d_k)

## Question

- Primary question: Why does the Transformer scale attention logits by 1/sqrt(d_k)?
- Secondary questions: What happens to softmax gradients without the scaling?

## Scope

- In scope: the scaling factor in the Transformer attention mechanism, its stated motivation, and the mathematical argument.
- Out of scope: alternatives to softmax attention, positional encodings, multi-head mechanics beyond what the question needs.
- Audience: future me.
- Deadline: none

## Depth

- Depth: `full`
- Deliverable: short technical report PDF (this study is the repo's worked example; it was seeded with a `full` dossier to exercise the scripts).

## Prior understanding

- What you already know: softmax, dot products, basic transformer architecture.
- Repos, notes, glossary pages to reuse: none yet.

## Constraints

- Sources: peer-reviewed or canonical preprints only.
- Experiments: none.
- Anything prohibited: none.

## Definition of done

- [ ] Report builds clean and lint passes
- [ ] Every non-trivial claim traces to an eligible note or verified claim
- [ ] Glossary and library.bib merged on completion
