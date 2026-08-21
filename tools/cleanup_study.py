#!/usr/bin/env python3
"""Slim a signed-off study down to its knowledge core.

This repo stores self-study, not academic publication. During a study the
full evidence chain is kept; raw source snapshots, experiment artifacts,
review drafts, and the .research dossier all guard in-progress work and are
checked by tools/research/audit_research.py. After the human signs the review
off, only the distilled knowledge retains lasting value. The chain stays
recoverable in git history, and the registry URLs can re-fetch raw sources.

Kept:    brief.md, study.yaml, notes/, report/ (sources), slides/ (sources),
         sources/registry.yaml, sources/repos.yaml
Removed: sources/docs/, sources/pdfs/, experiments/, .research/, reviews/

Run manifests reference paths that existed at capture time; after cleanup
those paths are historical. Registry `snapshot` entries likewise become
historical references that re-fetch from `url`. Gitignored build outputs
(report/build, slides/build) are not touched.

Refuses to run unless study.yaml records `status: done`,
`gates.review_signed_off: true`, and no `cleaned` stamp yet. Interactive
studies are refused outright: their archive path arrives with the Phase 4
archive records. Stamps `cleaned: "YYYY-MM-DD"` on success.

Usage: python3 tools/cleanup_study.py <study-dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

import yaml

REMOVABLE = ("sources/docs", "sources/pdfs", "experiments", ".research", "reviews")


def tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def load_manifest(study: Path) -> dict:
    manifest = study / "study.yaml"
    if not manifest.is_file():
        raise SystemExit(f"error: {manifest} not found")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"error: {manifest} did not parse to a mapping")
    return data


def check_gates(data: dict) -> None:
    if data.get("mode") == "interactive":
        raise SystemExit("refusing: interactive studies keep their learning record; cleanup handles delegated studies")
    if data.get("status") != "done":
        raise SystemExit(f"refusing: status is {data.get('status')!r}, expected 'done'")
    gates = data.get("gates") or {}
    if gates.get("review_signed_off") is not True:
        raise SystemExit("refusing: gates.review_signed_off is not true")
    if data.get("cleaned"):
        raise SystemExit(f"refusing: study already cleaned on {data.get('cleaned')!r}")


def stamp_cleaned(study: Path, text: str) -> str:
    today = dt.date.today().isoformat()
    line = f'cleaned: "{today}"'
    if re.search(r"(?m)^cleaned:", text):
        new = re.sub(r"(?m)^cleaned:.*$", line, text, count=1)
    else:
        new = re.sub(r"(?m)^(status:[^\n]*\n)", rf"\g<1>{line}\n", text, count=1)
        if new == text:
            new = text.rstrip("\n") + f"\n\n{line}\n"
    (study / "study.yaml").write_text(new, encoding="utf-8")
    return line


def clean(study: Path, dry_run: bool) -> list[tuple[str, int]]:
    manifest = study / "study.yaml"
    data = load_manifest(study)
    check_gates(data)
    removed = []
    for rel in REMOVABLE:
        target = study / rel
        if not target.exists():
            continue
        size = tree_size(target)
        if not dry_run:
            shutil.rmtree(target)
        removed.append((rel, size))
    if removed and not dry_run:
        stamp_cleaned(study, manifest.read_text(encoding="utf-8"))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Slim a signed-off study down to its knowledge core."
    )
    parser.add_argument("study_dir", help="path to the study directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be removed without deleting anything",
    )
    args = parser.parse_args()
    study = Path(args.study_dir).resolve()
    if not study.is_dir():
        print(f"error: study directory not found: {study}", file=sys.stderr)
        return 2
    before = tree_size(study)
    removed = clean(study, args.dry_run)
    verb = "would remove" if args.dry_run else "removed"
    for rel, size in removed:
        print(f"{verb} {rel} ({size // 1024} KB)")
    if not removed:
        print("nothing to remove; study already slim")
    else:
        freed = sum(size for _, size in removed)
        print(f"{'would free' if args.dry_run else 'freed'} {freed // 1024} KB; study was {before // 1024} KB on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
