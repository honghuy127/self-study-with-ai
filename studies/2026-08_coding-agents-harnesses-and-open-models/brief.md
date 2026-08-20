# Brief: Coding agents and open-source models (combined study)

This study combines two prior studies merged on 2026-08-20 (see
`study.yaml: merged_from`): `2026-08_coding-agent-harnesses` (done,
cleaned) and `2026-08_open-source-model-compat` (was in review,
unsigned). Their notes, registries, snapshots, and reviews move here;
the combined deliverable is one integrated report and one slide deck.
Gates are reset: the integrated draft needs fresh approval.

## Question

- Primary question, Part I (harness architecture): How do Claude Code,
  Codex, and OpenCode implement their coding-agent harnesses, and where
  do they genuinely differ?
- Primary question, Part II (open-model support): How compatible are
  these agents with open-source models, and through which integration
  surface (native provider code, generic OpenAI-compatible endpoint, or
  documentation only)?
- Secondary questions, Part I:
  - What components make up a coding-agent harness in general (turn
    loop, tools, context management, permissions, extensibility)?
  - How does each system trade capability against safety in shell and
    file access?
  - What does Claude Code's closed core reveal through its docs, plugin
    surface, and third-party teardowns?
- Secondary questions, Part II:
  - What is the minimum contract an OpenAI-compatible server must
    satisfy for each agent (wire API shape, tool calling, context-window
    reporting, streaming)?
  - Where does support degrade with open models: model-ID-gated features
    (patch-tool selection), context accounting defaults, compaction
    triggers, reasoning-token handling?

## Scope

- In scope:
  - Harness machinery at the pinned local checkouts: agent/turn loop,
    tool design and apply-patch strategy, context management and
    compaction, memory files, permissions and sandboxing,
    MCP/plugins/hooks/subagents, configuration, session state and
    rollout, interfaces (TUI/ACP/LSP); official docs for all three
    systems; a small literature set (ReAct, SWE-agent/SWE-bench,
    Toolformer) framing what a coding agent is; third-party Claude Code
    teardowns as context only, `tier: blog`.
  - Open-model surfaces: Ollama and LM Studio as named providers;
    generic OpenAI-compatible endpoints (llama.cpp server, vLLM,
    LiteLLM-style gateways) as configured by base URL; open-weight
    models reached through cloud APIs (e.g., Bedrock) only as context,
    not a primary surface; server-side contract traced from the
    reference servers' own documentation.
- Out of scope:
  - Model capability and benchmark comparisons between the underlying
    LLMs; CLI UX polish beyond harness architecture; paid or cloud-only
    features except where they form the harness boundary.
  - Running any agent, model, or server (static traces only, decided);
    fine-tuning; Claude Code third-party routers beyond blog-tier hedged
    context.
- Audience: future me, choosing or building agent harnesses and choosing
  an agent to point at a local model.
- Deadline: none.

## Depth

- Depth: `full` (the harness part was full; the open-model part was
  carried out at briefing depth and is retained at that evidence level
  inside Part II).
- Deliverable: one integrated LaTeX technical report (Part I harness
  architecture, Part II open-source model support) plus one beamer slide
  deck.

## Prior understanding

- What was already established in Part I extractions and is reused by
  Part II at its anchors, not re-derived:
  - Codex has exactly five built-in provider IDs: openai,
    amazon-bedrock, amazon-bedrock-runtime, ollama, lmstudio; reserved
    against override except Bedrock.
  - Codex's wire protocol is pinned to the Responses API; the chat path
    is rejected as a hard error.
  - OpenCode ships 24 bundled AI-SDK provider packages, installs
    arbitrary provider SDKs at runtime, and fetches a hosted model
    catalog (models.opencode.ai, 5-minute cache).
  - OpenCode gates its apply_patch port on gpt-* model IDs except
    gpt-4/oss; open models therefore exercise the edit/write path.
  - OpenCode estimates unknown token counts as chars/4 and defaults
    OUTPUT_TOKEN_MAX to 32,000.
  - Claude Code's loader is closed; Bedrock/Vertex environment variables
    are attested only through plugin hook surfaces.
- Repos, notes, glossary pages to reuse:
  - shared/knowledge/coding-agent-harnesses.md
  - notes/codexConfigProviders.md, notes/opencodeConfigProviders.md,
    notes/codexToolsPatch.md, notes/opencodeTools.md within this study.
- Repos: local clones at
  /Users/hong.huy.nguyen/Work/Code/references/coding-agents/{claude-code,codex,opencode}.

## Constraints

- Sources: open-source repositories and official documentation primary;
  a small preprint set for framing; third-party teardowns and community
  routers limited to `tier: blog`, hedged context only, never used for
  strong claims. No leaked-source material.
- Experiments: static traces only (control flow, tool schemas, policy
  extraction); the 300-anchor re-verification from Part I is smoke-test
  plumbing, not behavioral evidence. No live agent, model, or server
  runs; no provider installs; no model-weight downloads.
- Anything prohibited: running the agent CLIs against paid APIs; claims
  about code outside the pinned commits.

## Definition of done

- [ ] Integrated report builds clean and lint passes
- [ ] Every non-trivial claim traces to an eligible note; code claims
      resolve to `file:line` at the pinned commits
- [ ] Harness comparison matrix has no blank cells (grounded finding or
      explicit gap marker)
- [ ] Compatibility matrix covers all three agents x three surfaces
      (Ollama, LM Studio, generic OpenAI-compatible) with evidence tier
      per cell
- [ ] Glossary, knowledge page, and library.bib updated on completion
