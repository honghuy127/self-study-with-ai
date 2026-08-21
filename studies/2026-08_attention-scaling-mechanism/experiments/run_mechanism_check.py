#!/usr/bin/env python3
"""Synthetic mechanism check for attention logit scaling.

Tests, under controlled Gaussian sampling, whether dividing query-key dot
products by sqrt(d_k) normalizes logit variance and reduces softmax
concentration and gradient attenuation, as the standard derivation predicts.

This is a mechanism check on idealized synthetic vectors. It does not load or
train a neural network and makes no claim about trained Transformers.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np


def softmax(z: np.ndarray) -> np.ndarray:
    """Row-wise numerically stable softmax. z shape (..., n)."""
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def softmax_entropy(p: np.ndarray) -> np.ndarray:
    """Row-wise entropy in nats. p shape (..., n)."""
    return -np.where(p > 0, p * np.log(p), 0.0).sum(axis=-1)


def jacobian_frobenius(p: np.ndarray) -> np.ndarray:
    """Row-wise Frobenius norm of the softmax Jacobian.

    J = diag(p) - p p^T has diagonal p_i (1 - p_i) and off-diagonal
    -p_i p_j, so ||J||_F^2 = sum_i p_i^2 (1 - p_i)^2 + sum_{i != j} p_i^2 p_j^2,
    and sum_{i != j} p_i^2 p_j^2 = (sum_i p_i^2)^2 - sum_i p_i^4.
    """
    s2 = (p**2).sum(axis=-1)
    s4 = (p**4).sum(axis=-1)
    diag_term = ((p**2) * (1.0 - p) ** 2).sum(axis=-1)
    off_term = s2**2 - s4
    # Under saturation off_term can be a tiny negative from floating-point
    # round-off; clamp the radicand so the norm is never NaN.
    return np.sqrt(np.maximum(diag_term + off_term, 0.0))


def dot_stats(q: np.ndarray, k: np.ndarray, scale: float) -> dict:
    """Logit statistics for query/key pairs. q,k shape (N, d_k)."""
    logits = (q * k).sum(axis=1) / scale
    return {
        "mean": float(logits.mean()),
        "std": float(logits.std(ddof=1)),
        "theory_std": float(math.sqrt(q.shape[1]) * (1.0 / scale)),
    }


def run(args: argparse.Namespace) -> dict:
    rng = np.random.default_rng(args.seed)
    dk_grid = [int(x) for x in args.dk.split(",")]
    sigma_grid = [float(x) for x in args.sigma.split(",")]
    out: dict = {
        "config": {
            "dk_grid": dk_grid,
            "n_keys": args.n_keys,
            "n_pairs": args.n_pairs,
            "n_rows": args.n_rows,
            "sigma_grid": sigma_grid,
            "seed": args.seed,
        },
        "logit_stats": [],
        "softmax_concentration": [],
        "gradient_magnitude": [],
        "assumption_relaxation": [],
    }

    # (1) Logit variance and standard deviation versus d_k, scaled vs unscaled.
    for dk in dk_grid:
        q = rng.normal(size=(args.n_pairs, dk))
        k = rng.normal(size=(args.n_pairs, dk))
        out["logit_stats"].append(
            {
                "d_k": dk,
                "unscaled": dot_stats(q, k, 1.0),
                "scaled": dot_stats(q, k, math.sqrt(dk)),
            }
        )

    # (2) Softmax concentration and (3) gradient magnitude versus d_k.
    for dk in dk_grid:
        rows = {"d_k": dk, "unscaled": {}, "scaled": {}}
        grads = {"d_k": dk, "unscaled": {}, "scaled": {}}
        for label, scale in (("unscaled", 1.0), ("scaled", math.sqrt(dk))):
            q = rng.normal(size=(args.n_rows, 1, dk))
            keys = rng.normal(size=(args.n_rows, args.n_keys, dk))
            logits = (q * keys).sum(axis=-1) / scale  # shape (n_rows, n_keys)
            p = softmax(logits)
            rows[label] = {
                "entropy_nats": float(softmax_entropy(p).mean()),
                "max_prob": float(p.max(axis=-1).mean()),
            }
            grads[label] = {"jacobian_frobenius": float(jacobian_frobenius(p).mean())}
        out["softmax_concentration"].append(rows)
        out["gradient_magnitude"].append(grads)

    # (4) Relaxing the unit-variance assumption.
    for dk in dk_grid:
        for sigma in sigma_grid:
            q = rng.normal(scale=sigma, size=(args.n_pairs, dk))
            k = rng.normal(scale=sigma, size=(args.n_pairs, dk))
            logits_unscaled = (q * k).sum(axis=1)
            logits_scaled = logits_unscaled / math.sqrt(dk)
            out["assumption_relaxation"].append(
                {
                    "d_k": dk,
                    "sigma": sigma,
                    "unscaled_std": float(logits_unscaled.std(ddof=1)),
                    "scaled_std": float(logits_scaled.std(ddof=1)),
                    "theory_unscaled_std": float(math.sqrt(dk) * sigma * sigma),
                    "theory_scaled_std": float(sigma * sigma),
                }
            )

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dk", default="8,64,512", help="comma-separated d_k values")
    ap.add_argument("--sigma", default="0.5,1.0,2.0", help="coordinate std values for the relaxation arm")
    ap.add_argument("--n-keys", type=int, default=64)
    ap.add_argument("--n-pairs", type=int, default=20000)
    ap.add_argument("--n-rows", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="write JSON results here")
    args = ap.parse_args()

    results = run(args)
    text = json.dumps(results, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
