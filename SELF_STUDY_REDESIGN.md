# Dual-Mode Redesign for Agent-Assisted Self-Study

Status: strategy proposal

Assessment date: 2026-08-21

Scope: repository workflow, agent design, state model, artifacts, validation, interactive learning outcomes, and delegated research delivery

## Executive decision

The repository should support **two first-class study modes over one shared evidence kernel**:

1. **Interactive mastery mode:** the agent tutors the user through diagnosis, explanation, practice, transfer, assessment, and later review. Success means the user can perform the target capability with limited or no assistance.
2. **Delegated deep-study mode:** the user delegates a difficult, time-consuming investigation to agents and later consumes a comprehensive, traceable report. Success means the agents answer the approved research questions at the requested assurance level, expose uncertainty, and produce an independently reviewed deliverable.

“Non-interactive” does not mean unsupervised or ungoverned. In delegated mode, the human still owns scope, consequential resource decisions, evidence acceptance, and final sign-off. The agents may work for a long interval between those checkpoints without requiring the user to participate in the learning process.

The modes have different primary loops:

```text
interactive: diagnose -> plan -> encounter -> explain -> practice -> assess -> distill -> revisit

delegated:   scope -> decompose -> gather -> verify -> synthesize -> review -> report -> archive
```

The current repository is a strong early implementation of delegated deep study. Its mistake is not producing reports. Its mistake is treating that production workflow as the only shape of self-study. The redesign should preserve and strengthen it while adding an equally deliberate interactive mode.

## What was inspected

This assessment is based on:

- The operating contract in `AGENTS.md` and the public workflow in `README.md`.
- All five role definitions under `.opencode/agents/` and all four lifecycle commands under `.opencode/commands/`.
- The study, brief, note, comparison, LaTeX, and slide templates under `shared/templates/`.
- The scaffold, validation, cleanup, report-lint, repository-pinning, and research-dossier tools under `tools/`.
- The unit tests under `tests/`.
- Both completed studies, including their manifests, briefs, registries, notes, syntheses, reports, slides, and locally available builds.
- Recent git history, to distinguish intended contracts from repair and migration work.
- A clean run of `python3 tools/check_all.py` on 2026-08-21.

The current automated check reports every group as `PASS`. It also says `audit: no .research dossiers found; skipping`, which is important to the diagnosis below.

## What should be preserved

Several current choices are strong and should survive the redesign:

1. **No fabrication.** Unknowns remain explicit instead of becoming plausible prose.
2. **Human authority.** Agents do not approve scope, risk, final claims, or external actions.
3. **Source discipline.** Canonical metadata, source tiers, snapshots, pinned repositories, and anchored notes make agent output inspectable.
4. **Truth-state separation.** Proposed, executed, analyzed, verified, and reported are meaningfully different states.
5. **Untrusted-input handling.** Papers, pages, repositories, and packages do not get to instruct or silently execute themselves.
6. **Plain-file ownership.** The learner can inspect, version, export, and repair the system without a proprietary database.
7. **Synthesis before presentation.** Cross-source reasoning should precede a report or deck.

These are differentiators. The redesign should reduce ceremony without weakening them.

## Diagnosis

### 1. The success criterion covers delegated research, not interactive mastery

The brief template asks for a question, scope, constraints, and deliverable. Its definition of done checks whether a report builds, claims trace to evidence, and shared files are updated. It does not ask what the learner should be able to do unaided.

Across the workflow and templates there is no first-class representation of:

- a baseline attempt or diagnostic;
- learning objectives stated as observable performances;
- learner-generated explanations;
- misconceptions and confidence calibration;
- worked examples followed by independent problems;
- transfer tasks;
- mastery checks performed without agent help;
- delayed retrieval or a review schedule.

This is a valid success model for delegated deep study: the user asked the agents to investigate and return a trustworthy report. It is not a valid success model for interactive mastery, where the user intends to learn the capability personally. The manifest does not distinguish those intentions, so an artifact-complete study can be mistaken for evidence that its owner learned the material.

This is not a cosmetic omission. Repeated retrieval has been shown to improve delayed retention relative to repeated study, and learners can misjudge which method is helping them ([Karpicke and Roediger, 2008](https://doi.org/10.1126/science.1152408)). Self-generated explanations are also associated with better principle-based problem solving than example dependence ([Chi et al., 1989](https://doi.org/10.1207/s15516709cog1302_1)).

### 2. One fixed pipeline cannot represent both modes

The current tracks vary the evidence source, but all remain oriented toward research production:

```text
brief -> gather -> summarize -> optional experiment -> report -> review -> done
```

A quick concept clarification, preparation for an implementation task, a delegated technology comparison, and a publication-grade literature review do not need the same user participation, artifacts, or gates.

The two completed studies illustrate the spread:

| Study | Sources or source notes | Report | Slides |
|---|---:|---:|---:|
| Scaled dot-product attention | 1 source, 1 source note | 2 pages | 6 pages |
| Coding-agent harnesses and open models | 47 registry entries, 47 Markdown files in `notes/` including syntheses | 20 pages | 33 pages |

The smaller study was marked `depth: full` but describes itself as a single-source briefing and retains unresolved evidence gaps in its synthesis. The larger study produced a substantial reference artifact, but its size makes human verification and later review expensive.

The workflow needs both a cheap interactive path for learning a bounded concept and a rigorous delegated path for difficult research. `track` and `depth` currently mix interaction mode, methodology, assurance, effort, and output format.

### 3. Human gates are clerical rather than evidential

Approval is represented as booleans that the human edits in YAML. The files do not require the approver to record:

- what was inspected;
- which criteria passed;
- accepted uncertainty;
- the decision rationale;
- what would reopen the decision.

Both completed briefs still contain unchecked definition-of-done boxes. The larger completed study has an empty `last_gate_verdict`. These states pass `tools/check_all.py`.

The gate mechanism therefore proves that a boolean was flipped, not that a decision was informed. Manual YAML editing also makes an invalid transition easy and gives the learner no useful review interface.

### 4. State is duplicated and can disagree

There are at least four state concepts:

1. `study.yaml.status` for workflow position.
2. Boolean fields under `study.yaml.gates`.
3. `study.yaml.last_gate_verdict` for the latest quality judgment.
4. `.research/state.json` and claim lifecycle states for research maturity.

No single transition engine reconciles them. `check_all.py` validates status enums and one track-specific gate, but it does not enforce the expected relationship between status, gates, artifacts, and verdicts.

The cleaned studies make this concrete:

- Their manifests still advertise `.research/` as the dossier artifact, but the directory is absent.
- `reviews/` and `sources/docs/` are absent by design after cleanup.
- Many registry `snapshot` fields point to files described as historical.
- The repo-wide audit treats the absence of every dossier as a skipped check, then summarizes the audit group as `PASS`.

`PASS`, `NOT_ASSESSED`, and `archived evidence unavailable in the worktree` should not collapse into the same result.

### 5. Role permissions and role instructions conflict

The intended zone separation is useful, but several procedures cannot be performed under their declared boundaries:

- The summarizer must update `sources/registry.yaml`, while its edit permissions and prose boundary allow only `notes/` and `study.yaml`.
- The researcher must append `.research/evidence.jsonl`, while its final prose boundary says it may write only `sources/` and `study.yaml`.
- The experimenter is permitted to edit `.research/claims.jsonl`, while its prose boundary says it may write only `experiments/` and `study.yaml`.
- The writer is told to compile and lint but has `bash: deny`.
- Multiple agents may edit the whole `study.yaml`, even though gates are human-owned and only limited fields should be agent-writable.
- Glob permissions are repository-wide, not scoped to the exact study supplied to the task.

These contradictions encourage either failed runs or permission workarounds. They also make it difficult to tell whether the permission policy or the prose contract is authoritative.

### 6. Evidence is duplicated, then made inconvenient to inspect

For a full study, source identity and support relationships can appear in the registry, source note, bibliography, evidence ledger, claim ledger, synthesis, and report. Some duplication is useful for human-readable views, but the current files are independently authored and can drift.

Cleanup then removes the dossier, source snapshots, experiment artifacts, and reviews from the working tree. Git history is a recovery mechanism, not an ergonomic evidence store. A future learner opening a completed study cannot immediately follow many snapshot paths or inspect the final review that justified sign-off.

The durable knowledge core should remain compact, but compactness should be achieved through deduplication and archival indexes, not broken live references.

### 7. Automation validates form more than lifecycle semantics

The current tests cover useful low-level behavior: lint rules, YAML rendering, cleanup preconditions, pinning, pin verification, and a small subset of manifest validity. Missing checks include:

- required brief fields and unresolved template guidance;
- complete registry schema validation;
- note-template and anchor validation;
- status and gate consistency;
- artifact paths declared by the manifest actually existing;
- a completed study satisfying its own definition of done;
- `last_gate_verdict` being present and compatible with progression;
- permission-policy compatibility with each agent procedure;
- lifecycle behavior across scaffold, approval, production, review, and archive;
- learning evidence such as baseline, independent assessment, and delayed review.

The result is a green CI run for a repository with no auditable dossiers in the current tree and incomplete completion checklists.

### 8. Delegated work has no explicit effort controller

Every additional source tends to create another note and more review obligations. The system has no explicit source budget, stop rule based on information gain, or progressive evidence policy. Reports are appropriate in delegated mode, but slides and publication-shaped formatting should still be selected only when useful.

Recent history contains explicit backfill, schema-alignment, audit-repair, and cleanup-fix commits. This is expected during an early design, but it is also evidence that the present contract has high coordination cost relative to the two studies completed so far.

### 9. Shared knowledge supports reference reuse but not interactive review

`shared/knowledge/` usefully avoids rediscovery, but it is not a learner model. A knowledge page does not record:

- prerequisites;
- questions the learner can now answer;
- known misconceptions;
- confidence versus demonstrated performance;
- last successful recall;
- when to review again;
- which later study superseded a claim.

As a result, the repository accumulates useful reference text but not a maintained map of what the learner knows. The former is the desired output of delegated mode; the latter is required for interactive mode.

### 10. There is no mode-specific feedback loop

The repository does not record time spent, agent cost, number of human interventions, source yield, assessment performance, delayed retention, or usefulness of artifacts. Without mode-specific outcome metrics, it cannot tell whether delegated mode produced a useful report efficiently or whether interactive mode produced durable understanding.

## Target strategy

### Select the operating mode explicitly

Every study begins by declaring `mode: interactive` or `mode: delegated`. The mode changes the success contract, required artifacts, agent behavior, and gate sequence.

| Property | Interactive mastery | Delegated deep study |
|---|---|---|
| User's intent | Personally understand or perform | Receive a trustworthy investigation and report |
| User participation | Frequent attempts, explanations, and decisions | Scope approval and bounded review checkpoints |
| Agent behavior | Tutor, questioner, coach, evaluator | Research coordinator and specialist team |
| Primary artifact | Learner attempts and mastery record | Evidence-backed synthesis and comprehensive report |
| Success test | Unaided performance plus transfer | Answer coverage, traceability, independent review, and useful conclusions |
| Typical duration | One or several focused sessions | Hours, days, or multiple agent waves |
| Default deliverable | Learning note and mastery record | Technical report; slides optional |

The user may consume a delegated report and later open an interactive study for selected concepts. That is a new study or an explicit child phase, not an automatic assumption that reading the report produced mastery.

### Keep mode, assurance, methodology, and output independent

Replace the current overloaded `track` and `depth` pair with explicit dimensions:

| Dimension | Suggested values | Controls |
|---|---|---|
| Mode | `interactive`, `delegated` | User participation and success contract |
| Intent | `understand`, `solve`, `build`, `compare`, `decide`, `refresh`, `survey` | Questions, task form, and synthesis |
| Evidence assurance | `quick`, `grounded`, `audited` | Verification depth, snapshots, ledgers, and independent review |
| Methodology | `source-only`, `static-code`, `experimental`, `mixed` | Which evidence can answer the questions |
| Deliverable | `learning-note`, `implementation`, `decision-brief`, `report`, `slides`, `none` | Outputs to create |

Valid examples include:

- `interactive + understand + grounded + source-only + learning-note` for attention scaling.
- `delegated + compare + audited + static-code + report,slides` for coding-agent harnesses.
- `delegated + survey + audited + source-only + report` for a literature synthesis.
- `interactive + build + grounded + experimental + implementation` for learning an algorithm by implementing and testing it.

Experiments are chosen because the question needs execution evidence, not because interaction mode implies them.

For migration, existing studies default to `mode: delegated`, because their stored artifacts and approvals were produced under the report contract. Existing `track` values map initially to methodology: `concept` and `review` become `source-only`, while `experimental` remains `experimental`. `depth: briefing` can suggest `grounded`; `depth: full` can suggest `audited`, but the new validator must inspect retained evidence before granting that assurance verdict.

### Define the shared study contract

Every mode records:

- **Purpose:** why the study matters.
- **Questions:** what must be answered.
- **Scope and exclusions:** where the conclusions may apply.
- **Evidence assurance and methodology:** what level and kind of support are promised.
- **Budget and stop rules:** time, sources, compute, money, and saturation or kill criteria.
- **Deliverables:** the exact outputs expected.
- **Human decision points:** what agents may do between checkpoints.

Interactive mode additionally records target capability, prior model, prerequisites, mastery task, transfer task, and review schedule.

Delegated mode additionally records report audience, decomposition plan, coverage dimensions, required comparisons, expected depth, source cutoff, independent-review requirements, and what uncertainty must remain visible.

### Interactive mode: use a guarded tutor loop

The main agent behaves as a tutor-coordinator:

1. **Diagnose first.** Ask the learner to predict, derive, explain, or attempt a small problem before showing a solution.
2. **Plan a concept path.** Identify prerequisites, target concepts, likely misconceptions, and the final transfer task.
3. **Gather the minimum evidence packet.** Start with the smallest source set capable of resolving the next uncertainty.
4. **Teach through questions and hints.** Prefer prompts, partial structure, counterexamples, and feedback before a full answer.
5. **Require learner production.** Store the learner's explanation, code, diagram, or decision before the agent's polished synthesis.
6. **Practice variation.** Use at least one near problem and one transfer problem where appropriate.
7. **Assess without assistance.** The learner completes the declared mastery task with agent help disabled or limited to administering the task.
8. **Give corrective feedback.** Record errors and misconceptions, then target only the weak component.
9. **Distill.** Promote compact, sourced knowledge that survived the mastery check.
10. **Revisit.** Schedule retrieval after a delay and update mastery based on performance, not confidence alone.

This design matters specifically for agentic AI. In a 2025 field experiment, an unguarded GPT interface improved supported practice performance but reduced later unassisted performance, while tutoring safeguards largely mitigated the harm ([Bastani et al., 2025](https://doi.org/10.1073/pnas.2422633122)). Interactive mode should therefore prevent answer outsourcing by design.

### Delegated mode: preserve and strengthen the research pipeline

Delegated mode is the right choice when the user wants agents to absorb complexity and return a comprehensive product. The coding-agent harness study is a representative case: dozens of source components, pinned repositories, closed-source boundaries, cross-system matrices, a long synthesis, and a reviewed report.

Its loop is:

1. **Scope.** The human approves questions, systems, exclusions, evidence cutoff, assurance level, budget, and deliverables.
2. **Decompose.** A coordinator builds a coverage matrix and assigns disjoint source, code, or experiment packets.
3. **Gather.** Specialist agents retrieve, pin, snapshot, and register sources with explicit coverage limits.
4. **Verify.** Agents produce anchored notes and evidence records; a separate verifier checks central claims and contested gaps.
5. **Synthesize.** The coordinator reconciles terminology, contradictions, missing cells, and cross-source conclusions before prose drafting.
6. **Draft.** A writer produces the comprehensive report only from accepted evidence and verified synthesis.
7. **Review.** An independent reviewer traces material claims, numbers, citations, limitations, and scope.
8. **Revise and sign off.** Agents address human-approved findings; the human accepts the final artifact.
9. **Archive.** Durable evidence locators, report sources, decisions, and final reviews remain usable.

Agents may perform steps 2 through 7 with little interaction when the approved contract is precise. They must stop when evidence changes scope, cost, risk, or the meaning of the requested deliverable.

Delegated mode does not require a learner baseline, teach-back, mastery test, or delayed recall. Those would measure a different objective. Its quality burden is comprehensive coverage within scope, evidence integrity, honest uncertainty, synthesis quality, and report usefulness.

### Use a mode-specific agent topology

Keep one coordinator and instantiate only the roles needed for the selected mode:

| Role | Interactive responsibility | Delegated responsibility |
|---|---|---|
| Coordinator | Own learning contract, tutor state, and integration | Own research contract, task graph, canonical state, and report integration |
| Source scout or researcher | Build a small grounded packet | Search broad assigned scopes, verify metadata, and preserve evidence |
| Tutor or practice designer | Ask questions, create exercises, and give calibrated hints | Usually not used |
| Summarizer | Explain a source only when learning needs it | Produce anchored source or code-component notes |
| Experimenter or engineer | Support an implementation-based mastery task | Run approved claim-eligible experiments with provenance |
| Writer | Distill a short post-mastery learning note | Produce the comprehensive report and optional slides |
| Independent verifier or reviewer | Evaluate mastery without seeing intended answers | Audit important claims and the integrated report with fresh context |

The current researcher, summarizer, experimenter, writer, and reviewer roles remain valuable in delegated mode after their permission contradictions are repaired. Interactive mode should not invoke all of them by default.

The learner's attempt and the verifier's judgment must be protected from contamination by the tutor's intended answer. In delegated mode, writable artifacts must have one owner per agent wave, and the coordinator must reconcile every handoff before promoting claims.

## Target information architecture

Use a shared envelope with mode-specific workspaces. Directories marked interactive or delegated are created only for that mode:

```text
studies/<id>/
├── study.yaml                 # schema version, mode, configuration, derived state
├── brief.md                   # shared contract plus mode-specific fields
├── events.jsonl               # append-only transitions and human decisions
├── learning/                  # interactive mode
│   ├── baseline.md            # unaided initial attempt and confidence
│   ├── map.md                 # concepts, prerequisites, misconceptions
│   ├── journal.md             # learner explanations and tutor feedback
│   ├── practice/              # exercises, learner answers, rubrics
│   └── mastery.md             # independent assessment and later reviews
├── evidence/
│   ├── sources.yaml           # canonical source identity and snapshot locator
│   ├── snapshots/             # retained or content-addressed source text
│   ├── notes/                 # assurance-appropriate anchored notes
│   ├── claims.jsonl           # audited assurance only
│   └── archive.yaml           # content hashes and archive locations
├── research/                  # delegated mode
│   ├── decomposition.md       # coverage matrix and agent task packets
│   ├── synthesis.md           # reconciled cross-source findings
│   └── reviews/               # review rounds and finding dispositions
├── work/                      # optional implementation or experiments
└── outputs/
    ├── learning-note.md       # interactive, optional compact distillation
    ├── report/                # delegated, normally required
    └── slides/                # optional in either mode
```

Important rules:

- A fact has one canonical source record. Bibliographies and report references are generated views.
- A gate decision is an event with actor, time, inspected evidence, rationale, and reopen condition.
- `study.yaml` contains the current materialized state, while `events.jsonl` explains how it got there.
- Artifact fields may not point to missing paths. Archived artifacts use an explicit archive record and content hash.
- Interactive learner attempts are never overwritten by an agent revision.
- Delegated task packets, handoffs, synthesis, and review dispositions remain distinguishable from the final report.
- Claims ledgers are reserved for audited work. A bounded grounded study should not pay full dossier cost.

## State and gate redesign

Use one state engine with two allowed transition graphs:

```text
interactive: scoped -> diagnosing -> learning -> practicing -> assessing -> retained -> archived

delegated:   scoped -> decomposing -> gathering -> verifying -> synthesizing -> drafting -> review -> done -> archived
```

Allow backward transitions. Interactive assessment can return to learning or practice. Delegated review can return to gathering, verification, synthesis, or drafting.

Shared human decisions:

1. **Scope approval:** the questions, budget, assurance, deliverables, and stop rules are right.
2. **Evidence acceptance:** the factual basis is sufficient for the selected assurance level.
3. **Archive approval:** durable knowledge and evidence locators are complete.

Interactive-only decision:

- **Mastery acceptance:** the learner demonstrated the target capability and required transfer at the recorded help level.

Delegated-only decisions:

- **Draft acceptance:** the comprehensive report matches the accepted evidence and requested coverage.
- **Review sign-off:** material findings are resolved or explicitly accepted by the human.

Keep three quality verdicts separate:

- **Evidence quality:** are factual claims grounded at the promised assurance level?
- **Mastery quality:** in interactive mode, did the learner demonstrate the declared capability and transfer?
- **Artifact quality:** in delegated mode, is the comprehensive report accurate, complete within scope, useful, and renderable?

An excellent report does not imply interactive mastery, and failed mastery does not invalidate an otherwise sound delegated report. They are different contracts. Strong mastery of a bounded concept does not require a publication-style report; a delegated complex investigation normally does require a comprehensive report.

Human decisions should be made through a command, not direct YAML editing. For example:

```text
study approve <id> evidence --note "Checked source packet and accepted two scoped gaps"
```

The tool writes the event and derives the manifest state. Agents may propose `ready_for_review`, but only the human command records approval.

## Command and tool design

Build one lifecycle CLI as the source of truth, with slash commands as thin adapters:

```text
study new       require --mode interactive|delegated and scaffold mode artifacts
study status    show mode, current state, open gaps, approvals, and next action
study next      perform the next authorized bounded action
study approve   record a human gate decision
study practice  interactive: administer an exercise without exposing the answer
study assess    interactive: run mastery and record the rubric result
study revisit   interactive: administer due retrieval and update mastery history
study run       delegated: execute the next approved research wave
study report    delegated: synthesize, draft, build, or review as state permits
study verify    run assurance-specific structural checks
study archive   preserve durable knowledge and valid evidence locators
```

This removes state-transition logic from prompt prose. Agent files should describe judgment and handoffs, while code enforces schemas, permissions, and transitions.

## Validation redesign

### Structural checks

Add machine-readable schemas and checks for:

- required brief fields and absence of template guidance;
- valid mode and mode-specific required fields;
- one valid state transition path;
- gate-to-state consistency;
- human identity and rationale on approval events;
- all declared artifacts resolving to live or explicitly archived targets;
- source keys being unique and metadata complete for their type;
- note anchors and source relationships;
- no report citation whose source is absent or rejected;
- no completed study with an empty final verdict or unchecked required criteria;
- exact agreement between agent procedures and permission tests;
- agent write scope restricted to the selected study;
- generated bibliography and other views matching canonical records.

If no dossier exists, the dossier result must be `NOT_ASSESSED`, not summarized as `PASS`.

### Lifecycle tests

Add end-to-end tests for at least these paths:

1. interactive concept learning with no report;
2. interactive implementation with a smoke test and mastery task;
3. failed interactive mastery returning to practice;
4. delegated grounded comparison with source notes and a decision brief;
5. delegated audited literature review with claims, comprehensive report, and independent verification;
6. delegated experimental study with frozen design and measured runs;
7. archive and reopen in both modes with every evidence locator still usable.

### Mode-specific completion checks

CI cannot decide whether a person understands something or whether a complex synthesis is insightful. It can require that the declared contract has supporting artifacts.

Interactive checks:

- baseline attempt exists before tutoring output;
- mastery artifact is learner-authored and time-stamped;
- rubric and evaluator are recorded;
- help level is recorded;
- at least one transfer item exists when the objective claims application;
- delayed review is scheduled or explicitly declined by the human.

Delegated checks:

- approved decomposition covers every research question and comparison dimension;
- every research packet has a disposition and structured handoff;
- material report claims trace to accepted notes, evidence records, or eligible runs;
- contradictions and unavailable evidence remain visible in the synthesis;
- an independent review and human disposition exist before sign-off;
- the comprehensive report and every requested derived deliverable build and pass their format checks.

## Evidence and archive policy

Keep the current ban on fabricated citations and uninspected code. Change the storage policy:

1. Preserve compact text snapshots, final claim/evidence records, decision events, and final review results in the current tree for audited studies.
2. Deduplicate snapshots by content hash if size is the concern.
3. Generate BibTeX and report references from source records.
4. Remove temporary caches and build products during archive, but do not leave a live manifest pointing at deleted artifacts.
5. If an artifact must leave the tree, record its archive mechanism, commit or object identifier, hash, retrieval command, and availability status.
6. Treat source freshness separately from historical integrity. A snapshot can remain valid evidence of what was inspected while being marked stale for current product behavior.

## Shared knowledge redesign

Both modes can update shared knowledge, but they contribute different metadata. Delegated studies contribute sourced concept pages, comparison frameworks, and known evidence limits. Interactive studies additionally contribute mastery and review state. Keep prose pages for reading, but back interactive knowledge units with small structured records:

```yaml
id: attention.logit-scaling
question: Why divide attention logits by sqrt(d_k)?
prerequisites:
  - variance-of-independent-sums
  - softmax-derivative
source_ids:
  - vaswani2017attention
misconceptions:
  - "The factor normalizes every realized logit to unit variance"
mastery:
  last_assessed: 2026-08-21
  level: applied
  help: none
review:
  next_due: 2026-08-28
```

The exact scheduling algorithm is less important than recording retrieval performance and adapting the next review. Do not infer mastery from a delegated report. The user may explicitly adopt selected concepts into an interactive review queue. Do not generate a large flashcard deck automatically; promote a small number of high-value questions, common errors, and transfer prompts after the learner has used them.

## Metrics that align with the goal

Track metrics that match the selected mode:

| Interactive mastery | Delegated deep study | Shared cost and quality |
|---|---|---|
| Baseline score and confidence | Research-question coverage | Elapsed time and agent turns or cost |
| Immediate mastery and help level | Comparison-matrix coverage | Human review minutes |
| Delayed retrieval | Material claims independently checked | Sources opened versus retained |
| Transfer-task result | Unresolved gaps by severity | Rework and invalidated artifacts |
| Confidence-error gap | Report usefulness for the stated audience | User-rated usefulness |
| Time to mastery | Time to accepted report | Archive and reopen success |

Do not optimize source count, note count, report length, or number of passed structural checks. In delegated mode these can indicate scale, but they remain costs or safeguards rather than outcomes. In interactive mode they are especially poor proxies for learning.

## Prioritized implementation plan

### Phase 0: measure the current workflow

Priority: immediate, low risk.

- Add this strategy document to the repository.
- Label the next suitable current study as a delegated-mode baseline.
- Record time, agent cost or turns, source yield, human review time, coverage, rework, and report usefulness.
- Separately run the interactive case study below and record baseline ability, mastery, help level, and one-week recall.
- Keep the current delegated workflow operational while collecting both baselines.

Exit criterion: one delegated study and one interactive study have mode-appropriate outcome and cost measurements.

### Phase 1: build one interactive vertical slice

Priority: highest.

- Extend `brief.md` with target capability, baseline task, mastery task, transfer task, budget, and stop rule.
- Add `learning/baseline.md`, `learning/journal.md`, and `learning/mastery.md` templates.
- Implement `study status`, `study approve`, `study practice`, and `study assess` in a single CLI.
- Add `mode: interactive|delegated`; preserve existing studies as delegated through migration defaults.
- Scaffold reports by default only in delegated mode; keep them opt-in for interactive mode.
- Pilot the attention-scaling case study below.

Exit criterion: the learner completes diagnosis, tutoring, independent mastery, and delayed review without disrupting the current delegated report workflow.

### Phase 2: unify state and repair contracts

Priority: highest.

- Introduce a schema version and event ledger.
- Implement both transition graphs in the same state engine.
- Make the CLI the only writer of lifecycle state and approval records.
- Remove general agent write permission to `study.yaml`.
- Add permission contract tests for every agent procedure.
- Make skipped checks report `NOT_ASSESSED`.
- Validate artifact existence, completion criteria, and state consistency.

Exit criterion: invalid transitions and the current permission contradictions fail tests.

### Phase 3: make assurance adaptive

Priority: high.

- Implement `quick`, `grounded`, and `audited` evidence profiles.
- Use one canonical source model and generate derived bibliography views.
- Require claims ledgers and independent verification only for audited work.
- Add explicit source budgets and stop rules.
- Pilot `grounded` assurance in interactive mode and `audited` assurance in a delegated comparison.

Exit criterion: both modes share canonical evidence without forcing interactive studies to pay audited-dossier cost or weakening delegated traceability.

### Phase 4: fix durable knowledge and archive behavior

Priority: high.

- Add structured knowledge-unit metadata and review history.
- Replace destructive evidence cleanup with deduplication or explicit archive records.
- Ensure every declared evidence locator remains resolvable after archive.
- Add reopen and stale-source checks.

Exit criterion: a completed study can be reopened from the current checkout, assessed, and refreshed without mining git history for its evidence contract.

### Phase 5: make output modules mode-aware

Priority: medium.

- Keep comprehensive reports and independent manuscript review as the delegated-mode default.
- Make LaTeX styling selectable rather than hardwiring a conference template to every report.
- Keep reports and slides optional in interactive mode.
- Replace `/gather`, `/draft`, and `/review` as lifecycle controllers with thin calls to the unified CLI.
- Preserve research-publication support for delegated studies that explicitly request it.

Exit criterion: a new user can choose interactive mastery or delegated deep study without accidentally entering the other mode, and the harness-scale report workflow remains fully supported.

## Interactive case study: scaled dot-product attention

This case is intentionally similar in scope to `studies/2026-08_scaled-dot-product-attention`. It demonstrates what the existing two-page concept report does not: whether the user can derive, explain, and transfer the idea.

This is an implementation specification, not a claim that a learner has completed or passed it.

### Study contract

```yaml
mode: interactive
intent: understand
assurance: grounded
methodology: source-only
deliverables:
  - learning-note
time_budget_minutes: 75
source_budget: 2
target_capability: >
  Derive the sqrt(d_k) attention-logit scale from explicit variance
  assumptions, explain its connection to softmax saturation, distinguish
  the paper's stated motivation from later interpretation, and adapt the
  scale when the assumptions change.
mastery_help_level: none
delayed_review_days: 7
```

The source packet starts with the existing `vaswani2017attention` registry record and anchored note, plus `shared/knowledge/attention-scaling.md`. The source scout verifies the relevant primary-source passage before the tutoring session. A second source is gathered only if the learner asks a question that the existing packet cannot support or if an empirical claim about scaled-versus-unscaled behavior becomes necessary.

### Artifacts

```text
studies/<interactive-attention-id>/
├── study.yaml
├── brief.md
├── events.jsonl
├── learning/
│   ├── baseline.md
│   ├── map.md
│   ├── journal.md
│   ├── practice/
│   │   ├── near-problem.md
│   │   └── transfer-problem.md
│   └── mastery.md
├── evidence/
│   ├── sources.yaml
│   └── notes/vaswani2017attention.md
└── outputs/learning-note.md
```

No LaTeX report, slide deck, claims ledger, or research dossier is required. The existing report can be linked as optional reading after the baseline attempt, but it is not shown beforehand.

### Step 1: unaided baseline

The tutor records the learner's answers before giving corrections:

1. Write the scaled dot-product attention equation from memory or state which part is uncertain.
2. If the components of a query and key are independent, zero mean, and unit variance, estimate the variance and standard deviation of their unscaled dot product as a function of `d_k`.
3. Predict what increasingly large-magnitude logits do to a softmax distribution and its gradients.
4. Explain whether `1/sqrt(d_k)` is an empirical constant, a mathematical consequence, or a design heuristic under assumptions.
5. Record confidence from 0 to 100 for each answer.

The tutor does not score for progression yet. It uses the attempt to decide whether the concept path must first revisit variance, dot products, or softmax derivatives.

### Step 2: adaptive concept path

The default path is:

```text
independent sums
  -> variance of q_i k_i
  -> variance of the dot product
  -> standard-deviation normalization
  -> softmax concentration and derivative behavior
  -> what Vaswani et al. state versus what the derivation adds
```

For each link, the tutor asks the learner to supply the next step. Help is recorded on a four-level scale:

| Level | Tutor behavior |
|---|---|
| 0 | Restate the question only |
| 1 | Point to the prerequisite or relevant variable |
| 2 | Supply an intermediate equation or counterexample |
| 3 | Show the step and ask the learner to explain it back |

The journal preserves the learner's original response, the hint level, the revised response, and the tutor's evidence-grounded correction.

### Step 3: near practice

The learner solves this without a displayed solution:

> Let every coordinate of `q` and `k` be independent, zero mean, and unit variance. For `d_k = 64`, derive the standard deviation of `q dot k` before and after division by `sqrt(d_k)`. Explain what is and is not guaranteed about any individual realized logit.

The expected reasoning path used by the evaluator is that the variance of the sum grows with `d_k`, its standard deviation grows with `sqrt(d_k)`, and the scale normalizes the distribution under the assumptions. The answer must not claim that every realized logit becomes bounded or has unit magnitude.

### Step 4: transfer practice

The learner receives a changed-assumptions problem:

> Suppose each query coordinate has variance `sigma_q^2` and each key coordinate has variance `sigma_k^2`, with independence and zero means retained. Derive a scale that gives the dot product unit variance. Then state why a learned model may violate the assumptions even if `1/sqrt(d_k)` remains useful.

This tests whether the learner can reconstruct the scaling logic rather than recall the familiar formula. An optional implementation variant asks the learner to sample synthetic vectors, plot the logit distributions at several `d_k` values, and label the run as conceptual plumbing rather than empirical evidence about trained Transformers.

### Step 5: mastery assessment

After a short break and with tutoring disabled, the learner completes five tasks:

1. Reconstruct the attention equation and define `d_k`.
2. Derive `Var(q dot k)` and the standard normalization under unit-variance assumptions.
3. Explain how logit scale affects softmax concentration and gradient magnitude without claiming that the paper provides an ablation.
4. Separate three truth types: what the primary paper states, what follows from the simplified assumptions, and what remains empirically unverified in this study.
5. Solve the changed-variance transfer problem.

Each task receives 0, 1, or 2 points:

- `0`: missing or materially incorrect;
- `1`: directionally correct with an important gap;
- `2`: correct, scoped, and independently explained.

The proposed mastery criterion is at least 8 of 10, no task at 0, and help level 0 during assessment. Failure returns the study to `practicing` with a targeted exercise for the weakest task. The human may change the threshold when approving the study contract, but it must be fixed before assessment.

### Step 6: distillation and delayed review

Only after mastery does the agent help produce `outputs/learning-note.md`. It contains:

- the learner's final explanation in their own words;
- the compact derivation;
- the primary-source boundary;
- the misconception that normalization controls the distribution, not every realized value;
- the transfer rule under changed variances;
- links to the source note and mastery artifact.

Seven days later, `study revisit` asks three short questions without displaying the learning note: reconstruct the scale, explain the softmax connection, and solve one changed-assumptions item. The result updates review state but does not rewrite the original mastery record.

### Why this belongs in interactive mode

The question is narrow, prerequisites are identifiable, the derivation can be practiced within one session, and the user's unaided reasoning is the desired outcome. If the request instead becomes “survey the theoretical and empirical literature on attention scaling variants and return a comprehensive account,” it should be opened as a delegated study that may reuse this study's evidence.

## Delegated reference case: coding-agent harnesses

The existing harness study maps naturally to:

```yaml
mode: delegated
intent: compare
assurance: audited
methodology: static-code
deliverables:
  - report
  - slides
```

Its primary success evidence is not a learner quiz. It is the coverage of three systems and their subsystems, 47 registered evidence components, pinned repository commits, anchored notes, explicit closed-source boundaries, cross-system synthesis, a comprehensive report, and independent review.

Under the redesigned delegated mode, the study would gain:

- an approved decomposition and coverage matrix before broad gathering;
- explicit source, time, and review budgets;
- structured handoffs for each component;
- a coordinator-owned synthesis and claim map;
- central-claim verification with fresh context;
- review findings with recorded human dispositions;
- archive records that keep final evidence locators usable.

It would not gain baseline questions, forced teach-backs, mastery scoring, or spaced repetition unless the user later chooses to learn one of its concepts interactively.

## First implementation evaluation

The first release should run two acceptance pilots, not treat the modes as competitors:

| Pilot | Interactive attention scaling | Delegated regression study |
|---|---|---|
| Purpose | Validate tutoring and mastery mechanics | Confirm comprehensive research was not weakened |
| Required output | Baseline, journal, practice, mastery, learning note | Decomposition, evidence, synthesis, review, report |
| Main quality result | Unaided derivation and transfer | Coverage, traceability, review verdict, report usefulness |
| Delayed result | Seven-day retrieval | Reopen and source-freshness audit |
| Cost result | Time to mastery and hint usage | Agent effort and human review time |

The delegated regression can use a bounded update to the coding-agent harness comparison or another similarly complex study. Acceptance requires the interactive pilot to add measurable mastery without report ceremony and the delegated pilot to retain or improve report quality without requiring continuous user interaction.

## Decisions to make before implementation

The human owner should decide these points because they materially affect the product:

1. Which mode is the default when the user's wording is ambiguous, with `interactive` recommended for “teach me” and `delegated` for “study this and report back.”
2. Whether learner attempts and assessment history may be committed, since they can be personal and sometimes embarrassing by design.
3. The default evidence assurance level.
4. Whether delayed review should live entirely in the repository or integrate with an external scheduler.
5. Whether backward compatibility with the current study layout is required or a migration tool is acceptable.
6. How long delegated agents may work between human checkpoints and which budget thresholds always require renewed approval.

## Recommended immediate decision

Adopt the explicit two-mode contract now, then implement Phase 0 and the interactive Phase 1 vertical slice without removing the current delegated workflow. Treat existing studies as delegated during migration. The cheapest decisive test is the paired evaluation above: the attention case must demonstrate usable interactive mechanics, and a delegated regression must confirm that comprehensive report production remains traceable and can proceed with sparse user interaction.

## Assessment verdict

Gate: repository strategy

Status: `CONDITIONAL`

Decision controlled: whether to begin a two-mode redesign that supports interactive mastery and delegated deep study

Evidence: repository contracts, tools, tests, two completed studies, build artifacts, git history, and the cited primary research

Uncertainty: no current learning, time, cost, delayed-retention, or report-usefulness measurements exist, so neither mode's effectiveness can be compared retrospectively

Deviations: none

Waivers: none

Next decisive action: run the interactive attention-scaling pilot and one delegated regression study under explicit mode contracts

## References

- Bastani, H., Bastani, O., Sungu, A., Ge, H., Kabakcı, Ö., and Mariman, R. (2025). “Generative AI without guardrails can harm learning: Evidence from high school mathematics.” *Proceedings of the National Academy of Sciences*, 122(26), e2422633122. <https://doi.org/10.1073/pnas.2422633122>
- Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P., and Glaser, R. (1989). “Self-Explanations: How Students Study and Use Examples in Learning to Solve Problems.” *Cognitive Science*, 13(2), 145-182. <https://doi.org/10.1207/s15516709cog1302_1>
- Karpicke, J. D., and Roediger, H. L. III. (2008). “The Critical Importance of Retrieval for Learning.” *Science*, 319(5865), 966-968. <https://doi.org/10.1126/science.1152408>
