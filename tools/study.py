#!/usr/bin/env python3
"""Lifecycle CLI for studies: the human-facing front door.

Usage: python3 tools/study.py <command> [args]

  new         scaffold a study (same flags as tools/new_study.py; --mode required)
  status      <id>                    show mode, state, gates, and next action
  status-set  <id> <status> --note .. move the study along its transition graph
  approve     <id> <gate> --note ...  record a human gate decision
  practice    <id>                    interactive: show practice items without exposing answers
  assess      <id>                    interactive: administer the mastery task
  revisit     <id>                    interactive: list due delayed-review items
  reopen      <id>                    report what reopening a finished study needs (read-only)

This CLI is the only writer of lifecycle state and gate decisions. Every
change appends an event to the study's events.jsonl. Agents propose; the
human approves gates; nobody hand-edits study.yaml state or gates.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

import check_all

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"

MODE_GATES = {
    "delegated": ("sources_approved", "notes_approved", "experiments_approved", "draft_approved", "review_signed_off"),
    "interactive": ("scope_approved", "evidence_approved", "experiments_approved", "mastery_approved"),
    "paper-reading": ("paper_approved", "analysis_approved", "deck_approved", "review_signed_off"),
}

# One state engine, three allowed transition graphs. Backward edges exist on
# purpose: assessment can return to practice, review can return to drafting,
# and a finished non-interactive study can reopen into review for refresh work.
TRANSITIONS = {
    "delegated": {
        "proposed": {"gathering"},
        "gathering": {"summarizing", "proposed"},
        "summarizing": {"experimenting", "drafting", "gathering"},
        "experimenting": {"drafting", "summarizing"},
        "drafting": {"review", "summarizing", "experimenting"},
        "review": {"done", "gathering", "summarizing", "experimenting", "drafting"},
        "done": {"review"},
    },
    "interactive": {
        "scoped": {"diagnosing"},
        "diagnosing": {"learning", "scoped"},
        "learning": {"practicing", "diagnosing"},
        "practicing": {"assessing", "learning"},
        "assessing": {"retained", "practicing", "learning"},
        "retained": set(),
    },
    "paper-reading": {
        "proposed": {"gathering"},
        "gathering": {"analyzing", "proposed"},
        "analyzing": {"presenting", "gathering"},
        "presenting": {"review", "analyzing"},
        "review": {"done", "gathering", "analyzing", "presenting"},
        "done": {"review"},
    },
}

# Gates that must be approved before entering a state. The experiments gate
# only binds when the methodology runs experiments.
ENTRY_GATES = {
    "delegated": {
        "drafting": ("sources_approved", "notes_approved"),
        "review": ("draft_approved",),
        "done": ("review_signed_off",),
    },
    "interactive": {
        "diagnosing": ("scope_approved",),
        "learning": ("evidence_approved",),
        "retained": ("mastery_approved",),
    },
    "paper-reading": {
        "analyzing": ("paper_approved",),
        "presenting": ("analysis_approved",),
        "review": ("deck_approved",),
        "done": ("review_signed_off",),
    },
}

EXPERIMENTAL_METHODOLOGIES = ("experimental", "mixed")

GATE_ALIASES = {
    "sources": "sources_approved",
    "notes": "notes_approved",
    "experiments": "experiments_approved",
    "draft": "draft_approved",
    "review": "review_signed_off",
    "scope": "scope_approved",
    "evidence": "evidence_approved",
    "mastery": "mastery_approved",
    "paper": "paper_approved",
    "analysis": "analysis_approved",
    "deck": "deck_approved",
}

NEXT_ACTION = {
    "delegated": {
        "proposed": "fill brief.md, then /gather and stop for sources approval",
        "gathering": "register sources, then stop for sources approval",
        "summarizing": "note every registered source, then stop for notes approval",
        "experimenting": "run the approved experiments, then stop for experiments approval",
        "drafting": "synthesize and draft the report, then stop for draft approval",
        "review": "independent review, then stop for review sign-off",
        "done": "merge shared/ knowledge, then tools/cleanup_study.py; reopen later via study.py reopen",
    },
    "interactive": {
        "scoped": "record the unaided baseline in learning/baseline.md, then approve scope",
        "diagnosing": "plan the concept path in learning/map.md from the baseline",
        "learning": "tutor one link at a time; journal every exchange in learning/journal.md",
        "practicing": "administer near and transfer practice (study practice)",
        "assessing": "administer the mastery task unaided (study assess), then approve mastery",
        "retained": "distill outputs/learning-note.md and schedule the delayed review (study revisit)",
    },
    "paper-reading": {
        "proposed": "fill the exact target-paper and talk contracts, then /read-paper",
        "gathering": "verify one target paper and context packet, then stop for paper approval",
        "analyzing": "produce the anchored paper analysis, then stop for analysis approval",
        "presenting": "storyboard, build, lint, and render the deck, then stop for deck approval",
        "review": "independently audit slide claims and rendered output, then stop for review sign-off",
        "done": "merge reusable knowledge, then tools/cleanup_study.py; reopen later via study.py reopen",
    },
}


def resolve_study(ident: str) -> Path:
    path = Path(ident)
    if path.is_dir():
        return path.resolve()
    candidate = STUDIES / ident
    if candidate.is_dir():
        return candidate
    raise SystemExit(f"study: not found: {ident} (expected a study id or directory)")


def load_manifest(study: Path) -> dict:
    manifest = study / "study.yaml"
    if not manifest.is_file():
        raise SystemExit(f"study: {manifest} not found")
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(f"study: invalid YAML in {manifest}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"study: {manifest} did not parse to a mapping")
    return data


def require_interactive(study: Path, data: dict) -> None:
    if data.get("mode") != "interactive":
        raise SystemExit(f"study: {study.name} is not an interactive study")


def append_event(study: Path, event: dict) -> None:
    event = {"ts": dt.datetime.now().astimezone().isoformat(timespec="seconds"), **event}
    with (study / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def gate_value(text: str, gate: str) -> object:
    match = re.search(rf"(?m)^  {gate}: (\S+)", text)
    if not match:
        return None
    value = match.group(1)
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def cmd_status_set(study: Path, target: str, note: str) -> int:
    data = load_manifest(study)
    mode = data.get("mode")
    if mode not in TRANSITIONS:
        raise SystemExit(f"study: unknown mode {mode!r} in {study.name}")
    current = data.get("status")
    allowed = TRANSITIONS[mode].get(current, set())
    if target not in allowed:
        options = ", ".join(sorted(allowed)) if allowed else "none (terminal state)"
        raise SystemExit(f"study: transition {current!r} -> {target!r} is not allowed for {mode} mode (allowed: {options})")

    methodology = data.get("methodology")
    if target == "experimenting" and methodology not in EXPERIMENTAL_METHODOLOGIES:
        raise SystemExit(
            f"study: entering 'experimenting' is restricted to experimental or mixed methodologies, "
            f"got {methodology!r}"
        )

    gates = data.get("gates") or {}
    required = list(ENTRY_GATES[mode].get(target, ()))
    if target == "drafting" and methodology in EXPERIMENTAL_METHODOLOGIES:
        required.append("experiments_approved")
    if target == "retained" and gates.get("experiments_approved") != "n_a":
        required.append("experiments_approved")
    for gate in required:
        if gates.get(gate) is not True:
            raise SystemExit(f"study: entering {target!r} requires gate {gate}; approve it first")

    manifest = study / "study.yaml"
    text = manifest.read_text(encoding="utf-8")
    new_text, count = re.subn(rf"(?m)^status: {re.escape(str(current))}\b", f"status: {target}", text, count=1)
    if count != 1:
        raise SystemExit(f"study: could not locate status {current!r} in {manifest}")
    manifest.write_text(new_text, encoding="utf-8")
    append_event(study, {"type": "transition", "from": current, "to": target, "note": note, "actor": "agent"})
    print(f"{study.name}: {current} -> {target}")
    return 0


def cmd_status(study: Path) -> int:
    data = load_manifest(study)
    mode = data.get("mode", "?")
    dims = f"intent: {data.get('intent', '?')}  assurance: {data.get('assurance', '?')}  methodology: {data.get('methodology', '?')}"
    deliverables = data.get("deliverables") or []
    status = data.get("status", "?")
    cleaned = data.get("cleaned") or ""
    print(f"{data.get('id', study.name)}: {data.get('title', '')}")
    print(f"mode: {mode}  {dims}")
    print(f"deliverables: {', '.join(deliverables) if deliverables else 'none'}")
    print(f"status: {status}" + (f" (cleaned {cleaned})" if cleaned else ""))
    print("gates:")
    gates = data.get("gates") or {}
    for name in MODE_GATES.get(mode, ()):  # type: ignore[index]
        value = gates.get(name, "missing")
        mark = "ok" if value is True else ("n_a" if value == "n_a" else ("missing" if value == "missing" else "pending"))
        print(f"  {name:24} {mark}")
    artifacts = data.get("artifacts") or {}
    if artifacts:
        print("artifacts:")
        for name, rel in artifacts.items():
            mark = "present" if (study / str(rel)).exists() else "missing"
            print(f"  {name:24} {rel} ({mark})")
    next_action = NEXT_ACTION.get(mode, {}).get(status, "no automatic suggestion for this state")
    print(f"next: {next_action}")
    allowed = sorted(TRANSITIONS.get(mode, {}).get(status, set()))
    if allowed:
        print(f"allowed transitions: {', '.join(allowed)} (via study.py status-set)")
    return 0


def cmd_approve(study: Path, gate: str, note: str, evidence: str = "", reopen: str = "", verdict: str = "PASS") -> int:
    data = load_manifest(study)
    mode = data.get("mode")
    if mode not in MODE_GATES:
        raise SystemExit(f"study: unknown mode {mode!r} in {study.name}")
    resolved = GATE_ALIASES.get(gate, gate)
    if resolved not in MODE_GATES[mode]:
        allowed = ", ".join(MODE_GATES[mode])
        raise SystemExit(f"study: {gate!r} is not a {mode} gate (allowed: {allowed})")

    manifest = study / "study.yaml"
    text = manifest.read_text(encoding="utf-8")
    if re.search(rf"(?m)^  {resolved}: true\s*$", text):
        raise SystemExit(f"study: gate {resolved} is already approved")
    if re.search(rf"(?m)^  {resolved}: n_a", text):
        raise SystemExit(f"study: gate {resolved} is n_a for this methodology")
    new_text, count = re.subn(rf"(?m)^(  {resolved}: )false(\s*(?:#.*)?)$", rf"\g<1>true\2", text, count=1)
    if count != 1:
        raise SystemExit(f"study: gate {resolved} not found as pending in {manifest}")
    new_text, count = re.subn(
        r'(?m)^last_gate_verdict: "[^"]*"', f'last_gate_verdict: "{verdict}"', new_text, count=1
    )
    if count != 1:
        if not new_text.endswith("\n"):
            new_text += "\n"
        new_text += f'last_gate_verdict: "{verdict}"\n'
    manifest.write_text(new_text, encoding="utf-8")

    record = {"type": "approval", "gate": resolved, "note": note, "actor": "human", "date": dt.date.today().isoformat()}
    record["verdict"] = verdict
    if evidence:
        record["evidence_inspected"] = evidence
    if reopen:
        record["reopen_condition"] = reopen
    append_event(study, record)
    print(f"approved {resolved} for {study.name}")
    return 0


def cmd_practice(study: Path) -> int:
    data = load_manifest(study)
    require_interactive(study, data)
    status = data.get("status")
    if status not in ("learning", "practicing", "assessing"):
        print(f"note: status is {status!r}; practice usually happens from the practicing state")
    practice = study / "learning" / "practice"
    items = sorted(practice.glob("*.md")) if practice.is_dir() else []
    if not items:
        print("no practice items recorded yet")
        print("the tutor adds a near problem and a transfer problem as learning/practice/*.md")
        return 0
    print("administer one item at a time; never display a solution before the learner attempts it")
    for item in items:
        print(f"  {item.relative_to(study)}")
    return 0


def cmd_assess(study: Path) -> int:
    data = load_manifest(study)
    require_interactive(study, data)
    mastery = study / "learning" / "mastery.md"
    if not mastery.is_file():
        raise SystemExit(f"study: {mastery} not found")
    print("mastery assessment rules:")
    print("  - tutoring disabled; help level none; the learner completes the task unaided")
    print("  - record, per capability, demonstrated yes/no with the learner's own words as evidence")
    print("  - write the verdict (pass | needs-practice) into learning/mastery.md")
    print("  - needs-practice returns to practicing with an exercise targeting the weakest capability")
    print(f"  - then record the decision: python3 tools/study.py approve {study.name} mastery --note \"...\"")
    print(f"task: {mastery.relative_to(study)}")
    return 0


def cmd_revisit(study: Path) -> int:
    data = load_manifest(study)
    require_interactive(study, data)
    mastery = study / "learning" / "mastery.md"
    if not mastery.is_file():
        raise SystemExit(f"study: {mastery} not found")
    text = mastery.read_text(encoding="utf-8")
    scheduled = re.findall(r"(?im)^\s*(?:-\s*)?next due:\s*(\d{4}-\d{2}-\d{2})", text)
    if not scheduled:
        print("no delayed review scheduled yet; append one under Reviews in learning/mastery.md")
        return 0
    today = dt.date.today().isoformat()
    due = [d for d in scheduled if d <= today]
    if due:
        print(f"due for retrieval today ({today}):")
        for d in due:
            print(f"  scheduled {d}; administer without displaying the learning note, then append the result")
    else:
        print(f"next retrieval is scheduled for {scheduled[-1]}; nothing due today ({today})")
    return 0


def cmd_reopen(study: Path) -> int:
    """Report what reopening a finished study needs. Read-only.

    Checks pinned checkouts, archive-record resolvability, and registry
    snapshot availability so a completed study can be evaluated from the
    current checkout without mining git history. State itself only moves
    through status-set.
    """
    data = load_manifest(study)
    mode = data.get("mode")
    status = data.get("status")
    cleaned = data.get("cleaned") or ""
    print(f"{data.get('id', study.name)}: {data.get('title', '')}")
    print(f"mode: {mode}  status: {status}" + (f" (cleaned {cleaned})" if cleaned else ""))
    if mode == "interactive":
        print("interactive studies stay terminal; retrieval reviews run via study.py revisit")
        return 0

    problems: list[str] = []

    repos = study / "sources" / "repos.yaml"
    if repos.is_file():
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "verify_pins.py"), str(study)],
            capture_output=True,
            text=True,
        )
        print(proc.stdout.strip())
        if proc.returncode != 0:
            if proc.stderr.strip():
                print(proc.stderr.strip())
            problems.append("pinned checkouts no longer match the recorded commits")
    else:
        print("pinned checkouts: none recorded")

    archive = study / "archive.yaml"
    if archive.is_file():
        try:
            record = yaml.safe_load(archive.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            record = None
        if not isinstance(record, dict):
            problems.append("archive.yaml is unreadable")
        else:
            commit = str(record.get("git_commit", ""))
            removed = record.get("removed") or []
            if not removed:
                print("archive: cleaned, nothing was removed; knowledge core complete")
            else:
                resolvable = check_all.commit_resolvable(study, commit)
                if resolvable is False:
                    problems.append(f"archive commit {commit[:12]} is not resolvable in this checkout")
                elif resolvable is None:
                    print(f"archive: {len(removed)} removed paths recorded; commit not verifiable outside a git checkout")
                else:
                    print(f"archive: {len(removed)} removed paths recoverable at commit {commit[:12]}")
    elif cleaned:
        problems.append("cleaned study has no archive.yaml; evidence locators are not resolvable")
    else:
        print("archive: study not cleaned, all declared paths should be live")

    registry = study / "sources" / "registry.yaml"
    if registry.is_file():
        try:
            reg = yaml.safe_load(registry.read_text(encoding="utf-8"))
            entries = (reg or {}).get("sources") if isinstance(reg, dict) else []
        except yaml.YAMLError:
            entries = []
        missing = []
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            snapshot = entry.get("snapshot")
            if isinstance(snapshot, str) and snapshot and not (study / snapshot).exists():
                missing.append(str(entry.get("key", "?")))
        if missing:
            shown = ", ".join(missing[:5]) + (" ..." if len(missing) > 5 else "")
            print(f"snapshots: {len(missing)} historical (refetch from url when current behavior matters): {shown}")
        else:
            print("snapshots: all present")

    if status == "done":
        print(f"reopen with: python3 tools/study.py status-set {study.name} review --note \"reopen: <reason>\"")
    elif status == "review":
        if mode == "paper-reading":
            print("already reopened; resume presenting, analyzing, or gathering as the review directs")
        else:
            print("already reopened; resume drafting, gathering, or experimenting as the review directs")
    if problems:
        print("problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "new":
        import new_study  # noqa: PLC0415

        return new_study.main(argv[1:])

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show mode, state, gates, and next action")
    p_status.add_argument("study", help="study id or directory")

    p_set = sub.add_parser("status-set", help="move the study along its transition graph")
    p_set.add_argument("study", help="study id or directory")
    p_set.add_argument("status", help="target status for this study's mode")
    p_set.add_argument("--note", required=True, help="why the study moves now")

    p_approve = sub.add_parser("approve", help="record a human gate decision")
    p_approve.add_argument("study", help="study id or directory")
    p_approve.add_argument(
        "gate",
        help="gate name, e.g. sources, notes, experiments, draft, review, scope, evidence, mastery, paper, analysis, deck",
    )
    p_approve.add_argument("--note", required=True, help="what was inspected and why this is approved")
    p_approve.add_argument("--evidence", default="", help="what was inspected, in more detail than the note")
    p_approve.add_argument("--reopen", default="", help="what would reopen this decision")
    p_approve.add_argument(
        "--verdict",
        choices=("PASS", "CONDITIONAL"),
        default="PASS",
        help="skill verdict written to last_gate_verdict; check_all requires it for done/retained studies",
    )

    for name, help_text in (
        ("practice", "interactive: show practice items without exposing answers"),
        ("assess", "interactive: administer the mastery task"),
        ("revisit", "interactive: list due delayed-review items"),
        ("reopen", "report what reopening a finished study needs (read-only)"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("study", help="study id or directory")

    args = parser.parse_args(argv)
    study = resolve_study(args.study)
    if args.command == "status":
        return cmd_status(study)
    if args.command == "status-set":
        return cmd_status_set(study, args.status, args.note)
    if args.command == "approve":
        return cmd_approve(study, args.gate, args.note, evidence=args.evidence, reopen=args.reopen, verdict=args.verdict)
    if args.command == "practice":
        return cmd_practice(study)
    if args.command == "assess":
        return cmd_assess(study)
    if args.command == "revisit":
        return cmd_revisit(study)
    if args.command == "reopen":
        return cmd_reopen(study)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
