---
description: Scaffold a new study directory from a topic. Usage: /new-study <topic-slug> [title] --mode interactive|delegated
agent: build
---

Create a new study for the topic: $ARGUMENTS

Steps:

1. Parse a lowercase-hyphen slug, an optional human-readable title, and a
   required `--mode` value from the argument string. If no title is given,
   derive one from the slug. If no mode is given, ask the user:
   `interactive` means the user personally learns and demonstrates the
   capability; `delegated` means agents investigate and return a report.
   Never guess the mode.
2. Run: `python3 tools/new_study.py <slug> --title "<title>" --mode <mode>`,
   adding `--intent`, `--assurance`, `--methodology`, `--deliverables`, or
   `--report-style` only when the user specified them. `--report-style` is
   `neurips` (default, publication-shaped) or `plain` (lighter article) and
   only matters when `report` is a deliverable.
3. When it succeeds, open the new `brief.md` and tell the user which fields
   to fill in before work starts (purpose, questions, scope, budgets, stop
   rules, and the mode-specific contract). Do not fill them yourself; the
   brief is human-owned.

Stop after scaffolding. Do not start gathering or tutoring.
