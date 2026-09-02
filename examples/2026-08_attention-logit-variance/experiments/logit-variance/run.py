#!/usr/bin/env python3
"""Measure how attention logit variance scales with the key dimension.

The prior study established, from the source's own argument, that a dot
product of two d_k-dimensional vectors with independent zero-mean unit-variance
components has variance d_k, so dividing by sqrt(d_k) restores unit variance.
That is a derivation. This measures it, under exactly those assumptions, and
reports what the numbers actually say.

Standard library only, so there is nothing to pin and nothing to drift. The
run is fully determined by --seed: the same seed reproduces the same file,
byte for byte, on any platform.

    python3 run.py --seed 20260901 --out results/main.json

Outputs are written with explicit LF newlines so the recorded sha256 is
platform independent, which matters because the dossier hashes them.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

DIMENSIONS = (8, 32, 128, 512)
PAIRS = 20000          # dot products sampled per dimension
KEYS_PER_ROW = 64      # keys competing in one softmax row
ROWS = 2000            # softmax rows sampled per dimension


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def gaussian_vector(rng: random.Random, size: int) -> list[float]:
    return [rng.gauss(0.0, 1.0) for _ in range(size)]


def softmax_max(logits: list[float]) -> float:
    """Largest probability in a softmax row, computed stably."""
    top = max(logits)
    weights = [math.exp(value - top) for value in logits]
    return max(weights) / sum(weights)


def measure(d_k: int, rng: random.Random) -> dict:
    """Variance of raw and scaled logits, plus softmax concentration."""
    raw = []
    for _ in range(PAIRS):
        query = gaussian_vector(rng, d_k)
        key = gaussian_vector(rng, d_k)
        raw.append(dot(query, key))
    scale = 1.0 / math.sqrt(d_k)
    scaled = [value * scale for value in raw]

    raw_row_max = []
    scaled_row_max = []
    for _ in range(ROWS):
        query = gaussian_vector(rng, d_k)
        row = [dot(query, gaussian_vector(rng, d_k)) for _ in range(KEYS_PER_ROW)]
        raw_row_max.append(softmax_max(row))
        scaled_row_max.append(softmax_max([value * scale for value in row]))

    return {
        "d_k": d_k,
        "pairs": PAIRS,
        "variance_unscaled": round(statistics.pvariance(raw), 4),
        "variance_scaled": round(statistics.pvariance(scaled), 4),
        "mean_unscaled": round(statistics.fmean(raw), 4),
        "max_abs_unscaled": round(max(abs(value) for value in raw), 4),
        "max_abs_scaled": round(max(abs(value) for value in scaled), 4),
        "softmax_rows": ROWS,
        "keys_per_row": KEYS_PER_ROW,
        "mean_max_prob_unscaled": round(statistics.fmean(raw_row_max), 4),
        "mean_max_prob_scaled": round(statistics.fmean(scaled_row_max), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", required=True, help="path to the JSON results file")
    parser.add_argument("--label", default="", help="what this run is for, recorded in the output")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    payload = {
        "label": args.label,
        "seed": args.seed,
        "uniform_key_prob": round(1.0 / KEYS_PER_ROW, 4),
        "measurements": [measure(d_k, rng) for d_k in DIMENSIONS],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(f"wrote {out}")
    for row in payload["measurements"]:
        print(
            f"  d_k={row['d_k']:4}  var(unscaled)={row['variance_unscaled']:10}  "
            f"var(scaled)={row['variance_scaled']:7}  "
            f"max softmax prob {row['mean_max_prob_unscaled']:.4f} -> {row['mean_max_prob_scaled']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
