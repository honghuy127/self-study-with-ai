---
# Note for the MinusX blog teardown of Claude Code (snapshot:
# studies/2026-08_coding-agent-harnesses/sources/docs/minusXClaudeCodeTeardown.html).
# The full article body was read from the snapshot; the Appendix's collapsed
# panels ("Main Claude Code System Prompt", "All Claude Code Tools") contain no
# body text in the static HTML and could not be consulted. Anchors cite the
# blog's section headings and their heading ids, figure captions, the top Note
# callout, the intro paragraphs, and the article byline. Every claim below is
# the blog author's assertion, reported without asserting accuracy; per the
# registry's provenance rules this source may only support hedged contextual
# claims about the closed core.
source_key: "minusXClaudeCodeTeardown"
read_date: "2026-08-20"
confidence: "high"    # the article body in the snapshot was read in full; trust in the blog's underlying claims is low (see Limitations)
relevance: "2"        # useful context for RQ4; cannot bear strong claims (registry: context only)
---

# Notes: What makes Claude Code so damn good (and how to recreate that magic in your agent)!?

## Source identification

- Key: minusXClaudeCodeTeardown
- Authors, year, venue: vivek (MinusX), 2025, MinusX blog (third-party
  teardown). Article byline in the snapshot: "vivek / 2025-08-21 / 57 min
  read / AI & ML"; the byline name links to https://x.com/nuwandavek and the
  head carries `article:published_time` "2025-08-21", `article:author`
  "vivek", `twitter:creator` "@minusxai" (Article byline; snapshot `<head>`).
- Tier: blog
- URL / DOI: https://minusx.ai/blog/decoding-claude-code/ (snapshot:
  `sources/docs/minusXClaudeCodeTeardown.html`; the head's canonical link
  confirms the same URL).
- Snapshot coverage: the complete article body, figure captions, and head
  metadata. The Appendix section contains two collapsed panels labeled "Main
  Claude Code System Prompt" and "All Claude Code Tools" whose body text is
  not present in the static HTML (rendered via client-side toggles), so the
  full prompt and tool texts the blog references were not consulted
  (Section "Appendix", #appendix).

## Problem and motivation

The post states its question as "What makes Claude Code so good, and how can
you give a CC-like experience in your own chat-based-LLM agent?" (Intro,
paragraph 2). The author claims Claude Code "just simply works" because it
"has been crafted with a fundamental understanding of what the LLM is good at
and what it is terrible at", and that its control loop "is extremely simple
to follow and trivial to debug" (Intro, paragraph 1). The post explicitly
disclaims being an architecture dump: it is "a guide for building delightful
LLM agents, based on my own experience using and tinkering with Claude Code
over the last few months (and all the logs we intercepted and analyzed)"
(Note callout, top of article). Its claimed evidentiary basis is network
interception: "Sreejith wrote a logger that intercepts and logs every network
request made" (Intro, paragraph 2).

## Method or core idea

Method the blog claims (observation side):

- A custom logger that "intercepts and logs every network request" from
  Claude Code (CC), analyzed over the author's "extensive use over the last
  couple of months" at MinusX (Intro, paragraph 2). No further method detail
  (capture scope, CC version, request counts, measurement technique) appears
  anywhere in the snapshot; see Limitations.
- Evidence is presented through three figures: prompts.png, captioned "You
  can clearly see the different Claude Code updates" (figure caption before
  TL;DR); tools.png, captioned "Edit is the most frequent tool, followed by
  Read and ToDoWrite" (figure caption before TL;DR); control_loop.gif
  (Section~1.1, #1-control-loop-design). The figure contents themselves are
  images and were not independently verifiable beyond the captions.

Core ideas the blog prescribes (advice side), organized by its TL;DR
(Section "How to build a Claude Code like agent: TL;DR",
#how-to-build-a-claude-code-like-agent-tldr):

- Overarching rule: "Keep Things Simple, Dummy"; complexity such as
  multi-agents, agent handoffs, or complex RAG search "only makes debugging
  10x harder" (TL;DR).
- 1. Control Loop: 1.1 keep one main loop with at most one branch and one
  message history; 1.2 use a smaller model for everything (TL;DR, items 1.1,
  1.2).
- 2. Prompts: 2.1 the claude.md context-file pattern; 2.2 special XML tags,
  markdown, and many examples (TL;DR, items 2.1, 2.2).
- 3. Tools: 3.1 LLM search over RAG; 3.2 mix of low-level and high-level
  tools; 3.3 let the agent manage its own todo list (TL;DR, items 3.1, 3.2,
  3.3).
- 4. Steerability: 4.1 tone and style sections; 4.2 "PLEASE THIS IS
  IMPORTANT" style emphasis; 4.3 write out the algorithm with heuristics and
  examples (TL;DR, items 4.1, 4.2, 4.3).

## Key claims with anchors

Claims the blog reports as observations from its intercepted logs (harness
mechanics). All are the blog's assertions, not established facts:

- Claim 1 (Section~1.1, #11-keep-one-main-loop): "Claude Code has just one
  main thread"; it "maintains a flat list of messages" and only periodically
  uses other prompt types "to summarize the git history, to clobber up the
  message history into one message or to come up with some fun UX elements".
- Claim 2 (Section~1.1): hierarchical tasks are handled "by spawning itself
  as a sub-agent without the ability to spawn more sub-agents"; "There is a
  maximum of one branch, the result of which is added to the main message
  history as a 'tool response'". These are the author's inferences from
  traffic, not verified against code.
- Claim 3 (Section~1.2, #12-use-a-smaller-model-for-everything): "Over 50%
  of all important LLM calls made by CC are to claude-3-5-haiku", used "to
  read large files, parse web pages, process git history and summarize long
  conversations", and to produce the one-word processing label "literally
  for every key stroke". "Important LLM calls" is never defined.
- Claim 4 (Section~2, #2-prompts-1; Section~3, #3-tools-1; Section~2.1):
  "The system prompt is ~2800 tokens long, with the Tools taking up a whopping
  9400 tokens"; "The user prompt always contains the claude.md file, which
  can typically be another 1000-2000 tokens"; "CC sends the entire contents
  of the claude.md with every user request".
- Claim 5 (Section~2; Section~2.2): the system prompt contains sections "on
  tone, style, proactiveness, task management, tool usage policy and doing
  tasks", plus "the date, current working directory, platform and OS
  information and recent commits". Markdown headings listed: Tone and style,
  Proactiveness, Following conventions, Code style, Task Management, Tool use
  policy, Doing Tasks, Tools (Section~2.2).
- Claim 6 (Section~2.2, #22-special-xml-tags-markdown-and-lots-of-examples):
  CC uses XML tags extensively, including `<system-reminder>` (quoted
  example: the empty-todo-list reminder beginning "This is a reminder that
  your todo list is currently empty") and `<good-example>`/`<bad-example>`
  (quoted example contrasting `pytest /foo/bar/tests` with
  `cd /foo/bar && pytest tests`).
- Claim 7 (Section~3.1, #31-llm-search---rag-based-search): CC rejects RAG
  and "searches your code base just as you would, with really complex
  `ripgrep`, `jq` and `find` commands"; "Sometimes it ends up reading whole
  files with a smaller model."
- Claim 8 (Section~3.2, #32-how-to-design-good-tools-low-level-vs-high-level-tools):
  tool levels are "low level (Bash, Read, Write), medium level (Edit, Grep,
  Glob) and high level tools (Task, WebFetch, exit_plan_mode)"; the stated
  trade-off is "how often you expect your agent to use the tool vs accuracy
  of the agent in using the tool". Full roster listed: Task, Bash, Glob,
  Grep, LS, ExitPlanMode, Read, Edit, MultiEdit, Write, NotebookEdit,
  WebFetch, TodoWrite, WebSearch, plus MCP-provided `mcp__ide__getDiagnostics`
  and `mcp__ide__executeCode`.
- Claim 9 (Section~3.3, #33-let-the-agent-manage-a-todo-list): "CC uses an
  explicit todo list, but one that the model maintains", is "heavily prompted
  to refer to the todo list frequently", and leverages "the model's
  interleaved thinking abilities to either reject or insert new todo items on
  the fly".
- Claim 10 (tools.png caption, before TL;DR): "Edit is the most frequent
  tool, followed by Read and ToDoWrite".
- Claim 11 (Section~4.1, #41-tone-and-style; Section~4.2,
  #42-this-is-important-is-still-state-of-the-art): quoted prompt excerpts,
  including "IMPORTANT: You should NOT answer with unnecessary preamble or
  postamble", "Only use emojis if the user explicitly requests it",
  "IMPORTANT: DO NOT ADD ***ANY*** COMMENTS unless asked", "VERY IMPORTANT:
  You MUST avoid using search commands like `find` and `grep`. Instead use
  Grep, Glob, or Task to search", and "IMPORTANT: You must NEVER generate or
  guess URLs for the user unless you are confident that the URLs are for
  helping the user with programming."

Claims that are the author's interpretations or recommendations (opinions,
not observations):

- "Debuggability >>> complicated hand-tuned multi-agent lang-chain-graph-node
  mishmash" and "I highly doubt your app needs a multi-agent system"
  (Section~1.1).
- Small models are "70-80% cheaper than the standard ones (Sonnet 4,
  GPT-4.1)" so "Use them liberally!" (Section~1.2).
- RAG "introduces new (and more importantly, hidden) failure modes" around
  similarity function, reranker, chunking, and large JSON or log files
  (Section~3.1).
- "'THIS IS IMPORTANT' is unfortunately still state of the art" for steering
  (Section~4.2); avoid "a big soup of Dos and Don'ts" in favor of written-out
  algorithms (Section~4.3).
- Watching BigLab prompts helps because steering is "trying to reverse
  engineer their post-training / RLHF data distribution" (Bonus section,
  #bonus-why-pay-attention-to-biglab-prompts).
- "Extreme scaffolding frameworks will hurt more than help you" (Conclusion,
  #conclusion).

Claims marked speculative (by the blog or by me):

- "this is RL learnable - something BigLabs are already working on"
  (Section~3.1): speculation about labs' training plans, no evidence given.
- Per-keystroke haiku labeling: "literally for every key stroke!"
  (Section~1.2): hyperbolic; no measurement shown.
- The subagent recursion ban and one-branch maximum (Section~1.1): inferred
  from traffic without code evidence; the blog gives no mechanism.
- The attribution of CC's quality partly to "the new Claude 4 model
  (especially interleaved thinking)" (Intro, paragraph 1): author
  interpretation.
- The "Camera vs Lidar of the LLM era" comparison for LLM search vs RAG
  (Section~3.1): the author says "I'm only half joking".

## Evaluation and evidence

There is no formal evaluation (no datasets, baselines, or metrics beyond the
figures). Values copied character-exact from the snapshot:

- "Over 50% of all important LLM calls made by CC are to claude-3-5-haiku."
  (Section~1.2)
- Smaller models are "70-80% cheaper than the standard ones (Sonnet 4,
  GPT-4.1)". (Section~1.2)
- System prompt "~2800 tokens", tools "a whopping 9400 tokens", claude.md
  "another 1000-2000 tokens". (Section~2; Section~3)
- Byline: "2025-08-21", "57 min read" (Article byline); the post
  self-describes as "~2k words long" (Note callout), which conflicts with the
  57-minute reading time.
- Figure captions: "You can clearly see the different Claude Code updates."
  and "Edit is the most frequent tool, followed by Read and ToDoWrite"
  (image captions, before TL;DR).
- The blog names no API endpoints, hosts, headers, or telemetry flows.
  [CITATION NEEDED] for the CC version observed, capture dates, request
  counts, token-counting method, and the definition of "important LLM calls":
  I looked in the Intro, Section~1, the Bonus section, and the Appendix
  toggles; none of it is stated in the snapshot.

## Limitations

Plainly stated: this is an unverifiable third-party teardown. Every claim in
this note is the blog's assertion; none of it could be independently
confirmed from the snapshot, and per the registry's provenance rules the
source may only support hedged, contextual statements about Claude Code's
closed core in the report. Specific weaknesses:

1. No method disclosure: the CC version, capture window, traffic volume, user
   workload, and the measurement procedures behind the token counts, tool
   frequencies, and the "Over 50%" haiku figure are never given (Intro and
   throughout; see Evaluation). Reproduction or falsification is impossible
   from the post.
2. Single-site sample: the evidence is one company's intercepted traffic from
   heavy use by its own staff in the months before 2025-08-21. Generalization
   to other users or to 2026-era Claude Code is unsupported; the blog's own
   prompts.png caption reports visible version drift within the capture
   window.
3. Appendix evidence absent from the snapshot: the "Main Claude Code System
   Prompt" and "All Claude Code Tools" collapsed panels (Section "Appendix")
   contain no body text in the static HTML, so the quoted prompt excerpts
   (Sections 2.2, 4.1, 4.2) and the tool roster (Section~3.2) cannot be
   re-checked against the full artifacts; they may be partial, edited, or
   outdated reproductions.
4. Internal inconsistency: "57 min read" byline versus "~2k words long"
   self-description (Article byline; Note callout).
5. Commercial interest: MinusX sells LLM agents and states "We've
   incorporated most of these into MinusX already"; the post doubles as a
   sales and recruiting funnel (Intro, paragraph 2; Conclusion). Selection and
   framing bias are plausible.
6. Prescriptive, not descriptive: the blog self-identifies as not an
   architecture dump (Note callout); much of Sections 1, 3, 4 and the TL;DR
   is advice and opinion that other builders may reasonably dispute.
7. Mechanism claims of varying status are mixed without labeling: some are
   traffic observations (tool frequency figure), some are inferences (one
   main loop, one-branch subagents), and some are speculation (RL learnability,
   per-keystroke haiku calls). This note separates them, but the blog largely
   does not.
8. Coverage gap relative to the brief's interest in network behavior and
   telemetry: despite being built on intercepted network requests, the post
   names no endpoints, hosts, or telemetry channels; it offers nothing usable
   on those dimensions.

## Relevance to the brief

My inference, separated from source claims:

- RQ4 (Claude Code's closed core): this is one of the three permitted
  context lenses. It yields hypotheses to cross-check against primary
  sources, not conclusions: single main loop with non-recursive subagents and
  one-branch depth (check against the claude-code docs subagents note and the
  plugin-surface note); a small, atomic tool roster including Grep/Glob/Edit/
  TodoWrite/Task (check names against docs and the pinned claude-code repo
  surface); CLAUDE.md contents sent with every request (check against the
  memory docs note); a `<system-reminder>` injection mechanism; and background
  routing of summarization and file-reading work to a smaller model (no
  official corroboration located yet for the last two).
- RQ1/RQ2 (comparison and harness taxonomy): hedged, the post supplies a
  third-party characterization of CC's stated design doctrine (simplicity,
  LLM-driven search instead of indexes, model-maintained todo ledger) that can
  be contrasted with the codex and opencode codebase notes. Any such contrast
  in the report must be attributed to the teardown, not asserted as fact.
- RQ3 (capability vs safety): the quoted prompt rules (prefer dedicated tools
  over raw shell search commands, never guess URLs) are weak, prompt-level
  evidence only; they say nothing about enforcement, and the permissions and
  sandboxing questions remain with the docs and codebase notes.
- Left open by this source: observed version, endpoints and telemetry (the
  tenguDecoded note covers that angle), compaction implementation, session
  storage, and permission enforcement.

## Quotables for the report

- "Over 50% of all important LLM calls made by CC are to claude-3-5-haiku."
  (Section~1.2). Suggested frame: "one third-party teardown of intercepted
  traffic reported ...~\citep{minusXClaudeCodeTeardown}"; hedge required.
- "The system prompt is ~2800 tokens long, with the Tools taking up a whopping
  9400 tokens." (Section~2). Suggested frame: characterize as the teardown's
  measurement, unverifiable.
- "Claude Code chooses architectural simplicity at every juncture - one main
  loop, simple search, simple todolist" (blockquote, TL;DR). Suggested frame:
  the author's design reading, presented as opinion.
- "There is a maximum of one branch, the result of which is added to the main
  message history as a 'tool response'." (Section~1.1). Suggested frame:
  attribute as inferred behavior, mark as unverified.
- The `<system-reminder>` empty-todo excerpt beginning "This is a reminder
  that your todo list is currently empty." (Section~2.2). Suggested frame:
  cite as a quoted artifact from the teardown; note the appendix source text
  is unavailable in the snapshot.
- "Edit is the most frequent tool, followed by Read and ToDoWrite" (tools.png
  caption). Suggested frame: teardown-reported frequency, no sample size.
