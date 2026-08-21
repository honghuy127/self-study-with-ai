# Brief: <topic>

<!--
Human-owned. Fill every field before work starts. Agents refuse to act on a
templated brief. Delete bracketed guidance once filled.
-->

## Mode and dimensions

- Mode: `delegated` <!-- interactive (you learn it) | delegated (agents investigate and report); set by new_study.py --mode -->
- Intent: `survey` <!-- understand | solve | build | compare | decide | refresh | survey -->
- Assurance: `grounded` <!-- quick | grounded | audited: how much verification this study promises -->
- Methodology: `source-only` <!-- source-only | static-code | experimental | mixed -->
- Deliverables: `report` <!-- learning-note | implementation | decision-brief | report | slides | none -->

## Purpose

[Why this study matters, in one or two sentences]

## Questions

- Primary question: [one sentence, answerable]
- Secondary questions: [optional, one per line]

## Scope

- In scope: [topics, methods, time range]
- Out of scope: [explicit exclusions]
- Audience: [your future self, a colleague, ...]

## Budget and stop rules

- Time budget: [minutes, sessions, or "none"]
- Source budget: [max sources to open before the next human decision point]
- Compute or spend budget: [n_a or a cap]
- Stop rule: [saturation or kill criterion, or "none"]

## Human decision points

[What agents may do between checkpoints, and what always needs fresh
approval: scope changes, budget overruns, new systems, external actions]

## Prior understanding

- What you already know: [agents will not re-teach this]
- Repos, notes, glossary pages to reuse: [shared/knowledge/...]

## Mode-specific contract

<!-- Keep only the subsection matching this study's mode; delete the other. -->

### Interactive: learning contract

- Target capability: [what the learner can do unaided at the end, stated as an observable performance]
- Baseline task: [the unaided attempt that opens the study]
- Mastery task: [the unaided assessment, administered at help level none]
- Mastery criterion: [what counts as demonstrated; fixed before assessment]
- Transfer task: [a changed-conditions problem]
- Review schedule: [delayed retrieval, e.g. 7 days after mastery]

### Delegated: research contract

- Report audience: [who reads the deliverable]
- Coverage dimensions: [systems, questions, or comparison axes the deliverable must cover]
- Required comparisons: [explicit matrix dimensions, or "none"]
- Source cutoff: [date or version bound for evidence]
- Independent review: [required at audited assurance; who reviews]
- Uncertainty to keep visible: [gaps that must survive into the deliverable]

## Definition of done

<!-- Keep only the checklist matching this study's mode. -->

Delegated:

- [ ] Every declared deliverable builds clean and passes lint
- [ ] Every material claim traces to an eligible note, evidence record, or run
- [ ] Independent review findings resolved or explicitly accepted
- [ ] Glossary and library.bib merged on completion

Interactive:

- [ ] Baseline attempt recorded before any teaching
- [ ] Mastery task completed unaided at help level none and the criterion met
- [ ] Transfer task attempted and recorded
- [ ] Learning note distilled after mastery
- [ ] Delayed review scheduled or explicitly declined
