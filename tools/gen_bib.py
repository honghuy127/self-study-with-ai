#!/usr/bin/env python3
"""Generate report/refs.bib from the study's canonical source records.

The registry is the single source of truth for source identity. Entries
carry an optional `bibtex` block; this tool concatenates those blocks into
report/refs.bib under a generated header. Hand-editing refs.bib is allowed,
but the next run overwrites it, so durable fixes belong in the registry's
`bibtex` field.

Usage: python3 tools/gen_bib.py <study-dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

HEADER = (
    "% Generated from sources/registry.yaml by tools/gen_bib.py.\n"
    "% Durable fixes belong in the registry's bibtex field; this file is rebuilt.\n\n"
)


def load_entries(study: Path) -> list[dict]:
    registry = study / "sources" / "registry.yaml"
    if not registry.is_file():
        raise SystemExit(f"gen_bib: {registry} not found")
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(f"gen_bib: invalid YAML in {registry}: {exc}")
    entries = (data or {}).get("sources") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise SystemExit(f"gen_bib: {registry} has no top-level sources list")
    return [e for e in entries if isinstance(e, dict) and e.get("key")]


def generate(study: Path) -> tuple[str, list[str], list[str]]:
    """Return (bib text, keys written, keys skipped without a bibtex field)."""
    written: list[str] = []
    skipped: list[str] = []
    blocks: list[str] = []
    for entry in load_entries(study):
        if entry.get("status") == "rejected":
            continue
        bibtex = entry.get("bibtex")
        if isinstance(bibtex, str) and bibtex.strip():
            blocks.append(bibtex.strip() + "\n")
            written.append(str(entry["key"]))
        else:
            skipped.append(str(entry["key"]))
    return HEADER + "\n".join(blocks), written, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("study_dir", help="path to the study directory")
    args = parser.parse_args()
    study = Path(args.study_dir).resolve()
    if not study.is_dir():
        print(f"gen_bib: study directory not found: {study}", file=sys.stderr)
        return 2
    report = study / "report"
    if not report.is_dir():
        print(f"gen_bib: {study.name} has no report/ deliverable; nothing to generate", file=sys.stderr)
        return 2
    text, written, skipped = generate(study)
    (report / "refs.bib").write_text(text, encoding="utf-8")
    print(f"gen_bib: wrote {len(written)} entries to {report / 'refs.bib'}")
    for key in skipped:
        print(f"gen_bib: WARN no bibtex field for registry entry '{key}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
