# examples/

Two finished studies and the knowledge units they produced, tracked in git, so
the workflow can be read rather than imagined and so CI has something real to
validate.

`studies/` is gitignored by design: your reading and learning record is your
data, not machinery. The cost is that a fresh clone would otherwise contain no
study at all, leaving every per-study check group in `tools/check_all.py` with
nothing to look at. These examples pay that cost back.

`tools/check_all.py` validates `examples/` exactly as it validates `studies/`:
same manifest schema, same artifact resolution, same brief check, same linter,
same dossier audit. If a contract changes and these examples are not updated,
CI fails.

## What is here

- **`2026-08_scaled-dot-product-attention/`** is the light path: a delegated,
  grounded, source-only `understand` study answering why attention scores are
  divided by the square root of the head dimension. One source, signed off,
  left uncleaned so the full shape including `reviews/` stays visible.
- **`2026-08_attention-logit-variance/`** is the heavy one: the same question
  at `audited` assurance and `experimental` methodology. It measures what the
  first study derived, with two recorded runs, per-run manifests carrying
  content hashes, a claims ledger, and an independent replication behind every
  reported claim. It is the only study that exercises `audit_research.py`.
- **`knowledge/`** holds what those studies left behind. AGENTS.md requires a
  finished study to distill into a unit, so both examples would be incomplete
  against their own contract without these. It is
  also the only knowledge base that ships, which is what gives the `knowledge`
  and `knowledge-base` check groups something to validate on a fresh clone.

Your own units live in `shared/knowledge/`, which is gitignored. The tools
default there; point them here with `--dir`:

```bash
python3 tools/knowledge.py --dir examples/knowledge search "attention scaling"
python3 tools/knowledge.py --dir examples/knowledge link
```

Neither shipped unit carries a `review.next_due`. Review state is per-person,
and a date baked into the repository would show up as overdue in every clone
forever.

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

Both of these bit this example before it shipped. Neither is visible on the
machine that created the dossier, so expect them if you commit one of your
own.

**Absolute paths.** `capture_run.py` records paths that resolve only on the
machine that ran the experiment. `tools/research.py` relativizes after every
capture, and `check_all.py` warns if it finds an absolute path left over; for
a dossier captured before that existed, run `python3 tools/research.py
<study-dir> relativize`.

The same command normalizes Windows path separators, which matters more than
it sounds. A relative path recorded as `.research\runs\x\manifest.json`
resolves on Windows and reads as one strange filename on Linux, so the
manifest looks unledgered and every claim linking that run fails behind it.

**Line endings.** The audit rehashes the recorded artifacts on every
`check_all.py` run, so `.gitattributes` marks those paths `-text`. Without
that, git's line-ending translation changes their bytes on checkout: the
dossier verifies on the machine that captured it and looks tampered with
everywhere else.

If you have WSL, `wsl -e bash -lc "cd /mnt/c/... && python3
tools/check_all.py"` catches both before CI does.

## What these examples leave out

The source snapshot under `2026-08_scaled-dot-product-attention/sources/docs/`
is a provenance stub rather than a `pdftotext` extraction of the paper. This
repo does not redistribute paper text, and an invented extraction would be
exactly the fabrication the workflow exists to prevent. The stub records how
to regenerate the real extraction, and the notes anchor to sections of the
published paper so you can check every claim against your own copy.

For the same reason the audited study cites no external source at all. Its
dossier records `artifact-checked` evidence pointing at its own run outputs,
an attestation that can be honestly made here. Claiming `full-text-checked` on
a paper nobody in this repository read would not be.

Treat both as shapes to copy, not as studies whose conclusions you should
adopt without checking the sources and artifacts yourself.
