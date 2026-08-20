from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from new_study import TRACKS, copy_templates, is_valid_slug, render_study_yaml, slugify, study_dir_name  # noqa: E402


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
        out = render_study_yaml(self.template, "2026-08_foo", "Foo Study", "full", "review", "2026-08-19")
        self.assertIn('id: "2026-08_foo"', out)
        self.assertIn('title: "Foo Study"', out)
        self.assertIn('created: "2026-08-19"', out)
        self.assertIn("depth: full", out)
        self.assertNotIn('id: ""', out)
        self.assertNotIn('title: ""', out)

    def test_briefing_depth_kept(self):
        out = render_study_yaml(self.template, "i", "t", "briefing", "review", "2026-08-19")
        self.assertIn("depth: briefing", out)

    def test_review_track_sets_gate_na(self):
        out = render_study_yaml(self.template, "i", "t", "briefing", "review", "2026-08-19")
        self.assertIn("track: review", out)
        self.assertIn("experiments_approved: n_a", out)

    def test_concept_track_sets_gate_na(self):
        out = render_study_yaml(self.template, "i", "t", "briefing", "concept", "2026-08-19")
        self.assertIn("track: concept", out)
        self.assertIn("experiments_approved: n_a", out)

    def test_experimental_track_sets_boolean_gate(self):
        out = render_study_yaml(self.template, "i", "t", "full", "experimental", "2026-08-19")
        self.assertIn("track: experimental", out)
        self.assertIn("experiments_approved: false", out)
        self.assertNotIn("experiments_approved: n_a", out)

    def test_tracks_constant(self):
        self.assertEqual(TRACKS, ("review", "concept", "experimental"))


class CopyTemplatesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def scaffold(self, name: str, track: str) -> Path:
        study = Path(self._tmp.name) / name
        study.mkdir()
        copy_templates(study, name, name.replace("_", " "), "briefing", track)
        return study

    def test_review_track_skips_experiments_dir(self):
        study = self.scaffold("2026-08_foo", "review")
        self.assertFalse((study / "experiments").exists())
        self.assertTrue((study / "notes").is_dir())
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("track: review", text)
        self.assertIn("experiments_approved: n_a", text)

    def test_experimental_track_creates_experiments_dir(self):
        study = self.scaffold("2026-08_bar", "experimental")
        self.assertTrue((study / "experiments").is_dir())
        text = (study / "study.yaml").read_text(encoding="utf-8")
        self.assertIn("track: experimental", text)
        self.assertIn("experiments_approved: false", text)


if __name__ == "__main__":
    unittest.main()
