#!/usr/bin/env python3
"""Build a study's report or slide deck to PDF.

Replaces tools/build_report.sh and tools/build_slides.sh. Those were the last
shell dependency in the repo, which made every documented build command fail
on Windows unless the user happened to have a POSIX shell whose PATH also
carried a TeX distribution.

    python3 tools/build.py report studies/2026-08_attention
    python3 tools/build.py slides studies/2026-08_attention
    python3 tools/build.py both   studies/2026-08_attention

Uses latexmk when present and falls back to tectonic. Output lands in
`<deliverable>/build/`, which is gitignored.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ENGINES = (
    ("latexmk", ["-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=build", "main.tex"]),
    ("tectonic", ["--outdir", "build", "main.tex"]),
)


def find_engine() -> tuple[str, list[str]]:
    for name, args in ENGINES:
        found = shutil.which(name)
        if found:
            return found, args
    raise SystemExit("build: need latexmk or tectonic on PATH")


def bib_search_path(study: Path, kind: str) -> str | None:
    """Where BibTeX should look for refs.bib.

    New scaffolds keep a deliverable-local refs.bib. Older studies may carry
    only report/refs.bib, so slides fall back to it rather than failing.
    """
    local = study / kind / "refs.bib"
    if local.is_file():
        return str((study / kind).resolve())
    fallback = study / "report" / "refs.bib"
    if kind == "slides" and fallback.is_file():
        return str((study / "report").resolve())
    return None


def build(study: Path, kind: str) -> int:
    source_dir = study / kind
    main = source_dir / "main.tex"
    if not main.is_file():
        print(f"build: {main.as_posix()} not found", file=sys.stderr)
        return 1
    (source_dir / "build").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    bib_dir = bib_search_path(study, kind)
    if kind == "slides" and bib_dir is None:
        print(
            "build: no slides/refs.bib or report/refs.bib; run python3 tools/gen_bib.py first",
            file=sys.stderr,
        )
        return 1
    if bib_dir:
        env["BIBINPUTS"] = os.pathsep.join([".", bib_dir, ""])

    engine, args = find_engine()
    proc = subprocess.run([engine, *args], cwd=source_dir, env=env)
    if proc.returncode != 0:
        print(f"build: {Path(engine).name} failed for {source_dir.as_posix()}", file=sys.stderr)
        return proc.returncode
    print(f"built: {(source_dir / 'build' / 'main.pdf').as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=("report", "slides", "both"))
    ap.add_argument("study_dir")
    args = ap.parse_args(argv)

    study = Path(args.study_dir)
    if not study.is_dir():
        print(f"build: study directory not found: {args.study_dir}", file=sys.stderr)
        return 2
    kinds = ("report", "slides") if args.kind == "both" else (args.kind,)
    for kind in kinds:
        code = build(study, kind)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
