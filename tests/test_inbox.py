from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import inbox  # noqa: E402
import knowledge  # noqa: E402
import new_study  # noqa: E402


def quiet(fn, *args, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = fn(*args, **kwargs)
    return code, out.getvalue()


class InboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="inbox-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for module, name, value in (
            (inbox, "INBOX", self.tmp / "inbox"),
            (inbox, "QUEUE", self.tmp / "queue.yaml"),
            (knowledge, "KNOWLEDGE", self.tmp / "knowledge"),
            (new_study, "STUDIES", self.tmp / "studies"),
        ):
            old = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, old)
        (self.tmp / "studies").mkdir()

    def note_path(self) -> Path:
        return sorted(inbox.INBOX.glob("*.md"))[0]

    def test_new_creates_a_note_seeded_with_the_question(self) -> None:
        code, _ = quiet(inbox.main, ["new", "Why does RoPE need a base?"])
        self.assertEqual(code, 0)
        path = self.note_path()
        self.assertIn("why-does-rope-need-a-base", path.name)
        meta, body = inbox.split_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(meta["question"], "Why does RoPE need a base?")
        self.assertEqual(meta["status"], "open")
        self.assertIn("Why does RoPE need a base?", body)
        self.assertIn("## Not verified", body)

    def test_duplicate_note_is_refused(self) -> None:
        quiet(inbox.main, ["new", "Same question", "--slug", "same"])
        with self.assertRaises(SystemExit):
            inbox.main(["new", "Same question", "--slug", "same"])

    def test_list_filters_by_status(self) -> None:
        quiet(inbox.main, ["new", "First question"])
        code, out = quiet(inbox.main, ["list", "--status", "open"])
        self.assertEqual(code, 0)
        self.assertIn("First question", out)
        _, out = quiet(inbox.main, ["list", "--status", "distilled"])
        self.assertIn("(0 of 1 notes)", out)

    def test_promote_scaffolds_a_study_and_links_both_ways(self) -> None:
        quiet(inbox.main, ["new", "Attention scaling origins", "--slug", "attn"])
        code, _ = quiet(inbox.main, ["promote", str(self.note_path()), "--mode", "delegated"])
        self.assertEqual(code, 0)
        meta, _ = inbox.split_frontmatter(self.note_path().read_text(encoding="utf-8"))
        self.assertEqual(meta["status"], "promoted")
        self.assertTrue(meta["study"])
        studies = sorted((self.tmp / "studies").iterdir())
        self.assertEqual(len(studies), 1)
        self.assertEqual(studies[0].name, meta["study"])

    def test_distill_creates_a_unit_carrying_the_answer(self) -> None:
        quiet(inbox.main, ["new", "Why sqrt(d_k)?", "--slug", "sqrt"])
        path = self.note_path()
        meta, body = inbox.split_frontmatter(path.read_text(encoding="utf-8"))
        body = body.replace(
            "[Two to five sentences. Every factual sentence must be attributable to an\nentry under Evidence. If it cannot be, it belongs under Not verified.]",
            "It normalizes logit variance to 1.",
        )
        meta["sources"] = ["vaswani2017attention"]
        inbox.write_note(path, meta, body)

        code, _ = quiet(inbox.main, ["distill", str(path), "--id", "attention.scale"])
        self.assertEqual(code, 0)
        meta, _ = inbox.split_frontmatter(path.read_text(encoding="utf-8"))
        self.assertEqual(meta["status"], "distilled")
        self.assertEqual(meta["unit"], "attention.scale")

        units = knowledge.by_id(knowledge.load_units(knowledge.KNOWLEDGE))
        self.assertIn("attention.scale", units)
        unit = units["attention.scale"]
        self.assertEqual(unit.list_field("source_ids"), ["vaswani2017attention"])
        self.assertIn("It normalizes logit variance to 1.", unit.body)

    def test_extract_section_ignores_untouched_template_guidance(self) -> None:
        body = "## Answer\n\n[Two to five sentences.]\n\n## Evidence\n\n- real line\n"
        self.assertEqual(inbox.extract_section(body, "Answer"), "")
        self.assertEqual(inbox.extract_section(body, "Evidence"), "- real line")

    def test_missing_note_is_refused(self) -> None:
        with self.assertRaises(SystemExit):
            inbox.main(["distill", "no-such-note", "--id", "x"])


class ReadingQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="queue-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for module, name, value in (
            (inbox, "QUEUE", self.tmp / "queue.yaml"),
            (new_study, "STUDIES", self.tmp / "studies"),
        ):
            old = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, old)
        (self.tmp / "studies").mkdir()

    def test_add_then_list(self) -> None:
        quiet(inbox.main, ["queue", "add", "Attention Is All You Need", "--url", "https://arxiv.org/abs/1706.03762"])
        code, out = quiet(inbox.main, ["queue", "list"])
        self.assertEqual(code, 0)
        self.assertIn("Attention Is All You Need", out)
        self.assertIn("1706.03762", out)

    def test_start_scaffolds_a_paper_reading_study(self) -> None:
        quiet(inbox.main, ["queue", "add", "Attention Is All You Need"])
        code, _ = quiet(inbox.main, ["queue", "start", "1"])
        self.assertEqual(code, 0)
        record = yaml.safe_load(inbox.QUEUE.read_text(encoding="utf-8"))
        self.assertEqual(record["queue"][0]["status"], "started")
        studies = sorted((self.tmp / "studies").iterdir())
        self.assertEqual(len(studies), 1)
        manifest = (studies[0] / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("mode: paper-reading", manifest)

    def test_start_rejects_an_out_of_range_number(self) -> None:
        quiet(inbox.main, ["queue", "add", "One item"])
        with self.assertRaises(SystemExit):
            inbox.main(["queue", "start", "5"])


if __name__ == "__main__":
    unittest.main()
