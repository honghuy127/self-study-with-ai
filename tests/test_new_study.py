from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from new_study import is_valid_slug, render_study_yaml, slugify, study_dir_name  # noqa: E402


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
        out = render_study_yaml(self.template, "2026-08_foo", "Foo Study", "full", "2026-08-19")
        self.assertIn('id: "2026-08_foo"', out)
        self.assertIn('title: "Foo Study"', out)
        self.assertIn('created: "2026-08-19"', out)
        self.assertIn("depth: full", out)
        self.assertNotIn('id: ""', out)
        self.assertNotIn('title: ""', out)

    def test_briefing_depth_kept(self):
        out = render_study_yaml(self.template, "i", "t", "briefing", "2026-08-19")
        self.assertIn("depth: briefing", out)


if __name__ == "__main__":
    unittest.main()
