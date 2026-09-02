#!/usr/bin/env python3
"""The cheap path: one question, one anchored note, no study directory.

The full lifecycle is right for a week-long investigation and absurd for
"what is the default RoPE base in Llama 3". Without somewhere cheap to put
the small question you ask a chatbot instead and lose the record, which is
the exact failure this repo exists to prevent. An inbox note keeps the
auditability property (verified sources, explicit gaps) at a fraction of the
ceremony, and can graduate later.

    python3 tools/inbox.py new "Why does RoPE need a base?"
    python3 tools/inbox.py list [--status open]
    python3 tools/inbox.py promote shared/inbox/2026-09-02_rope-base.md --mode delegated
    python3 tools/inbox.py distill shared/inbox/2026-09-02_rope-base.md --id rope.base
    python3 tools/inbox.py queue add "Attention Is All You Need" --url https://...
    python3 tools/inbox.py queue list
    python3 tools/inbox.py queue start 1 --mode paper-reading

`promote` and `start` scaffold a real study and record the link in both
directions, so a question never loses the trail from asking to answering.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import knowledge  # noqa: E402
import new_study  # noqa: E402
from knowledge import rel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "shared" / "inbox"
QUEUE = ROOT / "shared" / "queue.yaml"
TEMPLATE = ROOT / "shared" / "templates" / "inbox-note.md"
TOOLS = Path(__file__).resolve().parent

STATUSES = ("open", "answered", "promoted", "distilled")


def slugify(text: str, limit: int = 6) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words[:limit]) or "question"


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    try:
        meta = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), text[end + 4:].lstrip("\n")


def write_note(path: Path, meta: dict, body: str) -> None:
    path.write_text("---\n" + yaml.dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n" + body, encoding="utf-8")


def load_notes() -> list[tuple[Path, dict, str]]:
    if not INBOX.is_dir():
        return []
    notes = []
    for path in sorted(INBOX.glob("*.md")):
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        notes.append((path, meta, body))
    return notes


def resolve_note(target: str) -> tuple[Path, dict, str]:
    path = Path(target)
    if not path.is_file():
        candidate = INBOX / target
        if candidate.is_file():
            path = candidate
        elif (INBOX / f"{target}.md").is_file():
            path = INBOX / f"{target}.md"
        else:
            raise SystemExit(f"inbox: no note at {target}")
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return path, meta, body


def cmd_new(args: argparse.Namespace) -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    slug = args.slug or slugify(args.question)
    path = INBOX / f"{today}_{slug}.md"
    if path.exists():
        raise SystemExit(f"inbox: {path.name} already exists")
    meta, body = split_frontmatter(TEMPLATE.read_text(encoding="utf-8"))
    meta.update({"question": args.question, "asked": today, "status": "open"})
    body = body.replace("[The question as asked, verbatim]", args.question, 1)
    write_note(path, meta, body)
    print(f"created {rel(path)}")
    print("answer it with verified sources only; anything unverifiable goes under 'Not verified'")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    notes = load_notes()
    if not notes:
        print("inbox: empty")
        return 0
    shown = 0
    for path, meta, _ in notes:
        status = str(meta.get("status") or "open")
        if args.status and status != args.status:
            continue
        shown += 1
        marker = {"open": "?", "answered": "+", "promoted": ">", "distilled": "*"}.get(status, " ")
        print(f" {marker} {status:10} {path.name}")
        print(f"   {meta.get('question', '')}")
        if meta.get("study"):
            print(f"   study: {meta['study']}")
        if meta.get("unit"):
            print(f"   unit:  {meta['unit']}")
    print(f"({shown} of {len(notes)} notes)")
    return 0


def scaffold_study(slug: str, title: str, mode: str, extra: dict[str, str]) -> Path | None:
    """Scaffold a study in-process and return its directory.

    In-process rather than by subprocess so the caller and the scaffolder
    agree on where `studies/` is, which also makes both call sites testable.
    """
    argv = [slug, "--title", title, "--mode", mode]
    for flag, value in extra.items():
        if value:
            argv += [flag, value]
    if new_study.main(argv) != 0:
        return None
    directory = new_study.STUDIES / new_study.study_dir_name(slug, dt.date.today())
    return directory if directory.is_dir() else None


def cmd_promote(args: argparse.Namespace) -> int:
    """Turn a question that outgrew the inbox into a real study."""
    path, meta, body = resolve_note(args.note)
    question = str(meta.get("question") or path.stem)
    slug = args.slug or slugify(question)
    directory = scaffold_study(
        slug,
        question,
        args.mode,
        {"--intent": args.intent, "--assurance": args.assurance, "--methodology": args.methodology},
    )
    if directory is None:
        return 1
    meta.update({"status": "promoted", "study": directory.name})
    write_note(path, meta, body)
    brief = directory / "brief.md"
    if brief.is_file():
        text = brief.read_text(encoding="utf-8")
        marker = "## Prior understanding"
        addition = f"- Promoted from inbox note: `{rel(path)}`\n"
        brief.write_text(text.replace(marker, marker + "\n\n" + addition, 1), encoding="utf-8")
    print(f"inbox: {path.name} promoted to {directory.name}")
    print("the inbox answer is not this study's answer; the study starts from the brief, not from that note")
    return 0


def cmd_distill(args: argparse.Namespace) -> int:
    """Fold an answered question into the knowledge base."""
    path, meta, body = resolve_note(args.note)
    question = str(meta.get("question") or path.stem)
    argv = ["new", args.id, "--question", question]
    for source in meta.get("sources") or []:
        argv += ["--source", str(source)]
    if knowledge.main(argv) != 0:
        return 1
    unit = knowledge.KNOWLEDGE / f"{args.id.replace('.', '-')}.md"
    if unit.is_file():
        answer = extract_section(body, "Answer")
        evidence = extract_section(body, "Evidence")
        gaps = extract_section(body, "Not verified")
        unit.write_text(
            unit.read_text(encoding="utf-8").replace(
                "State the claim, the evidence behind it, and its evidential limits.\n"
                "Link related units with [[other-id]].\n",
                f"## Answer\n\n{answer or '[fill from the inbox note]'}\n\n"
                f"## Evidence\n\n{evidence or '[fill from the inbox note]'}\n\n"
                f"## Evidential limits\n\n{gaps or '[what this does not establish]'}\n\n"
                f"Distilled from `{rel(path)}`.\n",
            ),
            encoding="utf-8",
        )
    meta.update({"status": "distilled", "unit": args.id})
    write_note(path, meta, body)
    print(f"inbox: {path.name} distilled into {args.id}")
    print(f"next: python3 tools/knowledge.py index && python3 tools/review.py schedule {args.id} --in 7d")
    return 0


def extract_section(body: str, heading: str) -> str:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body)
    if not match:
        return ""
    text = re.sub(r"(?s)<!--.*?-->", "", match.group(1)).strip()
    return "" if text.startswith("[") and text.endswith("]") else text


# --- reading queue ---------------------------------------------------------


def load_queue() -> list[dict]:
    if not QUEUE.is_file():
        return []
    data = yaml.safe_load(QUEUE.read_text(encoding="utf-8"))
    items = (data or {}).get("queue") if isinstance(data, dict) else None
    return items if isinstance(items, list) else []


def save_queue(items: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(
        "# Reading queue. Add with tools/inbox.py queue add; start one with queue start <n>.\n"
        + yaml.dump({"queue": items}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def cmd_queue(args: argparse.Namespace) -> int:
    items = load_queue()
    if args.queue_command == "add":
        items.append(
            {
                "title": args.title,
                "url": args.url,
                "why": args.why,
                "added": dt.date.today().isoformat(),
                "status": "queued",
            }
        )
        save_queue(items)
        print(f"queued #{len(items)}: {args.title}")
        return 0
    if args.queue_command == "list":
        if not items:
            print("queue: empty")
            return 0
        for index, item in enumerate(items, start=1):
            flag = "x" if item.get("status") == "started" else " "
            print(f" [{flag}] {index}. {item.get('title', '')}")
            if item.get("url"):
                print(f"        {item['url']}")
            if item.get("why"):
                print(f"        why: {item['why']}")
        return 0
    if args.queue_command == "start":
        if not 1 <= args.number <= len(items):
            raise SystemExit(f"queue: no item {args.number} (queue holds {len(items)})")
        item = items[args.number - 1]
        title = str(item.get("title", ""))
        directory = scaffold_study(slugify(title, limit=8), title, args.mode, {})
        if directory is None:
            return 1
        item["status"] = "started"
        item["study"] = directory.name
        save_queue(items)
        if item.get("url"):
            print(f"record the exact target in {directory.name}/brief.md: {item['url']}")
        return 0
    raise SystemExit("queue: expected add, list, or start")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="open a question note")
    p_new.add_argument("question")
    p_new.add_argument("--slug", default="", help="override the derived filename slug")

    p_list = sub.add_parser("list", help="list question notes")
    p_list.add_argument("--status", default="", choices=("", *STATUSES))

    p_promote = sub.add_parser("promote", help="scaffold a study from a question note")
    p_promote.add_argument("note")
    p_promote.add_argument("--mode", required=True, choices=("interactive", "delegated", "paper-reading"))
    p_promote.add_argument("--slug", default="")
    p_promote.add_argument("--intent", default="")
    p_promote.add_argument("--assurance", default="")
    p_promote.add_argument("--methodology", default="")

    p_distill = sub.add_parser("distill", help="fold a question note into a knowledge unit")
    p_distill.add_argument("note")
    p_distill.add_argument("--id", required=True, help="knowledge unit id to create")

    p_queue = sub.add_parser("queue", help="reading queue")
    qsub = p_queue.add_subparsers(dest="queue_command", required=True)
    q_add = qsub.add_parser("add")
    q_add.add_argument("title")
    q_add.add_argument("--url", default="")
    q_add.add_argument("--why", default="")
    qsub.add_parser("list")
    q_start = qsub.add_parser("start")
    q_start.add_argument("number", type=int)
    q_start.add_argument("--mode", default="paper-reading", choices=("interactive", "delegated", "paper-reading"))

    args = ap.parse_args(argv)
    return {
        "new": cmd_new,
        "list": cmd_list,
        "promote": cmd_promote,
        "distill": cmd_distill,
        "queue": cmd_queue,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
