#!/usr/bin/env python3
"""Cross-study retrieval practice over shared/knowledge/.

A study ends the moment its report is written, which is exactly when
forgetting starts. The repo already carried the pieces of a review loop, a
`review.next_due` field on every knowledge unit and a Reviews section in every
mastery record, but nothing read them. This is the part that reads them.

    python3 tools/review.py due                 # everything due today
    python3 tools/review.py run attention.scale # ask the question, withhold the answer
    python3 tools/review.py record attention.scale --result recalled
    python3 tools/review.py schedule attention.scale --in 7d
    python3 tools/review.py log --limit 20

Scheduling is a fixed expanding ladder rather than a tuned SM-2: a recalled
item moves out one rung, a partial recall repeats the current rung, and a
miss drops back to the first. The ladder is legible, which matters more here
than optimality, and every outcome is appended to shared/review-log.jsonl so
the record survives any change to the algorithm.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import knowledge  # noqa: E402
from knowledge import rel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STUDIES = ROOT / "studies"
EXAMPLES = ROOT / "examples"
LOG = ROOT / "shared" / "review-log.jsonl"

LADDER = (1, 7, 30, 90, 180, 365)
RESULTS = ("recalled", "partial", "missed")
HELP_LEVELS = ("none", "hint")

# Sections of a knowledge unit that would give the answer away during
# retrieval. Everything else is context the learner may see up front.
WITHHELD_HEADINGS = ("answer", "claim", "explanation", "derivation", "evidence", "worked")


def today(value: str = "") -> dt.date:
    return dt.date.fromisoformat(value) if value else dt.date.today()


def parse_interval(text: str) -> int:
    match = re.fullmatch(r"(\d+)\s*([dwmy]?)", text.strip().lower())
    if not match:
        raise SystemExit(f"review: cannot read interval {text!r}; use forms like 7d, 3w, 6m")
    count = int(match.group(1))
    return count * {"": 1, "d": 1, "w": 7, "m": 30, "y": 365}[match.group(2)]


def next_interval(current: int, result: str) -> int:
    """Advance, hold, or reset on the ladder."""
    if result == "missed":
        return LADDER[0]
    if result == "partial":
        return current if current in LADDER else LADDER[0]
    for rung in LADDER:
        if rung > current:
            return rung
    return LADDER[-1]


def review_state(unit: knowledge.Unit) -> dict:
    state = unit.meta.get("review")
    return dict(state) if isinstance(state, dict) else {}


def write_review_state(unit: knowledge.Unit, state: dict) -> None:
    """Rewrite only the review block, leaving the rest of the file untouched."""
    text = unit.path.read_text(encoding="utf-8")
    meta, body, error = knowledge.split_frontmatter(text)
    if error:
        raise SystemExit(f"review: {unit.path.name}: {error}")
    meta["review"] = state
    unit.path.write_text(
        "---\n" + yaml.dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n" + body,
        encoding="utf-8",
    )


def append_log(record: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"ts": dt.datetime.now().astimezone().isoformat(timespec="seconds"), **record}) + "\n")


def mastery_due(on: dt.date) -> list[tuple[str, str, str]]:
    """Delayed reviews scheduled inside interactive mastery records.

    Returns (study id, scheduled date, path). These stay owned by
    `study.py revisit`, which administers the original mastery task; review.py
    only surfaces them so one command answers "what is due today".
    """
    found: list[tuple[str, str, str]] = []
    for root in (STUDIES, EXAMPLES):
        if not root.is_dir():
            continue
        for mastery in sorted(root.glob("*/learning/mastery.md")):
            text = mastery.read_text(encoding="utf-8")
            dates = re.findall(r"(?im)^\s*(?:-\s*)?next due:\s*(\d{4}-\d{2}-\d{2})", text)
            if not dates:
                continue
            latest = max(dates)
            if dt.date.fromisoformat(latest) <= on:
                found.append((mastery.parent.parent.name, latest, rel(mastery)))
    return found


def cmd_due(args: argparse.Namespace) -> int:
    on = today(args.on)
    units = [u for u in knowledge.load_units() if not u.superseded_by]
    scheduled = [(u, u.next_due) for u in units if u.next_due]
    due = sorted(((u, d) for u, d in scheduled if dt.date.fromisoformat(d) <= on), key=lambda pair: pair[1])
    upcoming = sorted(((u, d) for u, d in scheduled if dt.date.fromisoformat(d) > on), key=lambda pair: pair[1])
    unscheduled = [u for u in units if not u.next_due]

    if due:
        print(f"due for retrieval on {on.isoformat()}:")
        for unit, when in due:
            overdue = (on - dt.date.fromisoformat(when)).days
            late = f" ({overdue} days late)" if overdue > 0 else ""
            print(f"  {unit.id:32} scheduled {when}{late}")
        print("\nadminister one with: python3 tools/review.py run <id>")
    else:
        print(f"nothing due on {on.isoformat()}")

    mastery = mastery_due(on)
    if mastery:
        print("\ninteractive mastery reviews due (administer via study.py revisit):")
        for study_id, when, path in mastery:
            print(f"  {study_id:32} scheduled {when}  {path}")

    if upcoming and args.verbose:
        print("\nupcoming:")
        for unit, when in upcoming[:10]:
            print(f"  {unit.id:32} {when}")
    if unscheduled:
        print(f"\n{len(unscheduled)} unit(s) have no review scheduled: {', '.join(u.id for u in unscheduled[:8])}")
        print("schedule one with: python3 tools/review.py schedule <id> --in 7d")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    units = knowledge.by_id(knowledge.load_units())
    unit = units.get(args.id)
    if unit is None:
        raise SystemExit(f"review: no unit with id {args.id!r}")
    print(f"retrieval: {unit.id}   (answer from memory before reading anything)")
    print(f"\nquestion: {unit.question}")
    prereqs = unit.list_field("prerequisites")
    if prereqs:
        print(f"assumes: {', '.join(prereqs)}")
    withheld = False
    for heading, body in _sections(unit.body):
        if any(heading.strip().lower().startswith(name) for name in WITHHELD_HEADINGS):
            withheld = True
            continue
        text = body.strip()
        if text:
            print(f"\n## {heading}\n\n{text}")
    if withheld:
        print("\n[the answering sections are withheld until you record a result]")
    print(
        f"\nthen: python3 tools/review.py record {unit.id} --result recalled|partial|missed"
        f"\nthe full page is at {rel(unit.path)}"
    )
    return 0


def _sections(body: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", body))
    out = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        out.append((match.group(1), body[match.end():end]))
    return out


def cmd_record(args: argparse.Namespace) -> int:
    units = knowledge.by_id(knowledge.load_units())
    unit = units.get(args.id)
    if unit is None:
        raise SystemExit(f"review: no unit with id {args.id!r}")
    on = today(args.on)
    state = review_state(unit)
    current = int(state.get("interval_days") or 0)
    interval = next_interval(current, args.result)
    due = on + dt.timedelta(days=interval)
    state.update(
        {
            "next_due": due.isoformat(),
            "interval_days": interval,
            "last_reviewed": on.isoformat(),
            "last_result": args.result,
            "reviews": int(state.get("reviews") or 0) + 1,
        }
    )
    write_review_state(unit, state)
    append_log(
        {
            "unit": unit.id,
            "date": on.isoformat(),
            "result": args.result,
            "help": args.help_level,
            "interval_days": interval,
            "next_due": due.isoformat(),
            "note": args.note,
        }
    )
    print(f"review: {unit.id} {args.result} at help level {args.help_level}; next due {due.isoformat()} (+{interval}d)")
    if args.result != "recalled":
        print(f"reread {rel(unit.path)} now, while the gap is still open")
    print("rerun: python3 tools/knowledge.py index")
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    units = knowledge.by_id(knowledge.load_units())
    unit = units.get(args.id)
    if unit is None:
        raise SystemExit(f"review: no unit with id {args.id!r}")
    days = parse_interval(args.interval)
    due = today(args.on) + dt.timedelta(days=days)
    state = review_state(unit)
    state.update({"next_due": due.isoformat(), "interval_days": days})
    write_review_state(unit, state)
    append_log({"unit": unit.id, "date": today(args.on).isoformat(), "result": "scheduled", "next_due": due.isoformat()})
    print(f"review: {unit.id} next due {due.isoformat()} (+{days}d)")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    if not LOG.is_file():
        print("review: no review log yet")
        return 0
    lines = [line for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in lines[-args.limit:]:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        print(
            f"{record.get('date', '?'):12} {record.get('unit', '?'):32} "
            f"{record.get('result', '?'):10} next {record.get('next_due', '?')}"
        )
    print(f"({len(lines)} entries in {rel(LOG)})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_due = sub.add_parser("due", help="list units and mastery reviews due")
    p_due.add_argument("--on", default="", help="pretend today is this ISO date")
    p_due.add_argument("--verbose", action="store_true", help="also show upcoming reviews")

    p_run = sub.add_parser("run", help="administer one retrieval, answer withheld")
    p_run.add_argument("id")

    p_record = sub.add_parser("record", help="record a retrieval outcome and reschedule")
    p_record.add_argument("id")
    p_record.add_argument("--result", required=True, choices=RESULTS)
    p_record.add_argument("--help-level", default="none", choices=HELP_LEVELS, dest="help_level")
    p_record.add_argument("--note", default="", help="what was missing, in your own words")
    p_record.add_argument("--on", default="", help="pretend today is this ISO date")

    p_sched = sub.add_parser("schedule", help="set the next review explicitly")
    p_sched.add_argument("id")
    p_sched.add_argument("--in", dest="interval", required=True, help="7d, 3w, 6m, 1y")
    p_sched.add_argument("--on", default="", help="pretend today is this ISO date")

    p_log = sub.add_parser("log", help="show recent review outcomes")
    p_log.add_argument("--limit", type=int, default=20)

    args = ap.parse_args(argv)
    return {"due": cmd_due, "run": cmd_run, "record": cmd_record, "schedule": cmd_schedule, "log": cmd_log}[
        args.command
    ](args)


if __name__ == "__main__":
    sys.exit(main())
