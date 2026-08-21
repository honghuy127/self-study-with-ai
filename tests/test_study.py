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

    def read_events(self, study_dir: Path) -> list[dict]:
        events = study_dir / "events.jsonl"
        if not events.is_file():
            return []
        return [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines() if line]

    def test_status_prints_mode_and_next_action(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_status(self.interactive), 0)
        text = out.getvalue()
        self.assertIn("mode: interactive", text)
        self.assertIn("status: scoped", text)
        self.assertIn("mastery_approved", text)
        self.assertIn("next:", text)
        self.assertIn("allowed transitions: diagnosing", text)

    def test_approve_flips_gate_and_records_event(self) -> None:
        self.assertEqual(study.cmd_approve(self.interactive, "scope", "checked brief and budgets"), 0)
        self.assertIn("scope_approved: true", self.read_manifest(self.interactive))
        events = self.read_events(self.interactive)
        approvals = [e for e in events if e.get("type") == "approval"]
        self.assertEqual(len(approvals), 1)
        record = approvals[0]
        self.assertEqual(record["gate"], "scope_approved")
        self.assertEqual(record["note"], "checked brief and budgets")
        self.assertEqual(record["actor"], "human")
        self.assertIn("ts", record)

    def test_approve_records_evidence_and_reopen_condition(self) -> None:
        study.cmd_approve(
            self.interactive,
            "scope",
            "checked",
            evidence="brief.md budgets and stop rule",
            reopen="source budget changes",
        )
        record = self.read_events(self.interactive)[-1]
        self.assertEqual(record["evidence_inspected"], "brief.md budgets and stop rule")
        self.assertEqual(record["reopen_condition"], "source budget changes")

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

    def test_status_set_valid_transition(self) -> None:
        study.cmd_approve(self.interactive, "scope", "contract right")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_status_set(self.interactive, "diagnosing", "baseline recorded"), 0)
        self.assertIn("status: diagnosing", self.read_manifest(self.interactive))
        transitions = [e for e in self.read_events(self.interactive) if e.get("type") == "transition"]
        self.assertEqual(transitions[-1]["from"], "scoped")
        self.assertEqual(transitions[-1]["to"], "diagnosing")

    def test_status_set_rejects_invalid_transition(self) -> None:
        with self.assertRaises(SystemExit):
            study.cmd_status_set(self.interactive, "assessing", "skip ahead")
        self.assertIn("status: scoped", self.read_manifest(self.interactive))

    def test_status_set_enforces_gate_precondition(self) -> None:
        with self.assertRaises(SystemExit):
            study.cmd_status_set(self.interactive, "diagnosing", "scope not approved yet")
        self.assertIn("status: scoped", self.read_manifest(self.interactive))

    def test_status_set_delegated_drafting_requires_gates(self) -> None:
        for transition in ("gathering", "summarizing"):
            study.cmd_status_set(self.delegated, transition, "advancing")
        with self.assertRaises(SystemExit):
            study.cmd_status_set(self.delegated, "drafting", "notes not approved")
        study.cmd_approve(self.delegated, "sources", "packet complete")
        study.cmd_approve(self.delegated, "notes", "notes reviewed")
        self.assertEqual(study.cmd_status_set(self.delegated, "drafting", "gates approved"), 0)
        self.assertIn("status: drafting", self.read_manifest(self.delegated))

    def test_status_set_experimental_drafting_requires_experiments_gate(self) -> None:
        config = dict(DELEGATED_CONFIG, methodology="experimental", deliverables=["report"])
        experimental = scaffold(self.tmp, "2026-08_experimental", config)
        study.cmd_status_set(experimental, "gathering", "advancing")
        study.cmd_status_set(experimental, "summarizing", "advancing")
        study.cmd_status_set(experimental, "experimenting", "advancing")
        study.cmd_approve(experimental, "sources", "ok")
        study.cmd_approve(experimental, "notes", "ok")
        with self.assertRaises(SystemExit):
            study.cmd_status_set(experimental, "drafting", "experiments gate still pending")
        study.cmd_approve(experimental, "experiments", "runs reviewed")
        self.assertEqual(study.cmd_status_set(experimental, "drafting", "all gates approved"), 0)

    def test_status_set_backward_transition_allowed(self) -> None:
        study.cmd_approve(self.interactive, "scope", "ok")
        study.cmd_status_set(self.interactive, "diagnosing", "baseline")
        study.cmd_approve(self.interactive, "evidence", "packet grounded")
        study.cmd_status_set(self.interactive, "learning", "path planned")
        self.assertEqual(study.cmd_status_set(self.interactive, "diagnosing", "re-diagnose weak prerequisite"), 0)

    def test_status_set_rejects_terminal_state(self) -> None:
        # Interactive retained is genuinely terminal; only delegated done reopens.
        text = self.read_manifest(self.interactive).replace("status: scoped", "status: retained")
        (self.interactive / "study.yaml").write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            study.cmd_status_set(self.interactive, "practicing", "reopen")
        self.assertIn("status: retained", self.read_manifest(self.interactive))

    def test_status_set_reopen_delegated_done_to_review(self) -> None:
        text = self.read_manifest(self.delegated).replace("status: proposed", "status: done")
        text = text.replace("draft_approved: false", "draft_approved: true")
        (self.delegated / "study.yaml").write_text(text, encoding="utf-8")
        self.assertEqual(study.cmd_status_set(self.delegated, "review", "reopen for refresh"), 0)
        self.assertIn("status: review", self.read_manifest(self.delegated))

    def test_status_set_reopen_requires_draft_gate(self) -> None:
        text = self.read_manifest(self.delegated).replace("status: proposed", "status: done")
        (self.delegated / "study.yaml").write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            study.cmd_status_set(self.delegated, "review", "reopen without draft gate")
        self.assertIn("status: done", self.read_manifest(self.delegated))

    def make_done_delegated(self, cleaned: bool) -> Path:
        text = self.read_manifest(self.delegated).replace("status: proposed", "status: done")
        text = text.replace("draft_approved: false", "draft_approved: true")
        if cleaned:
            text = text.replace('cleaned: ""', 'cleaned: "2026-08-21"')
        (self.delegated / "study.yaml").write_text(text, encoding="utf-8")
        return self.delegated

    def test_reopen_interactive_is_terminal(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_reopen(self.interactive), 0)
        self.assertIn("stay terminal", out.getvalue())

    def test_reopen_reports_recoverable_archive(self) -> None:
        done = self.make_done_delegated(cleaned=True)
        (done / "archive.yaml").write_text(
            "archived_at: '2026-08-21'\n"
            "git_commit: abc123\n"
            "removed:\n"
            "  - path: .research\n"
            "    size_kb: 1\n"
            "    files: 1\n"
            "    retrieve: git show abc123:studies/x/.research\n",
            encoding="utf-8",
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_reopen(done), 0)
        self.assertIn("archive: 1 removed paths", out.getvalue())

    def test_reopen_flags_cleaned_study_without_archive(self) -> None:
        done = self.make_done_delegated(cleaned=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(study.cmd_reopen(done), 1)
        self.assertIn("no archive.yaml", out.getvalue())

    def test_status_set_via_main(self) -> None:
        study.main(["approve", str(self.interactive), "scope", "--note", "ok"])
        self.assertEqual(study.main(["status-set", str(self.interactive), "diagnosing", "--note", "baseline recorded"]), 0)
        self.assertIn("status: diagnosing", self.read_manifest(self.interactive))

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
