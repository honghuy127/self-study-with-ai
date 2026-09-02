"""End-to-end lifecycle tests: scaffold a study and drive it to completion.

Every other test exercises one function. These walk a real study through
every state and gate of its mode, the way a user does, and assert both that
the happy path completes and that each gate actually blocks before approval.
This is the behavior CI could never check before: `studies/` is gitignored, so
there was no study anywhere for the pipeline to run against.

Each mode is run twice over: once forward through every transition, and once
attempting each ungated jump to confirm it is refused.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_all  # noqa: E402
import cleanup_study  # noqa: E402
import contracts  # noqa: E402
import new_study  # noqa: E402
import study  # noqa: E402

# (mode, methodology, deliverables, [(status, gates that must be approved first)])
WALKS = {
    "delegated": (
        "source-only",
        ["report"],
        [
            ("gathering", []),
            ("summarizing", []),
            ("drafting", ["sources", "notes"]),
            ("review", ["draft"]),
            ("done", ["review"]),
        ],
    ),
    "interactive": (
        "source-only",
        ["learning-note"],
        [
            ("diagnosing", ["scope"]),
            ("learning", ["evidence"]),
            ("practicing", []),
            ("assessing", []),
            ("retained", ["mastery"]),
        ],
    ),
    "paper-reading": (
        "source-only",
        ["slides"],
        [
            ("gathering", []),
            ("analyzing", ["paper"]),
            ("presenting", ["analysis"]),
            ("review", ["deck"]),
            ("done", ["review"]),
        ],
    ),
}

EXPERIMENTAL_WALK = [
    ("gathering", []),
    ("summarizing", []),
    ("experimenting", []),
    ("drafting", ["sources", "notes", "experiments"]),
    ("review", ["draft"]),
    ("done", ["review"]),
]


def quiet(fn, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = fn(*args, **kwargs)
    return result, out.getvalue()


class LifecycleWalkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="lifecycle-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.studies = self.tmp / "studies"
        self.studies.mkdir()
        self._patch(new_study, "STUDIES", self.studies)
        self._patch(study, "STUDIES", self.studies)

    def _patch(self, module, name: str, value) -> None:
        old = getattr(module, name)
        setattr(module, name, value)
        self.addCleanup(setattr, module, name, old)

    def scaffold(self, slug: str, mode: str, methodology: str, deliverables: list[str]) -> Path:
        argv = [slug, "--mode", mode, "--title", f"{slug} title", "--methodology", methodology,
                "--deliverables", ",".join(deliverables)]
        code, _ = quiet(new_study.main, argv)
        self.assertEqual(code, 0)
        created = sorted(self.studies.iterdir())
        self.assertEqual(len(created), 1, "scaffold created more than one study")
        return created[0]

    def status_of(self, directory: Path) -> str:
        return str(study.load_manifest(directory).get("status"))

    def walk(self, mode: str, methodology: str, deliverables: list[str], steps: list) -> Path:
        directory = self.scaffold(f"walk-{mode.replace('-', '')}", mode, methodology, deliverables)
        self.assertEqual(self.status_of(directory), contracts.STATES[mode][0])

        for target, gates in steps:
            if gates:
                # The gate is not approved yet, so the move must be refused.
                with self.assertRaises(SystemExit, msg=f"{mode}: {target} was allowed without {gates}"):
                    quiet(study.cmd_status_set, directory, target, "premature")
                for gate in gates:
                    code, _ = quiet(study.cmd_approve, directory, gate, f"approving {gate}")
                    self.assertEqual(code, 0)
            code, _ = quiet(study.cmd_status_set, directory, target, f"moving to {target}")
            self.assertEqual(code, 0)
            self.assertEqual(self.status_of(directory), target)
            self.assertEqual(check_all.validate_manifest(directory / "study.yaml"), [])
        return directory

    def test_delegated_walk(self) -> None:
        methodology, deliverables, steps = WALKS["delegated"]
        directory = self.walk("delegated", methodology, deliverables, steps)
        self.assertEqual(self.status_of(directory), "done")

    def test_interactive_walk(self) -> None:
        methodology, deliverables, steps = WALKS["interactive"]
        directory = self.walk("interactive", methodology, deliverables, steps)
        self.assertEqual(self.status_of(directory), "retained")

    def test_paper_reading_walk(self) -> None:
        methodology, deliverables, steps = WALKS["paper-reading"]
        directory = self.walk("paper-reading", methodology, deliverables, steps)
        self.assertEqual(self.status_of(directory), "done")

    def test_experimental_walk_passes_through_experimenting(self) -> None:
        directory = self.walk("delegated", "experimental", ["report"], EXPERIMENTAL_WALK)
        self.assertEqual(self.status_of(directory), "done")
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        transitions = [e["to"] for e in events if e.get("type") == "transition"]
        self.assertIn("experimenting", transitions)

    def test_source_only_cannot_enter_experimenting(self) -> None:
        directory = self.scaffold("no-experiments", "delegated", "source-only", ["report"])
        quiet(study.cmd_approve, directory, "sources", "ok")
        quiet(study.cmd_status_set, directory, "gathering", "go")
        quiet(study.cmd_status_set, directory, "summarizing", "go")
        with self.assertRaises(SystemExit):
            quiet(study.cmd_status_set, directory, "experimenting", "should be refused")

    def test_every_gate_decision_is_logged(self) -> None:
        methodology, deliverables, steps = WALKS["delegated"]
        directory = self.walk("delegated", methodology, deliverables, steps)
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        approvals = [e["gate"] for e in events if e.get("type") == "approval"]
        self.assertEqual(
            approvals,
            ["sources_approved", "notes_approved", "draft_approved", "review_signed_off"],
        )
        for event in events:
            self.assertIn("ts", event)

    def test_backward_edges_allow_reopening_a_finished_study(self) -> None:
        methodology, deliverables, steps = WALKS["delegated"]
        directory = self.walk("delegated", methodology, deliverables, steps)
        code, _ = quiet(study.cmd_status_set, directory, "review", "reopen: new source appeared")
        self.assertEqual(code, 0)
        code, _ = quiet(study.cmd_status_set, directory, "drafting", "revise the draft")
        self.assertEqual(code, 0)

    def test_retained_is_terminal(self) -> None:
        methodology, deliverables, steps = WALKS["interactive"]
        directory = self.walk("interactive", methodology, deliverables, steps)
        for target in contracts.STATES["interactive"]:
            with self.assertRaises(SystemExit):
                quiet(study.cmd_status_set, directory, target, "nothing follows retained")


class CleanupPacksBeforeDeletingTests(unittest.TestCase):
    """Cleanup must not remove evidence it has not verifiably packed."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cleanup-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.studies = self.tmp / "studies"
        self.studies.mkdir()
        self._old = new_study.STUDIES
        new_study.STUDIES = self.studies
        self.addCleanup(setattr, new_study, "STUDIES", self._old)
        code, _ = quiet(
            new_study.main,
            ["packed", "--mode", "delegated", "--title", "packed", "--deliverables", "report"],
        )
        self.assertEqual(code, 0)
        self.directory = sorted(self.studies.iterdir())[0]
        docs = self.directory / "sources" / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        self.snapshot = docs / "page.txt"
        self.snapshot.write_text("snapshot body\n", encoding="utf-8")
        self.snapshot_bytes = self.snapshot.read_bytes()
        (self.directory / "reviews").mkdir(exist_ok=True)
        (self.directory / "reviews" / "r1.md").write_text("# review\n", encoding="utf-8")
        manifest = self.directory / "study.yaml"
        text = manifest.read_text(encoding="utf-8")
        text = text.replace("status: proposed", "status: done").replace(
            "review_signed_off: false", "review_signed_off: true"
        )
        manifest.write_text(text, encoding="utf-8")

    def test_archive_is_written_and_verifiable(self) -> None:
        archive_dir = self.tmp / "archive"
        removed = cleanup_study.clean(self.directory, dry_run=False, archive_dir=archive_dir)
        self.assertTrue(removed)
        self.assertFalse((self.directory / "sources" / "docs").exists())

        import yaml

        record = yaml.safe_load((self.directory / "archive.yaml").read_text(encoding="utf-8"))
        archive = archive_dir / f"{self.directory.name}.zip"
        self.assertTrue(archive.is_file())
        self.assertEqual(record["archive_sha256"], cleanup_study.sha256_file(archive))

        import zipfile

        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            self.assertIn("sources/docs/page.txt", names)
            self.assertEqual(bundle.read("sources/docs/page.txt"), self.snapshot_bytes)

    def test_check_all_accepts_a_verified_archive(self) -> None:
        cleanup_study.clean(self.directory, dry_run=False, archive_dir=self.tmp / "archive")
        record = check_all.load_archive_record(self.directory)
        ok, reason = check_all.archive_status(self.directory, record)
        self.assertTrue(ok, reason)

    def test_check_all_rejects_a_missing_archive(self) -> None:
        archive_dir = self.tmp / "archive"
        cleanup_study.clean(self.directory, dry_run=False, archive_dir=archive_dir)
        (archive_dir / f"{self.directory.name}.zip").unlink()
        record = check_all.load_archive_record(self.directory)
        ok, reason = check_all.archive_status(self.directory, record)
        self.assertFalse(ok)
        self.assertIn("missing", reason)

    def test_dry_run_removes_nothing(self) -> None:
        cleanup_study.clean(self.directory, dry_run=True, archive_dir=self.tmp / "archive")
        self.assertTrue((self.directory / "sources" / "docs" / "page.txt").is_file())
        self.assertFalse((self.directory / "archive.yaml").exists())

    def test_no_archive_flag_records_the_weaker_guarantee(self) -> None:
        cleanup_study.clean(self.directory, dry_run=False, no_archive=True)
        import yaml

        record = yaml.safe_load((self.directory / "archive.yaml").read_text(encoding="utf-8"))
        self.assertEqual(record["archive"], "")
        self.assertIn("may resolve to nothing", record["note"])


if __name__ == "__main__":
    unittest.main()
