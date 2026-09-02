# examples/

One finished study, tracked in git, so that the workflow can be read rather
than imagined and so CI has something real to validate.

`studies/` is gitignored by design: your reading and learning record is your
data, not machinery. The cost of that choice used to be that a fresh clone
contained no study at all, which meant every per-study check group in
`tools/check_all.py` reported `NOT_ASSESSED` and the pipeline's most important
behavior, a study passing all of its gates, was never exercised anywhere.
This directory pays that cost back with a single small example.

`tools/check_all.py` validates `examples/` exactly as it validates
`studies/`: same manifest schema, same artifact resolution, same brief check,
same linter. If the contracts change and this example is not updated, CI
fails, which is the point.

## What is here

- `2026-08_scaled-dot-product-attention/`: a delegated, grounded,
  source-only `understand` study answering why attention scores are divided by
  the square root of the head dimension. One source, signed off, not cleaned,
  so the full shape including `reviews/` stays visible.

## What is deliberately not here

The source snapshot under `sources/docs/` is a provenance stub rather than a
`pdftotext` extraction of the paper. This repo does not redistribute paper
text, and an invented extraction would be exactly the fabrication the whole
workflow exists to prevent. The stub records how to regenerate the real
extraction, and the notes anchor to sections of the published paper so you can
check every claim against your own copy.

Treat the example as a shape to copy, not as a study whose conclusions you
should adopt without reading its one source yourself.
