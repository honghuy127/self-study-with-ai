#!/usr/bin/env python3
"""Lint a LaTeX report for the repo's hard style and integrity rules.

Checks:
  1. Unresolved markers: [CITATION NEEDED], [EVIDENCE NEEDED], [RESULT PENDING]
  2. Em-dashes: literal '—' or '---' outside math comments.
  3. Untied citations/references: a word character, then a plain space, then a
     \cite/\cref/\ref command (missing ~); and a cite/ref command that opens a
     line whose preceding content line does not end with a tie.
  4. British spellings from the project style rules.

Exit 1 on any finding; print findings with line numbers.

Usage: python3 tools/lint_report.py [study-dir-or-tex-path ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MARKERS = ("[CITATION NEEDED]", "[EVIDENCE NEEDED]", "[RESULT PENDING]")

BRITISH = (
    "behaviour", "colour", "favour", "neighbour", "organise", "organised",
    "organising", "organisation", "optimise", "optimised", "optimisation",
    "recognise", "recognised", "analyse", "analysed", "analysing",
    "localise", "globalise", "normalise", "normalised", "stabilise",
    "destabilise", "verbalise", "randomise", "randomised", "capitalise",
    "evidentially",
)

# A word character directly followed by a space then a cite/ref-ish command means
# the tie (~) is missing somewhere in front of the command.
UNTIED = re.compile(r"[A-Za-z0-9)\]}][^\S\n]+(\\[a-zA-Z]*cite[a-zA-Z]*\{|\\citea?p?\{|\\cref\{|\\Cref\{|\\ref\{)")

# A cite/ref command that opens a line is untied unless the previous content line
# ends with a tie; the line break itself breaks the tie.
CITE_START = re.compile(r"^\s*(\\[a-zA-Z]*cite[a-zA-Z]*\{|\\citea?p?\{|\\cref\{|\\Cref\{|\\ref\{)")


def lint(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{path}: unreadable: {e}"]
    lines = text.splitlines()
    prev_stripped = ""
    for lineno, line in enumerate(lines, start=1):
        stripped = line.split("%", 1)[0]
        for marker in MARKERS:
            if marker in stripped:
                findings.append(f"{path}:{lineno}: unresolved marker {marker}")
        if "---" in stripped or "—" in stripped:
            findings.append(f"{path}:{lineno}: em-dash (use commas, colons, or restructure)")
        for m in UNTIED.finditer(stripped):
            findings.append(f"{path}:{lineno}: untied reference/citation near {m.group(1)} (tie with ~)")
        if CITE_START.match(stripped) and prev_stripped.strip() and not prev_stripped.rstrip().endswith("~"):
            findings.append(
                f"{path}:{lineno}: untied reference/citation at line start (tie the command to the preceding text with ~)"
            )
        lowered = stripped.lower()
        for w in BRITISH:
            if re.search(rf"\b{re.escape(w)}\b", lowered):
                findings.append(f"{path}:{lineno}: British spelling '{w}'")
        prev_stripped = stripped
    return findings


def resolve(target: str) -> list[Path]:
    p = Path(target)
    if p.is_dir():
        paths = [p / "report" / "main.tex", p / "slides" / "main.tex"]
        return [t for t in paths if t.exists()]
    return [p]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    all_findings: list[str] = []
    for arg in sys.argv[1:]:
        for tex in resolve(arg):
            all_findings.extend(lint(tex))
    if all_findings:
        print("\n".join(all_findings))
        return 1
    print("lint clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
