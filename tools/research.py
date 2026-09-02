#!/usr/bin/env python3
"""Run a dossier script against a study. Replaces tools/research/research.sh.

    python3 tools/research.py <study-dir> research_state.py validate
    python3 tools/research.py <study-dir> capture_run.py --experiment x ...
    python3 tools/research.py <study-dir> audit_research.py
    python3 tools/research.py <study-dir> relativize

`--root <study-dir>` is appended rather than prepended: research_state.py
defines --root per subparser, so putting it first dies with "invalid choice".

After a successful `capture_run.py` this wrapper relativizes the dossier, and
that is not a cosmetic step. capture_run.py records resolved absolute paths,
which are correct on the machine that ran the experiment and resolve to
nothing anywhere else, so a dossier committed as captured fails its own audit
on any other checkout. Rewriting them to study-relative paths is what makes a
dossier portable; content hashes are unaffected. Run the `relativize`
pseudo-command by hand for a dossier captured before this existed.

The scripts themselves are vendored under tools/research/ from the
conduct-cs-ai-research skill, with their upstream commit recorded in
tools/research/UPSTREAM.md. Vendoring keeps the dossier workflow usable in a
checkout whose submodule was never initialized, which is the common case.
Refresh them with `python3 tools/sync_skill.py`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path, PureWindowsPath

SCRIPTS = ("research_state.py", "capture_run.py", "audit_research.py")
HERE = Path(__file__).resolve().parent / "research"


def _relative(value: str, root: Path) -> str:
    """Study-relative POSIX path, or the value unchanged if it lies outside.

    Separators matter as much as relativity here. capture_run.py can record a
    path that is already relative but Windows-flavored (`.research\\runs\\x`),
    and POSIX has no such convention: Linux reads the whole thing as one
    filename, so the manifest looks unledgered and every claim that links the
    run falls over behind it. Normalize separators whether or not the path
    needed relativizing.
    """
    if not Path(value).is_absolute() and "\\" not in value:
        return value
    candidate = Path(value)
    if not candidate.is_absolute():
        # A Windows-relative path: reinterpret it against the study root.
        candidate = root / PureWindowsPath(value).as_posix()
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        # Genuinely outside the study, a shared dataset for instance. It is an
        # absolute machine-specific locator whichever way its separators lean,
        # so leave the provenance record exactly as it was recorded.
        return value


def _fix_file_records(records: object, root: Path) -> int:
    changed = 0
    if not isinstance(records, list):
        return 0
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("path"), str):
            new = _relative(record["path"], root)
            if new != record["path"]:
                record["path"] = new
                changed += 1
    return changed


def _write_json(path: Path, payload: dict) -> None:
    """Always LF: these files sit next to hash-verified artifacts."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def relativize(study: Path) -> int:
    """Rewrite absolute paths in a dossier into study-relative ones.

    Returns the number of paths changed. Safe to run repeatedly.
    """
    root = study.resolve()
    dossier = root / ".research"
    if not dossier.is_dir():
        return 0
    changed = 0

    for manifest_path in sorted((dossier / "runs").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            continue
        before = changed
        for group in ("configs", "inputs", "outputs"):
            changed += _fix_file_records(manifest.get(group), root)
        versions = manifest.get("versions")
        if isinstance(versions, dict):
            rewritten = {_relative(key, root): value for key, value in versions.items()}
            if rewritten != versions:
                manifest["versions"] = rewritten
                changed += 1
        if changed != before:
            _write_json(manifest_path, manifest)

    ledger = dossier / "experiments.jsonl"
    if ledger.is_file():
        records = []
        ledger_changed = False
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record.get("manifest_path"), str):
                new = _relative(record["manifest_path"], root)
                if new != record["manifest_path"]:
                    record["manifest_path"] = new
                    ledger_changed = True
                    changed += 1
            records.append(json.dumps(record, ensure_ascii=False))
        if ledger_changed:
            with ledger.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write("\n".join(records) + "\n")
    return changed


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    study_dir, script, *rest = argv
    study = Path(study_dir)

    if script == "relativize":
        changed = relativize(study)
        print(f"research: relativized {changed} path(s) in {study_dir}")
        return 0

    if script not in SCRIPTS:
        print(
            f"research: unknown script {script!r}; choose from {', '.join(SCRIPTS)} or 'relativize'",
            file=sys.stderr,
        )
        return 2
    target = HERE / script
    if not target.is_file():
        print(f"research: {target} is missing; run python3 tools/sync_skill.py", file=sys.stderr)
        return 2
    code = subprocess.run([sys.executable, str(target), *rest, "--root", study_dir]).returncode
    if code == 0 and script == "capture_run.py":
        changed = relativize(study)
        if changed:
            print(f"research: relativized {changed} recorded path(s) so the dossier audits anywhere")
    return code


if __name__ == "__main__":
    sys.exit(main())
