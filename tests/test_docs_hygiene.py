"""Docs must not promise tools, paths, or commands that do not exist.

The README and AGENTS.md are the contract a new reader reads first, and they
have drifted from the tree before: they advertised example studies that
existed in no clone, and kept citing shell scripts after they were replaced.
These checks are cheap and catch exactly that class of rot. The contract
tables themselves are generated and checked separately by tools/docsgen.py.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("README.md", "AGENTS.md", "CLAUDE.md", "examples/README.md")

# Tokens left behind by removed templates and replaced scripts.
BANNED_TOKENS = (
    "fake-beamer",
    "/powerpoint",
    "build_report.sh",
    "build_slides.sh",
    "research.sh",
)

TOOL_REFERENCE = re.compile(r"tools/([a-z_]+\.py)")
PATH_REFERENCE = re.compile(r"\]\((?!http)([^)#]+)[^)]*\)")


def doc_text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


class DocsHygieneTests(unittest.TestCase):
    def test_no_removed_tokens(self) -> None:
        for name in DOCS:
            text = doc_text(name)
            for token in BANNED_TOKENS:
                with self.subTest(file=name, token=token):
                    self.assertNotIn(token, text)

    def test_every_referenced_tool_exists(self) -> None:
        for name in DOCS:
            for tool in sorted(set(TOOL_REFERENCE.findall(doc_text(name)))):
                with self.subTest(file=name, tool=tool):
                    self.assertTrue(
                        (ROOT / "tools" / tool).is_file(),
                        f"{name} references tools/{tool}, which does not exist",
                    )

    def test_every_relative_link_resolves(self) -> None:
        for name in DOCS:
            base = (ROOT / name).parent
            for target in sorted(set(PATH_REFERENCE.findall(doc_text(name)))):
                with self.subTest(file=name, link=target):
                    self.assertTrue(
                        (base / target).exists(),
                        f"{name} links to {target}, which does not exist",
                    )

    def test_readme_advertises_only_examples_that_ship(self) -> None:
        """The README used to list five example studies that shipped in no clone."""
        text = doc_text("README.md")
        for match in re.findall(r"examples/(20\d\d-\d\d_[a-z0-9-]+)", text):
            with self.subTest(example=match):
                self.assertTrue((ROOT / "examples" / match).is_dir())

    def test_generated_directories_warn_against_hand_editing(self) -> None:
        for generated in (
            ROOT / ".opencode" / "agents" / "researcher.md",
            ROOT / ".claude" / "agents" / "researcher.md",
            ROOT / ".opencode" / "commands" / "gather.md",
            ROOT / ".claude" / "commands" / "gather.md",
        ):
            with self.subTest(path=generated.name):
                self.assertIn("Generated from runtime/", generated.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
