#!/usr/bin/env python3
r"""Lint a LaTeX report for the repo's hard style and integrity rules.

Checks:
  1. Unresolved markers: [CITATION NEEDED], [EVIDENCE NEEDED], [RESULT PENDING]
  2. Em-dashes: literal '—' or '---' outside math comments.
  3. Untied citations/references: a word character, then a plain space, then a
     \cite/\cref/\ref command (missing ~); and a cite/ref command that opens a
     line whose preceding content line does not end with a tie.
  4. British spellings from the project style rules.
  5. Study-level citation discipline (when given a study directory): every
     cited key resolves in the deliverable-local refs.bib, no key the registry marked
     rejected is cited, and bib entries absent from the registry are warned
     about (the registry is the canonical source record).
  6. The intent contract (when given a study directory whose status says the
     deliverable is finished): a `compare` study must actually contain a
     comparison section and a table, a `decide` study must name a
     recommendation, and so on, per tools/contracts.py. Intent used to be a
     field nothing read; this is what makes choosing it mean something.

Exit 1 on any finding; print findings with line numbers.

Usage: python3 tools/lint_report.py [study-dir-or-tex-path ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contracts import INTENT_CONTRACTS  # noqa: E402

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


CITE_KEYS = re.compile(r"\\(?:no)?[a-zA-Z]*cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]+)\}")
BIB_ENTRIES = re.compile(r"@\w+\{\s*([^,\s]+)\s*,")


def strip_comments(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def registry_key_sets(study: Path) -> tuple[set[str], set[str]] | None:
    """Return (all keys, rejected keys) from the registry, or None if absent."""
    registry = study / "sources" / "registry.yaml"
    if not registry.is_file():
        return None
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    entries = (data or {}).get("sources") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return None
    keys = {e.get("key") for e in entries if isinstance(e, dict) and e.get("key")}
    rejected = {e.get("key") for e in entries if isinstance(e, dict) and e.get("status") == "rejected"}
    return keys, rejected


def citation_findings(study: Path) -> tuple[list[str], list[str]]:
    """Cross-check citations against the bib and the canonical registry."""
    errors: list[str] = []
    warnings: list[str] = []
    cited: list[tuple[Path, Path, str]] = []
    for tex in (study / "report" / "main.tex", study / "slides" / "main.tex"):
        if not tex.is_file():
            continue
        local_bib = tex.parent / "refs.bib"
        fallback_bib = study / "report" / "refs.bib"
        bib = local_bib if local_bib.is_file() else fallback_bib
        for match in CITE_KEYS.finditer(strip_comments(tex.read_text(encoding="utf-8"))):
            for key in match.group(1).split(","):
                key = key.strip()
                if key:
                    cited.append((tex, bib, key))
    bib_cache: dict[Path, set[str]] = {}
    for tex, bib, key in cited:
        if bib.is_file():
            bib_keys = bib_cache.setdefault(
                bib, set(BIB_ENTRIES.findall(strip_comments(bib.read_text(encoding="utf-8"))))
            )
            if key not in bib_keys:
                errors.append(f"{tex}: cited key '{key}' missing from {bib.relative_to(study).as_posix()}")
    registry = registry_key_sets(study)
    if registry is not None:
        all_keys, rejected = registry
        for tex, _, key in cited:
            if key in rejected:
                errors.append(f"{tex}: cites registry-rejected source '{key}'")
        if all_keys:
            for bib, bib_keys in bib_cache.items():
                for key in sorted(bib_keys - all_keys):
                    warnings.append(f"{bib}: entry '{key}' has no registry record")
    return errors, warnings


# The intent contract is a promise about the finished deliverable, so it binds
# only once the study claims to have one. Enforcing it earlier would fail every
# freshly scaffolded study against its own template.
FINISHED_STATUSES = {"review", "done"}


def intent_findings(study: Path) -> list[str]:
    """Check that the deliverable contains what its intent promised."""
    manifest = study / "study.yaml"
    if not manifest.is_file():
        return []
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict) or str(data.get("status")) not in FINISHED_STATUSES:
        return []
    contract = INTENT_CONTRACTS.get(str(data.get("intent")))
    if contract is None or not contract.required_sections:
        return []
    targets = [t for t in (study / "report" / "main.tex", study / "slides" / "main.tex") if t.is_file()]
    if not targets:
        return []
    findings: list[str] = []
    for tex in targets:
        text = strip_comments(tex.read_text(encoding="utf-8"))
        for label, pattern in contract.required_sections:
            if not re.search(pattern, text, re.IGNORECASE):
                findings.append(
                    f"{tex}: intent '{data.get('intent')}' promises a {label}, which this deliverable does not contain"
                )
    return findings


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    all_findings: list[str] = []
    all_warnings: list[str] = []
    for arg in sys.argv[1:]:
        target = Path(arg)
        if target.is_dir():
            errors, warnings = citation_findings(target)
            all_findings.extend(errors)
            all_warnings.extend(warnings)
            all_findings.extend(intent_findings(target))
        for tex in resolve(arg):
            all_findings.extend(lint(tex))
    for warning in all_warnings:
        print(f"WARN {warning}")
    if all_findings:
        print("\n".join(all_findings))
        return 1
    print("lint clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
