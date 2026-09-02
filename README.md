# Structured Self-Study with AI Agents

[![check](https://github.com/honghuy127/self-study-with-ai/actions/workflows/check.yml/badge.svg)](https://github.com/honghuy127/self-study-with-ai/actions/workflows/check.yml)

A working system for studying technical topics in depth with AI agents, where
the point is that you end up knowing something and can prove where every
claim came from.

Three study modes sit on one evidence kernel. In **delegated mode** you pose a
question and specialist agents gather sources, write anchored notes, and draft
a technical report. In **interactive mode** the agent tutors you through
diagnosis and practice, and a separate agent that never saw the tutoring
administers an unaided assessment, because a report someone else wrote is not
the same as understanding. In **paper-reading mode** agents analyze one exact
paper and turn the approved analysis into a presentation. Around all three sit
two things that make the effort compound: a queryable knowledge base that
studies distill into, and a retrieval schedule that brings it back before you
forget it.

The goal is not to automate research but to make AI-assisted study auditable
and cumulative. A chat transcript rots: months later you cannot tell which
statements came from verified sources and which came from a plausible-sounding
model, and you have forgotten the answer anyway. This workflow forces the
first distinction into the open, with `[CITATION NEEDED]` markers instead of
confident prose, local source snapshots, and explicit claim truth states. And
it answers the second by treating what you learned as an asset with a review
schedule rather than a finished document.

Everything is plain files, so oversight equals reading git diffs.

## The loop

```text
question --> /ask ------------------> inbox note ---> distill --> knowledge unit
         \                                                     /        |
          --> /new-study --> study --> gates --> deliverable --/         v
                                                                    /review-due
                                                                  (retrieval,
                                                                   rescheduled)
```

A small question costs one command and produces one anchored note. A real
question becomes a study with human gates. Both end in the same place: a
knowledge unit that gets asked back to you on a schedule. Nothing is finished
when the PDF builds.

## How a study flows

Every study declares a mode at scaffold time; there is no default.

<!-- BEGIN GENERATED: pipelines -->
```text
interactive:   scoped --> diagnosing --> learning --> practicing --> assessing --> retained
delegated:     proposed --> gathering --> summarizing --> experimenting --> drafting --> review --> done
paper-reading: proposed --> gathering --> analyzing --> presenting --> review --> done
```
<!-- END GENERATED: pipelines -->

<!-- BEGIN GENERATED: modes -->
| Mode | What it does | Gates, in order |
|---|---|---|
| `interactive` | the agent tutors you to an unaided mastery demonstration | `scope_approved`, `evidence_approved`, `experiments_approved`, `mastery_approved` |
| `delegated` | agents investigate and return a traceable report | `sources_approved`, `notes_approved`, `experiments_approved`, `draft_approved`, `review_signed_off` |
| `paper-reading` | agents analyze one approved paper into a comprehensive deck | `paper_approved`, `analysis_approved`, `deck_approved`, `review_signed_off` |
<!-- END GENERATED: modes -->

Each arrow is a human gate: the agent stops, you read what it produced, and
you approve (`python3 tools/study.py approve <study-id> <gate> --note "..."`)
before the next stage runs. In interactive mode the primary artifact is your
own recorded performance, not a report.

Four dimensions are independent of the mode:

<!-- BEGIN GENERATED: dimensions -->
| Dimension | Values | Controls |
|---|---|---|
| Intent | `understand`, `solve`, `build`, `compare`, `decide`, `refresh`, `survey` | Question and synthesis shape; enforced by lint_report.py where it promises a section |
| Assurance | `quick`, `grounded`, `audited` | Verification depth; `audited` adds a claims dossier and independent review |
| Methodology | `source-only`, `static-code`, `experimental`, `mixed` | What counts as evidence; only experimental and mixed enter `experimenting` |
| Deliverables | `learning-note`, `implementation`, `decision-brief`, `report`, `slides`, `none` | Outputs to scaffold |
<!-- END GENERATED: dimensions -->

Intent is not decoration. It seeds the brief's questions at scaffold time and
binds the finished deliverable, which `tools/lint_report.py` checks once a
study reaches `review`:

<!-- BEGIN GENERATED: intents -->
| Intent | Shape of the answer | Deliverable must contain |
|---|---|---|
| `understand` | explain a mechanism from first principles; the answer is a derivation or causal account | no structural requirement |
| `solve` | resolve one concrete problem; the answer is an approach with its failure conditions | approach or solution |
| `build` | produce something runnable; the answer is an implementation plus what it was verified against | implementation |
| `compare` | place systems side by side on fixed dimensions; the answer is a matrix, not a narrative | comparison section, comparison table |
| `decide` | reach a defensible decision; the answer names the option taken and what would reverse it | recommendation |
| `refresh` | re-establish something you once knew; the answer is a delta against prior understanding | no structural requirement |
| `survey` | map a literature or landscape; the answer is organized coverage with its limits stated | coverage or scope |
<!-- END GENERATED: intents -->

Methodologies that do not run experiments skip the experiment stage entirely;
their `experiments_approved` gate is `n_a` rather than a checkbox nobody can
honestly flip. Assurance sets how much verification the study pays for:
`quick` needs registry entries with canonical metadata, `grounded` adds local
snapshots and anchored notes, and `audited` adds a claims dossier plus
independent review.

## Getting started

### Requirements

- Python 3.10 or newer, and `pip install -r requirements.txt` (PyYAML)
- git with submodule support
- `latexmk` or `tectonic`, only if you build reports or slides
- `pdftotext` (poppler), only for paper snapshots during gathering
- An agent harness: [OpenCode](https://opencode.ai) or
  [Claude Code](https://claude.com/claude-code). Both are generated from the
  same source, see [Runtimes](#runtimes).

Every command below is written `python3`. On Windows use `python` or `py -3`;
nothing else differs, and there are no shell scripts left in the repo.

```bash
git clone --recurse-submodules https://github.com/honghuy127/self-study-with-ai.git
cd self-study-with-ai
pip install -r requirements.txt
python3 tools/check_all.py     # should pass on a fresh clone
```

### Three entry points, by size of question

```bash
# Small: one question, verified sources, no study directory
python3 tools/inbox.py new "Why does RoPE need a base?"     # or /ask "..."

# Medium to large: a gated study
python3 tools/new_study.py transformer-length-extrapolation \
  --title "How do transformers extrapolate to longer sequences?" \
  --mode delegated --intent survey

python3 tools/new_study.py attention-scaling \
  --title "Derive the sqrt(d_k) attention scale" --mode interactive

python3 tools/new_study.py attention-is-all-you-need-reading \
  --title "Attention Is All You Need: paper reading" --mode paper-reading

# Recurring: what needs rehearsing today
python3 tools/review.py due
```

Scaffolding creates `studies/YYYY-MM_<slug>/`. Fill in `brief.md` (purpose,
questions, scope, budgets, stop rules, and the mode-specific contract). The
brief is human-owned: agents refuse to act on a blank template.

## Commands

Agent-driven, as slash commands in either harness:

| Command | What it does |
|---|---|
| `/ask "<question>"` | One question, three to five verified sources, into `shared/inbox/`. No study directory |
| `/new-study <topic>` | Scaffolds a study; `--mode` required |
| `/gather <study-dir>` | The researcher collects sources, verifies metadata, and snapshots papers and pages |
| `/draft <study-dir>` | Delegated: summarizes unnoted sources, runs experiments where the methodology calls for them, then drafts `report/main.tex`. Stops at each gate |
| `/read-paper <study-dir>` | Paper-reading: verifies one target, produces the anchored analysis, then builds and visually verifies the deck |
| `/learn <study-dir>` | Interactive: baseline, concept path, tutoring, practice. Stops before assessment |
| `/practice <study-dir> [item]` | Administers one practice item with hints and solution withheld |
| `/assess <study-dir>` | Dispatches the independent assessor for the unaided mastery task |
| `/review <study-dir>` | The reviewer audits claims, citations, and traceability |
| `/review-due` | Today's retrieval practice across every knowledge unit and mastery record |

Human-driven, via the CLIs:

| Command | What it does |
|---|---|
| `python3 tools/study.py status <id>` | Mode, state, gates, artifacts, intent contract, allowed transitions, next action |
| `python3 tools/study.py status-set <id> <status> --note "..."` | Moves along the transition graph; refuses invalid jumps and ungated entries |
| `python3 tools/study.py approve <id> <gate> --note "..."` | Records a human gate decision in `events.jsonl`; `--verdict`, `--evidence`, `--reopen` |
| `python3 tools/study.py practice <id> --item <name>` | Prints the problem, withholds hints and solution, logs the attempt |
| `python3 tools/study.py assess <id>` | Opens a timestamped attempt record; refuses if the baseline is still templated |
| `python3 tools/study.py revisit <id>` | Lists due delayed-review items for an interactive study |
| `python3 tools/study.py reopen <id>` | Read-only report of what a finished study needs to reopen |
| `python3 tools/knowledge.py search "<question>"` | What the repo already knows. Run this before gathering |
| `python3 tools/knowledge.py new\|index\|link\|show\|supersede` | Create, index, validate, read, retire knowledge units |
| `python3 tools/review.py due\|run\|record\|schedule\|log` | The retrieval loop |
| `python3 tools/inbox.py new\|list\|promote\|distill` | The cheap path, and its two graduations |
| `python3 tools/inbox.py queue add\|list\|start` | Reading queue, straight into a paper-reading study |

## Who does what

Eight specialist roles, each confined to its own write zone:

| Agent | Stage | Role | Writes |
|---|---|---|---|
| researcher | gathering | Searches scholarly and official sources, verifies each against a canonical page or DOI, snapshots papers and pages, pins local codebases | `sources/`, `.research/evidence.jsonl` |
| summarizer | summarizing | One structured note per source, every claim anchored to a page, section, or code line. No web access | `notes/`, registry status fields |
| paper analyst | analyzing | Paper-reading only: one target paper into a claim-evidence map and teaching blueprint. No web access | `notes/_paper-analysis.md` |
| experimenter | experimenting | Experimental methodologies only: pinned dependencies, isolated runs, per-run manifests; smoke tests never count as evidence | `experiments/`, `.research/claims.jsonl` |
| writer | drafting / presenting | Turns approved notes or the approved analysis into a report or deck. No web access | `report/`, `slides/` |
| reviewer | review | Adversarial pass: claim traceability, citation honesty, numbers, style | `reviews/` |
| tutor | diagnosing / learning / practicing | Interactive: baseline, concept path, journalled tutoring, practice items | `learning/` minus the mastery record, `outputs/` |
| assessor | assessing | Interactive: administers the unaided mastery task in its own context, without the tutoring history | `learning/mastery.md`, `learning/attempts/` |

The permission boundaries are the design, not documentation of it. The writer
cannot browse, so nothing from memory can leak into a deliverable. The tutor
cannot write the mastery record and the assessor cannot read the journal or
the practice solutions, so the assessment measures the learner rather than the
conversation. `tests/test_agents.py` fails if either boundary is widened.

## What a study looks like

```text
studies/<YYYY-MM_slug>/
├── brief.md                   # your input: purpose, questions, scope, budgets, stop rules
├── study.yaml                 # manifest: schema_version, mode, dimensions, status, human gates
├── events.jsonl               # append-only log of transitions and gate decisions
├── sources/registry.yaml      # every gathered source with bibtex key + trust tier
├── sources/repos.yaml         # pinned local codebase checkouts (codebase studies)
├── sources/docs/              # pdftotext and page snapshots; PDF binaries are never committed
├── notes/                     # source notes plus synthesis or paper analysis
├── learning/                  # interactive: baseline, map, journal, practice, mastery, attempts
├── outputs/                   # interactive: distilled learning note
├── experiments/               # runnable code with pinned deps (experimental methodology only)
├── report/main.tex + refs.bib # technical report, built with tools/build.py
├── slides/deck-plan.md        # talk contract, storyboard, evidence map, visual QA record
├── slides/main.tex + refs.bib # beamer deck and deliverable-local generated bibliography
├── reviews/                   # per-round review notes
└── .research/                 # epistemic dossier (claims, evidence, run ledger), audited assurance
```

## The two state layers

- **Workflow state** (`study.yaml.status`): where the study sits in its
  pipeline, human-gated, moved only by `tools/study.py`.
- **Epistemic state** (`.research/claims.jsonl`): the truth state of each
  claim. Claims from experimental methodologies move `PROPOSED → ... →
  EXECUTED → ANALYZED → VERIFIED → REPORTED`; source-grounded claims move
  `PROPOSED → VERIFIED → REPORTED`. A claim enters a report or deck only if it
  is `VERIFIED` or traces to an eligible source note.

The dossier audit checks the links, not the science: every evidence-bearing
claim must point at evidence records or run manifests that exist, hash-check
against disk, and carry no unresolved gap markers.

## The knowledge base

`shared/knowledge/` holds one page per durable idea, with structured
frontmatter (id, question, prerequisites, source ids, misconceptions, review
state). It is the reason a fifth study is cheaper than the first.

```bash
python3 tools/knowledge.py search "attention scaling variance"   # before gathering
python3 tools/knowledge.py new attention.scale --question "Why 1/sqrt(d_k)?"
python3 tools/knowledge.py index      # rebuild INDEX.md and index.json
python3 tools/knowledge.py link       # dangling prerequisites, duplicate ids, broken [[links]]
python3 tools/knowledge.py supersede attention.scale attention.scale-v2
```

`check_all.py` fails on a stale index, a duplicate id, or a link that resolves
to nothing, so the base cannot quietly rot into a folder of orphans.

## Retrieval, so the study survives

```bash
python3 tools/review.py due                          # what needs rehearsing today
python3 tools/review.py run attention.scale          # asks the question, withholds the answer
python3 tools/review.py record attention.scale --result recalled
python3 tools/review.py schedule attention.scale --in 7d
```

Scheduling is a fixed expanding ladder (1, 7, 30, 90, 180, 365 days): recalled
moves out one rung, partial repeats the rung, missed drops to the first. Every
outcome is appended to `shared/review-log.jsonl`, so the record outlives any
change to the algorithm. `review.py due` also surfaces delayed reviews
scheduled inside interactive mastery records, so one command answers "what is
due today" across the whole repo.

## Finishing a study

When a study reaches `done` and you sign off, `tools/cleanup_study.py` slims
it to its knowledge core (brief, notes, report sources, registry) and packs
everything it removes:

```bash
python3 tools/cleanup_study.py studies/<slug> --dry-run
python3 tools/cleanup_study.py studies/<slug>
```

Nothing is deleted until it is inside a verified archive. Cleanup writes
`archive/<study-id>.zip`, reopens it, confirms every packed file is present at
its recorded size, and only then removes the originals. `archive.yaml` records
the archive path, its sha256, its file count, and a retrieval command that
works in any checkout, and `check_all.py` fails if that archive later goes
missing or stops matching its checksum.

This replaced a git-history promise that could not be kept: `studies/` is
gitignored by default, so the old `git show <commit>:<path>` retrieval
commands resolved to nothing whenever the evidence had never been committed.
`--no-archive` still exists and still deletes, but requires `--force`.

## Repository layout

```text
.github/workflows/check.yml    # CI: check_all.py + ruff, on Linux, Windows, and macOS
runtime/                       # single source of truth for agents and commands
├── agents/                    # eight specialist roles with neutral write zones
└── commands/                  # lifecycle entry points
.opencode/                     # generated: OpenCode agents and commands
└── skills/conduct-cs-ai-research/   # git submodule: research playbooks and gates
.claude/                       # generated: Claude Code agents, commands, and the zone-guard hook
examples/                      # one finished study, tracked, so CI validates something real
studies/                       # your studies (gitignored)
shared/
├── templates/                 # brief, notes, study.yaml, learning-*, practice-item, inbox-note, knowledge-unit
│   ├── latex/                 # report templates: neurips/ (vendored style) and plain/
│   └── slides/                # beamer skeleton plus design principles
├── knowledge/                 # your knowledge units, INDEX.md, index.json (gitignored)
├── inbox/                     # your question notes (gitignored)
├── review-log.jsonl           # your retrieval history (gitignored)
├── library.bib, glossary.md   # merged bibliography and cross-study terms (gitignored)
tools/
├── contracts.py               # single source of truth: modes, states, gates, transitions, intents
├── study.py                   # lifecycle CLI: status, status-set, approve, practice, assess, revisit, reopen
├── new_study.py               # scaffolder (--mode required)
├── knowledge.py               # knowledge base: new, index, search, link, show, supersede
├── review.py                  # retrieval: due, run, record, schedule, log
├── inbox.py                   # cheap path and reading queue
├── build.py                   # latexmk/tectonic wrapper for report/ and slides/
├── gen_bib.py                 # generate refs.bib from registry bibtex blocks
├── lint_report.py             # prose, citation, and intent-contract linter
├── check_all.py               # repo-wide gate (see below)
├── cleanup_study.py           # pack and slim a signed-off study; writes archive.yaml
├── pin_repos.py, verify_pins.py   # pin and verify local codebase checkouts
├── docsgen.py                 # render the contract tables in README.md and AGENTS.md
├── sync_runtimes.py           # generate .opencode/ and .claude/ from runtime/
├── sync_skill.py              # refresh the vendored dossier scripts from the skill
├── zone_guard.py              # Claude Code PreToolUse hook: refuses edits the CLIs own
├── research.py                # run a dossier script against a study
└── research/                  # vendored dossier scripts + UPSTREAM.md pin
AGENTS.md                      # the operating manual the agents follow
CLAUDE.md                      # Claude Code specifics; read AGENTS.md first
tests/                         # unit and end-to-end lifecycle tests, run in CI
```

## Build a report or deck

```bash
python3 tools/gen_bib.py studies/<slug>
python3 tools/build.py report studies/<slug>
python3 tools/build.py slides studies/<slug>
python3 tools/build.py both   studies/<slug>
```

Reports use the style chosen at scaffold time via `report_style` in
`study.yaml`: `neurips` (the official NeurIPS 2025 style in preprint mode) or
`plain`. Decks are Beamer through metropolis; the density limits, title case,
evidence map, and visual QA rules live in
[`shared/templates/slides/README.md`](shared/templates/slides/README.md).

## Lint and audit

```bash
python3 tools/check_all.py                       # the whole gate
python3 tools/lint_report.py studies/<slug>
python3 tools/research.py studies/<slug> audit_research.py
```

`check_all.py` is the pre-review gate. It lints every study in `studies/` and
`examples/`, validates every manifest against `tools/contracts.py`, checks
that every artifact path resolves or is retrievable from its archive, checks
briefs for leftover template guidance, validates knowledge-unit frontmatter
and the knowledge base's index and links, audits every `.research/` dossier,
fails on git-tracked PDF binaries, checks that the generated doc tables and
generated runtimes are current, checks the vendored dossier scripts and their
upstream pin, and runs the unit tests. Groups with nothing to check report
`NOT_ASSESSED` instead of collapsing into `PASS`.

Source PDFs are never committed. The registry's `pdf` field holds a remote URL
and the local evidence is a pdftotext snapshot under `sources/docs/`, so the
evidence base survives URL rot without binaries in git.

## Runtimes

The agents and commands are defined once, in [`runtime/`](runtime/), and
rendered into both harnesses by `python3 tools/sync_runtimes.py`. Never edit
the generated directories; `check_all.py` fails when they drift.

The two harnesses enforce write zones differently, and the difference is real:

- **OpenCode** takes each zone as per-glob edit permissions, enforced by the
  harness. A summarizer physically cannot write into `report/`.
- **Claude Code** has no per-glob edit permission, so each generated agent
  carries its zone in prose, and the repo-wide invariants are enforced by the
  `PreToolUse` hook in `tools/zone_guard.py`, which refuses edits to
  `study.yaml`, `events.jsonl`, `archive.yaml`, and any `.pdf` under a study.

See [CLAUDE.md](CLAUDE.md) for the Claude Code specifics.

## Your content stays private

The repository tracks the workflow machinery: templates, tools, agents,
skills, docs, and one example study. Your own studies, questions, and
accumulated knowledge are your data, not machinery, and are gitignored by
default: `studies/`, `archive/`, `shared/knowledge/`, `shared/inbox/`,
`shared/queue.yaml`, `shared/review-log.jsonl`, `shared/glossary.md`,
`shared/library.bib`. A fresh clone contains the full machinery plus the
example, and nothing about your reading or learning record, unless you opt in
by un-ignoring those paths.

## The example study

[`examples/2026-08_scaled-dot-product-attention/`](examples/) is a finished
delegated study, tracked in git: grounded, source-only, `understand` intent,
signed off and deliberately not cleaned so the whole shape stays visible. CI
validates it exactly as it validates your own studies, which is what keeps the
per-study check groups from silently reporting `NOT_ASSESSED` everywhere. Read
[`examples/README.md`](examples/README.md) for what it deliberately does not
ship.

## Adapting this repo

Fork or clone, then scaffold your first study with `new_study.py`. The
harness-specific surface is generated from `runtime/`; the contracts,
templates, gates, and scripts are plain files and Python. The research
discipline itself lives in the `conduct-cs-ai-research` submodule, which
follows the [Agent Skills specification](https://agentskills.io/specification)
and loads in any compatible runtime.

## Update the research skill

```bash
python3 tools/sync_skill.py --update    # pull the submodule, re-vendor, record the pin
python3 tools/sync_skill.py --check     # report whether the pin is current
```

The dossier scripts are vendored under `tools/research/` so the workflow keeps
working in a checkout whose submodule was never initialized;
`tools/research/UPSTREAM.md` records which commit they came from.

Upstream: <https://github.com/honghuy127/cs-ai-research-skills> (MIT).

## License

MIT, see [LICENSE](LICENSE).
