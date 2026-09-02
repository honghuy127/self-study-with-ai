#!/usr/bin/env python3
"""PreToolUse hook: refuse edits to files the lifecycle CLI owns.

OpenCode enforces each agent's write zone with per-glob edit permissions.
Claude Code has no equivalent, so the invariants that do not depend on which
agent is running are enforced here instead, for every agent and the main
session alike:

  * `study.yaml` gates and status move only through `python3 tools/study.py`
    (status-set and approve), which validates the transition and appends an
    event. A hand-edited manifest is a lie the rest of the system trusts.
  * `events.jsonl` is append-only provenance, written by that same CLI.
  * `archive.yaml` is written by `tools/cleanup_study.py` and records where
    the packed evidence went; editing it by hand breaks retrieval.
  * PDF binaries are never committed under a study; the hygiene gate fails on
    tracked PDFs, so catch them at write time.

The append-only rule for the learner's own records (`learning/baseline.md`,
`learning/mastery.md`, `learning/attempts/`) is deliberately not enforced
here: those files have to be written once, legitimately, by the tutor and the
assessor. That boundary lives in the agent write zones and in the prose.

Blocking is exit code 2 with the reason on stderr, which is what tells the
model why the edit was refused. Everything else exits 0 and stays silent.

Wire it up in .claude/settings.json (already done in this repo):

    "hooks": {"PreToolUse": [{"matcher": "Edit|Write|NotebookEdit",
      "hooks": [{"type": "command", "command": "python3 tools/zone_guard.py"}]}]}
"""
from __future__ import annotations

import json
import sys
from pathlib import PurePosixPath

WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}

RULES = (
    (
        lambda p: p.name == "study.yaml" and _under_study(p),
        "study.yaml is owned by the lifecycle CLI. Move state with "
        "`python3 tools/study.py status-set <id> <status> --note \"...\"` and record gate "
        "decisions with `python3 tools/study.py approve <id> <gate> --note \"...\"`, which "
        "validate the transition and append to events.jsonl.",
    ),
    (
        lambda p: p.name == "events.jsonl",
        "events.jsonl is append-only provenance written by tools/study.py. Never edit it by hand.",
    ),
    (
        lambda p: p.name == "archive.yaml" and _under_study(p),
        "archive.yaml is written by tools/cleanup_study.py and names the packed archive plus its "
        "checksum. Editing it by hand breaks evidence retrieval.",
    ),
    (
        lambda p: p.suffix.lower() == ".pdf",
        "PDF binaries are never written into the repo. Keep the remote URL in the registry and "
        "a pdftotext snapshot under sources/docs/ instead; the hygiene gate fails on tracked PDFs.",
    ),
)


def _under_study(path: PurePosixPath) -> bool:
    return "studies" in path.parts or "examples" in path.parts


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if payload.get("tool_name") not in WRITE_TOOLS:
        return 0
    target = (payload.get("tool_input") or {}).get("file_path")
    if not isinstance(target, str) or not target:
        return 0
    path = PurePosixPath(target.replace("\\", "/"))
    for matches, reason in RULES:
        if matches(path):
            print(f"zone_guard: refusing to edit {path.name}. {reason}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
