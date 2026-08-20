#!/usr/bin/env python3
"""Repo-wide pre-review gate.

Runs, in order:
  0. recreate empty dossier runtime dirs (.research/runs) that git cannot
     store, so a fresh clone does not fail the dossier audit;
  1. lint_report.py over every study directory (report + slides);
  2. a manifest check that every study.yaml has valid status/depth/track
     and a track-consistent experiments_approved gate;
  3. audit_research.py over every study that has a .research/ dossier,
     honoring the human-owned `audit_waiver` field in study.yaml;
  4. a hygiene check that fails on git-tracked PDF binaries and warns on
     oversized tracked files;
  5. a drift check that tools/research/*.py match the skill submodule's
     scripts/*.py byte-for-byte;
  6. the repo unit tests under tests/.

Exits non-zero on the first failing group, after printing a summary of every
group it ran. Usage: python3 tools/check_all.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"
TOOLS = ROOT / "tools"
SKILL_SCRIPTS = ROOT / ".opencode" / "skills" / "conduct-cs-ai-research" / "scripts"
VENDORED = TOOLS / "research"
VENDORED_SCRIPTS = ("research_state.py", "capture_run.py", "audit_research.py")

VALID_STATUSES = {"proposed", "gathering", "summarizing", "experimenting", "drafting", "review", "done"}
VALID_DEPTHS = {"briefing", "full"}
VALID_TRACKS = {"review", "concept", "experimental"}


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_lint() -> bool:
    studies = sorted(p for p in STUDIES.iterdir() if p.is_dir()) if STUDIES.is_dir() else []
    if not studies:
        print("lint: no studies found; skipping")
        return True
    ok = True
    for study in studies:
        code, out = run([sys.executable, str(TOOLS / "lint_report.py"), str(study)])
        status = "PASS" if code == 0 else "FAIL"
        print(f"lint  {study.name}: {status}")
        if code != 0:
            print(out)
            ok = False
    return ok


def validate_manifest(manifest: Path) -> list[str]:
    """Return manifest field errors; empty list when the manifest is consistent.

    Checks the status/depth/track enums and that the experiments_approved gate
    matches the track: boolean on experimental tracks, `n_a` on review and
    concept tracks (which never enter the experimenting state).
    """
    errors: list[str] = []
    if not manifest.is_file():
        return [f"missing {manifest.name}"]
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"invalid YAML in {manifest.name}: {exc}"]
    if not isinstance(data, dict):
        return [f"{manifest.name} did not parse to a mapping"]
    status = data.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"invalid status: {status!r}")
    if data.get("depth") not in VALID_DEPTHS:
        errors.append(f"invalid depth: {data.get('depth')!r}")
    track = data.get("track")
    if track not in VALID_TRACKS:
        errors.append(f"invalid or missing track: {track!r}")
        return errors
    gate = (data.get("gates") or {}).get("experiments_approved")
    if track == "experimental":
        if not isinstance(gate, bool):
            errors.append(f"experimental track requires a boolean experiments_approved, got {gate!r}")
    else:
        if gate != "n_a":
            errors.append(f"{track} track requires experiments_approved: n_a, got {gate!r}")
        if status == "experimenting":
            errors.append(f"{track} track entered the experimenting state")
    return errors


def check_manifests() -> bool:
    studies = sorted(p for p in STUDIES.iterdir() if p.is_dir()) if STUDIES.is_dir() else []
    if not studies:
        print("manifest: no studies found; skipping")
        return True
    ok = True
    for study in studies:
        errors = validate_manifest(study / "study.yaml")
        status = "PASS" if not errors else "FAIL"
        print(f"manifest {study.name}: {status}")
        for error in errors:
            print(f"manifest {study.name}: {error}")
        if errors:
            ok = False
    return ok


def ensure_runtime_dirs() -> None:
    """Recreate empty dossier runtime dirs that git cannot store.

    `research_state.py init` creates `.research/runs/`, and `validate()`
    requires it to exist. A study with no experiments leaves that directory
    empty, so git tracks nothing and a fresh clone (including CI) lacks it.
    We restore it before auditing rather than failing on a git limitation.
    """
    if not STUDIES.is_dir():
        return
    for dossier in sorted((p / ".research") for p in STUDIES.iterdir() if (p / ".research").is_dir()):
        runs = dossier / "runs"
        if not runs.is_dir():
            runs.mkdir(parents=True)
            print(f"prep  {dossier.parent.name}: recreated empty .research/runs (git does not track empty dirs)")


def read_audit_waiver(study: Path) -> str:
    """Human-owned waiver for residual dossier-audit errors.

    Agents never set this field; like the gates it records a human
    disposition, here that the documented deviations remain acceptable.
    """
    manifest = study / "study.yaml"
    if not manifest.is_file():
        return ""
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return ""
    value = data.get("audit_waiver", "") if isinstance(data, dict) else ""
    return value.strip() if isinstance(value, str) else ""


def check_audit() -> bool:
    dossiers = sorted((p / ".research") for p in STUDIES.iterdir() if (p / ".research").is_dir()) if STUDIES.is_dir() else []
    if not dossiers:
        print("audit: no .research dossiers found; skipping")
        return True
    ok = True
    for dossier in dossiers:
        study = dossier.parent
        code, out = run([sys.executable, str(VENDORED / "audit_research.py"), "--root", str(study)])
        status = "PASS" if code == 0 else "FAIL"
        print(f"audit {study.name}: {status}")
        if code != 0:
            waiver = read_audit_waiver(study)
            if waiver:
                print(f"audit {study.name}: WAIVED ({waiver})")
                continue
            print(out)
            ok = False
    return ok


HYGIENE_SIZE_LIMIT = 250 * 1024


def check_hygiene() -> bool:
    """Enforce the URL-not-binary source policy at the git level.

    PDF binaries are never committed; the registry's `pdf` field holds a
    remote URL and local evidence is a pdftotext snapshot. Tracked PDFs are
    a hard fail. Other tracked files above HYGIENE_SIZE_LIMIT are warnings.
    """
    code, out = run(["git", "ls-files"])
    if code != 0:
        print("hygiene: FAIL (git ls-files failed)")
        return False
    files = [name for name in out.splitlines() if name]
    pdfs = [f for f in files if f.lower().endswith(".pdf")]
    for f in pdfs:
        print(
            f"hygiene {f}: FAIL (PDF binaries are never committed; keep the "
            "remote URL in the registry and a pdftotext snapshot instead)"
        )
    if not pdfs:
        print("hygiene pdfs: PASS")
    for f in files:
        path = ROOT / f
        if path.suffix.lower() == ".pdf" or not path.is_file():
            continue
        size = path.stat().st_size
        if size > HYGIENE_SIZE_LIMIT:
            print(f"hygiene {f}: WARN ({size // 1024} KB tracked; consider trimming or gitignoring)")
    return not pdfs


def check_drift() -> bool:
    if not SKILL_SCRIPTS.is_dir():
        print(
            "drift: skill submodule missing at "
            f"{SKILL_SCRIPTS.relative_to(ROOT)}; run "
            "'git submodule update --init --recursive'"
        )
        return False
    ok = True
    for name in VENDORED_SCRIPTS:
        vendored = VENDORED / name
        upstream = SKILL_SCRIPTS / name
        if not vendored.is_file():
            print(f"drift {name}: FAIL (missing vendored copy)")
            ok = False
            continue
        if not upstream.is_file():
            print(f"drift {name}: FAIL (missing submodule copy)")
            ok = False
            continue
        if vendored.read_bytes() != upstream.read_bytes():
            print(f"drift {name}: FAIL (vendored copy differs from submodule)")
            ok = False
        else:
            print(f"drift {name}: PASS")
    return ok


def check_tests() -> bool:
    code, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", str(ROOT), "-v"])
    print("tests: " + ("PASS" if code == 0 else "FAIL"))
    if code != 0:
        print(out)
    return code == 0


def main() -> int:
    ensure_runtime_dirs()
    results = {
        "lint": check_lint(),
        "manifest": check_manifests(),
        "audit": check_audit(),
        "hygiene": check_hygiene(),
        "drift": check_drift(),
        "tests": check_tests(),
    }
    print()
    for name, ok in results.items():
        print(f"{name:6} {'PASS' if ok else 'FAIL'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
