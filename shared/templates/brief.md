# Brief: <topic>

<!--
Human-owned. Fill every field before work starts. Agents refuse to act on a
templated brief. Delete bracketed guidance once filled.
-->

## Mode and dimensions

- Mode: `delegated` <!-- interactive (you learn) | delegated (agents investigate) | paper-reading (one paper to a deck) -->
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

<!-- Keep only the subsection matching this study's mode; delete the others. -->

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

### Paper-reading: paper and talk contract

- Target paper: [exact title, authors, year, canonical URL or DOI, and version]
- Reading depth: [main paper, appendices, supplementary material, companion code]
- Context allowance: [target paper only, or named related sources the agent may gather]
- Audience and assumed prerequisites: [who will consume the deck and what they know]
- Talk format and time allotment: [live, recorded, self-paced; minutes]
- Required coverage: [problem, notation, method, derivation, experiments, limitations, or other]
- Figure reuse policy: [redraw with attribution, quote under permitted use, or no reuse]
- Distribution and confidentiality: [private, internal, public; any restrictions]
- Exact-version rule: [what version changes require a new paper gate]

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

Paper-reading:

- [ ] Exactly one approved `role: target-paper` source has verified metadata and a full-text snapshot
- [ ] `notes/_paper-analysis.md` covers the declared reading depth with locators for every substantive claim and number
- [ ] `slides/deck-plan.md` maps every slide to analysis claims and source locators
- [ ] The deck bibliography is generated, the deck builds and lints clean, and every rendered slide is visually inspected
- [ ] Independent review findings resolved or explicitly accepted
