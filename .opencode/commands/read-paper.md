---
description: Advance a paper-reading study one gated step from target-paper acquisition through analysis and presentation. Usage: /read-paper studies/<slug>
agent: build
---

Advance the paper-reading pipeline for: $ARGUMENTS

This command drives `mode: paper-reading` only and is idempotent. Read the
current state, perform the next authorized stage, and stop at the next human
gate.

1. Read `brief.md` and `study.yaml`. Refuse if the brief is blank, the mode is
   not `paper-reading`, the methodology is experimental or mixed, or slides
   are not a deliverable. Load the `conduct-cs-ai-research` skill and its
   research-contract, paper-writing, presentation-slides,
   figures-and-diagrams, analysis-and-statistics, and quality-gates playbooks.
2. If `gates.paper_approved` is not true, move `proposed` to `gathering` via
   `python3 tools/study.py status-set`. Dispatch the researcher. It must
   verify exact metadata and a full-text snapshot, register exactly one
   non-rejected `role: target-paper`, and mark any other sources
   `role: context`. Stop with the paper-gate verdict and ask the human to run
   `python3 tools/study.py approve <id> paper --note "..."`.
3. If `gates.analysis_approved` is not true, move `gathering` to `analyzing`.
   Dispatch the summarizer once for every approved registry source that is not
   noted. Then dispatch the paper-analyst to fill
   `notes/_paper-analysis.md`. Stop with the analysis-gate verdict and ask the
   human to run `python3 tools/study.py approve <id> analysis --note "..."`.
4. If `gates.deck_approved` is not true, move `analyzing` to `presenting`.
   Dispatch the writer on the paper-reading route. It fills
   `slides/deck-plan.md`, authors `slides/main.tex`, runs
   `python3 tools/gen_bib.py <study-dir>`, builds and lints the deck, renders
   it to images, and visually inspects every slide. Stop with the talk-gate
   verdict and ask the human to inspect the rendered deck and run `python3
   tools/study.py approve <id> deck --note "..."`.
5. With the deck gate approved, tell the human to run `/review <study-dir>`.
   Review remains independent. Do not sign off or move the study to done.
