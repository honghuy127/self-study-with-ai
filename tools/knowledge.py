#!/usr/bin/env python3
"""Manage shared/knowledge/: the durable residue of finished studies.

Studies are disposable; what they leave behind is not. This tool is what
makes "later studies start smarter" a mechanism instead of a hope. Agents run
`search` before gathering so they can skip what the repo already understands,
and `check_all.py` runs `index --check` and `link --check` so the base cannot
rot into duplicate ids and dangling prerequisites.

    python3 tools/knowledge.py new attention.scale --question "Why 1/sqrt(d_k)?"
    python3 tools/knowledge.py search "attention scaling variance"
    python3 tools/knowledge.py index          # rebuild INDEX.md and index.json
    python3 tools/knowledge.py index --check  # fail if they are stale
    python3 tools/knowledge.py link --check   # dangling prereqs and [[links]]
    python3 tools/knowledge.py show attention.scale
    python3 tools/knowledge.py supersede attention.scale attention.scale-v2

A unit is one markdown file with the frontmatter from
shared/templates/knowledge-unit.md. The id is the identity: filenames may
change, ids may not.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "shared" / "knowledge"
TEMPLATE = ROOT / "shared" / "templates" / "knowledge-unit.md"
INDEX_MD = "INDEX.md"
INDEX_JSON = "index.json"
GENERATED = {INDEX_MD, INDEX_JSON}

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def rel(path: Path) -> str:
    """Repo-relative display path, falling back to the absolute one."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from", "how", "in", "is",
    "it", "of", "on", "or", "that", "the", "to", "what", "when", "why", "with",
}


@dataclass
class Unit:
    path: Path
    meta: dict
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        value = self.meta.get("id")
        return value if isinstance(value, str) else ""

    @property
    def question(self) -> str:
        value = self.meta.get("question")
        return value if isinstance(value, str) else ""

    @property
    def title(self) -> str:
        match = re.search(r"(?m)^#\s+(.+?)\s*$", self.body)
        return match.group(1).strip() if match else self.path.stem

    def list_field(self, name: str) -> list[str]:
        value = self.meta.get(name)
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []

    @property
    def next_due(self) -> str:
        review = self.meta.get("review")
        if isinstance(review, dict) and isinstance(review.get("next_due"), str):
            return review["next_due"].strip()
        return ""

    @property
    def superseded_by(self) -> str:
        value = self.meta.get("superseded_by")
        return value.strip() if isinstance(value, str) else ""

    @property
    def links(self) -> list[str]:
        return [match.group(1).strip() for match in WIKILINK.finditer(self.body)]


def split_frontmatter(text: str) -> tuple[dict, str, str]:
    """Return (meta, body, error). A unit without frontmatter is an error."""
    if not text.startswith("---\n"):
        return {}, text, "no frontmatter block"
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text, "frontmatter opened but never closed"
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        return {}, text[end + 4:], f"invalid YAML frontmatter: {exc}"
    if not isinstance(meta, dict):
        return {}, text[end + 4:], "frontmatter did not parse to a mapping"
    return meta, text[end + 4:].lstrip("\n"), ""


def load_units(directory: Path | None = None) -> list[Unit]:
    base = directory or KNOWLEDGE
    if not base.is_dir():
        return []
    units: list[Unit] = []
    for path in sorted(base.glob("*.md")):
        if path.name in GENERATED:
            continue
        meta, body, error = split_frontmatter(path.read_text(encoding="utf-8"))
        unit = Unit(path=path, meta=meta, body=body)
        if error:
            unit.errors.append(error)
        units.append(unit)
    return units


def by_id(units: list[Unit]) -> dict[str, Unit]:
    return {unit.id: unit for unit in units if unit.id}


# --- new -------------------------------------------------------------------


def cmd_new(args: argparse.Namespace) -> int:
    if not ID_RE.match(args.id):
        raise SystemExit(f"knowledge: invalid id {args.id!r}; use lowercase words separated by . - or _")
    KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    existing = by_id(load_units())
    if args.id in existing:
        raise SystemExit(f"knowledge: id {args.id!r} already exists at {existing[args.id].path.name}")
    path = KNOWLEDGE / f"{args.id.replace('.', '-')}.md"
    if path.exists():
        raise SystemExit(f"knowledge: {path.name} already exists")
    meta = {
        "id": args.id,
        "question": args.question,
        "prerequisites": args.prereq,
        "source_ids": args.source,
        "misconceptions": [],
        "tags": args.tag,
        "studies": [args.study] if args.study else [],
        "mastery": {"last_assessed": "", "level": "", "help": ""},
        "review": {"next_due": ""},
        "superseded_by": "",
    }
    path.write_text(
        "---\n"
        + yaml.dump(meta, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + f"# {args.title or args.question}\n\n"
        + "State the claim, the evidence behind it, and its evidential limits.\n"
        + "Link related units with [[other-id]].\n",
        encoding="utf-8",
    )
    print(f"created {rel(path)}")
    return 0


# --- index -----------------------------------------------------------------


def render_index_md(units: list[Unit]) -> str:
    live = [u for u in units if not u.superseded_by]
    retired = [u for u in units if u.superseded_by]
    lines = [
        "<!-- Generated by tools/knowledge.py index. Do not edit by hand. -->",
        "# Knowledge index",
        "",
        f"{len(live)} live units, {len(retired)} superseded. "
        "Search before gathering: `python3 tools/knowledge.py search \"<question>\"`.",
        "",
        "| Unit | Question | Prerequisites | Next review |",
        "|---|---|---|---|",
    ]
    for unit in sorted(live, key=lambda u: u.id):
        prereqs = ", ".join(f"`{p}`" for p in unit.list_field("prerequisites")) or "none"
        due = unit.next_due or "unscheduled"
        lines.append(f"| [`{unit.id}`]({unit.path.name}) | {unit.question} | {prereqs} | {due} |")
    if retired:
        lines += ["", "## Superseded", ""]
        for unit in sorted(retired, key=lambda u: u.id):
            lines.append(f"- `{unit.id}` superseded by `{unit.superseded_by}`")
    return "\n".join(lines) + "\n"


def render_index_json(units: list[Unit]) -> str:
    payload = [
        {
            "id": unit.id,
            "file": unit.path.name,
            "title": unit.title,
            "question": unit.question,
            "prerequisites": unit.list_field("prerequisites"),
            "source_ids": unit.list_field("source_ids"),
            "tags": unit.list_field("tags"),
            "studies": unit.list_field("studies"),
            "next_due": unit.next_due,
            "superseded_by": unit.superseded_by,
        }
        for unit in sorted(units, key=lambda u: u.id)
    ]
    return json.dumps({"generated_by": "tools/knowledge.py", "units": payload}, indent=2) + "\n"


def cmd_index(args: argparse.Namespace) -> int:
    units = load_units()
    if not units:
        print("knowledge: no units yet; nothing to index")
        return 0
    targets = {KNOWLEDGE / INDEX_MD: render_index_md(units), KNOWLEDGE / INDEX_JSON: render_index_json(units)}
    stale = [p for p, content in targets.items() if not p.is_file() or p.read_text(encoding="utf-8") != content]
    if args.check:
        if stale:
            names = ", ".join(p.name for p in stale)
            print(f"knowledge: index is stale ({names}); run python3 tools/knowledge.py index")
            return 1
        print(f"knowledge: index current ({len(units)} units)")
        return 0
    for path, content in targets.items():
        path.write_text(content, encoding="utf-8")
    print(f"knowledge: indexed {len(units)} units into {INDEX_MD} and {INDEX_JSON}")
    return 0


# --- link ------------------------------------------------------------------


def link_errors(units: list[Unit]) -> list[str]:
    """Structural problems that make the base unreliable to read from."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    for unit in units:
        name = unit.path.name
        for problem in unit.errors:
            errors.append(f"{name}: {problem}")
        if not unit.id:
            errors.append(f"{name}: frontmatter has no id")
            continue
        if unit.id in seen:
            errors.append(f"{name}: duplicate id {unit.id!r} (also in {seen[unit.id]})")
        else:
            seen[unit.id] = name
        if not unit.question:
            errors.append(f"{name}: frontmatter has no question")
    known = set(seen)
    for unit in units:
        name = unit.path.name
        for prereq in unit.list_field("prerequisites"):
            if prereq not in known:
                errors.append(f"{name}: prerequisite {prereq!r} resolves to no unit")
        target = unit.superseded_by
        if target and target not in known:
            errors.append(f"{name}: superseded_by {target!r} resolves to no unit")
        for link in unit.links:
            if link not in known and not (KNOWLEDGE / f"{link}.md").exists():
                errors.append(f"{name}: [[{link}]] resolves to no unit")
    return errors


def cmd_link(args: argparse.Namespace) -> int:
    units = load_units()
    if not units:
        print("knowledge: no units yet; nothing to link-check")
        return 0
    errors = link_errors(units)
    for error in errors:
        print(f"knowledge {error}")
    if errors:
        return 1
    orphans = [u.id for u in units if not u.list_field("prerequisites") and not u.links]
    print(f"knowledge: {len(units)} units, links resolve")
    if orphans and not args.check:
        print(f"unlinked units (fine early on, worth connecting later): {', '.join(sorted(orphans))}")
    return 0


# --- search ----------------------------------------------------------------


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1]


def score(unit: Unit, terms: list[str]) -> int:
    """Weighted term hits: the question is what a unit promises to answer."""
    haystacks = (
        (unit.question.lower(), 5),
        (unit.id.lower().replace(".", " "), 4),
        (" ".join(unit.list_field("tags")).lower(), 3),
        (unit.title.lower(), 3),
        (unit.body.lower(), 1),
    )
    total = 0
    for term in terms:
        for text, weight in haystacks:
            total += text.count(term) * weight
    return total


def cmd_search(args: argparse.Namespace) -> int:
    terms = tokenize(" ".join(args.query))
    if not terms:
        raise SystemExit("knowledge: nothing searchable in that query")
    units = load_units()
    ranked = sorted(
        ((score(u, terms), u) for u in units if score(u, terms) > 0),
        key=lambda pair: (-pair[0], pair[1].id),
    )[: args.limit]
    if args.json:
        print(json.dumps(
            [
                {"id": u.id, "file": u.path.name, "question": u.question, "score": s, "superseded_by": u.superseded_by}
                for s, u in ranked
            ],
            indent=2,
        ))
        return 0
    if not ranked:
        print("no existing unit covers this; gather from sources")
        return 0
    print(f"{len(ranked)} existing unit(s) may already answer this:")
    for value, unit in ranked:
        flag = f"  [superseded by {unit.superseded_by}]" if unit.superseded_by else ""
        print(f"  {unit.id:32} {unit.question}{flag}")
        print(f"  {'':32} {rel(unit.path)} (score {value})")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    units = by_id(load_units())
    unit = units.get(args.id)
    if unit is None:
        raise SystemExit(f"knowledge: no unit with id {args.id!r}")
    print(unit.path.read_text(encoding="utf-8"))
    return 0


# --- supersede -------------------------------------------------------------


def cmd_supersede(args: argparse.Namespace) -> int:
    units = by_id(load_units())
    old, new = units.get(args.old), units.get(args.new)
    if old is None:
        raise SystemExit(f"knowledge: no unit with id {args.old!r}")
    if new is None:
        raise SystemExit(f"knowledge: no unit with id {args.new!r}; write the replacement first")
    if old.id == new.id:
        raise SystemExit("knowledge: a unit cannot supersede itself")
    text = old.path.read_text(encoding="utf-8")
    if re.search(r"(?m)^superseded_by:", text):
        updated = re.sub(r"(?m)^superseded_by:.*$", f"superseded_by: {args.new}", text, count=1)
    else:
        updated = text.replace("---\n", f"---\nsuperseded_by: {args.new}\n", 1)
    old.path.write_text(updated, encoding="utf-8")
    print(f"knowledge: {args.old} is now superseded by {args.new}")
    print("rerun: python3 tools/knowledge.py index")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--dir",
        default="",
        help="knowledge base to operate on (default: shared/knowledge; examples/knowledge is the shipped one)",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="create a knowledge unit")
    p_new.add_argument("id", help="stable id, e.g. attention.scale")
    p_new.add_argument("--question", required=True, help="the single question this unit answers")
    p_new.add_argument("--title", default="", help="page title (defaults to the question)")
    p_new.add_argument("--prereq", action="append", default=[], help="prerequisite unit id (repeatable)")
    p_new.add_argument("--source", action="append", default=[], help="registry key backing this unit (repeatable)")
    p_new.add_argument("--tag", action="append", default=[], help="tag (repeatable)")
    p_new.add_argument("--study", default="", help="study id this unit was distilled from")

    p_index = sub.add_parser("index", help="rebuild INDEX.md and index.json")
    p_index.add_argument("--check", action="store_true", help="fail if the index is stale instead of rebuilding")

    p_link = sub.add_parser("link", help="validate ids, prerequisites, and [[links]]")
    p_link.add_argument("--check", action="store_true", help="suppress the advisory orphan list")

    p_search = sub.add_parser("search", help="rank units against a question")
    p_search.add_argument("query", nargs="+")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--json", action="store_true")

    p_show = sub.add_parser("show", help="print one unit")
    p_show.add_argument("id")

    p_sup = sub.add_parser("supersede", help="mark one unit superseded by another")
    p_sup.add_argument("old")
    p_sup.add_argument("new")

    args = ap.parse_args(argv)
    if args.dir:
        # Point every command at an alternate base. Used by check_all.py to
        # validate the shipped examples/knowledge tree the same way it
        # validates the user's own.
        global KNOWLEDGE
        KNOWLEDGE = Path(args.dir).resolve()
    handlers = {
        "new": cmd_new,
        "index": cmd_index,
        "link": cmd_link,
        "search": cmd_search,
        "show": cmd_show,
        "supersede": cmd_supersede,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
