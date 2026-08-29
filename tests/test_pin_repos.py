from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import pin_repos  # noqa: E402


def make_git_repo(path: Path, message: str = "init") -> str:
    path.mkdir(parents=True)
    (path / "f.txt").write_text("hello\n", encoding="utf-8")
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "PATH": __import__("os").environ["PATH"],
        "HOME": __import__("os").environ["HOME"],
    }
    for args in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        ["git", "commit", "-q", "-m", message],
    ):
        subprocess.run(args, cwd=path, check=True, env=env, capture_output=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, check=True, capture_output=True, text=True
    ).stdout.strip()


class StudyFactory:
    def __init__(self, tmp: Path) -> None:
        self.study = tmp / "study"
        (self.study / "sources").mkdir(parents=True)

    def with_dossier(self) -> "StudyFactory":
        (self.study / ".research").mkdir()
        (self.study / ".research" / "evidence.jsonl").write_text("", encoding="utf-8")
        return self


class InspectRepoTest(unittest.TestCase):
    def test_reads_commit_and_clean_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha = make_git_repo(repo)
            info = pin_repos.inspect_repo(repo)
            self.assertEqual(info["commit"], sha)
            self.assertFalse(info["dirty"])
            self.assertIsNone(info["remote"])

    def test_detects_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            make_git_repo(repo)
            (repo / "f.txt").write_text("changed\n", encoding="utf-8")
            self.assertTrue(pin_repos.inspect_repo(repo)["dirty"])

    def test_rejects_non_git_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                pin_repos.inspect_repo(Path(tmp))

    def test_rejects_missing_dir(self):
        with self.assertRaises(ValueError):
            pin_repos.inspect_repo(Path("/nonexistent/path/xyz"))


class YamlRoundTripTest(unittest.TestCase):
    def test_round_trips_all_fields(self):
        repos = [
            {
                "key": "codex",
                "path": '/tmp/a "quoted" path',
                "remote": None,
                "branch": "main",
                "commit": "abc123",
                "dirty": True,
                "pinned_at": "2026-08-20T00:00:00+00:00",
            }
        ]
        text = pin_repos.render_repos_yaml(repos, "2026-08-20T00:00:00+00:00")
        parsed = pin_repos.parse_repos_yaml(text)
        self.assertEqual(parsed, repos)

    def test_parses_multiple_entries(self):
        repos = [
            {"key": "a", "path": "/x", "remote": None, "branch": "main", "commit": "1", "dirty": False, "pinned_at": "t"},
            {"key": "b", "path": "/y", "remote": "r", "branch": "dev", "commit": "2", "dirty": True, "pinned_at": "t"},
        ]
        parsed = pin_repos.parse_repos_yaml(pin_repos.render_repos_yaml(repos, "t"))
        self.assertEqual([r["key"] for r in parsed], ["a", "b"])
        self.assertFalse(parsed[0]["dirty"])
        self.assertTrue(parsed[1]["dirty"])


class EvidenceIdTest(unittest.TestCase):
    def test_continues_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "evidence.jsonl"
            ledger.write_text(json.dumps({"id": "EVD-002"}) + "\n", encoding="utf-8")
            self.assertEqual(pin_repos.next_evidence_id(ledger), "EVD-003")

    def test_starts_at_001_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "evidence.jsonl"
            self.assertEqual(pin_repos.next_evidence_id(ledger), "EVD-001")

    def test_ignores_foreign_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "evidence.jsonl"
            ledger.write_text(json.dumps({"id": "EVD-x"}) + "\nnot-json\n", encoding="utf-8")
            self.assertEqual(pin_repos.next_evidence_id(ledger), "EVD-001")


class MainTest(unittest.TestCase):
    def _call(self, argv: tuple) -> int:
        sys.argv = ["pin_repos", *argv]
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                return pin_repos.main()
        except SystemExit as exc:
            return int(exc.code or 0)

    def test_pin_writes_repos_yaml_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            sha = make_git_repo(repo)
            study = StudyFactory(tmp_path).with_dossier().study
            code = self._call((str(study), f"codex={repo}"))
            self.assertEqual(code, 0)
            parsed = pin_repos.parse_repos_yaml((study / "sources" / "repos.yaml").read_text())
            self.assertEqual(parsed[0]["key"], "codex")
            self.assertEqual(parsed[0]["commit"], sha)
            evidence = [json.loads(line) for line in (study / ".research" / "evidence.jsonl").read_text().splitlines() if line.strip()]
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["id"], "EVD-001")
            self.assertEqual(evidence[0]["source_type"], "code-snapshot")
            self.assertEqual(evidence[0]["verification"], "artifact-checked")
            self.assertEqual(evidence[0]["locator"], sha)

    def test_duplicate_key_requires_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            make_git_repo(repo)
            study = StudyFactory(tmp_path).study
            self.assertEqual(self._call((str(study), f"codex={repo}")), 0)
            self.assertEqual(self._call((str(study), f"codex={repo}")), 1)
            self.assertEqual(self._call((str(study), f"codex={repo}", "--update")), 0)
            parsed = pin_repos.parse_repos_yaml((study / "sources" / "repos.yaml").read_text())
            self.assertEqual(len(parsed), 1)

    def test_skips_evidence_without_dossier(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            make_git_repo(repo)
            study = StudyFactory(tmp_path).study
            self.assertEqual(self._call((str(study), f"codex={repo}")), 0)
            self.assertFalse((study / ".research").exists())

    def test_rejects_bad_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            make_git_repo(repo)
            study = StudyFactory(tmp_path).study
            self.assertEqual(self._call((str(study), f"Bad_Key={repo}")), 2)

    def test_rejects_non_git_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            study = StudyFactory(tmp_path).study
            self.assertEqual(self._call((str(study), f"codex={tmp_path / 'empty'}")), 2)


if __name__ == "__main__":
    unittest.main()
