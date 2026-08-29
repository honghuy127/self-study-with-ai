from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from lint_report import citation_findings, lint  # noqa: E402


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


REGISTRY = (
    "sources:\n"
    "  - key: good2026\n"
    "    status: noted\n"
    "  - key: rejected2026\n"
    "    status: rejected\n"
)


def make_study(tmp: Path, tex: str, bib: str, registry: str | None = REGISTRY) -> Path:
    study = tmp / "study"
    (study / "report").mkdir(parents=True)
    (study / "sources").mkdir(parents=True)
    (study / "report" / "main.tex").write_text(tex, encoding="utf-8")
    (study / "report" / "refs.bib").write_text(bib, encoding="utf-8")
    if registry is not None:
        (study / "sources" / "registry.yaml").write_text(registry, encoding="utf-8")
    return study


class CitationCrossCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_consistent_study_clean(self):
        study = make_study(
            Path(self._tmp.name),
            "claim~\\citep{good2026}.\n",
            "@article{good2026,\n  title = {T}\n}\n",
        )
        errors, warnings = citation_findings(study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_cited_key_missing_from_bib_fails(self):
        study = make_study(Path(self._tmp.name), "claim~\\citep{ghost2026}.\n", "")
        errors, _ = citation_findings(study)
        self.assertTrue(any("ghost2026" in e and "missing from report/refs.bib" in e for e in errors))

    def test_multi_key_citation_checked(self):
        study = make_study(
            Path(self._tmp.name),
            "claims~\\citep{good2026,ghost2026}.\n",
            "@article{good2026,\n  title = {T}\n}\n",
        )
        errors, _ = citation_findings(study)
        self.assertTrue(any("ghost2026" in e for e in errors))
        self.assertFalse(any("good2026" in e for e in errors))

    def test_rejected_source_cited_fails(self):
        study = make_study(
            Path(self._tmp.name),
            "claim~\\citep{rejected2026}.\n",
            "@article{rejected2026,\n  title = {T}\n}\n",
        )
        errors, _ = citation_findings(study)
        self.assertTrue(any("registry-rejected" in e for e in errors))

    def test_bib_key_without_registry_record_warns(self):
        study = make_study(
            Path(self._tmp.name),
            "claim~\\citep{unregistered2026}.\n",
            "@article{unregistered2026,\n  title = {T}\n}\n",
        )
        errors, warnings = citation_findings(study)
        self.assertEqual(errors, [])
        self.assertTrue(any("unregistered2026" in w for w in warnings))

    def test_commented_citation_ignored(self):
        study = make_study(
            Path(self._tmp.name),
            "% \\citep{ghost2026}\nclean~\\citep{good2026}.\n",
            "@article{good2026,\n  title = {T}\n}\n",
        )
        errors, _ = citation_findings(study)
        self.assertEqual(errors, [])

    def test_no_registry_skips_registry_checks(self):
        study = make_study(
            Path(self._tmp.name),
            "claim~\\citep{good2026}.\n",
            "@article{good2026,\n  title = {T}\n}\n",
            registry=None,
        )
        errors, warnings = citation_findings(study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_slides_use_deck_local_bibliography(self):
        study = make_study(Path(self._tmp.name), "", "")
        (study / "slides").mkdir()
        (study / "slides" / "main.tex").write_text(
            "claim~\\citep{good2026}.\n", encoding="utf-8"
        )
        (study / "slides" / "refs.bib").write_text(
            "@article{good2026,\n  title = {T}\n}\n", encoding="utf-8"
        )
        errors, warnings = citation_findings(study)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
