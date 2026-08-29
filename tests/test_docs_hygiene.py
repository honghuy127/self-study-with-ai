from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Tokens left behind by removed templates; docs must not reference them.
BANNED_TOKENS = ("fake-beamer", "/powerpoint")


class DocsHygieneTests(unittest.TestCase):
    def test_readme_and_agents_carry_no_removed_template_tokens(self) -> None:
        for name in ("README.md", "AGENTS.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for token in BANNED_TOKENS:
                with self.subTest(file=name, token=token):
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
