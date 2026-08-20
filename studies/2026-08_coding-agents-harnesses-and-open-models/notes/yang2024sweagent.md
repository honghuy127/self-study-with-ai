---
# per-source note. Every field required. Every claim about the source
# carries a page/section anchor. Delete guidance when final.
source_key: "yang2024sweagent"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
---

# Notes: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering

## Source identification

- Key: yang2024sweagent
- Authors, year, venue: John Yang, Carlos E. Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik Narasimhan, Ofir Press; 2024; Princeton Language and Intelligence. Extracted PDF header reads "arXiv:2405.15793v3 [cs.SE] 11 Nov 2024" and the first-page footer reads "38th Conference on Neural Information Processing Systems (NeurIPS 2024)." (p. 1). Registry tiers it as preprint.
- Tier: preprint
- URL / DOI: https://arxiv.org/abs/2405.15793 (snapshot: pdftotext -layout extraction of the registered PDF, sources/docs/swe-agent-2405.15793.txt)

## Problem and motivation

- LM agents are increasingly applied to code generation with execution feedback, but applying them to complex software engineering tasks "remains unexplored" (p. 1).
- Existing LM agents are typically built against human interfaces: the Linux shell or a Python interpreter (p. 1). Human engineers instead benefit from sophisticated applications like VSCode, and human-computer interaction (HCI) research shows interfaces affect human performance; the paper asks whether LM agents similarly benefit from better-designed interfaces (p. 1).
- Observed failure of the status quo: interacting directly with a Linux shell, LM agents "fail to provide simple commands to edit a small file segment" and the shell gives "no feedback if the user makes an invalid edit"; these deficits "substantially hamper performance" (p. 1).
- This motivates the agent-computer interface (ACI), "an abstraction layer between the LM agent and computer, to enhance the LM agent's abilities in computer environments" (p. 1). The paper argues "LM agents represent a new category of end user, with their own needs and abilities" (Section~2, p. 2), analogous to how IDEs help humans (Figure 2, p. 2).
- Why human UIs suit humans but not LMs: current LMs lack visual understanding to operate GUIs; humans can ignore irrelevant information, whereas "all content has a fixed cost in memory and computation for LMs and distracting context can harm performance" (p. 2).

## Method or core idea

- SWE-agent = a fixed LM plus a custom ACI; the paper "assume[s] a fixed LM and focus[es] on designing the ACI" with no weight changes (Section~2, p. 2). Contributions: the ACI concept plus an open-source system (p. 1, Section~7, p. 9).
- Scope of the ACI: it "specifies both the commands available to the LM and how the environment state is communicated back to the LM", and "tracks the history of all previous commands and observations" and manages how each step's content is "formatted and combined with high-level instructions into a single input for the LM" (p. 2). So the ACI covers tools, feedback formatting, and context/history management, which is essentially the harness.
- Design process: (1) manually inspect agent behavior on hand-picked development examples and propose improvements; (2) grid-search ACI configurations (p. 2). Result: four design principles (Section~2, p. 3):
  1. "Actions should be simple and easy to understand for agents": few options, concise documentation, instead of bash commands with "dozens of options" (p. 3).
  2. "Actions should be compact and efficient": consolidate operations like navigation and editing "into as few actions as possible"; poor design requires composing "many simple actions ... across multiple turns" (p. 3).
  3. "Environment feedback should be informative but concise" about state and the effect of recent actions (p. 3).
  4. "Guardrails mitigate error propagation and hasten recovery", e.g., "a code syntax checker that automatically detects mistakes" (p. 3).
- Agent loop: at each step SWE-agent "generates a thought and a command, then incorporates the feedback from the command's execution" (ReAct-style); built atop the Linux shell, it still allows common Linux commands (Section~3, p. 3).
- Four ACI components (Section~3): search/navigation, file viewer, file editor, context management (p. 3).
  - Search/navigation: `find_file` (filename search), `search_file` and `search_dir` (string search), emitting summarized results (p. 3). Guardrail: "The search commands return at most 50 results for each search query; if a search exceeds this number, we do not report the results and instead suggest that the agent write a more specific query." (pp. 3-4).
  - File viewer: `open` on a file path shows "a window of at most 100 lines"; `scroll_down`, `scroll_up` move the window; `goto` jumps to a line; output shows full path, total line count, omitted lines above/below, and per-line line numbers (p. 4).
  - File editor: `edit` takes start line, end line, replacement text and replaces that range in the open file in one step; after an edit "the file viewer automatically displays the updated content" so no extra read command is needed (p. 4). A code linter is integrated: "Invalid edits are discarded, and the agent is asked to try editing the file again" (p. 4). Exact linter invocation given in Appendix A.1: `flake8 --isolated --select=F821,F822,F831,E111,E112,E113,E999,E902 "$CURRENT_FILE" 2>&1` covering undefined names, duplicate arguments, indentation, syntax errors, unreadable files (p. 19).
  - Context management: informative prompts, error messages, and history processors; agents generate a thought and an action per step; malformed generations trigger an error response and retry until valid, after which "all past error messages except the first are omitted" (p. 4). Empty-output runs get the explicit message "Your command ran successfully and did not produce any output" (p. 4). Observations preceding the last 5 "are each collapsed into a single line", preserving plan/action structure while reducing outdated context (p. 4).
- Full command set (Table 4, p. 17): file viewer (`open <path> [<line_number>]`, `goto <line_number>`, `scroll_down`, `scroll_up`), search (`search_file`, `search_dir`, `find_file`), editing (`edit <n>:<m> <replacement_text> end_of_edit`, `create <filename>`), task (`submit`), plus standard Linux bash commands.
- Harness configurability (Appendix A.3): the ACI is defined by a single config with four component categories: prompt templates, command files (bash/Python sources whose docstrings become in-prompt documentation), control flow (`parse_command`, `parse_function`, `history_processor`), and environment variables (pp. 21-22). Context management is a class selected via `history_processor`, invoked per turn to build the literal history fed to the model (Section A.3, p. 24). "Iteratively refining the configuration file is the main way we achieved better agent performance" (Section A.3, pp. 21).
- Environment: heavily influenced by InterCode; uses Docker containers "to ensure reproducible and safe execution", and the Dockerfile can be swapped for other codebases/languages (Section A.2, p. 20). Three modules: environment, agent (renders the ACI), logging into trajectories and patch files (Section A.2, p. 20).

## Key claims with anchors

- Claim 1 (p. 1): "ACIs tailored specifically for LMs outperform existing user interfaces (UIs) designed for human users, such as the Linux shell." Interface design is treated as a first-order factor: "careful ACI design can substantially improve LM agent performance without modifying the underlying LM's weights" (p. 1).
- Claim 2 (p. 5): "SWE-agent w/ GPT-4 Turbo achieves the best performance all-around, successfully solving 12.47% (286/2,294) of the full SWE-bench test set and 18.00% (54/300) of the Lite split."
- Claim 3 (p. 5): "An LM-friendly ACI's value is confirmed by SWE-agent's 64% relative increase compared to Shell-only, both with GPT-4 Turbo."
- Claim 4 (p. 5, Table~3 p. 6): removing the edit command drops Lite performance to "10.3% ↓ 7.7"; disabling linting drops it to "15.0% ↓ 3.0"; a UI-inspired iterative search interface (12.0%) performs worse than no added search tools at all (15.7%).
- Claim 5 (p. 8): editing remains hard: 1,185 of 2,294 instances (51.7%) have 1+ failed edits; "Any attempt at editing has a 90.5% chance of eventually being successful. This probability drops off to 57.2% after a single failed edit."
- Claim 6 (p. 8): "agents succeed quickly and fail slowly": successful runs finish with median cost $1.21 and 12 steps vs mean $2.52 and 21 steps for unsuccessful runs; 93.0% of resolved instances submit before exhausting budget vs 69.0% overall.
- Claim 7 (p. 3, stated as the fourth design principle): "Guardrails mitigate error propagation and hasten recovery."
- Claim 8 (Section~6.2, p. 9): "To the best of our knowledge, SWE-agent is the first work to explore language agents for end-to-end software engineering (SE)."
- Claim 9 (p. 20): guardrails trade flexibility for safety; the edit guardrail "forces some edits to be done in a particular order" (e.g., removing a parameter header and all its references must be coordinated). "Deciding whether to introduce a guardrail depends on how well it reduces common model errors compared to whether such restrictions hamper models' preferred workflows."

Source claims end here. Relevance to the brief is my inference, given separately below.

## Evaluation and evidence

- Benchmarks (Section~4): SWE-bench, "2,294 task instances from 12 different repositories of popular Python packages"; ablations on SWE-bench Lite, "a canonical subset of 300 instances ... focus[ed] on evaluating self-contained functional bug fixes"; plus HumanEvalFix, "a short-form code debugging benchmark" (pp. 4-5). Dataset table: SWE-bench released "10/10/2023", MIT license, Test 2294 / Lite 300 / Dev 225, Python only; HumanEvalFix released "07/23/2023", MIT, Test 164 (Table~12, p. 37). SWE-bench is valued because "performance is based on rigorous, execution-based evaluation with human-written unit tests" (Section~6.1, p. 9).
- Models: GPT-4 Turbo (`gpt-4-1106-preview`) and Claude 3 Opus (`claude-3-opus-20240229`), chosen after Llama 3 and DeepSeek Coder performed "subpar" in the agent setting; context windows 128k and 200k tokens (Section~4, p. 5).
- Baselines: (1) non-interactive RAG with BM25 retrieval from Jimenez et al.; (2) "Shell-only", an interactive Linux-shell agent adapted from InterCode (Section~4, p. 5).
- Metrics: "% Resolved or pass@1" and "$ Avg. Cost" averaged over resolved instances; per-instance budget $4, after which existing edits are auto-submitted (Section~4, p. 5).
- Main results (Table~1, p. 6), % Resolved and $ Avg. Cost, full / Lite:
  - RAG w/ GPT-4 Turbo: 1.31 / $0.13; Lite 2.67 / $0.13
  - RAG w/ Claude 3 Opus: 3.79 / $0.25; Lite 4.33 / $0.25
  - Shell-only w/ GPT-4 Turbo: full results not reported ("-"); Lite 11.00 / $1.46; w/o Demonstration Lite 7.33 / $0.79
  - SWE-agent w/ GPT-4 Turbo: 12.47 / $1.59; Lite 18.00 / $1.67
  - SWE-agent w/ Claude 3 Opus: 10.46 / $2.59; Lite 13.00 / $2.18
  - Prose: vs RAG on Lite, SWE-agent is "8-13x more costly but yields a 6.7-fold improved % Resolved rate" (p. 5). Prior best resolve rate was 3.8% by a non-interactive retrieval-augmented system (p. 1).
- HumanEvalFix (Table~2, p. 6), pass@1 Python/JS/Java: CodeLLaMa-instruct-13B 29.2/19.5/32.3; GPT-4 47.0/48.2/50.0; DeepseekCoder-CodeAlpaca-6.7B 49.4/51.8/45.1; WaveCoder-DS-6.7B 57.9/52.4/57.3; SWE-agent w/ GPT-4 Turbo 87.7/89.7/87.9. The abstract reports 87.7% (p. 1); Section~5 prose says "88.3% pass@1 rate" (p. 5), which does not match any column of Table~2; see Limitations.
- ACI ablations on SWE-bench Lite (Table~3, p. 6): Editor: `edit` action 15.0 ↓ 3.0 (relative to the full interface), w/ linting 18.0, No edit 10.3 ↓ 7.7. Search: Summarized 18.0, Iterative 12.0 ↓ 6.0, No search 15.7 ↓ 2.3. File viewer window: 30 lines 14.3 ↓ 3.7, 100 lines 18.0, Full file 12.7 ↓ 5.3. Context: Last 5 Obs. 18.0, Full history 15.0 ↓ 3.0, w/o demo. 16.3 ↓ 1.7.
- Search interface finding: with iterative (Vim/VSCode-style) search, agents "tend to look through every match exhaustively, calling next until each result has been inspected", which "can exhaust an agent's cost budget or context window" (Section~5.1, p. 6).
- Editing finding: shell editing (redirection, `sed`) is inefficient, error-prone, and silent; "both strategies lack immediate feedback about file updates" (Section~5.1, p. 6). "Either too little content (30 lines, 14.3% ↓ 3.7) or too much (entire file, 12.7% ↓ 5.3) lowers performance" (p. 7).
- Guardrail finding: the lint gate "improves performance considerably (without linting, 15.0% ↓ 3.0)" (Section~5.1, p. 7).
- Agent behavior (Section~5.2, pp. 7-8): trajectories begin with reproduction (`create`) or localization (`find_file`/`search_dir`); from turn 5 onward the dominant actions are `edit` and `python` ("edit, then execute" loops); "a non-trivial minority of edit actions raise a linting error; out of 2,294 task instances, 1,185 (51.7%) ... have 1+ failed edits"; recovery odds decline with accumulated failures; failure-mode categorization (GPT-4o auto-labeling, agreeing with authors on 87% of a hand-labeled validation set) finds ~half (52.0%) of unresolved instances are Incorrect or Overly Specific Implementation and 23.4% are cascading failed edits (Figure~8, Table~9, pp. 8, 34-35).
- Variance and pass@k (Table~10, p. 35): six Lite runs gave 17.33, 18.00, 18.00, 18.67, 17.33, 18.33, average "17.94±0.49" (rendered as 17.94 0.49 in extraction); pass@1 through pass@6: 17.94, 23.89, 27.35, 29.67, 31.33, 32.67.
- Hyperparameter sweep (Section B.1, Table~5, p. 25): over temperature/window/history on 37 dev instances; best GPT-4 Turbo config "temperature of 0.0, window length of 100 and history set to last five observations" at 15.1%; the same 0.0/100/Last-5 config used for test runs.
- Trajectory statistics (Section B.3.1, p. 26): on the full test set SWE-agent w/ GPT-4 Turbo takes "an average of 14.71 turns to finish a trajectory, with a median of 12 turns and 75% of trajectories being completed within 18 turns."
- Localization comparison (Section B.9, p. 37): F1 of edited/removed files vs gold patch: SWE-agent w/ GPT-4 Turbo 59.05% vs BM25 w/ Claude 3 Opus 45.47%.
- Episode endings (Table~13, pp. 37-38): for SWE-agent w/ GPT-4 Turbo on full SWE-bench, "14.3% of task instances that end with a submit are resolved, which is much higher than 3.1% for those finishing on exit_cost."

## Limitations

- Model scope: the ACI was "developed for GPT-4 Turbo" (p. 1); portability to Claude 3 Opus is shown, but other tried models (Llama 3, DeepSeek Coder) were "subpar", partly due to small context windows (p. 5). Interface choices are optimized against one or two frontier LMs and may not transfer to other models (the paper itself frames design as complementing a fixed LM's limitations, p. 2).
- Ablation scale and statistics: ablations run on 300 Lite instances (p. 1) and the hyperparameter sweep on only 37 dev instances (Section B.1, p. 25), with ACI design driven by qualitative analysis of "hand-picked examples" plus the sweep (Section~4, p. 5). No significance tests or error bars accompany Table~3; the six-run Lite variance of ±0.49 (Table~10, p. 35) implies several Table~3 deltas (e.g., 1.7-3.7 points) sit within roughly one to a few standard deviations of run noise (my observation, not the authors').
- Cost: the interactive agent is "8-13x more costly" than RAG for a 6.7-fold resolve improvement (p. 5); runs are capped at $4 per instance (p. 5).
- Internal number inconsistency: Section~5 states "88.3% pass@1 rate" on HumanEvalFix (p. 5) while the abstract (p. 1) and Table~2 (p. 6) give 87.7 for Python; I could not identify what 88.3 corresponds to in the extracted text.
- Weakly specified headline delta: the introduction's "10.7 percentage points more instances than the baseline agent" (p. 1) has no explicit baseline; Table~1 (p. 6) implies it is Shell-only without demonstration (7.33 to 18.00), my inference.
- Guardrail costs acknowledged by the authors: the edit gate "forces some edits to be done in a particular order" (p. 20), and the 50-result search cap can force extra, expensive re-queries (p. 20).
- Assumption behind lint gating: "the original codebase associated with each task instance is well-formed" (p. 18); in codebases with pre-existing syntax errors the gate could block legitimate edits (my inference).
- Failure analysis relies on GPT-4o auto-labeling with 87% agreement against author labels on a 15-instance validation set (pp. 8, 34-35), and covers only Lite unresolved trajectories (n=248, Section B.4, p. 32).
- Benchmark scope: SWE-bench is Python-only across 12 repositories and resolved by human-written unit tests (Section~4 p. 4-5; Section~6.1, p. 9); success on issue-fixing may not generalize to feature development or other languages.
- Safety is addressed only via Docker containers for "reproducible and safe execution" (Section A.2, p. 20); there is no permission model, approval flow, or sandboxing policy beyond the container.

## Relevance to the brief

All of the following is my inference; no statement here is a source claim.

- Directly frames RQ2 (what components make up a coding-agent harness): the ACI decomposes a harness into exactly the brief's dimensions, namely tools/commands, feedback formatting, context/history management (compaction ancestor: collapse observations older than the last 5, p. 4), and loop control (thought+action parsing, format-error retry, Section~3 p. 4 and Appendix C pp. 39-44). This is the vocabulary for comparing Claude Code, Codex, and OpenCode tool designs.
- Evidence for treating tool design as first-order: the same fixed LM gains 64% relative over Shell-only just from the interface (p. 5), and individual choices move Lite results by 3-8 points (Table~3, p. 6). The synthesis can use this to justify why apply-patch vs line-edit vs shell-only tooling is a real point of comparison between the three systems.
- Guardrail principle maps onto the capability/safety tradeoff (RQ3): SWE-agent's lint-gated `edit` (reject, show before/after, ask to retry, pp. 4, 19) is a content-level guardrail inside the tool, distinct from OS-level sandboxes; the paper names the flexibility cost explicitly (p. 20). Useful framing for whether Codex/OpenCode/Claude Code guardrails live in the tool (lint/apply-patch validation), the harness (permissions), or the OS (sandbox).
- Feedback-conciseness findings (50-result search cap, 100-line viewer window, omitted-line markers) anticipate output truncation and context-budget machinery in modern harnesses; the "too little or too much context lowers performance" result (p. 7) motivates compaction design.
- Configurability precedent: the single-config ACI (prompt templates, command files, control flow, env vars, pp. 21-22) prefigures harness config surfaces; comparisons in the report can note which of these four categories each system exposes.
- Leaves open for this study: permission/sandbox policy beyond one container, multi-model generality at 2026 capability levels, memory files and persistent state, extensibility (MCP/plugins/hooks), and any notion of human approval. Those are covered by the codebase and docs entries, not by this paper.

## Quotables for the report

- "LM agents represent a new category of end user, with their own needs and abilities." (p. 2) Use to motivate why harnesses are built for model users, not humans.
- "ACIs tailored specifically for LMs outperform existing user interfaces (UIs) designed for human users, such as the Linux shell." (p. 1) Framing sentence for the claim that interface design is a first-order factor.
- "The ACI uses guardrails to prevent common mistakes, and an agent receives specific, concise feedback about a command's effects at every turn." (p. 1) Definition of the guardrail-plus-feedback pattern.
- "Building in guardrails, such as a code syntax checker that automatically detects mistakes, can help agents recognize and quickly correct errors." (p. 3) Anchor for the lint-gated edit discussion.
- "An LM-friendly ACI's value is confirmed by SWE-agent's 64% relative increase compared to Shell-only, both with GPT-4 Turbo." (p. 5) The quantitative core of the first-order-factor claim.
- "We show that crafting LM-centric interactive components has meaningful effects on downstream task performance." (p. 1) Closing framing line.
