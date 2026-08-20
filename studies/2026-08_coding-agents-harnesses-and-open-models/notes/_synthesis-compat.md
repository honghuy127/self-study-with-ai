# Synthesis: open-source model compatibility (Claude Code, Codex, OpenCode)

Study: `2026-08_open-source-model-compat` (briefing). Basis: 11 notes in
`notes/` (3 codebase, 7 docs, 1 blog-context), pinned commits codex
`af70018`, opencode `d545d8fb` (dev), claude-code `c3d2e35`
(`sources/repos.yaml`), doc snapshots fetched 2026-08-20 under
`sources/docs/`. No execution; all claims static. Community router note
is hedged context and fills no matrix cell alone.

# Compatibility matrix (the deliverable shape)

| Agent | Ollama | LM Studio | Generic OpenAI-compatible server |
|---|---|---|---|
| Codex | native provider entry, `WireApi::Responses`, posts `POST /v1/responses` to `http://localhost:11434/v1/responses`; version gate rejects Ollama < 0.13.4 via `GET /api/version`; default model `gpt-oss:20b` (codexOssProviders: model-provider-info/src/lib.rs:514-521,:578-591; ollama/src/lib.rs:16,:46-70) | native provider entry, same Responses wire, `http://localhost:1234/v1/responses`; default model `openai/gpt-oss-20b`; model probe `GET {base}/models`, download via `lms get --yes`, warm-up `POST /responses` with max_output_tokens 1 (codexOssProviders: model-provider-info/src/lib.rs:514-521,:578-591; lmstudio/src/client.rs:51-77,:173-195) | via `model_providers.<name>` config entries; wire API restricted to Responses (`wire_api = "chat"` hard deserialization error); no oss entry carries auth (env_key None, requires_openai_auth false); env overrides `CODEX_OSS_BASE_URL`, `CODEX_OSS_PORT` (codexOssProviders: model-provider-info/src/lib.rs:56,:86,:487-488,:576-591,:594-615) |
| OpenCode | config-defined provider with `options.baseURL` (in-repo example `http://localhost:11434/v1`, limit context 8192 / output 2048); hosted catalog (test fixture) has `ollama-cloud` at `https://ollama.com/v1` but no bare local ollama entry; @ai-sdk/openai-compatible SDK fallback (opencodeOssProviders: provider.ts:117,:1248,:1474; test/provider/provider.test.ts:881-890; fixtures/models-api.json:75768-75774) | hosted catalog (test fixture) lists `lmstudio` provider, api `http://127.0.0.1:1234/v1`, env `LMSTUDIO_API_KEY`; otherwise same generic path (opencodeOssProviders: fixtures/models-api.json:41242-41248) | generic path for any unknown provider: `@ai-sdk/openai-compatible` factory, config keys `provider.<id>.options.{baseURL,apiKey}`, `.npm` for runtime install (`file://` allowed), `models.<id>.limit.{context,output}`; hosted catalog `models.opencode.ai/api.json`, 5-min TTL, overridable via `OPENCODE_MODELS_URL/PATH`, disable via `OPENCODE_DISABLE_MODELS_FETCH` (opencodeOssProviders: provider.ts:117-134,:1729-1746,:1813-1816; models-dev.ts:160-180,:257; flag.ts:29,:45-46) |
| Claude Code | no documented support; zero mentions of Ollama/LM Studio/open-weight in model-config and Bedrock snapshots; nearest mechanisms: `ANTHROPIC_BASE_URL` pass-through (changes where requests go, "Claude Code passes any string through without checking it"), `ANTHROPIC_CUSTOM_MODEL_OPTION` unvalidated picker entry, `CLAUDE_CODE_MAX_CONTEXT_TOKENS` applies to IDs not starting with `claude-`; gateway model discovery via gateway `/v1/models` behind `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` (claudeCodeModelDocs snapshot :23,:131,:655-661,:672,:684; claudeCodeBedrockDocs negative scope) | same as Ollama column: documentation negative scope; note LM Studio documents an Anthropic-compatible surface of its own (lmstudioServerDocs snapshot :11,:33), unverified against Claude Code | documented surface is Anthropic-model clouds only (API, Bedrock, Vertex/Agent Platform, Foundry), model IDs all `anthropic.*`; wire shape behind a custom base URL is unstated; capabilities are model-ID-gated with `_SUPPORTED_CAPABILITIES` overrides (claudeCodeModelDocs :719-723,:757-766; claudeCodeBedrockDocs :129,:230,:271-276) |

Degradation / open-model path details:

- Codex over its oss providers: fallback ModelInfo (catalog miss) sets
  `apply_patch_tool_type: None`, so apply_patch is not registered for
  default oss models (codexOssProviders: models-manager/src/model_info.rs:165;
  core/src/tools/spec_plan.rs:1112-1116). Requests still carry tools JSON,
  `tool_choice: "auto"`, `parallel_tool_calls`, schema `text.format`,
  `reasoning.summary` default auto, and `include:
  ["reasoning.encrypted_content"]` (client.rs:825-843,:892-930,:898-905;
  codex-api/src/common.rs:361-379). Fallback context accounting assumes a
  272,000-token window.
- OpenCode over open models: model-ID gate `gpt-*` except `oss` and
  `gpt-4` selects apply_patch; open models get `edit` and `write`
  (opencodeModelGating: registry.ts:297-300; edit.ts:58-59; write.ts:27-28).
  Token estimation chars/4, no tokenizer (packages/core/src/util/token.ts:3-5).
  `OUTPUT_TOKEN_MAX = 32_000`; unset output limit silently becomes 32,000
  requested tokens (transform.ts:18,:1418-1420; request.ts:129). Compaction
  reserve `min(20_000, maxOutputTokens)`; `limit.context === 0` disables
  auto-compaction entirely (session/overflow.ts:8-16,:29). Tools sent
  unconditionally (request.ts:184,:208-213); `capabilities.toolcall`
  defaults true but is write-only in every file searched. Finish reasons
  mapped stop/length/content_filter/tool_calls, else `unknown`; loop exit
  needs finish set and no open tool parts
  (packages/llm/src/protocols/openai-chat.ts:378-384; session/prompt.ts:1103-1116,:1295).
  Unknown model IDs hard-fail with fuzzy suggestions, no hidden fallback
  (provider.ts:1842-1864; prompt.ts:594-612). Stream usage forced
  (`includeUsage = true`) (provider.ts:1725-1727).
- Claude Code: capabilities (effort levels, thinking) enabled by matching
  model ID against known patterns, overridable via
  `_SUPPORTED_CAPABILITIES`; `CLAUDE_CODE_AUTO_COMPACT_WINDOW`
  (100K-1M range); `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1`
  defers compaction to a recognized too-long error, which fails "when a
  gateway rewrites the error" (claudeCodeModelDocs :616,:635-641,:655-661,:757-766).
  Bedrock feature losses: WebSearch unavailable, no Converse API support
  (claudeCodeBedrockDocs :257,:564).

# Server-side bar (RQ2), from the server-contract notes

- Baseline surface every compatible server provides: `/v1/chat/completions`
  plus `/v1/models`; Ollama's snapshot (2024, "initial compatibility")
  shows only chat completions at `http://localhost:11434`, placeholder auth,
  function calling listed as future work (ollamaCompatDocs :16,:412-450,:555-562).
- llama.cpp reference server (the generic bar): routes `/v1/models`,
  `/v1/completions`, `/v1/chat/completions` (+ `/control`), `/v1/responses`,
  `/v1/embeddings`, input-token endpoints, plus `/health`, `/props`,
  `/metrics`, slots, LoRA management, and Anthropic `POST /v1/messages`
  (llamaCppServerDocs :1236-1563). Self-limited compatibility statement:
  "no strong claims of compatibility with OpenAI API spec is being made"
  (:1272,:1303). Tools template-gated via `--jinja` (default enabled),
  `parse_tool_calls`, `parallel_tool_calls` "only supported on some models"
  (:1321-1323,:1384). Structured output: `json_object` and `json_schema`
  response_format plus server grammar flags (:1309,:562-564). Context
  reporting via usage (prompt_tokens_details.cached_tokens) and
  `n_ctx_train` in the models listing (:1260,:1414-1428).
- llama.cpp's `/v1/responses` exists but is a converter stub: "This
  endpoint works by converting Responses request into Chat Completions
  request"; no documented streaming, tools, reasoning, or
  previous_response_id for the route (llamaCppServerDocs :1454-1494).
- LM Studio: OpenAI-compatible base `http://localhost:1234/v1`
  (lmstudioChatCompletions.md :19); tools supported on
  `/v1/chat/completions` AND named on `v1/responses` (lmstudioCompatToolsDocs
  :10,:103-409); parallel calls undocumented (no `parallel` or
  `tool_choice` anywhere); streaming tool-call deltas indexed by `tc.index`
  (:1088-1102); malformed calls fall back to content (:176). Responses page
  documents streaming SSE (`response.created`, `response.output_text.delta`,
  `response.completed`), `reasoning.effort`, `previous_response_id`, and
  remote MCP tools only; no function tools, no `include`, no
  `reasoning.summary` on that page (lmstudioCompatResponsesDocs :3,:20,:26,:46-54,:63-69).
  Example model IDs `openai/gpt-oss-20b`, `ibm/granite-4-micro`.

# Cross-note connections (writer: mark each as inference where noted)

1. Codex speaks Responses to Ollama/LM Studio servers. llama.cpp documents
   `/v1/responses` (converter) and LM Studio documents a partial Responses
   surface; Ollama's pinned snapshot documents only chat completions, so
   Codex's 0.13.4 gate is consistent with Responses support landing in
   later Ollama versions (inference; the version-gate fact is code-anchored,
   the reason is not stated in code).
2. Codex sends `parallel_tool_calls`, `reasoning.summary`, and `include:
   ["reasoning.encrypted_content"]` to these servers; none of these appear
   in the LM Studio Responses page or llama.cpp Responses stub. Server
   acceptance is [EVIDENCE NEEDED] and belongs to a static-adjacent
   compatibility test this briefing does not run.
3. OpenCode's compaction disable when `limit.context === 0` interacts with
   its own config defaults (`?? 0`): a user who configures a provider
   without limits gets no auto-compaction. This is a degradation claim
   grounded entirely in code defaults.
4. Claude Code's gateway pass-through plus llama.cpp's `/v1/messages` and
   LM Studio's anthropic-compatible surface define a plausible but
   entirely unverified path; wire shape behind gateways is unstated in the
   Claude Code snapshot ([CITATION NEEDED] in claudeCodeModelDocs).
5. Community router claude-code-router claims a local gateway in front of
   Claude Code; hedged context only, never a matrix cell.

# Contradictions and drift

- Registry initially listed `src/session/compaction/overflow.ts`; actual
  file is `src/session/overflow.ts` at the pin (opencodeModelGating note);
  registry corrected during summarizing.
- Two compaction implementations coexist in opencode (v1
  `src/session/{compaction,overflow}.ts`; v2
  `packages/core/src/session/compaction.ts` used by
  `packages/core/src/session/runner/llm.ts`); which serves the default CLI
  run is unresolved ([EVIDENCE NEEDED] in opencodeModelGating). Both use a
  20,000 default buffer, so the report's claim holds for either path.
- LM Studio snapshot provenance is the docs-repo mirror (live site
  unreachable here), not the shipped site; drift unassessed (registry
  coverage limit).
- Ollama snapshot is the 2024 blog post; current-version surface beyond
  the Codex version gate is not snapshot-covered (registry coverage limit).

# Gap register (carried into report Limitations)

- Codex: whether Ollama >= 0.13.4 and LM Studio accept every field Codex
  sends (tools JSON, parallel_tool_calls, reasoning fields); whether the
  models-catalog refresh decodes against a plain `/v1/models` listing
  (expects Codex's ModelsResponse schema) [EVIDENCE NEEDED].
- OpenCode: production models.opencode.ai content (only test fixture
  verifiable); wire behavior inside @ai-sdk/openai-compatible; which
  compaction path the default run uses [EVIDENCE NEEDED]. Resolved
  2026-08-21: `stream: true` is unconditional in the openai-chat builder
  (`openai-chat.ts:359`, schema `Literal(true)` at `:487`; see
  opencodeModelGating note).
- Claude Code: everything behind the closed loader; the wire shape of
  gateway traffic; whether any anthropic-compatible server actually drives
  a Claude Code session [EVIDENCE NEEDED].
- Ollama current release behavior (beyond the 2024 post and the Codex
  version gate): not snapshot-covered.
- vLLM docs could not be located after a site move; generic bar carried by
  llama.cpp and LM Studio instead (registry coverage limit).
