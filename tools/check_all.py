#!/usr/bin/env python3
"""Repo-wide pre-review gate.

Runs, in order:
  0. recreate empty dossier runtime dirs (.research/runs) that git cannot
     store, so a fresh clone does not fail the dossier audit;
  1. lint_report.py over every study, in studies/ and in the tracked
     examples/, including the intent contract's required sections;
  2. a manifest check that every study.yaml declares a valid mode, intent,
     assurance, methodology, deliverables, schema_version, a mode-consistent
     status and gate block, and completion-consistent verdicts;
  3. an artifact check that every manifest artifact path resolves (build
     outputs are exempt by design), that archived paths are actually
     retrievable from their packed archive, that audited studies hold a live
     dossier, and that uncleaned delegated studies at done still hold their
     review record;
  4. a brief check that no template guidance remains and that the declared
     source budget is not exceeded (warning);
  5. a knowledge-unit frontmatter check, plus a knowledge-base check that the
     index is current and every id, prerequisite, and [[link]] resolves;
  6. audit_research.py over every study that has a .research/ dossier,
     honoring the human-owned `audit_waiver` field in study.yaml;
  7. a hygiene check that fails on git-tracked PDF binaries and warns on
     oversized tracked files;
  8. a docs check that the generated contract tables in README.md and
     AGENTS.md still match tools/contracts.py;
  9. a runtimes check that .opencode/ and .claude/ match their runtime/
     source;
 10. a skill check that the vendored dossier scripts exist and record their
     upstream pin;
 11. the repo unit tests under tests/.

Groups that find nothing to check report NOT_ASSESSED instead of collapsing
into PASS. Exits non-zero on any FAIL, after printing a summary of every
group. Usage: python3 tools/check_all.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contracts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"
EXAMPLES = ROOT / "examples"
TOOLS = ROOT / "tools"
SKILL = ROOT / ".opencode" / "skills" / "conduct-cs-ai-research"
SKILL_SCRIPTS = SKILL / "scripts"
VENDORED = TOOLS / "research"
VENDORED_SCRIPTS = (
    "research_contract.py",
    "research_state.py",
    "capture_run.py",
    "audit_research.py",
)

MODES = set(contracts.MODES)
INTENTS = set(contracts.INTENTS)
ASSURANCES = set(contracts.ASSURANCES)
METHODOLOGIES = set(contracts.METHODOLOGIES)
DELIVERABLE_VALUES = set(contracts.DELIVERABLES)
EXPERIMENTAL_METHODOLOGIES = set(contracts.EXPERIMENTAL_METHODOLOGIES)
REPORT_STYLES = set(contracts.REPORT_STYLES)
DEPRECATED_FIELDS = contracts.DEPRECATED_FIELDS
SCHEMA_VERSION = contracts.SCHEMA_VERSION
VERDICTS = set(contracts.VERDICTS)

VALID_STATUSES = {mode: set(states) for mode, states in contracts.STATES.items()}
MODE_GATES = contracts.MODE_GATES


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def list_studies() -> list[Path]:
    """Every study the gate validates: the user's own plus the shipped examples.

    `studies/` is gitignored, so on a fresh clone and in CI it is empty. The
    examples are tracked, which is what keeps the per-study groups from
    reporting NOT_ASSESSED everywhere and lets CI exercise a real study.
    """
    found: list[Path] = []
    for root in (STUDIES, EXAMPLES):
        if root.is_dir():
            found.extend(p for p in root.iterdir() if p.is_dir() and (p / "study.yaml").is_file())
    return sorted(found, key=lambda p: (p.parent.name, p.name))


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
    if mode == "paper-reading":
        if methodology not in {"source-only", "static-code"}:
            errors.append(
                f"paper-reading mode requires source-only or static-code methodology, got {methodology!r}"
            )
        if not isinstance(deliverables, list) or "slides" not in deliverables:
            errors.append("paper-reading mode requires slides in deliverables")
    if status == "experimenting" and not experimental:
        errors.append(f"status experimenting requires an experimental or mixed methodology, got {methodology!r}")

    if mode == "delegated" and status == "done":
        for name in ("draft_approved", "review_signed_off"):
            if gates.get(name) is not True:
                errors.append(f"status done requires gate {name}: true")
    if mode == "paper-reading" and status == "done":
        for name in ("paper_approved", "analysis_approved", "deck_approved", "review_signed_off"):
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


def archive_status(study: Path, record: dict | None) -> tuple[bool | None, str]:
    """Can the archived evidence actually be retrieved? (ok, human-readable reason).

    Packed archives are checked directly: the zip must exist where
    archive.yaml says and hash to the recorded sha256. Records written before
    archiving existed, or by --no-archive, fall back to git-commit
    resolvability, which is only meaningful when the study was committed.
    None means "cannot tell from here" and never fails a check.
    """
    if not record:
        return None, "no archive record"
    rel = str(record.get("archive") or "")
    if rel:
        # archive paths are recorded relative to the repo root (studies/..'s parent)
        archive = (study.parent.parent / rel).resolve()
        if not archive.is_file():
            archive = (study / rel).resolve()
        if not archive.is_file():
            return False, f"archive file {rel} is missing"
        raw = record.get("archive_sha256")
        expected = raw.strip() if isinstance(raw, str) else ""
        if not expected:
            return None, f"archive {rel} present but the record carries no checksum to verify it against"
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected:
            return False, f"archive {rel} does not match its recorded sha256"
        return True, f"archive {rel} present and verified"
    resolvable = commit_resolvable(study, str(record.get("git_commit", "")))
    if resolvable is False:
        return False, "no archive file, and the recorded git commit is not resolvable here"
    if resolvable is None:
        return None, "no archive file; commit not verifiable outside a git checkout"
    return True, "no archive file; recorded git commit is resolvable"


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

    Report and slide PDF entries are build output (gitignored, rebuilt on
    demand) and are never required in the tree. Artifacts listed in
    archive.yaml left the tree at
    cleanup on purpose; they pass while their archive commit stays
    resolvable and fail if that commit disappears. Cleaned studies without
    an archive record keep the older dossier exemption. Audited assurance
    additionally requires a live dossier, and an uncleaned delegated or
    paper-reading study at done must still hold its review record.
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
        if name in {"pdf", "slides_pdf"}:
            continue
        if (study / rel).exists():
            continue
        if is_archived(rel, record):
            ok, reason = archive_status(study, record)
            if ok is False:
                errors.append(f"artifact {name} was archived but is not retrievable: {reason}")
            continue
        if cleaned and name == "dossier" and record is None:
            continue
        errors.append(f"artifact {name} points at missing path {rel}")
    if data.get("assurance") == "audited" and not cleaned and not (study / ".research").is_dir():
        errors.append("audited assurance requires a .research/ dossier")
    if data.get("mode") in {"delegated", "paper-reading"} and data.get("status") == "done" and not cleaned:
        reviews = study / "reviews"
        if not reviews.is_dir() or not any(reviews.iterdir()):
            errors.append(f"{data.get('mode')} done requires a non-empty reviews/ record before cleanup")
    errors.extend(validate_paper_reading_packet(study, data, cleaned))
    return errors


def validate_paper_reading_packet(study: Path, data: dict, cleaned: bool) -> list[str]:
    """Check the target-paper invariant after the gathering stage.

    A paper-reading study has exactly one non-rejected registry entry marked
    `role: target-paper`. Context sources are allowed, but they cannot replace
    the target. The target must be noted before presentation work begins, and
    its grounded snapshot must remain live until done-time cleanup.
    """
    if data.get("mode") != "paper-reading" or data.get("status") in {"proposed", "gathering"}:
        return []
    registry = study / "sources" / "registry.yaml"
    if not registry.is_file():
        return ["paper-reading mode requires sources/registry.yaml"]
    try:
        parsed = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"paper-reading registry is invalid YAML: {exc}"]
    entries = (parsed or {}).get("sources") if isinstance(parsed, dict) else None
    if not isinstance(entries, list):
        return ["paper-reading registry requires a top-level sources list"]
    targets = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("role") == "target-paper"
        and entry.get("status") != "rejected"
    ]
    if len(targets) != 1:
        return [f"paper-reading mode requires exactly one non-rejected role: target-paper entry, found {len(targets)}"]
    target = targets[0]
    errors: list[str] = []
    if data.get("status") in {"presenting", "review", "done"}:
        if target.get("status") != "noted":
            errors.append("paper-reading target paper must have status: noted before presenting")
        notes_file = target.get("notes_file")
        if not isinstance(notes_file, str) or not notes_file or not (study / notes_file).is_file():
            errors.append("paper-reading target paper requires a live notes_file before presenting")
    if not cleaned:
        snapshot = target.get("snapshot")
        if not isinstance(snapshot, str) or not snapshot or not (study / snapshot).is_file():
            errors.append("paper-reading target requires a live full-text snapshot before cleanup")
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


# An unfilled question line, whichever intent seeded it: "- Primary question: [...]".
UNFILLED_QUESTION = re.compile(r"(?im)^-\s*primary question:\s*\[")

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
    if UNFILLED_QUESTION.search(text):
        errors.append("brief.md still has an unfilled primary question")
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
    """Validate knowledge-unit frontmatter in every knowledge base.

    Every page carries the structured header from
    shared/templates/knowledge-unit.md so mastery and review state live
    next to the prose. Legacy pages without frontmatter warn rather than
    fail; malformed frontmatter fails.
    """
    directories = [knowledge_dir] if knowledge_dir is not None else knowledge_dirs()
    # INDEX.md is generated by tools/knowledge.py and carries no frontmatter.
    pages = sorted(
        p for directory in directories if directory.is_dir()
        for p in directory.glob("*.md") if p.name != "INDEX.md"
    )
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
    empty, so git tracks nothing and it vanishes whenever the local
    studies/ tree is rebuilt. Because studies/ is gitignored by default,
    CI has no studies at all and the per-study
    check groups report NOT_ASSESSED by design; this helper only matters
    for local runs. We restore it before auditing rather than failing on a
    git limitation.
    """
    for dossier in sorted((p / ".research") for p in list_studies() if (p / ".research").is_dir()):
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


def absolute_recorded_paths(study: Path) -> list[str]:
    """Recorded paths that only resolve on the machine that captured them.

    capture_run.py records resolved absolute paths. tools/research.py now
    rewrites them after every capture, but a dossier captured before that, or
    edited by hand, still carries them, and it will fail its own audit on any
    other checkout. Reported as a warning with the fix rather than a failure:
    the dossier is intact, it is only unportable.
    """
    dossier = study / ".research"
    offenders: list[str] = []
    for manifest_path in sorted((dossier / "runs").glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(manifest, dict):
            continue
        for group in ("configs", "inputs", "outputs"):
            for record in manifest.get(group) or []:
                path = record.get("path") if isinstance(record, dict) else None
                if isinstance(path, str) and Path(path).is_absolute():
                    offenders.append(f"{manifest_path.parent.name}/{group}: {path}")
    ledger = dossier / "experiments.jsonl"
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            path = record.get("manifest_path") if isinstance(record, dict) else None
            if isinstance(path, str) and Path(path).is_absolute():
                offenders.append(f"experiments.jsonl: {path}")
    return offenders


def check_audit() -> str:
    dossiers = sorted((p / ".research") for p in list_studies() if (p / ".research").is_dir())
    if not dossiers:
        print("audit: no .research dossiers found")
        return "NOT_ASSESSED"
    ok = True
    for dossier in dossiers:
        study = dossier.parent
        for offender in absolute_recorded_paths(study):
            print(
                f"audit {study.name}: WARN absolute recorded path ({offender}); "
                f"run python3 tools/research.py {study.name} relativize"
            )
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


def check_skill() -> str:
    """The vendored dossier scripts must be present and their pin recorded.

    They are vendored on purpose so the dossier workflow survives a checkout
    with no submodule, which is why this no longer demands byte-for-byte
    equality with the submodule. What it does demand is that the scripts exist
    and that tools/research/UPSTREAM.md says where they came from. A newer
    submodule is reported, not failed: refreshing is a decision, not an
    emergency.
    """
    ok = True
    for name in VENDORED_SCRIPTS:
        if (VENDORED / name).is_file():
            print(f"skill {name}: PASS")
        else:
            print(f"skill {name}: FAIL (missing vendored copy; run python3 tools/sync_skill.py)")
            ok = False
    pin = VENDORED / "UPSTREAM.md"
    if not pin.is_file():
        print("skill pin: FAIL (tools/research/UPSTREAM.md missing; run python3 tools/sync_skill.py)")
        ok = False
    else:
        code, out = run([sys.executable, str(TOOLS / "sync_skill.py"), "--check"])
        print(f"skill pin: {'PASS' if code == 0 else 'FAIL'}")
        print(out)
        if code != 0:
            ok = False
    if not (SKILL / "SKILL.md").is_file():
        print(
            "skill playbooks: WARN (submodule not initialized; agents cannot read the "
            "references/ playbooks. Run: git submodule update --init --recursive)"
        )
    return "PASS" if ok else "FAIL"


def check_docs() -> str:
    """README and AGENTS.md contract tables must match tools/contracts.py."""
    code, out = run([sys.executable, str(TOOLS / "docsgen.py"), "--check"])
    print(f"docs: {'PASS' if code == 0 else 'FAIL'}")
    print(out)
    return "PASS" if code == 0 else "FAIL"


def check_runtimes() -> str:
    """.opencode/ and .claude/ must match their runtime/ source."""
    code, out = run([sys.executable, str(TOOLS / "sync_runtimes.py"), "--check"])
    print(f"runtimes: {'PASS' if code == 0 else 'FAIL'}")
    print(out)
    return "PASS" if code == 0 else "FAIL"


def knowledge_dirs() -> list[Path]:
    """Every knowledge base to validate: the shipped one plus the user's own."""
    found = []
    for directory in (EXAMPLES / "knowledge", ROOT / "shared" / "knowledge"):
        if directory.is_dir() and any(p.name not in GENERATED_KNOWLEDGE for p in directory.glob("*.md")):
            found.append(directory)
    return found


GENERATED_KNOWLEDGE = {"INDEX.md", "index.json"}


def check_knowledge_base() -> str:
    """Index freshness and link integrity across every knowledge base."""
    directories = knowledge_dirs()
    if not directories:
        print("knowledge-base: no units yet")
        return "NOT_ASSESSED"
    ok = True
    for directory in directories:
        name = directory.relative_to(ROOT).as_posix()
        for label, argv in (("link", ["link", "--check"]), ("index", ["index", "--check"])):
            code, out = run([sys.executable, str(TOOLS / "knowledge.py"), "--dir", str(directory), *argv])
            print(f"knowledge-base {name} {label}: {'PASS' if code == 0 else 'FAIL'}")
            print(out)
            if code != 0:
                ok = False
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
        "knowledge-base": check_knowledge_base(),
        "audit": check_audit(),
        "hygiene": check_hygiene(),
        "docs": check_docs(),
        "runtimes": check_runtimes(),
        "skill": check_skill(),
        "tests": check_tests(),
    }
    print()
    for name, status in results.items():
        print(f"{name:15} {status}")
    return 0 if all(status != "FAIL" for status in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
