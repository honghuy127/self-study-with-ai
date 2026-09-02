#!/usr/bin/env python3
"""Slim a signed-off study down to its knowledge core, packing what it removes.

This repo stores self-study, not academic publication. During a study the
full evidence chain is kept; raw source snapshots, experiment artifacts,
review drafts, and the .research dossier all guard in-progress work and are
checked by tools/research/audit_research.py. After the human signs the review
off, only the distilled knowledge stays in the working tree.

Kept:    brief.md, study.yaml, notes/, report/ (sources), slides/ (sources),
         sources/registry.yaml, sources/repos.yaml
Packed:  sources/docs/, sources/pdfs/, experiments/, .research/, reviews/

Nothing is deleted until it is inside a verified archive. Cleanup writes
`archive/<study-id>.zip`, re-opens it, confirms every packed file is present
with a matching size, and only then removes the originals. archive.yaml
records the archive path, its sha256, its file count, and a retrieval command
that works in any checkout.

This is deliberate: `studies/` is gitignored by default, so the git-history
recovery this tool used to promise resolved to nothing whenever the evidence
had never been committed. A local zip does not depend on what git happened to
track. `--no-archive` restores the old delete-only behavior and requires
`--force`, because it destroys the evidence chain the repo exists to protect.

Run manifests reference paths that existed at capture time; after cleanup
those paths live in the archive. Registry `snapshot` entries likewise become
archived references that can also be re-fetched from `url`. Gitignored build
outputs (report/build, slides/build) are not touched.

Refuses to run unless study.yaml records `status: done`,
`gates.review_signed_off: true`, and no `cleaned` stamp yet. Interactive
studies are refused outright because their learning record remains live.
Delegated and paper-reading studies share done-time cleanup. Stamps
`cleaned: "YYYY-MM-DD"` on success.

Usage: python3 tools/cleanup_study.py <study-dir> [--dry-run]
                                      [--archive-dir DIR] [--no-archive --force]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

REMOVABLE = ("sources/docs", "sources/pdfs", "experiments", ".research", "reviews")


def tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def tree_file_count(path: Path) -> int:
    if path.is_file():
        return 1
    return sum(1 for p in path.rglob("*") if p.is_file())


def head_commit(path: Path) -> str:
    """Commit where the removed content last existed (cleanup is uncommitted)."""
    proc = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def load_manifest(study: Path) -> dict:
    manifest = study / "study.yaml"
    if not manifest.is_file():
        raise SystemExit(f"error: {manifest} not found")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"error: {manifest} did not parse to a mapping")
    return data


def check_gates(data: dict) -> None:
    if data.get("mode") == "interactive":
        raise SystemExit(
            "refusing: interactive studies keep their learning record; "
            "cleanup handles delegated and paper-reading studies"
        )
    if data.get("status") != "done":
        raise SystemExit(f"refusing: status is {data.get('status')!r}, expected 'done'")
    gates = data.get("gates") or {}
    if gates.get("review_signed_off") is not True:
        raise SystemExit("refusing: gates.review_signed_off is not true")
    if data.get("cleaned"):
        raise SystemExit(f"refusing: study already cleaned on {data.get('cleaned')!r}")


def stamp_cleaned(study: Path, text: str) -> str:
    today = dt.date.today().isoformat()
    line = f'cleaned: "{today}"'
    if re.search(r"(?m)^cleaned:", text):
        new = re.sub(r"(?m)^cleaned:.*$", line, text, count=1)
    else:
        new = re.sub(r"(?m)^(status:[^\n]*\n)", rf"\g<1>{line}\n", text, count=1)
        if new == text:
            new = text.rstrip("\n") + f"\n\n{line}\n"
    (study / "study.yaml").write_text(new, encoding="utf-8")
    return line


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_archive(study: Path, paths: list[str], archive_dir: Path) -> Path:
    """Zip every removable path, then verify the archive can be read back.

    Verification is the point: the caller deletes originals only after this
    returns, and it returns only when every packed file is present in the
    archive at its recorded size. A half-written zip raises instead.
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / f"{study.name}.zip"
    if archive.exists():
        raise SystemExit(
            f"refusing: {archive} already exists; move it aside or pass --archive-dir"
        )
    expected: dict[str, int] = {}
    tmp = archive.with_suffix(".zip.part")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for rel in paths:
            target = study / rel
            if not target.exists():
                continue
            for item in sorted(target.rglob("*")):
                if not item.is_file():
                    continue
                arcname = item.relative_to(study).as_posix()
                bundle.write(item, arcname)
                expected[arcname] = item.stat().st_size
    with zipfile.ZipFile(tmp) as bundle:
        packed = {info.filename: info.file_size for info in bundle.infolist()}
        broken = bundle.testzip()
        if broken is not None:
            tmp.unlink(missing_ok=True)
            raise SystemExit(f"refusing: archive failed its own integrity check at {broken}")
    missing = sorted(set(expected) - set(packed))
    mismatched = sorted(name for name, size in expected.items() if packed.get(name) != size)
    if missing or mismatched:
        tmp.unlink(missing_ok=True)
        detail = ", ".join((missing + mismatched)[:5])
        raise SystemExit(f"refusing: archive did not capture {len(missing) + len(mismatched)} files ({detail})")
    tmp.replace(archive)
    return archive


def write_archive_record(
    study: Path,
    removed: list[tuple[str, int, int]],
    archive: Path | None,
) -> None:
    """Record what left the tree and exactly how to get it back.

    When an archive was packed, the retrieval command reads from that file and
    works in any checkout. Without one (`--no-archive --force`), the record
    falls back to git history and says plainly that recovery depends on the
    content having been committed, which the default gitignore makes unlikely.
    """
    commit = head_commit(study)
    if archive is not None:
        try:
            archive_rel = archive.relative_to(study.parent.parent).as_posix()
        except ValueError:
            archive_rel = archive.as_posix()
        record: dict = {
            "archived_at": dt.date.today().isoformat(),
            "archive": archive_rel,
            "archive_sha256": sha256_file(archive),
            "archive_files": len(zipfile.ZipFile(archive).infolist()),
            "git_commit": commit,
            "note": "Packed paths live in the archive file; retrieval does not depend on git history.",
        }
    else:
        record = {
            "archived_at": dt.date.today().isoformat(),
            "archive": "",
            "git_commit": commit,
            "note": (
                "Removed without an archive (--no-archive --force). Recovery depends on the content "
                "having been committed before cleanup; studies/ is gitignored by default, so these "
                "retrieval commands may resolve to nothing."
            ),
        }
    record["removed"] = [
        {
            "path": rel,
            "size_kb": size // 1024,
            "files": files,
            "retrieve": (
                f"python3 -m zipfile -e {record['archive']} <destination>"
                if archive is not None
                else (
                    f"git show {commit}:{study.parent.name}/{study.name}/{rel}"
                    if commit
                    else f"git log -- {study.parent.name}/{study.name}/{rel}"
                )
            ),
        }
        for rel, size, files in removed
    ]
    (study / "archive.yaml").write_text(
        "# Archive record written by tools/cleanup_study.py. Do not edit by hand.\n"
        + yaml.dump(record, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def clean(
    study: Path,
    dry_run: bool,
    archive_dir: Path | None = None,
    no_archive: bool = False,
) -> list[tuple[str, int]]:
    manifest = study / "study.yaml"
    data = load_manifest(study)
    check_gates(data)

    present = [rel for rel in REMOVABLE if (study / rel).exists()]
    archive: Path | None = None
    if present and not dry_run and not no_archive:
        archive = pack_archive(study, present, archive_dir or (study.parent.parent / "archive"))

    removed = []
    for rel in present:
        target = study / rel
        size = tree_size(target)
        files = tree_file_count(target)
        if not dry_run:
            shutil.rmtree(target)
        removed.append((rel, size, files))
    # Always write the archive record and stamp cleaned, even when nothing was
    # removed, so a cleaned study can be reopened without guessing whether the
    # absence of evidence means "archived" or "never existed".
    if not dry_run:
        write_archive_record(study, removed, archive)
        stamp_cleaned(study, manifest.read_text(encoding="utf-8"))
    return [(rel, size) for rel, size, _ in removed]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Slim a signed-off study down to its knowledge core."
    )
    parser.add_argument("study_dir", help="path to the study directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be packed and removed without changing anything",
    )
    parser.add_argument(
        "--archive-dir",
        default=None,
        help="where to write <study-id>.zip (default: archive/ beside studies/)",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="delete without packing an archive first; requires --force",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="acknowledge that --no-archive destroys the evidence chain",
    )
    args = parser.parse_args()
    if args.no_archive and not args.force:
        print(
            "error: --no-archive deletes the evidence chain with no verified copy. "
            "Pass --force if that is really what you want.",
            file=sys.stderr,
        )
        return 2
    study = Path(args.study_dir).resolve()
    if not study.is_dir():
        print(f"error: study directory not found: {study}", file=sys.stderr)
        return 2
    before = tree_size(study)
    archive_dir = Path(args.archive_dir).resolve() if args.archive_dir else None
    removed = clean(study, args.dry_run, archive_dir=archive_dir, no_archive=args.no_archive)
    verb = "would remove" if args.dry_run else "removed"
    for rel, size in removed:
        print(f"{verb} {rel} ({size // 1024} KB)")
    if not removed:
        print("nothing to remove; study already slim")
    else:
        freed = sum(size for _, size in removed)
        print(f"{'would free' if args.dry_run else 'freed'} {freed // 1024} KB; study was {before // 1024} KB on disk")
        if not args.dry_run and not args.no_archive:
            record = yaml.safe_load((study / "archive.yaml").read_text(encoding="utf-8"))
            print(f"archived to {record['archive']} ({record['archive_files']} files, sha256 {record['archive_sha256'][:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
