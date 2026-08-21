#!/usr/bin/env python3
"""Lifecycle CLI for studies: the human-facing front door.

Usage: python3 tools/study.py <command> [args]

  new        scaffold a study (same flags as tools/new_study.py; --mode required)
  status     <id>                    show mode, state, gates, and next action
  approve    <id> <gate> --note ...  record a human gate decision
  practice   <id>                    interactive: show practice items without exposing answers
  assess     <id>                    interactive: administer the mastery task
  revisit    <id>                    interactive: list due delayed-review items

`approve` is the only way gates flip: it records the decision with a note in
approvals.jsonl and updates the manifest. Agents may propose, never approve.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"

MODE_GATES = {
    "delegated": ("sources_approved", "notes_approved", "experiments_approved", "draft_approved", "review_signed_off"),
    "interactive": ("scope_approved", "evidence_approved", "experiments_approved", "mastery_approved"),
}

GATE_ALIASES = {
    "sources": "sources_approved",
    "notes": "notes_approved",
    "experiments": "experiments_approved",
    "draft": "draft_approved",
    "review": "review_signed_off",
    "scope": "scope_approved",
    "evidence": "evidence_approved",
    "mastery": "mastery_approved",
}

NEXT_ACTION = {
    "proposed": "fill brief.md and get scope approval, then /gather",
    "gathering": "register sources, then stop for sources approval",
    "summarizing": "note every registered source, then stop for notes approval",
    "experimenting": "run the approved experiments, then stop for experiments approval",
    "drafting": "synthesize and draft the report, then stop for draft approval",
    "review": "independent review, then stop for review sign-off",
    "done": "merge shared/ knowledge, then tools/cleanup_study.py",
    "scoped": "record the unaided baseline in learning/baseline.md, then approve scope",
    "diagnosing": "plan the concept path in learning/map.md from the baseline",
    "learning": "tutor one link at a time; journal every exchange in learning/journal.md",
    "practicing": "administer near and transfer practice (study practice)",
    "assessing": "administer the mastery task unaided (study assess), then approve mastery",
    "retained": "distill outputs/learning-note.md and schedule the delayed review (study revisit)",
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
    print(f"next: {NEXT_ACTION.get(status, 'no automatic suggestion for this state')}")
    return 0


def cmd_approve(study: Path, gate: str, note: str) -> int:
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
    manifest.write_text(new_text, encoding="utf-8")

    record = {"gate": resolved, "note": note, "actor": "human", "date": dt.date.today().isoformat()}
    with (study / "approvals.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
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


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "new":
        import new_study  # noqa: PLC0415

        return new_study.main(argv[1:])

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show mode, state, gates, and next action")
    p_status.add_argument("study", help="study id or directory")

    p_approve = sub.add_parser("approve", help="record a human gate decision")
    p_approve.add_argument("study", help="study id or directory")
    p_approve.add_argument("gate", help="gate name, e.g. sources, notes, experiments, draft, review, scope, evidence, mastery")
    p_approve.add_argument("--note", required=True, help="what was inspected and why this is approved")

    for name, help_text in (
        ("practice", "interactive: show practice items without exposing answers"),
        ("assess", "interactive: administer the mastery task"),
        ("revisit", "interactive: list due delayed-review items"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("study", help="study id or directory")

    args = parser.parse_args(argv)
    study = resolve_study(args.study)
    if args.command == "status":
        return cmd_status(study)
    if args.command == "approve":
        return cmd_approve(study, args.gate, args.note)
    if args.command == "practice":
        return cmd_practice(study)
    if args.command == "assess":
        return cmd_assess(study)
    if args.command == "revisit":
        return cmd_revisit(study)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
