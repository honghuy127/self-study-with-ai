#!/usr/bin/env python3
"""Verify pinned source checkouts for a study.

Reads <study-dir>/sources/repos.yaml and, for each pinned checkout, checks
that the recorded path exists and is a git repository, that the pinned
commit is still present, and that the recorded remote matches. HEAD drift
is a warning rather than a failure: codebase notes anchor to the pinned
commit, so a moved checkout stays usable as long as that commit remains
reachable.

Run when reopening or reusing a study whose checkouts may have changed,
for example after moving machines or pulling the reference repos.

Usage: python3 tools/verify_pins.py <study-dir>
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def run_git(path: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def load_repos(study: Path) -> list[dict]:
    repos_file = study / "sources" / "repos.yaml"
    if not repos_file.is_file():
        raise SystemExit(f"error: {repos_file} not found")
    data = yaml.safe_load(repos_file.read_text(encoding="utf-8")) or {}
    repos = data.get("repos", []) if isinstance(data, dict) else []
    if not isinstance(repos, list) or not repos:
        raise SystemExit(f"error: no pinned repos listed in {repos_file}")
    return repos


def verify_repo(record: dict) -> tuple[str, list[str]]:
    if not record.get("commit"):
        return FAIL, ["record has no commit"]
    path = Path(str(record.get("path", ""))).expanduser()
    if not path.is_dir():
        return FAIL, [f"checkout path does not exist: {path}"]
    code, _ = run_git(path, "rev-parse", "--git-dir")
    if code != 0:
        return FAIL, [f"not a git repository: {path}"]
    code, _ = run_git(path, "cat-file", "-e", f"{record['commit']}^{{commit}}")
    if code != 0:
        return FAIL, [f"pinned commit {record['commit'][:12]} not present in checkout"]
    notes = []
    remote = record.get("remote")
    if remote:
        code, found = run_git(path, "remote", "get-url", "origin")
        if code == 0 and found != remote:
            notes.append(f"remote is {found}, recorded {remote}")
    code, head = run_git(path, "rev-parse", "HEAD")
    if code == 0 and head != record["commit"]:
        notes.append(f"HEAD moved to {head[:12]}; notes still anchor to the pinned commit")
    return (WARN if notes else PASS), notes


def verify(study: Path) -> int:
    worst = PASS
    for record in load_repos(study):
        status, messages = verify_repo(record)
        if status == FAIL:
            worst = FAIL
        detail = "; ".join(messages) if messages else "ok"
        print(f"{status:4} {record.get('key', '?')}: {detail}")
    return 1 if worst == FAIL else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that pinned source checkouts still hold the recorded commits."
    )
    parser.add_argument("study_dir", help="path to the study directory")
    args = parser.parse_args()
    study = Path(args.study_dir).resolve()
    if not study.is_dir():
        print(f"error: study directory not found: {study}", file=sys.stderr)
        return 2
    return verify(study)


if __name__ == "__main__":
    sys.exit(main())
