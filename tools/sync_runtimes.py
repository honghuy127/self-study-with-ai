#!/usr/bin/env python3
"""Generate the OpenCode and Claude Code agent layers from runtime/.

The whole operating layer (six specialist agents and the lifecycle commands)
used to exist only as OpenCode files, so the repo could not be driven from any
other harness. The definitions now live once in `runtime/`, in a neutral
frontmatter, and this tool renders them into each harness's dialect.

    python3 tools/sync_runtimes.py           # regenerate .opencode/ and .claude/
    python3 tools/sync_runtimes.py --check   # fail if either is out of date

Neutral agent frontmatter:

    name:        agent id, matching the filename
    description: one line, used by both harnesses for dispatch
    stage:       which lifecycle stage runs this agent
    webfetch:    allow | ask | deny
    websearch:   allow | ask | deny
    bash:        allow | ask | deny
    writes:      list of globs the agent may edit; everything else is denied

The two harnesses enforce that differently, and the difference is real rather
than papered over. OpenCode takes per-glob edit rules directly. Claude Code
has no per-glob edit permission, so the write zone is rendered into the agent
prose and the repo-wide invariants (nobody hand-edits study.yaml or
events.jsonl) are enforced by the PreToolUse hook in tools/zone_guard.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "runtime"
OPENCODE = ROOT / ".opencode"
CLAUDE = ROOT / ".claude"

BANNER = "<!-- Generated from runtime/{kind}/{name}.md by tools/sync_runtimes.py. Edit the source, not this file. -->"

# Claude Code expresses capability as a tool allowlist rather than per-glob
# permissions. Every agent reads and writes files; the rest follows the
# neutral frontmatter.
BASE_TOOLS = ("Read", "Grep", "Glob", "Edit", "Write")


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit(f"sync_runtimes: {path.name} has no frontmatter block")
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise SystemExit(f"sync_runtimes: {path.name} frontmatter did not parse to a mapping")
    return meta, parts[2].lstrip("\n")


def yaml_line(key: str, value: str, indent: int = 0) -> str:
    """Emit one scalar, quoted whenever the value could break the parser."""
    needs_quotes = any(ch in value for ch in ':#"') or value.strip() != value
    rendered = '"' + value.replace('"', '\\"') + '"' if needs_quotes else value
    return f"{' ' * indent}{key}: {rendered}"


def wrap(text: str, width: int = 78, indent: int = 2) -> str:
    """Fold a long description onto continuation lines YAML reads as one scalar."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return ("\n" + " " * indent).join(lines)


def render_opencode_agent(meta: dict, body: str) -> str:
    writes = meta.get("writes") or []
    lines = ["---", yaml_line("description", meta["description"]), "mode: subagent", "permission:"]
    lines.append(f"  webfetch: {meta.get('webfetch', 'deny')}")
    lines.append(f"  websearch: {meta.get('websearch', 'deny')}")
    lines.append("  edit:")
    lines.append('    "*": deny')
    for glob in writes:
        lines.append(f'    "{glob}": allow')
    lines.append(f"  bash: {meta.get('bash', 'deny')}")
    lines.append("---")
    lines.append("")
    lines.append(BANNER.format(kind="agents", name=meta["name"]))
    lines.append("")
    return "\n".join(lines) + body


def claude_tools(meta: dict) -> list[str]:
    tools = list(BASE_TOOLS)
    if meta.get("webfetch") in ("allow", "ask"):
        tools.append("WebFetch")
    if meta.get("websearch") in ("allow", "ask"):
        tools.append("WebSearch")
    if meta.get("bash") in ("allow", "ask"):
        tools.append("Bash")
    return tools


def render_claude_agent(meta: dict, body: str) -> str:
    writes = meta.get("writes") or []
    zone = "\n".join(f"- `{glob}`" for glob in writes) or "- (nothing; this agent is read-only)"
    denied = []
    if meta.get("webfetch") == "deny" and meta.get("websearch") == "deny":
        denied.append(
            "You have no web access. If a fact is not in the study's files, it does not exist for you; "
            "mark the gap rather than filling it from memory."
        )
    if meta.get("bash") == "deny":
        denied.append("You may not run commands. Hand any command you need to the coordinator.")
    lines = [
        "---",
        yaml_line("name", meta["name"]),
        f"description: >-\n  {wrap(meta['description'])}",
        f"tools: {', '.join(claude_tools(meta))}",
        "---",
        "",
        BANNER.format(kind="agents", name=meta["name"]),
        "",
    ]
    trailer = [
        "",
        "## Write zone (enforced by contract)",
        "",
        "You may create or edit only these paths:",
        "",
        zone,
        "",
        "Anything else, including `study.yaml` and `events.jsonl`, is out of bounds. Lifecycle",
        "state and gates move only through `python3 tools/study.py`; the PreToolUse hook in",
        "`tools/zone_guard.py` refuses those edits outright.",
    ]
    if denied:
        trailer += ["", *[f"{line}" for line in denied]]
    return "\n".join(lines) + body.rstrip("\n") + "\n" + "\n".join(trailer) + "\n"


def render_opencode_command(meta: dict, body: str) -> str:
    lines = [
        "---",
        yaml_line("description", meta["description"]),
        f"agent: {meta.get('agent', 'build')}",
        "---",
        "",
        BANNER.format(kind="commands", name=meta["name"]),
        "",
    ]
    return "\n".join(lines) + body


def render_claude_command(meta: dict, body: str) -> str:
    lines = ["---", f"description: >-\n  {wrap(meta['description'])}"]
    if meta.get("argument-hint"):
        lines.append(yaml_line("argument-hint", str(meta["argument-hint"])))
    lines += ["---", "", BANNER.format(kind="commands", name=meta["name"]), ""]
    return "\n".join(lines) + body


TARGETS = (
    ("agents", OPENCODE / "agents", render_opencode_agent),
    ("agents", CLAUDE / "agents", render_claude_agent),
    ("commands", OPENCODE / "commands", render_opencode_command),
    ("commands", CLAUDE / "commands", render_claude_command),
)


def generate() -> dict[Path, str]:
    output: dict[Path, str] = {}
    for kind, directory, renderer in TARGETS:
        source_dir = SOURCE / kind
        if not source_dir.is_dir():
            continue
        for path in sorted(source_dir.glob("*.md")):
            meta, body = parse(path)
            if meta.get("name") != path.stem:
                raise SystemExit(f"sync_runtimes: {path.name} declares name {meta.get('name')!r}")
            output[directory / path.name] = renderer(meta, body)
    return output


def orphans(generated: dict[Path, str]) -> list[Path]:
    """Generated files whose source disappeared."""
    stale = []
    for _, directory, _ in TARGETS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path not in generated and "Generated from runtime/" in path.read_text(encoding="utf-8"):
                stale.append(path)
    return stale


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report differences instead of writing")
    args = ap.parse_args(argv)

    if not SOURCE.is_dir():
        print(f"sync_runtimes: no runtime/ directory at {SOURCE}")
        return 1
    generated = generate()
    stale = orphans(generated)
    differences = [
        path for path, content in generated.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]

    if args.check:
        for path in differences:
            print(f"sync_runtimes: stale {path.relative_to(ROOT).as_posix()}")
        for path in stale:
            print(f"sync_runtimes: orphaned {path.relative_to(ROOT).as_posix()} (no runtime/ source)")
        if differences or stale:
            print("run: python3 tools/sync_runtimes.py")
            return 1
        print(f"sync_runtimes: {len(generated)} generated files current")
        return 0

    for path, content in generated.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for path in stale:
        path.unlink()
        print(f"removed orphan {path.relative_to(ROOT).as_posix()}")
    print(f"sync_runtimes: wrote {len(generated)} files from {SOURCE.name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
