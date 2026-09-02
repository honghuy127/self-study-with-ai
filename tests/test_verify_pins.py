from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import verify_pins  # noqa: E402

from tests.gitenv import git, make_git_repo  # noqa: E402


def write_repos(study: Path, repos: list[dict]) -> None:
    (study / "sources").mkdir(parents=True, exist_ok=True)
    (study / "sources" / "repos.yaml").write_text(
        yaml.safe_dump({"pinned_at": "2026-08-20T00:00:00+00:00", "repos": repos}),
        encoding="utf-8",
    )


class VerifyPinsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.study = self.tmp / "study"

    def test_healthy_pin_passes(self) -> None:
        sha = make_git_repo(self.tmp / "repo")
        write_repos(self.study, [{"key": "repo", "path": str(self.tmp / "repo"), "commit": sha}])
        self.assertEqual(verify_pins.verify(self.study), 0)

    def test_missing_path_fails(self) -> None:
        write_repos(self.study, [{"key": "gone", "path": str(self.tmp / "nope"), "commit": "a" * 40}])
        self.assertEqual(verify_pins.verify(self.study), 1)

    def test_missing_commit_fails(self) -> None:
        make_git_repo(self.tmp / "repo")
        write_repos(
            self.study,
            [{"key": "repo", "path": str(self.tmp / "repo"), "commit": "b" * 40}],
        )
        self.assertEqual(verify_pins.verify(self.study), 1)

    def test_moved_head_warns_but_passes(self) -> None:
        repo = self.tmp / "repo"
        pinned = make_git_repo(repo)
        git("commit", "-q", "--allow-empty", "-m", "next", cwd=repo)
        write_repos(self.study, [{"key": "repo", "path": str(repo), "commit": pinned}])
        self.assertEqual(verify_pins.verify(self.study), 0)

    def test_not_a_git_repo_fails(self) -> None:
        (self.tmp / "plain").mkdir()
        write_repos(self.study, [{"key": "plain", "path": str(self.tmp / "plain"), "commit": "c" * 40}])
        self.assertEqual(verify_pins.verify(self.study), 1)

    def test_no_repos_file_exits(self) -> None:
        self.study.mkdir()
        with self.assertRaises(SystemExit):
            verify_pins.verify(self.study)


if __name__ == "__main__":
    unittest.main()
