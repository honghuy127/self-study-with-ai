from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from lint_report import lint  # noqa: E402


def lint_text(text: str) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "main.tex"
        path.write_text(text, encoding="utf-8")
        return lint(path)


class MarkerTest(unittest.TestCase):
    def test_flagged(self):
        findings = lint_text("We claim [CITATION NEEDED] something.\n")
        self.assertTrue(any("unresolved marker" in f for f in findings))

    def test_all_three_markers(self):
        text = "[CITATION NEEDED] [EVIDENCE NEEDED] [RESULT PENDING]\n"
        findings = lint_text(text)
        self.assertEqual(sum(1 for f in findings if "unresolved marker" in f), 3)


class EmDashTest(unittest.TestCase):
    def test_ascii(self):
        self.assertTrue(any("em-dash" in f for f in lint_text("word --- word\n")))

    def test_unicode(self):
        self.assertTrue(any("em-dash" in f for f in lint_text("word — word\n")))

    def test_en_dash_allowed(self):
        self.assertEqual(lint_text("key--value pairs\n"), [])


class CitationTieTest(unittest.TestCase):
    def test_untied_flagged(self):
        findings = lint_text("as shown \\cite{a} and claimed \\citep{b}\n")
        self.assertTrue(any("untied" in f for f in findings))

    def test_untied_ref_flagged(self):
        findings = lint_text("in Section \\ref{s} we see\n")
        self.assertTrue(any("untied" in f for f in findings))

    def test_tied_clean(self):
        self.assertEqual(lint_text("claim~\\citep{a}. See Section~\\ref{s}.\n"), [])


class BritishSpellingTest(unittest.TestCase):
    def test_flagged(self):
        findings = lint_text("We optimised the behaviour.\n")
        self.assertTrue(any("British spelling" in f for f in findings))

    def test_american_clean(self):
        self.assertEqual(lint_text("We optimized the behavior.\n"), [])


class CrossLineTieTest(unittest.TestCase):
    def test_line_start_cite_untied_flagged(self):
        findings = lint_text("asserted, not measured:\n\\citep{a} shows X.\n")
        self.assertTrue(any("line start" in f for f in findings))

    def test_line_start_cite_after_blank_ok(self):
        self.assertEqual(lint_text("Some text.\n\n\\citep{a} shows X.\n"), [])

    def test_tied_rewrite_clean(self):
        self.assertEqual(lint_text("not measured: Vaswani et~al.~\\citep{a} show X.\n"), [])


class CommentHandlingTest(unittest.TestCase):
    def test_comment_content_ignored(self):
        self.assertEqual(lint_text("% comment with --- and optimised\nClean line.\n"), [])

    def test_marker_in_comment_ignored(self):
        self.assertEqual(lint_text("% [CITATION NEEDED]\nBody.\n"), [])


class CleanFileTest(unittest.TestCase):
    def test_passthrough(self):
        self.assertEqual(lint_text("Plain text. Cite~\\citep{k} here.\n"), [])


if __name__ == "__main__":
    unittest.main()
