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

import knowledge  # noqa: E402
import review  # noqa: E402

from tests.test_knowledge import write_unit  # noqa: E402


def quiet(fn, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = fn(*args, **kwargs)
    return code, out.getvalue()


class LadderTests(unittest.TestCase):
    def test_recall_advances_one_rung(self) -> None:
        self.assertEqual(review.next_interval(0, "recalled"), 1)
        self.assertEqual(review.next_interval(1, "recalled"), 7)
        self.assertEqual(review.next_interval(7, "recalled"), 30)

    def test_recall_saturates_at_the_top_rung(self) -> None:
        self.assertEqual(review.next_interval(365, "recalled"), 365)

    def test_partial_holds_the_current_rung(self) -> None:
        self.assertEqual(review.next_interval(30, "partial"), 30)

    def test_miss_drops_to_the_first_rung(self) -> None:
        self.assertEqual(review.next_interval(365, "missed"), 1)

    def test_interval_parsing(self) -> None:
        self.assertEqual(review.parse_interval("7d"), 7)
        self.assertEqual(review.parse_interval("3w"), 21)
        self.assertEqual(review.parse_interval("6m"), 180)
        self.assertEqual(review.parse_interval("1y"), 365)
        with self.assertRaises(SystemExit):
            review.parse_interval("soon")


class ReviewQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="review-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.base = self.tmp / "knowledge"
        self.base.mkdir()
        for module, name, value in (
            (knowledge, "KNOWLEDGE", self.base),
            (review, "LOG", self.tmp / "review-log.jsonl"),
            (review, "STUDIES", self.tmp / "studies"),
            (review, "EXAMPLES", self.tmp / "examples"),
        ):
            old = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, old)

    def test_due_lists_only_what_is_due(self) -> None:
        write_unit(self.base, "due.now", due="2020-01-01")
        write_unit(self.base, "due.later", due="2999-01-01")
        code, out = quiet(review.main, ["due", "--on", "2026-09-02"])
        self.assertEqual(code, 0)
        self.assertIn("due.now", out)
        self.assertNotIn("due.later", out.split("unit(s) have no review")[0].split("upcoming")[0])

    def test_due_reports_unscheduled_units(self) -> None:
        write_unit(self.base, "never.scheduled")
        code, out = quiet(review.main, ["due", "--on", "2026-09-02"])
        self.assertEqual(code, 0)
        self.assertIn("no review scheduled", out)
        self.assertIn("never.scheduled", out)

    def test_run_withholds_the_answer(self) -> None:
        write_unit(self.base, "attention.scale", question="Why 1/sqrt(d_k)?", body="Variance normalization.")
        code, out = quiet(review.main, ["run", "attention.scale"])
        self.assertEqual(code, 0)
        self.assertIn("Why 1/sqrt(d_k)?", out)
        self.assertNotIn("Variance normalization", out)
        self.assertIn("withheld", out)

    def test_record_reschedules_and_logs(self) -> None:
        write_unit(self.base, "attention.scale", due="2026-09-01")
        code, out = quiet(review.main, ["record", "attention.scale", "--result", "recalled", "--on", "2026-09-02"])
        self.assertEqual(code, 0)
        self.assertIn("next due 2026-09-03", out)

        unit = knowledge.by_id(knowledge.load_units(self.base))["attention.scale"]
        self.assertEqual(unit.next_due, "2026-09-03")
        self.assertEqual(unit.meta["review"]["last_result"], "recalled")
        self.assertEqual(unit.meta["review"]["reviews"], 1)

        entries = [json.loads(line) for line in review.LOG.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(entries[-1]["unit"], "attention.scale")
        self.assertEqual(entries[-1]["result"], "recalled")

    def test_record_preserves_the_rest_of_the_unit(self) -> None:
        write_unit(self.base, "attention.scale", question="Why?", body="Because of variance.")
        quiet(review.main, ["record", "attention.scale", "--result", "partial", "--on", "2026-09-02"])
        unit = knowledge.by_id(knowledge.load_units(self.base))["attention.scale"]
        self.assertEqual(unit.question, "Why?")
        self.assertIn("Because of variance.", unit.body)

    def test_repeated_recall_walks_up_the_ladder(self) -> None:
        write_unit(self.base, "attention.scale")
        quiet(review.main, ["record", "attention.scale", "--result", "recalled", "--on", "2026-09-02"])
        quiet(review.main, ["record", "attention.scale", "--result", "recalled", "--on", "2026-09-03"])
        unit = knowledge.by_id(knowledge.load_units(self.base))["attention.scale"]
        self.assertEqual(unit.meta["review"]["interval_days"], 7)

    def test_miss_resets_the_ladder(self) -> None:
        write_unit(self.base, "attention.scale")
        for day in ("2026-09-02", "2026-09-03", "2026-09-04"):
            quiet(review.main, ["record", "attention.scale", "--result", "recalled", "--on", day])
        quiet(review.main, ["record", "attention.scale", "--result", "missed", "--on", "2026-09-05"])
        unit = knowledge.by_id(knowledge.load_units(self.base))["attention.scale"]
        self.assertEqual(unit.meta["review"]["interval_days"], 1)

    def test_schedule_sets_an_explicit_due_date(self) -> None:
        write_unit(self.base, "attention.scale")
        quiet(review.main, ["schedule", "attention.scale", "--in", "2w", "--on", "2026-09-02"])
        unit = knowledge.by_id(knowledge.load_units(self.base))["attention.scale"]
        self.assertEqual(unit.next_due, "2026-09-16")

    def test_unknown_unit_is_refused(self) -> None:
        for argv in (["run", "nope"], ["record", "nope", "--result", "recalled"], ["schedule", "nope", "--in", "7d"]):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit):
                    review.main(argv)

    def test_mastery_records_surface_in_the_queue(self) -> None:
        mastery = review.STUDIES / "2026-08_pilot" / "learning"
        mastery.mkdir(parents=True)
        (mastery / "mastery.md").write_text("## Reviews\n\n- Next due: 2026-08-30\n", encoding="utf-8")
        code, out = quiet(review.main, ["due", "--on", "2026-09-02"])
        self.assertEqual(code, 0)
        self.assertIn("2026-08_pilot", out)
        self.assertIn("study.py revisit", out)


if __name__ == "__main__":
    unittest.main()
