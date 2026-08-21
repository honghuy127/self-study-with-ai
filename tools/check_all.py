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
     outputs and post-cleanup dossiers are exempt by design), that audited
     studies hold a live dossier, and that uncleaned delegated studies at
     done still hold their review record;
  4. a brief check that no template guidance remains and that the declared
     source budget is not exceeded (warning);
  5. audit_research.py over every study that has a .research/ dossier,
     honoring the human-owned `audit_waiver` field in study.yaml;
  6. a hygiene check that fails on git-tracked PDF binaries and warns on
     oversized tracked files;
  7. a drift check that tools/research/*.py match the skill submodule's
     scripts/*.py byte-for-byte;
  8. the repo unit tests under tests/.

Groups that find nothing to check report NOT_ASSESSED instead of collapsing
into PASS. Exits non-zero on any FAIL, after printing a summary of every
group. Usage: python3 tools/check_all.py
"""
from __future__ import annotations

import datetime as dt
import re
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
REPORT_STYLES = {"neurips", "plain"}
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

    report_style = data.get("report_style")
    if report_style is not None:
        if report_style not in REPORT_STYLES:
            errors.append(f"invalid report_style: {report_style!r}")
        if not isinstance(deliverables, list) or "report" not in deliverables:
            errors.append("report_style is set but report is not a deliverable")

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


def load_archive_record(study: Path) -> dict | None:
    archive = study / "archive.yaml"
    if not archive.is_file():
        return None
    try:
        data = yaml.safe_load(archive.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def commit_resolvable(cwd: Path, sha: str) -> bool | None:
    """True or False when git can answer, None outside a git repository."""
    if not sha:
        return None
    probe = subprocess.run(
        ["git", "-C", str(cwd), "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True
    )
    if probe.returncode == 0:
        return True
    repo = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--git-dir"], capture_output=True)
    if repo.returncode != 0:
        return None
    return False


def is_archived(rel: str, record: dict | None) -> bool:
    if not record:
        return False
    for entry in record.get("removed") or []:
        path = str((entry or {}).get("path", ""))
        if path and (rel == path or rel.startswith(path.rstrip("/") + "/")):
            return True
    return False


def validate_artifacts(study: Path) -> list[str]:
    """Every manifest artifact path must resolve, with designed exemptions.

    `pdf` is build output (gitignored, rebuilt on demand) and is never
    required in the tree. Artifacts listed in archive.yaml left the tree at
    cleanup on purpose; they pass while their archive commit stays
    resolvable and fail if that commit disappears. Cleaned studies without
    an archive record keep the older dossier exemption. Audited assurance
    additionally requires a live dossier, and an uncleaned delegated study
    at done must still hold its review record.
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
    record = load_archive_record(study)
    errors: list[str] = []
    for name, rel in (data.get("artifacts") or {}).items():
        rel = str(rel)
        if name == "pdf":
            continue
        if (study / rel).exists():
            continue
        if is_archived(rel, record):
            resolvable = commit_resolvable(study, str((record or {}).get("git_commit", "")))
            if resolvable is False:
                errors.append(f"artifact {name} archived but archive commit is not resolvable")
            continue
        if cleaned and name == "dossier" and record is None:
            continue
        errors.append(f"artifact {name} points at missing path {rel}")
    if data.get("assurance") == "audited" and not cleaned and not (study / ".research").is_dir():
        errors.append("audited assurance requires a .research/ dossier")
    if data.get("mode") == "delegated" and data.get("status") == "done" and not cleaned:
        reviews = study / "reviews"
        if not reviews.is_dir() or not any(reviews.iterdir()):
            errors.append("delegated done requires a non-empty reviews/ record before cleanup")
    return errors


def snapshot_warnings(study: Path) -> list[str]:
    """Cleaned studies keep historical snapshot references; flag them once."""
    if not (study / "study.yaml").is_file():
        return []
    try:
        manifest = yaml.safe_load((study / "study.yaml").read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    if not isinstance(manifest, dict) or not manifest.get("cleaned"):
        return []
    registry = study / "sources" / "registry.yaml"
    if not registry.is_file():
        return []
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    entries = (data or {}).get("sources") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    missing = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        snapshot = entry.get("snapshot")
        if isinstance(snapshot, str) and snapshot and not (study / snapshot).exists():
            missing += 1
    if missing:
        return [
            f"{missing} registry snapshot paths are historical (removed at cleanup); refetch from url when needed"
        ]
    return []


BRIEF_SENTINELS = (
    "[one sentence, answerable]",
    "[Why this study matters",
    "[topics, methods, time range]",
    "[max sources to open",
    "[saturation or kill criterion",
    "Keep only the subsection matching this study's mode",
    "Keep only the checklist matching this study's mode",
)


def validate_brief(study: Path) -> tuple[list[str], list[str]]:
    """The brief must be filled in, and the source budget must hold.

    Template guidance left in place fails the check: agents refuse to act on
    a templated brief, and so does CI. A registered source count above the
    brief's declared source budget is a warning, because the stop rule is a
    human decision, not an automatic block.
    """
    errors: list[str] = []
    warnings: list[str] = []
    brief = study / "brief.md"
    if not brief.is_file():
        return errors, warnings
    text = brief.read_text(encoding="utf-8")
    for sentinel in BRIEF_SENTINELS:
        if sentinel in text:
            errors.append(f"brief.md still contains template guidance ({sentinel!r})")
    budget_match = re.search(r"(?im)^-\s*source budget:\s*(\d+)", text)
    if budget_match:
        budget = int(budget_match.group(1))
        registry = study / "sources" / "registry.yaml"
        if registry.is_file():
            try:
                data = yaml.safe_load(registry.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                data = None
            entries = (data or {}).get("sources") if isinstance(data, dict) else None
            if isinstance(entries, list):
                kept = sum(1 for e in entries if isinstance(e, dict) and e.get("status") != "rejected")
                if kept > budget:
                    warnings.append(f"source budget {budget} exceeded: {kept} sources registered")
    return errors, warnings


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
        for warning in snapshot_warnings(study):
            print(f"artifacts {study.name}: WARN {warning}")
        if errors:
            ok = False
    return "PASS" if ok else "FAIL"


def check_briefs() -> str:
    studies = list_studies()
    if not studies:
        print("briefs: no studies found")
        return "NOT_ASSESSED"
    ok = True
    for study in studies:
        errors, warnings = validate_brief(study)
        status = "PASS" if not errors else "FAIL"
        print(f"briefs {study.name}: {status}")
        for error in errors:
            print(f"briefs {study.name}: {error}")
        for warning in warnings:
            print(f"briefs {study.name}: WARN {warning}")
        if errors:
            ok = False
    return "PASS" if ok else "FAIL"


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (meta, error). meta is None when no frontmatter block exists."""
    if not text.startswith("---\n"):
        return None, ""
    end = text.find("\n---", 4)
    if end == -1:
        return None, "frontmatter opened but never closed"
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter did not parse to a mapping"
    return data, ""


def _is_iso_date(value: object) -> bool:
    try:
        dt.date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def validate_knowledge_unit(meta: dict) -> list[str]:
    errors: list[str] = []
    for field in ("id", "question"):
        value = meta.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"frontmatter field {field!r} is required and must be a non-empty string")
    for field in ("prerequisites", "source_ids", "misconceptions"):
        value = meta.get(field)
        if value is not None and (not isinstance(value, list) or not all(isinstance(item, str) for item in value)):
            errors.append(f"frontmatter field {field!r} must be a list of strings when present")
    mastery = meta.get("mastery")
    if mastery is not None:
        if not isinstance(mastery, dict):
            errors.append("frontmatter field 'mastery' must be a mapping when present")
        else:
            assessed = mastery.get("last_assessed")
            if assessed not in (None, "") and not _is_iso_date(assessed):
                errors.append(f"mastery.last_assessed {assessed!r} is not an ISO date")
    review = meta.get("review")
    if review is not None:
        if not isinstance(review, dict):
            errors.append("frontmatter field 'review' must be a mapping when present")
        else:
            due = review.get("next_due")
            if due not in (None, "") and not _is_iso_date(due):
                errors.append(f"review.next_due {due!r} is not an ISO date")
    superseded = meta.get("superseded_by")
    if superseded is not None and not isinstance(superseded, str):
        errors.append("frontmatter field 'superseded_by' must be a string when present")
    return errors


def check_knowledge(knowledge_dir: Path | None = None) -> str:
    """Validate knowledge-unit frontmatter in shared/knowledge.

    Every new page carries the structured header from
    shared/templates/knowledge-unit.md so mastery and review state live
    next to the prose. Legacy pages without frontmatter warn rather than
    fail; malformed frontmatter fails.
    """
    directory = knowledge_dir or ROOT / "shared" / "knowledge"
    pages = sorted(directory.glob("*.md")) if directory.is_dir() else []
    if not pages:
        print("knowledge: no pages found")
        return "NOT_ASSESSED"
    ok = True
    for page in pages:
        text = page.read_text(encoding="utf-8")
        meta, error = parse_frontmatter(text)
        if error:
            print(f"knowledge {page.name}: FAIL {error}")
            ok = False
            continue
        if meta is None:
            print(f"knowledge {page.name}: WARN no frontmatter (new pages require a knowledge-unit header)")
            continue
        errors = validate_knowledge_unit(meta)
        print(f"knowledge {page.name}: " + ("PASS" if not errors else "FAIL"))
        for message in errors:
            print(f"knowledge {page.name}: {message}")
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
        "briefs": check_briefs(),
        "knowledge": check_knowledge(),
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
