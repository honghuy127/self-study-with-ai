---
description: Scaffold a new study directory from a topic. Usage: /new-study <topic-slug> [title]
agent: build
---

Create a new study for the topic: $ARGUMENTS

Steps:

1. Parse a lowercase-hyphen slug and an optional human-readable title from the
   argument string. If no title is given, derive one from the slug.
2. Run: `python3 tools/new_study.py <slug> --title "<title>"`.
3. When it succeeds, open the new `brief.md` and tell the user which fields to
   fill in before `/gather` (question, scope, depth, deadline). Do not fill
   them yourself; the brief is human-owned.

Stop after scaffolding. Do not start gathering.
