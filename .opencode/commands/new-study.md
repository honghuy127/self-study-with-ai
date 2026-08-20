---
description: Scaffold a new study directory from a topic. Usage: /new-study <topic-slug> [title] [--track review|concept|experimental]
agent: build
---

Create a new study for the topic: $ARGUMENTS

Steps:

1. Parse a lowercase-hyphen slug, an optional human-readable title, and an
   optional `--track` value from the argument string. If no title is given,
   derive one from the slug. If no track is given, default to `review`;
   pick `experimental` only when the topic clearly needs runnable evidence.
2. Run: `python3 tools/new_study.py <slug> --title "<title>" --track <track>`.
3. When it succeeds, open the new `brief.md` and tell the user which fields to
   fill in before `/gather` (question, scope, depth, deadline). Do not fill
   them yourself; the brief is human-owned.

Stop after scaffolding. Do not start gathering.
