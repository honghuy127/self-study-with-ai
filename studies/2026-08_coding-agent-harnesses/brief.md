# Brief: Coding-agent harnesses: Claude Code, Codex, and OpenCode

## Question

- Primary question: How do Claude Code, Codex, and OpenCode implement their coding-agent harnesses, and where do they genuinely differ?
- Secondary questions:
  - What components make up a coding-agent harness in general (turn loop, tools, context management, permissions, extensibility)?
  - How does each system trade capability against safety in shell and file access?
  - What does Claude Code's closed core reveal through its docs, plugin surface, and third-party teardowns?

## Scope

- In scope: harness machinery at the pinned local checkouts: agent/turn loop, tool design and apply-patch strategy, context management and compaction, memory files, permissions and sandboxing, MCP/plugins/hooks/subagents, configuration, session state and rollout, interfaces (TUI/ACP/LSP). Official docs for all three systems. A small literature set (ReAct, SWE-agent/SWE-bench) framing what a coding agent is. Third-party Claude Code teardowns as context only, `tier: blog`.
- Out of scope: model capability and benchmark comparisons between the underlying LLMs; CLI UX polish beyond harness architecture; paid or cloud-only features except where they form the harness boundary (e.g., handoff to cloud execution).
- Audience: future me, choosing or building agent harnesses.
- Deadline: none

## Depth

- Depth: `full`
- Deliverable: LaTeX technical report plus beamer slide deck.

## Prior understanding

- What you already know: LLM tool-use loops, MCP basics, hands-on experience using these CLIs.
- Repos, notes, glossary pages to reuse: local clones at `/Users/hong.huy.nguyen/Work/Code/references/coding-agents/{claude-code,codex,opencode}`. Glossary and knowledge pages to be extended by this study.

## Constraints

- Sources: open-source repositories (primary), official docs (primary), small preprint set for framing, third-party teardowns limited to `tier: blog` and never used for strong claims.
- Experiments: static traces only (control flow, tool schemas, policy extraction), recorded as artifacts under `experiments/`; no live API runs.
- Anything prohibited: running the agent CLIs against paid APIs; claims about code outside the pinned commits.

## Definition of done

- [ ] Report builds clean and lint passes
- [ ] Every non-trivial claim traces to an eligible note or verified claim; code claims resolve to `file:line` at the pinned commits
- [ ] Comparison matrix in `_synthesis.md` has no blank cells (grounded finding or explicit gap marker)
- [ ] Glossary, knowledge page, and library.bib merged on completion
