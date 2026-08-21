from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import new_study  # noqa: E402
from new_study import (  # noqa: E402
    DELIVERABLES,
    INTERACTIVE_GATES_BLOCK,
    MODES,
    copy_templates,
    is_valid_slug,
    parse_deliverables,
    render_study_yaml,
    slugify,
    study_dir_name,
)


def fields(**overrides) -> dict:
    base = {
        "id": "2026-08_foo",
        "title": "Foo Study",
        "created": "2026-08-19",
        "mode": "delegated",
        "intent": "survey",
        "assurance": "grounded",
        "methodology": "source-only",
        "deliverables": ["report", "slides"],
        "status": "proposed",
    }
    base.update(overrides)
    return base


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_hyphenates(self):
        self.assertEqual(slugify("Hello World!"), "hello-world")

    def test_collapses_runs(self):
        self.assertEqual(slugify("a---b   c"), "a-b-c")

    def test_strips_edges(self):
        self.assertEqual(slugify("--abc--"), "abc")

    def test_empty_falls_back(self):
        self.assertEqual(slugify("!!!"), "study")


class SlugValidationTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(is_valid_slug("a"))
        self.assertTrue(is_valid_slug("ab-123"))

    def test_invalid(self):
        for bad in ("", "-abc", "Abc", "a_b", "a b"):
            with self.subTest(slug=bad):
                self.assertFalse(is_valid_slug(bad))


class StudyDirNameTest(unittest.TestCase):
    def test_prefixes_year_month(self):
        self.assertEqual(study_dir_name("foo", dt.date(2026, 8, 19)), "2026-08_foo")


class RenderStudyYamlTest(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "shared" / "templates" / "study.yaml").read_text(encoding="utf-8")

    def test_fills_fields(self):
        out = render_study_yaml(self.template, fields())
        self.assertIn('id: "2026-08_foo"', out)
        self.assertIn('title: "Foo Study"', out)
        self.assertIn('created: "2026-08-19"', out)
        self.assertIn("mode: delegated", out)
        self.assertIn("intent: survey", out)
        self.assertIn("assurance: grounded", out)
        self.assertIn("methodology: source-only", out)
        self.assertIn("status: proposed", out)
        self.assertNotIn('id: ""', out)
        self.assertNotIn('title: ""', out)
        self.assertNotIn('created: ""', out)

    def test_renders_deliverables_list(self):
        out = render_study_yaml(self.template, fields(deliverables=["learning-note"]))
        self.assertIn("  - learning-note\n", out)
        self.assertNotIn("  - report\n", out)

    def test_interactive_mode_swaps_gates_block(self):
        out = render_study_yaml(self.template, fields(mode="interactive", status="scoped"))
        self.assertIn("mode: interactive", out)
        self.assertIn("status: scoped", out)
        for gate in ("scope_approved: false", "evidence_approved: false", "mastery_approved: false"):
            self.assertIn(gate, out)
        self.assertNotIn("sources_approved", out)
        self.assertNotIn("review_signed_off", out)

    def test_experimental_methodology_sets_boolean_gate(self):
        out = render_study_yaml(self.template, fields(methodology="experimental"))
        self.assertIn("experiments_approved: false", out)
        self.assertNotIn("experiments_approved: n_a", out)

    def test_source_only_methodology_keeps_na_gate(self):
        out = render_study_yaml(self.template, fields())
        self.assertIn("experiments_approved: n_a", out)

    def test_interactive_gates_block_matches_template(self):
        self.assertIn("mastery_approved: false", INTERACTIVE_GATES_BLOCK)


class ParseDeliverablesTest(unittest.TestCase):
    def test_splits_and_strips(self):
        self.assertEqual(parse_deliverables("report, slides"), ["report", "slides"])

    def test_empty_becomes_none(self):
        self.assertEqual(parse_deliverables(""), ["none"])

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            parse_deliverables("report,paper")

    def test_values_cover_choices(self):
        self.assertIn("learning-note", DELIVERABLES)
        self.assertIn("none", DELIVERABLES)


class CopyTemplatesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def scaffold(self, name: str, **overrides) -> Path:
        config = {
            "mode": "delegated",
            "intent": "survey",
            "assurance": "grounded",
            "methodology": "source-only",
            "deliverables": ["report", "slides"],
        }
        config.update(overrides)
        study = Path(self._tmp.name) / name
        study.mkdir()
        copy_templates(study, name, name.replace("_", " "), config)
        return study

    def test_interactive_scaffold(self):
        study = self.scaffold(
            "2026-08_learn",
            mode="interactive",
            intent="understand",
            deliverables=["learning-note"],
        )
        for rel in (
            "learning/baseline.md",
            "learning/map.md",
            "learning/journal.md",
            "learning/mastery.md",
            "outputs/learning-note.md",
            "brief.md",
            "study.yaml",
            "sources/registry.yaml",
        ):
            self.assertTrue((study / rel).is_file(), rel)
        self.assertTrue((study / "learning" / "practice").is_dir())
        for rel in ("report", "slides", "reviews", "experiments"):
            self.assertFalse((study / rel).exists(), rel)
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("mode: interactive", text)
        self.assertIn("status: scoped", text)
        self.assertIn("mastery_approved: false", text)
        self.assertIn("experiments_approved: n_a", text)

    def test_delegated_scaffold(self):
        study = self.scaffold("2026-08_delegated")
        for rel in ("report/main.tex", "slides/main.tex", "brief.md", "sources/registry.yaml"):
            self.assertTrue((study / rel).is_file(), rel)
        self.assertTrue((study / "reviews").is_dir())
        self.assertTrue((study / "notes").is_dir())
        self.assertFalse((study / "learning").exists())
        self.assertFalse((study / "experiments").exists())
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("mode: delegated", text)
        self.assertIn("status: proposed", text)
        self.assertIn("sources_approved: false", text)

    def test_experimental_methodology_creates_experiments_dir(self):
        study = self.scaffold("2026-08_exp", methodology="experimental")
        self.assertTrue((study / "experiments").is_dir())
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("experiments_approved: false", text)

    def test_delegated_without_report_deliverable_skips_report(self):
        study = self.scaffold("2026-08_brief", deliverables=["decision-brief"])
        self.assertFalse((study / "report").exists())
        self.assertFalse((study / "slides").exists())


class MainCliTest(unittest.TestCase):
    def test_mode_is_required(self):
        with self.assertRaises(SystemExit) as cm:
            new_study.main(["foo"])
        self.assertEqual(cm.exception.code, 2)

    def test_unknown_deliverable_fails(self):
        self.assertEqual(new_study.main(["foo", "--mode", "delegated", "--deliverables", "paper"]), 2)

    def test_modes_constant(self):
        self.assertEqual(MODES, ("interactive", "delegated"))


if __name__ == "__main__":
    unittest.main()
