# Synthesis: combined study (harness architecture + open-source model support)

Study: `2026-08_coding-agents-harnesses-and-open-models`, merged on
2026-08-20 from `2026-08_coding-agent-harnesses` (RQ1–RQ4) and
`2026-08_open-source-model-compat` (RQ5–RQ7). Full per-part matrices,
conflict registers, and gap registers are preserved verbatim in
`_synthesis-harnesses.md` (eight-dimension comparison) and
`_synthesis-compat.md` (compatibility matrix plus server-contract bar).
This file carries only what the merge adds: the cross-reading, the
combined gap register, and the pointer map into the integrated report.

Pins (unchanged across both studies): codex `af70018`, opencode
`d545d8fb` (dev), claude-code `c3d2e35` (surface only; core closed).
Docs snapshots fetched 2026-08-20.

## Cross-reading: Part II is the stress test of Part I's config dimension

1. The provider-plumbing findings of Part II do not add a ninth
   dimension; they sharpen the configuration-and-providers dimension of
   Part I. Part I found three cultures (narrow reserved providers,
   widest runtime-installable provider layer, closed loader); Part II
   shows each culture's open-model consequence exactly where Part I
   would predict it:
   - Codex: reserved provider IDs plus a Responses-only wire become two
     native local-server entries (Ollama, LM Studio) with a version
     gate, and a hard refusal of everything else
     (codexConfigProviders + codexOssProviders).
   - OpenCode: the widest provider layer becomes the widest open-model
     acceptance, and Part I's permissive configuration culture
     reappears as permissive accounting defaults (zero limits silently
     disable compaction or balloon output requests)
     (opencodeConfigProviders + opencodeOssProviders +
     opencodeModelGating).
   - Claude Code: the closed loader of Part I stays closed for model
     wiring; Part I's "advisory context vs enforcement" split reappears
     as documented Anthropic-cloud enforcement plus pass-through
     variables whose wire behavior is unattested
     (claudeCodePluginSurface + claudeCodeModelDocs +
     claudeCodeBedrockDocs).

2. The patch-tool story is the same fact seen twice. Part I: OpenCode
   ports the Codex `apply_patch` format and selects it by model ID:
   `gpt-*` except `gpt-4`/`oss`. Part II: for open models that gate
   resolves to the edit/write path (OpenCode) or to `apply_patch` not
   being registered at all (Codex fallback metadata). One model-ID
   gate, three downstream consequences; this is the single cleanest
   thread through the combined study (codexToolsPatch, opencodeTools,
   codexOssProviders, opencodeModelGating).

3. Compaction findings compose. Part I established the trigger
   philosophies (Codex fraction of a 95% window; OpenCode reserved
   buffer min(20,000, maxOutputTokens); Claude Code undisclosed).
   Part II adds what happens when the accounting inputs are wrong or
   absent: Codex's fallback assumes a 272,000-token window; OpenCode
   disables auto-compaction at `limit.context === 0`; Claude Code can
   defer window enforcement to the server's too-long error, which fails
   when a gateway rewrites the error. For an open-model user, the
   Part I constants only matter after the Part II defaults are fixed
   by hand (codexContextCompaction, opencodeContextCompaction,
   codexOssProviders, opencodeModelGating, claudeCodeModelDocs).

4. The safety findings of Part I are untouched by Part II, with one
   interaction worth recording: every open-model path studied stays
   inside the agent's existing permission machinery. Codex's
   OSS provider entries carry no auth (env_key None,
   requires_openai_auth false), which is a localhost-shaped trust
   decision consistent with Part I's trust-gated configuration
   (codexSandboxPermissions + codexOssProviders).

5. Wire protocol is the variable that decides Part II's matrix, and
   Part I is what explains why each agent committed the way it did:
   Codex's protocol-first interface culture (one JSON-RPC protocol for
   every frontend) is the same instinct as pinning the Responses wire
   end to end; OpenCode's server-first culture (TUI as client of a
   local HTTP server, 24 provider packages) is the same instinct as
   accepting any chat-completions endpoint
   (codexInterfaces + opencodeInterfaces + part-II matrix).

## Combined gap register (carried into the integrated report)

Part I gaps (unchanged): Claude Code numeric compaction thresholds,
turn-loop implementation, full tool registry, provider plumbing,
sandbox enforcement internals; OpenCode permission merge precedence and
runtime enforcement of several schema defaults; Codex remote model
catalog and enterprise cloud-bundle contents. All `[EVIDENCE NEEDED]`;
the absence of an OS sandbox in the pinned OpenCode tree is a
searched-scope result, not a gap.

Part II additions:
- Codex: whether Ollama >= 0.13.4 and LM Studio accept every field
  Codex sends (tools JSON, parallel_tool_calls, reasoning fields);
  whether the models-catalog refresh decodes against a plain
  `/v1/models` listing `[EVIDENCE NEEDED]`.
- OpenCode: production models.opencode.ai content (fixture-only
  evidence); wire behavior inside @ai-sdk/openai-compatible; which
  compaction path the default run uses `[EVIDENCE NEEDED]`.
- Claude Code: wire shape of gateway traffic; whether any
  Anthropic-compatible server actually drives a session `[EVIDENCE
  NEEDED]`.
- Ollama current-release behavior beyond the 2024 post and the Codex
  version gate: not snapshot-covered.
- vLLM docs could not be re-located after a site move; the generic bar
  is carried by llama.cpp and LM Studio alone.

## Pointer map into the integrated report

- Eight-dimension decomposition, summary table, anatomy figure: report
  Section "What makes a coding-agent harness" (Part I of the report).
- Turn loops, tools, compaction, safety, extensibility, config,
  state/interfaces: report Part I findings, one section per dimension;
  anchors identical to `_synthesis-harnesses.md`.
- Server-contract bar and protocol figure: report Part II "What the
  servers themselves provide".
- Compatibility matrix and support graph: report Part II "The matrix".
- Combined discussion (this cross-reading): report "Synthesis" section.
