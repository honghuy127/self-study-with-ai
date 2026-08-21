---
id: coding-agent-harnesses.eight-dimensions
question: How do coding-agent harnesses decompose, and where do Claude Code, Codex, and OpenCode converge?
prerequisites: []
source_ids: [codexRepo, opencodeRepo, claudeCodePluginSurface]
misconceptions: []
mastery:
  last_assessed: ""
  level: ""
  help: ""
review:
  next_due: ""
superseded_by: ""
---

# Coding-agent harnesses

Distilled understanding from finished studies. Agents read relevant pages
here before gathering, to avoid re-learning established results.

## The eight-dimension decomposition

A coding-agent harness decomposes into eight machinery dimensions, each
independently implemented by Claude Code, Codex, and OpenCode at pinned
versions (codex af70018, opencode d545d8f dev branch, claude-code c3d2e35):
the turn loop; the tool surface and its file-edit protocol; context
assembly and compaction; persistent memory files; permission and sandbox
policy; extensibility (hooks, plugins, skills, subagents, MCP servers);
configuration and model-provider plumbing; and session state with durable
storage and user-facing transports.

## What converges across systems

Verified against pinned checkouts and documentation snapshots of
2026-08-20:

- All three implement the same abstract prompt-sample-execute-continue
  loop, and all three encode an explicit anti-loop defense (a typed
  rejection taxonomy in Codex, an identical-call tripwire in OpenCode,
  a stop-hook cap in Claude Code).
- The patch format is converging across vendors: OpenCode ports the Codex
  `apply_patch` format verbatim in type names and selects it for `gpt-*`
  model IDs except `gpt-4`/`oss`.
- Extension vocabularies converge on the Claude Code design: Codex exports
  `CLAUDE_PLUGIN_ROOT` compatibility variables and discovers
  `.claude-plugin` manifests; OpenCode reads `.claude` skill layouts and
  CLAUDE.md files as fallbacks.
- MCP is the shared external-tool boundary in all three.
- All three gate dangerous defaults behind enterprise layers (managed
  settings, `requirements.toml`, MDM plists).

## Where they genuinely diverge

- Control flow: an abortable-task state machine (Codex) against a
  persistence-driven loop recomputed from stored messages (OpenCode)
  against an undisclosed closed loop (Claude Code).
- Tool registration: conditional per-turn registration (Codex, 32
  handler-to-tool mappings) against a fixed 17-ID array (OpenCode) against
  a partly documented inventory (Claude Code).
- Safety substrate: OS sandbox plus Starlark rule engine with
  strictest-wins aggregation (Codex) against an in-process ruleset with no
  OS sandbox in the pinned tree (OpenCode) against a Bash-scoped OS
  sandbox plus a permission layer (Claude Code).
- Compaction triggers: a fraction of the context window, 9/10 of a 95%
  default effective window (Codex) against an overflow past the input
  limit minus a reservation defaulting to min(20,000, maxOutputTokens)
  tokens (OpenCode) against undisclosed numeric thresholds (Claude Code).
- State: append-only JSONL with a repairable SQLite mirror and exact
  replay (Codex) against event-sourced SQLite with shadow-git file
  snapshots (OpenCode) against undisclosed (Claude Code).

## Reusable methodological lesson

For a closed-source system, pin the documentation snapshot date, restrict
third-party teardowns to hedged context, and record unattested internals
as "undisclosed" rather than inferring them. Documentation describes
intended behavior, not necessarily shipped behavior; cite the snapshot,
not the floating site.

Known evidential status: all findings are bounded to the pinned commits
and the 2026-08-20 documentation snapshots; no behavioral measurement was
performed in the study.

Source: studies/2026-08_coding-agents-harnesses-and-open-models, Part I
(merged 2026-08-20 from studies/2026-08_coding-agent-harnesses; codexRepo,
opencodeRepo, claudeCodeSurface, and the official documentation snapshots
in shared/library.bib).
