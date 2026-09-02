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
- `2026-08_attention-logit-variance/`: the same question at `audited`
  assurance and `experimental` methodology. It measures what the first study
  derived, with two recorded runs, a claims dossier, and an independent
  replication behind every reported claim. This is the only study that
  exercises `audit_research.py`, so before it existed the `audit` group ran on
  nothing.
- `knowledge/`: what those studies left behind. AGENTS.md holds that a
  finished study with no knowledge unit has produced a document rather than
  knowledge, so both examples would be incomplete against their own contract
  without these. It is also the only knowledge base that ships, which is what
  lets the `knowledge` and `knowledge-base` check groups report `PASS` on a
  fresh clone instead of `NOT_ASSESSED`.

Your own units live in `shared/knowledge/`, which is gitignored. The tools
default there; point them here with `--dir`:

```bash
python3 tools/knowledge.py --dir examples/knowledge search "attention scaling"
python3 tools/knowledge.py --dir examples/knowledge link
```

The shipped unit deliberately carries no `review.next_due`. Review state is
per-person, and a date baked into the repository would show up as overdue in
every clone forever.

## Reproducing the audited study

Its numbers are real, produced on the machine that committed them, and its
runs are deterministic:

```bash
cd examples/2026-08_attention-logit-variance/experiments/logit-variance
python3 run.py --seed 20260901 --out /tmp/main.json --label "main measurement"
diff /tmp/main.json results/main.json      # expected: no output
```

Standard library only, about 105 seconds per run. Verified byte-identical
across Windows and Linux and across CPython 3.12 and 3.14.

## Two ways a committed dossier stops being portable

Both of these bit this example before it shipped, so if you commit a dossier
of your own, expect them.

`capture_run.py` records **absolute** paths, which resolve only on the machine
that ran the experiment. `tools/research.py` now relativizes after every
capture; for a dossier captured before that, run
`python3 tools/research.py <study-dir> relativize`. `check_all.py` warns when
it finds one. The same command also normalizes Windows path separators, which
matters more than it sounds: a relative path recorded as
`.research\runs\x\manifest.json` resolves on Windows and reads as one strange
filename on Linux, so the manifest looks unledgered and every claim linking
that run fails behind it.

The audit **rehashes** the recorded artifacts on every `check_all.py` run, so
`.gitattributes` marks those paths `-text`. Without that, git's line-ending
translation changes their bytes on checkout and the dossier verifies only on
the machine that captured it, while looking tampered with everywhere else.

Neither shows up on the machine that created the dossier. If you have WSL,
`wsl -e bash -lc "cd /mnt/c/... && python3 tools/check_all.py"` catches both
before CI does.

## What is deliberately not here

The source snapshot under `2026-08_scaled-dot-product-attention/sources/docs/`
is a provenance stub rather than a `pdftotext` extraction of the paper. This
repo does not redistribute paper text, and an invented extraction would be
exactly the fabrication the whole workflow exists to prevent. The stub records
how to regenerate the real extraction, and the notes anchor to sections of the
published paper so you can check every claim against your own copy.

For the same reason the audited study cites no external source at all. Its
dossier records `artifact-checked` evidence pointing at its own run outputs,
which is an attestation that can be honestly made here. Claiming
`full-text-checked` on a paper nobody in this repository read would not be.

Treat both as shapes to copy, not as studies whose conclusions you should
adopt without checking the sources and artifacts yourself.
