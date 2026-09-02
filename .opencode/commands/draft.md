---
description: "Advance a delegated study one gated step: summarize unnoted sources, run experiments on experimental methodologies, then draft the report. Idempotent; stops at each human gate. Usage: /draft studies/<slug>"
agent: build
---

<!-- Generated from runtime/commands/draft.md by tools/sync_runtimes.py. Edit the source, not this file. -->
Advance the drafting pipeline for: $ARGUMENTS

This command drives delegated studies only. For an interactive study, stop
and follow the tutor loop in AGENTS.md. For paper-reading, stop and use
`/read-paper` instead.

The command is idempotent: it reads current state, does the next ungated
step, and stops at the next human gate. A later `/draft` run continues where
the last one stopped.

1. Read `brief.md`, `study.yaml`, and `sources/registry.yaml`. Refuse if
   `gates.sources_approved` is not `true`.
2. Load the `conduct-cs-ai-research` skill.
3. If `gates.notes_approved` is not `true`: if the status is `gathering`,
   move it first (`python3 tools/study.py status-set <study-id> summarizing
   --note "..."`). Then dispatch the `summarizer`
   subagent once per registered source whose `status` is not `noted` (run
   them in parallel; each gets one source only). Then stop and ask the user
   to review `notes/` and approve the notes gate (`python3
   tools/study.py approve <study-id> notes --note "..."`) before re-running
   `/draft`.
4. If `study.yaml` says `methodology: experimental` or `methodology: mixed`
   and `gates.experiments_approved` is not `true`: move the status to
   `experimenting` (`python3 tools/study.py status-set <study-id>
   experimenting --note "..."`), dispatch the
   `experimenter`, then stop and ask the user to review `experiments/` and
   approve the experiments gate. On `source-only` and `static-code`
   methodologies this gate is `n_a`; skip the step entirely and never treat
   it as unflipped.
5. With the notes gate flipped (and the experiments gate too, on
   experimental methodologies), move the status to `drafting` (`python3
   tools/study.py status-set <study-id> drafting --note "..."`; the CLI
   refuses unless the required gates are approved). Then dispatch the
   `writer` subagent with the
   study directory. The writer produces `notes/_synthesis.md`, then
   `report/main.tex` and `report/refs.bib`.
6. Ask the human to run `python3 tools/build.py report <study-dir>` and
   `python3 tools/lint_report.py <study-dir>`; surface both outputs.
7. Summarize the draft status and any `[RESULT PENDING]` markers. Remind the
   user to approve the draft gate (`python3 tools/study.py approve
   <study-id> draft --note "..."`) before `/review`.
