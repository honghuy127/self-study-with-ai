"""Permission-contract tests for the agent definitions.

Each test asserts that a documented agent procedure is executable under the
agent's declared write zone, and that the boundaries the workflow depends on
are not quietly widened. The historical contradictions (summarizer updating
the registry, researcher appending the evidence ledger, experimenter
appending the claims ledger, writer compiling, agents editing study.yaml)
must fail these tests if reintroduced.

The definitions live in runtime/ and are rendered into both harnesses, so the
contract is asserted once, against the source.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime" / "agents"

DELEGATED_AGENTS = ("researcher", "summarizer", "paper-analyst", "experimenter", "writer", "reviewer")
INTERACTIVE_AGENTS = ("tutor", "assessor")
ALL_AGENTS = DELEGATED_AGENTS + INTERACTIVE_AGENTS


def frontmatter(name: str) -> dict:
    text = (RUNTIME / f"{name}.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    data = yaml.safe_load(parts[1])
    assert isinstance(data, dict), f"{name}.md frontmatter did not parse to a mapping"
    return data


def writes(name: str) -> list[str]:
    return list(frontmatter(name).get("writes") or [])


def allows(name: str, glob: str) -> bool:
    return glob in writes(name)


class ZoneBasicsTests(unittest.TestCase):
    def test_all_agents_exist(self):
        for name in ALL_AGENTS:
            with self.subTest(name=name):
                self.assertTrue((RUNTIME / f"{name}.md").is_file())

    def test_no_agent_writes_lifecycle_state(self):
        """Gates, status, and provenance are human-owned via tools/study.py."""
        for name in ALL_AGENTS:
            for protected in ("studies/**/study.yaml", "studies/**/events.jsonl", "studies/**/archive.yaml"):
                with self.subTest(name=name, path=protected):
                    self.assertNotIn(protected, writes(name))

    def test_every_agent_declares_a_zone(self):
        for name in ALL_AGENTS:
            with self.subTest(name=name):
                self.assertTrue(writes(name), f"{name} declares no write zone")

    def test_frontmatter_name_matches_filename(self):
        for name in ALL_AGENTS:
            with self.subTest(name=name):
                self.assertEqual(frontmatter(name).get("name"), name)


class SummarizerPermissionTests(unittest.TestCase):
    def test_can_write_notes(self):
        self.assertTrue(allows("summarizer", "studies/**/notes/**"))

    def test_can_update_registry_status(self):
        """Procedure step 3 updates status and notes_file in the registry."""
        self.assertTrue(allows("summarizer", "studies/**/sources/registry.yaml"))

    def test_no_web_access(self):
        meta = frontmatter("summarizer")
        self.assertEqual(meta.get("webfetch"), "deny")
        self.assertEqual(meta.get("websearch"), "deny")


class ResearcherPermissionTests(unittest.TestCase):
    def test_can_write_sources(self):
        self.assertTrue(allows("researcher", "studies/**/sources/**"))

    def test_can_append_evidence_ledger(self):
        """Procedure step 7 appends to .research/evidence.jsonl directly."""
        self.assertTrue(allows("researcher", "studies/**/.research/evidence.jsonl"))


class ExperimenterPermissionTests(unittest.TestCase):
    def test_can_write_experiments(self):
        self.assertTrue(allows("experimenter", "studies/**/experiments/**"))

    def test_can_append_claims_ledger(self):
        """Procedure step 5 appends claim records to .research/claims.jsonl."""
        self.assertTrue(allows("experimenter", "studies/**/.research/claims.jsonl"))


class WriterPermissionTests(unittest.TestCase):
    def test_bash_not_denied(self):
        """Procedure steps 4 and 6 compile and lint; bash: deny blocked both."""
        self.assertIn(frontmatter("writer").get("bash"), ("ask", "allow"))

    def test_can_write_report_slides_synthesis(self):
        self.assertTrue(allows("writer", "studies/**/report/**"))
        self.assertTrue(allows("writer", "studies/**/slides/**"))
        self.assertTrue(allows("writer", "studies/**/notes/_synthesis.md"))

    def test_no_web_access(self):
        meta = frontmatter("writer")
        self.assertEqual(meta.get("webfetch"), "deny")
        self.assertEqual(meta.get("websearch"), "deny")


class PaperAnalystPermissionTests(unittest.TestCase):
    def test_can_write_only_paper_analysis(self):
        self.assertEqual(writes("paper-analyst"), ["studies/**/notes/_paper-analysis.md"])

    def test_no_web_access(self):
        meta = frontmatter("paper-analyst")
        self.assertEqual(meta.get("webfetch"), "deny")
        self.assertEqual(meta.get("websearch"), "deny")


class ReviewerPermissionTests(unittest.TestCase):
    def test_can_write_reviews(self):
        self.assertTrue(allows("reviewer", "studies/**/reviews/**"))

    def test_cannot_edit_report(self):
        self.assertFalse(allows("reviewer", "studies/**/report/**"))


class AssessmentIndependenceTests(unittest.TestCase):
    """The tutor must not be able to write what the assessor grades.

    An assessment administered by the agent that wrote the answers is not an
    assessment. These are the structural halves of that separation; the rest
    lives in the two agents' prose.
    """

    def test_tutor_cannot_write_the_mastery_record(self):
        for path in ("studies/**/learning/mastery.md", "studies/**/learning/attempts/**"):
            with self.subTest(path=path):
                self.assertNotIn(path, writes("tutor"))

    def test_tutor_owns_teaching_artifacts(self):
        for path in (
            "studies/**/learning/map.md",
            "studies/**/learning/journal.md",
            "studies/**/learning/practice/**",
        ):
            with self.subTest(path=path):
                self.assertIn(path, writes("tutor"))

    def test_assessor_cannot_write_teaching_artifacts(self):
        for path in (
            "studies/**/learning/journal.md",
            "studies/**/learning/map.md",
            "studies/**/learning/practice/**",
            "studies/**/outputs/**",
        ):
            with self.subTest(path=path):
                self.assertNotIn(path, writes("assessor"))

    def test_assessor_owns_the_mastery_record(self):
        self.assertEqual(
            sorted(writes("assessor")),
            ["studies/**/learning/attempts/**", "studies/**/learning/mastery.md"],
        )

    def test_assessor_is_told_not_to_read_the_tutoring_history(self):
        text = (RUNTIME / "assessor.md").read_text(encoding="utf-8")
        for path in ("learning/journal.md", "learning/practice/", "outputs/learning-note.md"):
            with self.subTest(path=path):
                self.assertIn(path, text)

    def test_neither_side_has_web_access(self):
        for name in INTERACTIVE_AGENTS:
            with self.subTest(name=name):
                meta = frontmatter(name)
                self.assertEqual(meta.get("webfetch"), "deny")
                self.assertEqual(meta.get("websearch"), "deny")


if __name__ == "__main__":
    unittest.main()
