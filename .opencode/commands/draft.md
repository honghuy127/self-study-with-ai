---
description: Advance the study one gated step: summarize unnoted sources, run experiments if asked, then draft the report. Idempotent; stops at each human gate. Usage: /draft studies/<slug>
agent: build
---

Advance the drafting pipeline for: $ARGUMENTS

The command is idempotent: it reads current state, does the next ungated step,
and stops at the next human gate. A later `/draft` run continues where the last
one stopped.

1. Read `brief.md`, `study.yaml`, and `sources/registry.yaml`. Refuse if
   `gates.sources_approved` is not `true`.
2. Load the `conduct-cs-ai-research` skill.
3. If `gates.notes_approved` is not `true`: dispatch the `summarizer`
   subagent once per registered source whose `status` is not `noted` (run
   them in parallel; each gets one source only). Then stop and ask the user
   to review `notes/` and flip `gates.notes_approved` before re-running
   `/draft`.
4. If the brief asks for experiments and `gates.experiments_approved` is not
   `true`: dispatch the `experimenter`, then stop and ask the user to review
   `experiments/` and flip `gates.experiments_approved`.
5. With the notes gate (and the experiments gate, when experiments are part
   of the brief) flipped, dispatch the `writer` subagent with the study
   directory. The writer produces `notes/_synthesis.md`, then
   `report/main.tex` and `report/refs.bib`.
6. Ask the human to run `tools/build_report.sh <study-dir>` and
   `python3 tools/lint_report.py <study-dir>`; surface both outputs.
7. Summarize the draft status and any `[RESULT PENDING]` markers. Remind the
   user to flip `gates.draft_approved` before `/review`.
