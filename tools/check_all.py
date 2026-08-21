#!/usr/bin/env python3
"""Repo-wide pre-review gate.

Runs, in order:
  0. recreate empty dossier runtime dirs (.research/runs) that git cannot
     store, so a fresh clone does not fail the dossier audit;
  1. lint_report.py over every study directory (report + slides);
  2. a manifest check that every study.yaml declares a valid mode, intent,
     assurance, methodology, deliverables, schema_version, a mode-consistent
     status and gate block, and completion-consistent verdicts;
  3. an artifact check that every manifest artifact path resolves (build
     outputs and post-cleanup dossiers are exempt by design);
  4. audit_research.py over every study that has a .research/ dossier,
     honoring the human-owned `audit_waiver` field in study.yaml;
  5. a hygiene check that fails on git-tracked PDF binaries and warns on
     oversized tracked files;
  6. a drift check that tools/research/*.py match the skill submodule's
     scripts/*.py byte-for-byte;
  7. the repo unit tests under tests/.

Groups that find nothing to check report NOT_ASSESSED instead of collapsing
into PASS. Exits non-zero on any FAIL, after printing a summary of every
group. Usage: python3 tools/check_all.py
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

MODES = {"interactive", "delegated"}
INTENTS = {"understand", "solve", "build", "compare", "decide", "refresh", "survey"}
ASSURANCES = {"quick", "grounded", "audited"}
METHODOLOGIES = {"source-only", "static-code", "experimental", "mixed"}
DELIVERABLE_VALUES = {"learning-note", "implementation", "decision-brief", "report", "slides", "none"}
EXPERIMENTAL_METHODOLOGIES = {"experimental", "mixed"}
DEPRECATED_FIELDS = ("track", "depth")
SCHEMA_VERSION = 2
VERDICTS = {"PASS", "CONDITIONAL", "FAIL", "BLOCKED", "NOT_ASSESSED"}

VALID_STATUSES = {
    "delegated": {"proposed", "gathering", "summarizing", "experimenting", "drafting", "review", "done"},
    "interactive": {"scoped", "diagnosing", "learning", "practicing", "assessing", "retained"},
}
MODE_GATES = {
    "delegated": ("sources_approved", "notes_approved", "experiments_approved", "draft_approved", "review_signed_off"),
    "interactive": ("scope_approved", "evidence_approved", "experiments_approved", "mastery_approved"),
}


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def list_studies() -> list[Path]:
    return sorted(p for p in STUDIES.iterdir() if p.is_dir()) if STUDIES.is_dir() else []


def check_lint() -> str:
    studies = list_studies()
    if not studies:
        print("lint: no studies found")
        return "NOT_ASSESSED"
    ok = True
    for study in studies:
        code, out = run([sys.executable, str(TOOLS / "lint_report.py"), str(study)])
        status = "PASS" if code == 0 else "FAIL"
        print(f"lint  {study.name}: {status}")
        if code != 0:
            print(out)
            ok = False
    return "PASS" if ok else "FAIL"


def validate_manifest(manifest: Path) -> list[str]:
    """Return manifest field errors; empty list when the manifest is consistent.

    Checks the mode/intent/assurance/methodology/deliverables dimensions,
    schema_version, the mode-specific status enum, the mode-specific gate
    block (boolean gates plus an experiments_approved gate that is boolean
    only when the methodology runs experiments and `n_a` otherwise), and
    completion consistency: done and retained studies need their sign-off
    gates and a non-empty final verdict. The retired track and depth fields
    fail validation until migrated.
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

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}")

    for field in DEPRECATED_FIELDS:
        if field in data:
            errors.append(f"deprecated field {field!r}; migrate to mode/intent/assurance/methodology/deliverables")

    mode = data.get("mode")
    if mode not in MODES:
        errors.append(f"invalid or missing mode: {mode!r}")
        return errors
    if data.get("intent") not in INTENTS:
        errors.append(f"invalid or missing intent: {data.get('intent')!r}")
    if data.get("assurance") not in ASSURANCES:
        errors.append(f"invalid or missing assurance: {data.get('assurance')!r}")
    methodology = data.get("methodology")
    if methodology not in METHODOLOGIES:
        errors.append(f"invalid or missing methodology: {methodology!r}")
    deliverables = data.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        errors.append(f"deliverables must be a non-empty list, got {deliverables!r}")
    else:
        for item in deliverables:
            if item not in DELIVERABLE_VALUES:
                errors.append(f"invalid deliverable: {item!r}")

    status = data.get("status")
    if status not in VALID_STATUSES[mode]:
        errors.append(f"invalid status for {mode} mode: {status!r}")

    gates = data.get("gates") or {}
    experimental = methodology in EXPERIMENTAL_METHODOLOGIES
    for name in MODE_GATES[mode]:
        value = gates.get(name)
        if name == "experiments_approved":
            if experimental:
                if not isinstance(value, bool):
                    errors.append(f"{methodology} methodology requires a boolean experiments_approved, got {value!r}")
            elif value != "n_a":
                errors.append(f"{methodology} methodology requires experiments_approved: n_a, got {value!r}")
        elif not isinstance(value, bool):
            errors.append(f"{mode} mode requires a boolean {name}, got {value!r}")
    if status == "experimenting" and not experimental:
        errors.append(f"status experimenting requires an experimental or mixed methodology, got {methodology!r}")

    if mode == "delegated" and status == "done":
        for name in ("draft_approved", "review_signed_off"):
            if gates.get(name) is not True:
                errors.append(f"status done requires gate {name}: true")
    if mode == "interactive" and status == "retained" and gates.get("mastery_approved") is not True:
        errors.append("status retained requires gate mastery_approved: true")
    if status in ("done", "retained"):
        verdict = str(data.get("last_gate_verdict") or "").strip()
        if not verdict:
            errors.append("completed study has an empty last_gate_verdict")
        elif verdict not in VERDICTS:
            errors.append(f"invalid last_gate_verdict: {verdict!r}")
    return errors


def validate_artifacts(study: Path) -> list[str]:
    """Every manifest artifact path must resolve, with designed exemptions.

    `pdf` is build output (gitignored, rebuilt on demand) and is never
    required in the tree. Cleaned studies drop the dossier by design, so its
    path is exempt there; the chain stays recoverable in git history.
    """
    manifest = study / "study.yaml"
    if not manifest.is_file():
        return []
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    cleaned = bool(data.get("cleaned"))
    errors: list[str] = []
    for name, rel in (data.get("artifacts") or {}).items():
        rel = str(rel)
        if name == "pdf":
            continue
        if cleaned and name == "dossier":
            continue
        if not (study / rel).exists():
            errors.append(f"artifact {name} points at missing path {rel}")
    return errors


def check_manifests() -> str:
    studies = list_studies()
    if not studies:
        print("manifest: no studies found")
        return "NOT_ASSESSED"
    ok = True
    for study in studies:
        errors = validate_manifest(study / "study.yaml")
        status = "PASS" if not errors else "FAIL"
        print(f"manifest {study.name}: {status}")
        for error in errors:
            print(f"manifest {study.name}: {error}")
        if errors:
            ok = False
    return "PASS" if ok else "FAIL"


def check_artifacts() -> str:
    studies = list_studies()
    if not studies:
        print("artifacts: no studies found")
        return "NOT_ASSESSED"
    ok = True
    for study in studies:
        errors = validate_artifacts(study)
        status = "PASS" if not errors else "FAIL"
        print(f"artifacts {study.name}: {status}")
        for error in errors:
            print(f"artifacts {study.name}: {error}")
        if errors:
            ok = False
    return "PASS" if ok else "FAIL"


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


def check_audit() -> str:
    dossiers = sorted((p / ".research") for p in STUDIES.iterdir() if (p / ".research").is_dir()) if STUDIES.is_dir() else []
    if not dossiers:
        print("audit: no .research dossiers found")
        return "NOT_ASSESSED"
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
    return "PASS" if ok else "FAIL"


HYGIENE_SIZE_LIMIT = 250 * 1024


def check_hygiene() -> str:
    """Enforce the URL-not-binary source policy at the git level.

    PDF binaries are never committed; the registry's `pdf` field holds a
    remote URL and local evidence is a pdftotext snapshot. Tracked PDFs are
    a hard fail. Other tracked files above HYGIENE_SIZE_LIMIT are warnings.
    """
    code, out = run(["git", "ls-files"])
    if code != 0:
        print("hygiene: FAIL (git ls-files failed)")
        return "FAIL"
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
    return "FAIL" if pdfs else "PASS"


def check_drift() -> str:
    if not SKILL_SCRIPTS.is_dir():
        print(
            "drift: skill submodule missing at "
            f"{SKILL_SCRIPTS.relative_to(ROOT)}; run "
            "'git submodule update --init --recursive'"
        )
        return "FAIL"
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
    return "PASS" if ok else "FAIL"


def check_tests() -> str:
    code, out = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", str(ROOT), "-v"])
    print("tests: " + ("PASS" if code == 0 else "FAIL"))
    if code != 0:
        print(out)
    return "PASS" if code == 0 else "FAIL"


def main() -> int:
    ensure_runtime_dirs()
    results = {
        "lint": check_lint(),
        "manifest": check_manifests(),
        "artifacts": check_artifacts(),
        "audit": check_audit(),
        "hygiene": check_hygiene(),
        "drift": check_drift(),
        "tests": check_tests(),
    }
    print()
    for name, status in results.items():
        print(f"{name:9} {status}")
    return 0 if all(status != "FAIL" for status in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
