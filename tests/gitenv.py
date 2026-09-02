"""Portable environment for git subprocesses in tests.

The suite runs on Linux, macOS, and Windows. A hand-built env dict that
names POSIX-only variables (HOME) raises KeyError on Windows, and an env
without SYSTEMROOT breaks git's own process startup there. Start from the
real environment, pin a deterministic identity, and switch off the user's
global and system config so a developer's settings cannot change a result.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=True, env=GIT_ENV, capture_output=True, text=True)


def make_git_repo(path: Path, message: str = "init") -> str:
    """Create a one-commit repository and return its commit sha."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "f.txt").write_text("hello\n", encoding="utf-8")
    git("init", "-q", "-b", "main", cwd=path)
    git("add", ".", cwd=path)
    git("commit", "-q", "-m", message, cwd=path)
    return git("rev-parse", "HEAD", cwd=path).stdout.strip()
