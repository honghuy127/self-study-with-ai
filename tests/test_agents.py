"""Permission-contract tests for the agent definitions.

Each test asserts that a documented agent procedure is executable under the
agent's declared frontmatter permissions. The historical contradictions
(summarizer updating the registry, researcher appending the evidence
ledger, experimenter appending the claims ledger, writer compiling, agents
editing study.yaml) must fail these tests if reintroduced.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

AGENTS = Path(__file__).resolve().parent.parent / ".opencode" / "agents"


def frontmatter(name: str) -> dict:
    text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    data = yaml.safe_load(parts[1])
    assert isinstance(data, dict), f"{name}.md frontmatter did not parse to a mapping"
    return data


def edit_rules(name: str) -> dict:
    permission = frontmatter(name).get("permission") or {}
    return permission.get("edit") or {}


def allows(rules: dict, pattern: str) -> bool:
    return rules.get(pattern) == "allow"


class ZoneBasicsTests(unittest.TestCase):
    def test_all_agents_exist(self):
        for name in ("researcher", "summarizer", "experimenter", "writer", "reviewer"):
            with self.subTest(name=name):
                self.assertTrue((AGENTS / f"{name}.md").is_file())

    def test_no_agent_edits_study_yaml(self):
        """Gates and lifecycle state are human-owned via tools/study.py."""
        for name in ("researcher", "summarizer", "experimenter", "writer", "reviewer"):
            with self.subTest(name=name):
                self.assertNotIn("studies/**/study.yaml", edit_rules(name))

    def test_edit_defaults_to_deny(self):
        for name in ("researcher", "summarizer", "experimenter", "writer", "reviewer"):
            with self.subTest(name=name):
                self.assertEqual(edit_rules(name).get("*"), "deny")


class SummarizerPermissionTests(unittest.TestCase):
    def test_can_write_notes(self):
        self.assertTrue(allows(edit_rules("summarizer"), "studies/**/notes/**"))

    def test_can_update_registry_status(self):
        """Procedure step 3 updates status and notes_file in the registry."""
        self.assertTrue(allows(edit_rules("summarizer"), "studies/**/sources/registry.yaml"))

    def test_no_web_access(self):
        permission = frontmatter("summarizer")["permission"]
        self.assertEqual(permission.get("webfetch"), "deny")
        self.assertEqual(permission.get("websearch"), "deny")


class ResearcherPermissionTests(unittest.TestCase):
    def test_can_write_sources(self):
        self.assertTrue(allows(edit_rules("researcher"), "studies/**/sources/**"))

    def test_can_append_evidence_ledger(self):
        """Procedure step 7 appends to .research/evidence.jsonl directly."""
        self.assertTrue(allows(edit_rules("researcher"), "studies/**/.research/evidence.jsonl"))


class ExperimenterPermissionTests(unittest.TestCase):
    def test_can_write_experiments(self):
        self.assertTrue(allows(edit_rules("experimenter"), "studies/**/experiments/**"))

    def test_can_append_claims_ledger(self):
        """Procedure step 5 appends claim records to .research/claims.jsonl."""
        self.assertTrue(allows(edit_rules("experimenter"), "studies/**/.research/claims.jsonl"))


class WriterPermissionTests(unittest.TestCase):
    def test_bash_not_denied(self):
        """Procedure steps 4 and 6 compile and lint; bash: deny blocked both."""
        permission = frontmatter("writer")["permission"]
        self.assertIn(permission.get("bash"), ("ask", "allow"))

    def test_can_write_report_slides_synthesis(self):
        rules = edit_rules("writer")
        self.assertTrue(allows(rules, "studies/**/report/**"))
        self.assertTrue(allows(rules, "studies/**/slides/**"))
        self.assertTrue(allows(rules, "studies/**/notes/_synthesis.md"))

    def test_no_web_access(self):
        permission = frontmatter("writer")["permission"]
        self.assertEqual(permission.get("webfetch"), "deny")
        self.assertEqual(permission.get("websearch"), "deny")


class ReviewerPermissionTests(unittest.TestCase):
    def test_can_write_reviews(self):
        self.assertTrue(allows(edit_rules("reviewer"), "studies/**/reviews/**"))

    def test_cannot_edit_report(self):
        rules = edit_rules("reviewer")
        self.assertFalse(allows(rules, "studies/**/report/**"))


if __name__ == "__main__":
    unittest.main()
