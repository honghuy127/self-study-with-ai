#!/usr/bin/env python3
"""Run a dossier script against a study. Replaces tools/research/research.sh.

    python3 tools/research.py <study-dir> research_state.py validate
    python3 tools/research.py <study-dir> capture_run.py --experiment x ...
    python3 tools/research.py <study-dir> audit_research.py

`--root <study-dir>` is appended rather than prepended: research_state.py
defines --root per subparser, so putting it first dies with "invalid choice".

The scripts themselves are vendored under tools/research/ from the
conduct-cs-ai-research skill, with their upstream commit recorded in
tools/research/UPSTREAM.md. Vendoring keeps the dossier workflow usable in a
checkout whose submodule was never initialized, which is the common case.
Refresh them with `python3 tools/sync_skill.py`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = ("research_state.py", "capture_run.py", "audit_research.py")
HERE = Path(__file__).resolve().parent / "research"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    study_dir, script, *rest = argv
    if script not in SCRIPTS:
        print(f"research: unknown script {script!r}; choose from {', '.join(SCRIPTS)}", file=sys.stderr)
        return 2
    target = HERE / script
    if not target.is_file():
        print(f"research: {target} is missing; run python3 tools/sync_skill.py", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(target), *rest, "--root", study_dir]).returncode


if __name__ == "__main__":
    sys.exit(main())
