# Structured Self-Study with AI Agents

[![check](https://github.com/honghuy127/self-study-with-ai/actions/workflows/check.yml/badge.svg)](https://github.com/honghuy127/self-study-with-ai/actions/workflows/check.yml)

This repository is a working system for studying technical topics in depth
with AI agents. A human poses a question. Specialist agents gather sources,
write anchored notes, and draft a technical report in LaTeX. The human
reviews the output and approves it at defined gates, and every claim in the
final report traces to a checked source or a recorded experiment.

The goal is not to automate research but to make AI-assisted study
auditable. A chat transcript rots: months later you cannot tell which
statements came from verified sources and which came from a plausible-sounding
model. This workflow forces that distinction into the open. Gaps become
`[CITATION NEEDED]` markers instead of confident prose, sources are
snapshotted locally, and claims carry explicit truth states. The human, not
the agent, decides when a stage is good enough to proceed.

Everything is plain files, so oversight equals reading git diffs.

## How a study flows

A study moves through a fixed pipeline. Each arrow is a human gate: the
agent stops, you read what it produced, and you flip the corresponding field
in `study.yaml` by hand before the next stage runs.

```text
brief.md --> gather --> summarize --> (experiment) --> draft --> review --> done
                |           |              |             |          |
         sources_approved  notes_   experiments_     draft_    review_
                           approved  approved        approved  signed_off
```

Three tracks set what counts as evidence:

| Track | Purpose | Evidence base |
|---|---|---|
| `review` (default) | Literature synthesis: map a field, compare systems, survey a question | Sources only |
| `concept` | Concept exposition: explain some mechanism thoroughly | Sources only |
| `experimental` | Questions that need runnable evidence | Sources plus pinned, recorded runs |

Source-only tracks skip the experiment stage entirely; their
`experiments_approved` gate is `n_a` rather than a checkbox nobody can
honestly flip. Every study also picks a depth: `briefing` (notes plus a
short synthesis, light gates) or `full` (novelty checks, an audit-clean
dossier, and on experimental tracks frozen experiment plans and per-run
manifests).

When a study reaches `done` and you sign off, `tools/cleanup_study.py` slims
it to its knowledge core (brief, notes, report sources, registry) and drops
the working evidence chain from the tree. The chain stays recoverable in git
history. Distilled understanding is merged into `shared/` so later studies
start smarter.

## Getting started

### Requirements

- Python 3.10+ with PyYAML (the manifest and cleanup tools read YAML; the
  vendored dossier scripts are standard-library only)
- `latexmk` (or `tectonic`) for report and slide builds
- `pdftotext` (poppler) for paper snapshots during gathering
- git with submodule support
- [OpenCode](https://opencode.ai) to run the agents and lifecycle commands

### Clone and scaffold

```bash
git clone --recurse-submodules https://github.com/honghuy127/self-study-with-ai.git
cd self-study-with-ai

# A literature review (default track)
python3 tools/new_study.py transformer-length-extrapolation \
  --title "How do transformers extrapolate to longer sequences?"

# A study that runs experiments
python3 tools/new_study.py sgd-noise-scale \
  --title "What does SGD noise do to generalization?" --track experimental --depth full
```

This scaffolds `studies/YYYY-MM_<slug>/` from the templates in
`shared/templates/`. Fill in `brief.md` (question, scope, depth, deadline,
constraints). The brief is human-owned: agents refuse to act on a blank
template.

### Run the lifecycle

| Command | What it does |
|---|---|
| `/new-study <topic>` | Wraps `new_study.py`, scaffolds the study |
| `/gather <study-dir>` | The researcher agent collects sources into `sources/`, verifies metadata, and snapshots papers and pages |
| `/draft <study-dir>` | Idempotent; summarizes unnoted sources, runs experiments on experimental tracks, then the writer drafts `report/main.tex`. Stops at each gate |
| `/review <study-dir>` | The reviewer agent audits claims, citations, and traceability |

After each stage you review the output, flip the gate field in `study.yaml`,
and re-run the command to continue. One branch per study keeps the pull
request as your review surface.

## Who does what

Five subagents do the work, each confined to its own directory:

| Agent | Stage | Role | Writes |
|---|---|---|---|
| researcher | gathering | Searches scholarly and official sources, verifies each against a canonical page or DOI, snapshots papers (pdftotext) and pages, pins local codebases | `sources/` |
| summarizer | summarizing | One structured note per source, every claim anchored to a page, section, or code line. No web access | `notes/` |
| experimenter | experimenting | Experimental track only: pinned dependencies, isolated runs, per-run manifests; smoke tests are labeled as such and never count as evidence | `experiments/` |
| writer | drafting | Synthesizes notes into `notes/_synthesis.md`, then drafts the report and slides. No web access by design: its entire evidence base is what passed the gates | `report/`, `slides/` |
| reviewer | review | Adversarial pass over the draft: claim traceability, citation honesty, numbers, style | `reviews/` |

The permission boundaries are part of the design. The writer cannot browse,
so nothing from memory can leak into the report; if a fact is not in a note
or an approved experiment output, it does not exist for the writer.

## What a study looks like

```text
studies/<YYYY-MM_slug>/
├── brief.md                   # your input: question, scope, depth, deadline
├── study.yaml                 # manifest: track, depth, status, human gates
├── sources/registry.yaml      # every gathered source with bibtex key + trust tier
├── sources/repos.yaml         # pinned local codebase checkouts (codebase studies)
├── sources/docs/              # pdftotext and page snapshots; PDF binaries are never committed
├── notes/                     # one structured note per source + _synthesis.md
├── experiments/               # runnable code with pinned deps (experimental track only)
├── report/main.tex + refs.bib # NeurIPS preprint report, tools/build_report.sh
├── slides/main.tex            # beamer deck, tools/build_slides.sh; cites report/refs.bib
├── reviews/                   # per-round review notes
└── .research/                 # epistemic dossier (claims, evidence, run ledger)
```

## The two state layers

- **Workflow state** (`study.yaml.status`): where the study is in the
  pipeline (`proposed`, `gathering`, `summarizing`, `experimenting`,
  `drafting`, `review`, `done`). Human-gated. Review and concept tracks
  skip `experimenting`.
- **Epistemic state** (`.research/claims.jsonl`): the truth state of each
  claim, enforced by the `conduct-cs-ai-research` skill. Experimental
  claims move `PROPOSED → ... → EXECUTED → ANALYZED → VERIFIED →
  REPORTED`; review and concept claims move `PROPOSED → VERIFIED →
  REPORTED` grounded in evidence records. A claim enters the report only if
  it is `VERIFIED` or traces to an eligible source note.

The dossier audit checks the links, not the science: every evidence-bearing
claim must point at evidence records or run manifests that exist, hash-check
against disk, and carry no unresolved gap markers.

## Repository layout

```text
.github/workflows/check.yml    # CI: tools/check_all.py on every push and PR
.opencode/
├── agents/                    # specialist subagents (researcher, summarizer, writer, reviewer, experimenter)
├── commands/                  # lifecycle entry points (/new-study, /gather, /draft, /review)
└── skills/
    └── conduct-cs-ai-research/   # git submodule: research discipline playbooks + gates
studies/                       # one directory per study (see above)
shared/
├── templates/                 # brief, note, note-codebase, comparison, study.yaml
│   ├── latex/                 # NeurIPS 2025 preprint style (vendored neurips_2025.sty)
│   └── slides/                # beamer deck skeleton
├── library.bib                # master bibliography merged from finished studies
├── glossary.md                # cross-study terms
└── knowledge/                 # distilled cross-study concept pages
tools/
├── new_study.py               # study scaffolder
├── build_report.sh            # latexmk/tectonic wrapper for report/
├── build_slides.sh            # latexmk/tectonic wrapper for slides/
├── lint_report.py             # prose/citation/marker linter (report + slides)
├── check_all.py               # repo-wide gate: lint, manifest, dossier audit, PDF hygiene, drift check, tests
├── cleanup_study.py           # slim a signed-off study down to its knowledge core
├── pin_repos.py               # pin local codebase checkouts into sources/repos.yaml
├── verify_pins.py             # confirm pinned checkouts still hold their recorded commits
└── research/                  # vendored dossier scripts (research_state, capture_run, audit) + research.sh
AGENTS.md                      # the operating manual the agents follow; read it before changing contracts
tests/                         # unit tests for the tools, run in CI
```

## Build a report

```bash
tools/build_report.sh studies/2026-08_scaled-dot-product-attention
tools/build_slides.sh studies/2026-08_scaled-dot-product-attention
```

Reports use the official NeurIPS 2025 style in `preprint` mode
(`report/neurips/neurips_2025.sty`, vendored from
<https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip>). Slides are a
beamer deck that cites `report/refs.bib`; build the report first so the bib
exists.

## Lint and audit

```bash
python3 tools/check_all.py            # everything below, plus hygiene, drift, and tests
python3 tools/lint_report.py studies/<slug>
python3 tools/research/audit_research.py --root studies/<slug>
```

The linter checks em-dashes, untied citations (`X \cite` without `~`),
unresolved `[... NEEDED]` markers, and British spellings. The auditor checks
claim/evidence/run traceability in the dossier. `check_all.py` is the
pre-review gate: it lints every study, validates every `study.yaml` manifest
(status, depth, track, and a track-consistent `experiments_approved` gate),
audits every `.research/` dossier (honoring the human-only `audit_waiver`
field), fails on git-tracked PDF binaries, fails if the vendored
`tools/research/*.py` drift from the skill submodule, and runs the unit
tests. CI runs it on every push and pull request.

Source PDFs are never committed. The registry's `pdf` field holds a remote
URL and the local evidence is a pdftotext snapshot under `sources/docs/`, so
the evidence base survives URL rot without binaries in git.

## Completed studies in this repo

Two finished studies show the workflow end to end:

- [`studies/2026-08_scaled-dot-product-attention`](studies/2026-08_scaled-dot-product-attention):
  a `concept` study answering why attention scores are divided by the square
  root of the head dimension.
- [`studies/2026-08_coding-agents-harnesses-and-open-models`](studies/2026-08_coding-agents-harnesses-and-open-models):
  a `review` study tracing the harness architecture and open-source model
  support of Claude Code, Codex, and OpenCode from pinned checkouts and
  official docs, without running experiments.

Both are cleaned to their knowledge core. The full evidence chain (source
snapshots, dossier, review drafts) is preserved in git history.

## Adapting this repo

To run your own studies: fork or clone the repo, delete the contents of
`studies/` if you want a clean slate, and keep `shared/`, `tools/`, and
`.opencode/`. The OpenCode-specific surface is small (`agents/`,
`commands/`, and `opencode.json`); the contracts, templates, gates, and
scripts are plain files and Python. The research discipline itself lives in
the `conduct-cs-ai-research` submodule, which follows the
[Agent Skills specification](https://agentskills.io/specification) and loads
in any compatible runtime.

## Update the research skill

```bash
git submodule update --remote .opencode/skills/conduct-cs-ai-research
cp .opencode/skills/conduct-cs-ai-research/scripts/{research_state,capture_run,audit_research}.py tools/research/
```

The drift check in `check_all.py` requires `tools/research/*.py` to match the
submodule's `scripts/*.py` byte-for-byte, so re-vendor the copies after every
bump.

Upstream: <https://github.com/honghuy127/cs-ai-research-skills> (MIT).
