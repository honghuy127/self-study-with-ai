# logit-variance

Measures how attention logit variance and softmax concentration scale with
`d_k`, with and without the `1/sqrt(d_k)` factor.

## Environment

Python 3.10 or newer. Standard library only: `random`, `math`, `statistics`,
`json`. There is no `requirements.txt` because there is nothing to pin, which
is the strongest form of reproducibility available here.

Recorded environment for the committed runs: CPython 3.14.7 on Windows 11,
single process, CPU only, about 105 seconds per run.

## Reproduce

```bash
cd experiments/logit-variance
python3 run.py --seed 20260901 --out results/main.json --label "main measurement"
python3 run.py --seed 771244  --out results/replication.json --label "independent replication, different seed"
```

The seed fully determines the output. Re-running either command overwrites the
JSON with byte-identical content on any platform, which is what makes the
sha256 values recorded in `.research/runs/*/manifest.json` meaningful.

If a rerun produces a different file, that is a real finding about the
environment, not a nuisance: record it rather than deleting it.

## Outputs

- `results/main.json`: the claim-bearing run (`run-main-20260902`).
- `results/replication.json`: the independent check
  (`run-replication-20260902`), used as the verification run for every reported
  claim in `.research/claims.jsonl`.

Each file holds one record per `d_k` with the unscaled and scaled variance,
the mean and maximum absolute logit, and the mean largest softmax probability
over 64 competing keys.

## Reading the numbers honestly

`variance_unscaled` should sit near `d_k` and `variance_scaled` near 1. They do
not land exactly there, and the gap between the two runs is the scale of the
sampling error you should carry into any statement made from these files. The
concentration figures show what the scale bounds, not what it removes: the
scaled mean largest probability is about 0.106, well above the uniform 0.0156.
