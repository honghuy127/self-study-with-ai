# self-study-with-ai

A collaboration between a human and AI agents for structured self-study. You
pose a topic, agents gather and analyze the literature, optionally run
experiments, and draft a technical report in LaTeX (built to PDF). You review
and approve at defined gates. Everything is plain files, so oversight equals
reading git diffs.

## Requirements

- Python 3.10+ (dossier scripts are standard-library only)
- `latexmk` (or `tectonic`) for report builds
- git with submodule support

Clone with submodules:

```bash
git clone --recurse-submodules <this-repo-url>
```

## Start a study

```bash
python3 tools/new_study.py transformer-length-extrapolation --title "How do transformers extrapolate to longer sequences?"
```

This scaffolds `studies/YYYY-MM_transformer-length-extrapolation/` from the
templates in `shared/templates/`. Fill in `brief.md`, then run the lifecycle
through the OpenCode commands:

| Command | What it does |
|---|---|
| `/new-study <topic>` | Wraps `new_study.py`, scaffolds the study |
| `/gather <study-dir>` | Researcher agent collects sources into `sources/` |
| `/draft <study-dir>` | Idempotent; summarizes unnoted sources, then (after you approve the notes) the writer drafts `report/main.tex` |
| `/review <study-dir>` | Reviewer agent audits claims, style, and traceability |

Each stage ends by updating `study.yaml`; the next stage refuses to proceed
until you flip the gate field by hand. One branch per study; the pull request
is your review surface.

## Repository layout

```
.opencode/
├── agents/                    # specialist subagents (researcher, summarizer, writer, reviewer, experimenter)
├── commands/                  # lifecycle entry points (/new-study, /gather, /draft, /review)
└── skills/
    └── conduct-cs-ai-research/   # git submodule: research discipline playbooks + gates
studies/                       # one directory per study (see below)
shared/
├── templates/                 # brief, note, study.yaml, LaTeX report skeleton
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
├── check_all.py               # repo-wide: lint every study, audit dossiers, check vendored-script drift, run tests
└── research/                  # vendored dossier scripts (research_state, capture_run, audit) + research.sh
```

A study directory:

```
studies/<YYYY-MM_slug>/
├── brief.md                   # your input: question, scope, depth, deadline
├── study.yaml                 # manifest: workflow status + human gates
├── sources/registry.yaml      # every gathered source with bibtex key + trust tier
├── sources/pdfs/
├── notes/                     # one structured note per source + _synthesis.md
├── experiments/               # runnable code with pinned deps (optional)
├── report/main.tex + refs.bib # NeurIPS preprint report, tools/build_report.sh
├── slides/main.tex            # beamer deck, tools/build_slides.sh; cites report/refs.bib
├── reviews/                   # per-round review notes
└── .research/                 # epistemic dossier (claims, evidence, run ledger)
```

## The two state layers

- **Workflow state** (`study.yaml.status`): where the study is in the pipeline
  (`proposed`, `gathering`, `summarizing`, `experimenting`, `drafting`,
  `review`, `done`). Human-gated.
- **Epistemic state** (`.research/claims.jsonl`): the truth state of each
  claim, `PROPOSED → ... → EXECUTED → ANALYZED → VERIFIED → REPORTED`, enforced
  by the `conduct-cs-ai-research` skill. The writer may place a claim in the
  report only if it is `VERIFIED` or traces to an eligible external source.

Depth is set per study in `study.yaml`: `briefing` (notes + short synthesis,
light gates) or `full` (novelty checks, frozen experiment plans, run manifests,
audit-clean report).

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
python3 tools/check_all.py            # everything below, plus tests and drift check
python3 tools/lint_report.py studies/<slug>/report/main.tex
python3 tools/research/audit_research.py --root studies/<slug>
```

The linter checks em-dashes, untied citations (`X \cite` without `~`),
unresolved `[... NEEDED]` markers, and British spellings. The auditor checks
claim/evidence/run traceability in the dossier. `check_all.py` is the
pre-review gate: it lints every study, audits every `.research/` dossier,
fails if the vendored `tools/research/*.py` drift from the skill submodule,
and runs the unit tests.

Downloaded source PDFs are committed under each study's `sources/pdfs/` so the
evidence base survives even if a URL rots.

## Update the research skill

```bash
git submodule update --remote .opencode/skills/conduct-cs-ai-research
```

Upstream: <https://github.com/honghuy127/cs-ai-research-skills> (MIT).
