#!/usr/bin/env python3
"""Pin local source repositories for a study.

Records the exact checkout (path, remote, branch, commit, dirty flag) of each
local clone into <study-dir>/sources/repos.yaml, and appends one code-snapshot
evidence record per repo to <study-dir>/.research/evidence.jsonl when that
ledger exists. Every codebase note in the study must anchor to a repo key and
commit listed here.

Usage: python3 tools/pin_repos.py <study-dir> <key>=<path> [<key>=<path> ...] [--update]

- key: lowercase-hyphen repo key used in the registry and notes, e.g. codex
- path: absolute or relative path to a git checkout of the repository
- --update: replace an existing entry with the same key instead of erroring
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run_git(repo: Path, *args: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def inspect_repo(path: Path) -> dict:
    if not path.is_dir():
        raise ValueError(f"not a directory: {path}")
    commit = run_git(path, "rev-parse", "HEAD")
    if commit is None:
        raise ValueError(f"not a git checkout: {path}")
    dirty = bool(run_git(path, "status", "--porcelain"))
    return {
        "path": str(path.resolve()),
        "remote": run_git(path, "remote", "get-url", "origin"),
        "branch": run_git(path, "rev-parse", "--abbrev-ref", "HEAD"),
        "commit": commit,
        "dirty": dirty,
    }


def quote(value: str | None) -> str:
    if value is None:
        return "null"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_repos_yaml(repos: list[dict], pinned_at: str) -> str:
    lines = [
        "# Local source repositories pinned for this study. Written by tools/pin_repos.py.",
        "# Each entry records the exact checkout every codebase note must be anchored to.",
        f"pinned_at: {quote(pinned_at)}",
        "repos:",
    ]
    for repo in repos:
        lines.append(f"  - key: {repo['key']}")
        lines.append(f"    path: {quote(repo['path'])}")
        lines.append(f"    remote: {quote(repo['remote'])}")
        lines.append(f"    branch: {quote(repo['branch'])}")
        lines.append(f"    commit: {quote(repo['commit'])}")
        lines.append(f"    dirty: {'true' if repo['dirty'] else 'false'}")
        lines.append(f"    pinned_at: {quote(repo['pinned_at'])}")
    return "\n".join(lines) + "\n"


def parse_repos_yaml(text: str) -> list[dict]:
    """Parse the flat structure render_repos_yaml writes. Not a general YAML parser."""
    repos: list[dict] = []
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped == "repos:":
            continue
        if stripped.startswith("- key:"):
            if current is not None:
                repos.append(current)
            current = {"key": stripped.split(":", 1)[1].strip()}
            continue
        if current is not None and ":" in stripped and line.startswith("    "):
            field, value = (part.strip() for part in stripped.split(":", 1))
            if value == "null":
                current[field] = None
            elif value in ("true", "false"):
                current[field] = value == "true"
            elif value.startswith('"') and value.endswith('"'):
                current[field] = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            else:
                current[field] = value
    if current is not None:
        repos.append(current)
    return repos


def next_evidence_id(ledger: Path) -> str:
    highest = 0
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            match = re.fullmatch(r"EVD-(\d+)", str(record.get("id", "")))
            if match:
                highest = max(highest, int(match.group(1)))
    return f"EVD-{highest + 1:03d}"


def append_evidence(study: Path, repos: list[dict], pinned_at: str) -> int:
    ledger = study / ".research" / "evidence.jsonl"
    if not ledger.is_file():
        return 0
    added = 0
    for repo in repos:
        record = {
            "id": next_evidence_id(ledger),
            "title": f"Code snapshot: {repo['key']} at {repo['commit'][:12]}",
            "accessed_at": pinned_at[:10],
            "verification": "artifact-checked",
            "url": repo.get("remote"),
            "doi": None,
            "artifact_path": "sources/repos.yaml",
            "citation_key": None,
            "locator": repo["commit"],
            "source_type": "code-snapshot",
            "publication_status": None,
            "peer_review_status": None,
            "notes": (
                f"Local checkout pinned at commit {repo['commit']} "
                f"({'dirty' if repo['dirty'] else 'clean'} tree). "
                "All codebase notes for this key must anchor to this commit."
            ),
            "supports": [],
            "challenges": [],
            "contextualizes": [],
        }
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        added += 1
    return added


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("study_dir", help="study directory, e.g. studies/2026-08_foo")
    ap.add_argument("specs", nargs="+", metavar="KEY=PATH", help="repo key and checkout path pairs")
    ap.add_argument("--update", action="store_true", help="replace existing entries with the same key")
    args = ap.parse_args()

    study = Path(args.study_dir).resolve()
    if not study.is_dir():
        print(f"pin_repos: study directory not found: {study}", file=sys.stderr)
        return 2
    sources = study / "sources"
    if not sources.is_dir():
        print(f"pin_repos: {sources} not found; run tools/new_study.py first", file=sys.stderr)
        return 2

    pinned_at = now()
    new_entries: list[dict] = []
    for spec in args.specs:
        if "=" not in spec:
            print(f"pin_repos: bad spec {spec!r}, expected KEY=PATH", file=sys.stderr)
            return 2
        key, _, raw_path = spec.partition("=")
        if not KEY_RE.match(key):
            print(f"pin_repos: invalid key {key!r}", file=sys.stderr)
            return 2
        try:
            info = inspect_repo(Path(raw_path).expanduser())
        except ValueError as exc:
            print(f"pin_repos: {key}: {exc}", file=sys.stderr)
            return 2
        new_entries.append({"key": key, "pinned_at": pinned_at, **info})

    repos_file = sources / "repos.yaml"
    existing: list[dict] = []
    if repos_file.is_file():
        existing = parse_repos_yaml(repos_file.read_text(encoding="utf-8"))
    existing_keys = {repo["key"] for repo in existing}
    new_keys = [repo["key"] for repo in new_entries]
    if len(set(new_keys)) != len(new_keys):
        print("pin_repos: duplicate keys in one invocation", file=sys.stderr)
        return 2
    conflicts = sorted(existing_keys & set(new_keys))
    if conflicts and not args.update:
        print(
            f"pin_repos: keys already pinned: {', '.join(conflicts)} (use --update to replace)",
            file=sys.stderr,
        )
        return 1
    merged = [repo for repo in existing if repo["key"] not in set(new_keys)] + new_entries

    repos_file.write_text(render_repos_yaml(merged, pinned_at), encoding="utf-8")
    added = append_evidence(study, new_entries, pinned_at)
    for repo in new_entries:
        flag = " (dirty tree)" if repo["dirty"] else ""
        print(f"pinned {repo['key']} {repo['commit'][:12]}{flag} -> {repo['path']}")
    print(f"wrote {repos_file}")
    if added:
        print(f"appended {added} evidence record(s) to .research/evidence.jsonl")
    else:
        print("no .research/evidence.jsonl; skipped evidence records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
