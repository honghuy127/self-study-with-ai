#!/usr/bin/env python3
"""Render the contract tables in README.md and AGENTS.md from tools/contracts.py.

The lifecycle used to exist three times: as Python constants, as prose in the
README, and as prose in AGENTS.md. Two of those copies drifted silently. Now
the docs carry marked regions that this tool fills from the constants, and
`check_all.py` fails when they are stale.

    python3 tools/docsgen.py            # rewrite the marked regions in place
    python3 tools/docsgen.py --check    # exit 1 if any region is stale

A region looks like:

    <!-- BEGIN GENERATED: modes -->
    ...rendered markdown, do not edit by hand...
    <!-- END GENERATED: modes -->
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contracts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ("README.md", "AGENTS.md")

BLOCK_RE = re.compile(
    r"(?ms)^<!-- BEGIN GENERATED: (?P<name>[a-z-]+) -->\n.*?^<!-- END GENERATED: (?P=name) -->"
)


def render(name: str) -> str:
    renderer = contracts.BLOCKS.get(name)
    if renderer is None:
        raise SystemExit(f"docsgen: unknown generated block {name!r}; known: {', '.join(sorted(contracts.BLOCKS))}")
    return renderer()


def rewrite(text: str) -> tuple[str, list[str]]:
    """Return (new text, names of blocks found)."""
    names: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        names.append(name)
        body = render(name)
        return f"<!-- BEGIN GENERATED: {name} -->\n{body}\n<!-- END GENERATED: {name} -->"

    return BLOCK_RE.sub(replace, text), names


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report stale regions instead of rewriting them")
    args = ap.parse_args(argv)

    stale: list[str] = []
    total = 0
    for name in TARGETS:
        path = ROOT / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new_text, found = rewrite(text)
        total += len(found)
        if new_text == text:
            continue
        if args.check:
            stale.append(name)
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"docsgen: updated {name} ({len(found)} blocks)")

    if args.check:
        if stale:
            print(f"docsgen: stale generated blocks in {', '.join(stale)}; run python3 tools/docsgen.py")
            return 1
        print(f"docsgen: {total} generated blocks current")
        return 0
    if total == 0:
        print("docsgen: no generated blocks found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
