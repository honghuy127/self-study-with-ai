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

import study  # noqa: E402
from new_study import copy_templates  # noqa: E402

INTERACTIVE_CONFIG = {
    "mode": "interactive",
    "intent": "understand",
    "assurance": "grounded",
    "methodology": "source-only",
    "deliverables": ["learning-note"],
}
DELEGATED_CONFIG = {
    "mode": "delegated",
    "intent": "survey",
    "assurance": "grounded",
    "methodology": "source-only",
    "deliverables": ["report"],
}


def scaffold(tmp: Path, name: str, config: dict) -> Path:
    study_dir = tmp / name
    study_dir.mkdir(parents=True)
    copy_templates(study_dir, name, name.replace("_", " ").replace("-", " "), config)
    return study_dir


class StudyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="study-cli-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.interactive = scaffold(self.tmp, "2026-08_pilot", INTERACTIVE_CONFIG)
        self.delegated = scaffold(self.tmp, "2026-08_survey", DELEGATED_CONFIG)

    def read_manifest(self, study_dir: Path) -> str:
        return (study_dir / "study.yaml").read_text(encoding="utf-8")

    def test_status_prints_mode_and_next_action(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_status(self.interactive), 0)
        text = out.getvalue()
        self.assertIn("mode: interactive", text)
        self.assertIn("status: scoped", text)
        self.assertIn("mastery_approved", text)
        self.assertIn("next:", text)

    def test_approve_flips_gate_and_records_note(self) -> None:
        self.assertEqual(study.cmd_approve(self.interactive, "scope", "checked brief and budgets"), 0)
        self.assertIn("scope_approved: true", self.read_manifest(self.interactive))
        lines = (self.interactive / "approvals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["gate"], "scope_approved")
        self.assertEqual(record["note"], "checked brief and budgets")
        self.assertEqual(record["actor"], "human")

    def test_approve_full_gate_name(self) -> None:
        self.assertEqual(study.cmd_approve(self.delegated, "sources_approved", "packet complete"), 0)
        self.assertIn("sources_approved: true", self.read_manifest(self.delegated))

    def test_approve_rejects_foreign_gate(self) -> None:
        with self.assertRaises(SystemExit):
            study.cmd_approve(self.interactive, "sources", "n/a")
        self.assertIn("scope_approved: false", self.read_manifest(self.interactive))

    def test_approve_rejects_already_approved(self) -> None:
        study.cmd_approve(self.interactive, "scope", "first")
        with self.assertRaises(SystemExit):
            study.cmd_approve(self.interactive, "scope", "again")

    def test_approve_rejects_na_gate(self) -> None:
        with self.assertRaises(SystemExit):
            study.cmd_approve(self.interactive, "experiments", "n/a")

    def test_approve_via_main(self) -> None:
        self.assertEqual(study.main(["approve", str(self.interactive), "evidence", "--note", "packet grounded"]), 0)
        self.assertIn("evidence_approved: true", self.read_manifest(self.interactive))

    def test_interactive_commands_reject_delegated(self) -> None:
        for command in ("practice", "assess", "revisit"):
            with self.subTest(command=command):
                with self.assertRaises(SystemExit):
                    study.main([command, str(self.delegated)])

    def test_practice_lists_no_items_yet(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_practice(self.interactive), 0)
        self.assertIn("no practice items", out.getvalue())

    def test_practice_lists_items(self) -> None:
        item = self.interactive / "learning" / "practice" / "near-problem.md"
        item.write_text("# Near problem\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_practice(self.interactive), 0)
        self.assertIn("near-problem.md", out.getvalue())

    def test_assess_points_at_mastery_record(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_assess(self.interactive), 0)
        text = out.getvalue()
        self.assertIn("help level none", text)
        self.assertIn("mastery.md", text)

    def test_revisit_reports_unscheduled(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_revisit(self.interactive), 0)
        self.assertIn("no delayed review scheduled", out.getvalue())

    def test_revisit_reports_due(self) -> None:
        mastery = self.interactive / "learning" / "mastery.md"
        mastery.write_text(mastery.read_text(encoding="utf-8") + "\n- Next due: 2000-01-01\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_revisit(self.interactive), 0)
        self.assertIn("due for retrieval", out.getvalue())

    def test_revisit_reports_future(self) -> None:
        mastery = self.interactive / "learning" / "mastery.md"
        mastery.write_text(mastery.read_text(encoding="utf-8") + "\n- Next due: 2999-01-01\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_revisit(self.interactive), 0)
        self.assertIn("nothing due today", out.getvalue())


if __name__ == "__main__":
    unittest.main()
