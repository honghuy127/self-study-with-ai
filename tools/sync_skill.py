#!/usr/bin/env python3
"""Refresh the vendored dossier scripts from the conduct-cs-ai-research skill.

The four dossier scripts are vendored under `tools/research/` and the skill
submodule is their upstream. Vendoring is deliberate: a checkout whose
submodule was never initialized still has a working dossier workflow, and
that is the common case, including on a fresh clone without
`--recurse-submodules`.

What this replaces is worse: the repo used to keep both copies and enforce
them byte-for-byte with a CI drift check, so every skill bump required a
manual re-vendor step and the check existed only to catch you forgetting it.
Now the copy is the source of truth for running, the submodule is the source
of truth for updating, and this command moves one to the other and records
which commit it came from.

    python3 tools/sync_skill.py            # copy scripts, record the pin
    python3 tools/sync_skill.py --update   # git submodule update --remote first
    python3 tools/sync_skill.py --check    # report whether the pin is current

The submodule also carries the playbooks under `references/`, which are not
vendored. The portable adapters in `.agents/skills/` and `.claude/skills/`
load those files directly, so one submodule update refreshes Codex, OpenCode,
and Claude Code. Keep it initialized: `git submodule update --init --recursive`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".opencode" / "skills" / "conduct-cs-ai-research"
SKILL_SCRIPTS = SKILL / "scripts"
GITHUB_PLAYBOOK = SKILL / "references" / "github-collaboration.md"
VENDORED = ROOT / "tools" / "research"
PIN = VENDORED / "UPSTREAM.md"
SCRIPTS = ("research_contract.py", "research_state.py", "capture_run.py", "audit_research.py")
UPSTREAM_URL = "https://github.com/honghuy127/cs-ai-research-skills"


def submodule_commit() -> str:
    """HEAD of the skill submodule, or "" when it is not checked out.

    An uninitialized submodule is just an empty directory inside the
    superproject, so a bare `git -C <dir> rev-parse HEAD` there answers with
    the *superproject's* HEAD. Confirm the directory is its own repository
    root before trusting the answer.
    """
    if not SKILL.is_dir():
        return ""
    toplevel = subprocess.run(
        ["git", "-C", str(SKILL), "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if toplevel.returncode != 0:
        return ""
    if Path(toplevel.stdout.strip()).resolve() != SKILL.resolve():
        return ""
    proc = subprocess.run(
        ["git", "-C", str(SKILL), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def recorded_commit() -> str:
    if not PIN.is_file():
        return ""
    for line in PIN.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("- commit:"):
            return line.split(":", 1)[1].strip().strip("`")
    return ""


def write_pin(commit: str, copied: list[str]) -> None:
    PIN.write_text(
        "# Upstream of the vendored dossier scripts\n\n"
        f"The scripts in this directory are vendored copies from the\n"
        f"`conduct-cs-ai-research` skill ({UPSTREAM_URL}, MIT). They are the copies\n"
        "that actually run, so the dossier workflow keeps working in a checkout whose\n"
        "submodule was never initialized.\n\n"
        f"- Commit: `{commit or 'unknown'}`\n"
        f"- Vendored: {dt.date.today().isoformat()}\n"
        f"- Files: {', '.join(copied) if copied else 'none'}\n\n"
        "Refresh with `python3 tools/sync_skill.py --update`, which pulls the submodule,\n"
        "copies the scripts, and rewrites this record. Local edits to these files are\n"
        "allowed and will be overwritten by the next refresh; anything worth keeping\n"
        "belongs upstream.\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="git submodule update --remote before copying")
    ap.add_argument("--check", action="store_true", help="report the pin state without copying")
    args = ap.parse_args(argv)

    if args.check:
        pinned, current = recorded_commit(), submodule_commit()
        if not pinned:
            print("sync_skill: no UPSTREAM.md pin recorded")
            return 1
        if not current:
            print(f"sync_skill: vendored at {pinned[:12]}; submodule not initialized, cannot compare")
            return 0
        if not GITHUB_PLAYBOOK.is_file():
            print("sync_skill: GitHub collaboration playbook is missing")
            return 1
        if pinned == current:
            print(f"sync_skill: vendored scripts match the submodule at {pinned[:12]}")
            return 0
        print(f"sync_skill: vendored at {pinned[:12]}, submodule at {current[:12]}; run python3 tools/sync_skill.py")
        return 0

    if args.update:
        proc = subprocess.run(
            ["git", "submodule", "update", "--init", "--remote", str(SKILL.relative_to(ROOT).as_posix())],
            cwd=ROOT,
        )
        if proc.returncode != 0:
            return proc.returncode

    if not SKILL_SCRIPTS.is_dir():
        print(
            f"sync_skill: {SKILL_SCRIPTS.relative_to(ROOT).as_posix()} is missing. "
            "Run: git submodule update --init --recursive",
            file=sys.stderr,
        )
        return 1
    if not GITHUB_PLAYBOOK.is_file():
        print(
            f"sync_skill: {GITHUB_PLAYBOOK.relative_to(ROOT).as_posix()} is missing",
            file=sys.stderr,
        )
        return 1

    copied = []
    for name in SCRIPTS:
        source = SKILL_SCRIPTS / name
        if not source.is_file():
            print(f"sync_skill: upstream has no {name}", file=sys.stderr)
            continue
        shutil.copyfile(source, VENDORED / name)
        copied.append(name)
    commit = submodule_commit()
    write_pin(commit, copied)
    print(f"sync_skill: vendored {len(copied)} scripts at {commit[:12] or 'unknown commit'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
