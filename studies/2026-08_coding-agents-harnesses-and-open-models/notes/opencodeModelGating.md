---
source_key: opencodeModelGating
read_date: "2026-08-20"
confidence: high
relevance: 3
repo: opencode
commit: d545d8fba57283528db69281f59c803c646eb7e9
---

# Notes: OpenCode open-model path behavior: patch gating by model ID, token estimation, output caps (opencode)

## Source identification

- Key: `opencodeModelGating`
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`; checkout `.git/refs/heads/dev` matches this SHA)
- Component scope: `packages/opencode/src/tool/registry.ts` (apply_patch gating), `packages/core/src/util/token.ts` plus its re-export `packages/opencode/src/util/token.ts` (chars/4 estimate), `packages/opencode/src/provider/transform.ts` (`OUTPUT_TOKEN_MAX`, request transforms), `packages/opencode/src/tool/edit.ts`, `packages/opencode/src/tool/write.ts`, `packages/opencode/src/tool/apply_patch.ts` (edit paths), `packages/opencode/src/session/overflow.ts` (compaction reserve), `packages/opencode/src/session/compaction.ts` and `packages/core/src/session/compaction.ts` (compaction sizing), `packages/opencode/src/session/prompt.ts` (model selection, loop exit), `packages/opencode/src/session/processor.ts` (finish handling), `packages/opencode/src/session/llm/request.ts` (sampling and maxOutputTokens application), and `packages/opencode/src/provider/provider.ts` (model defaults). Consulted in `packages/llm/src`: `schema/ids.ts` (FinishReason), `protocols/openai-chat.ts` (OpenAI-compatible wire mapping).
- Tier: codebase

Path correction: the registry component lists `src/session/compaction/overflow.ts`; no `compaction/` subdirectory exists at this commit. The overflow logic lives at `packages/opencode/src/session/overflow.ts` (34 lines), imported by `packages/opencode/src/session/compaction.ts:17` as `import { isOverflow as overflow, usable } from "./overflow"`.

## Purpose and role in the harness

This component set determines what an arbitrary, non-OpenAI, non-Anthropic model experiences inside OpenCode: which file-editing tools it is offered, how its token usage and context budget are approximated when the catalog has no limit data, what output cap is requested, and how the session loop decides to continue. The tool registry filters the builtin tool list per-request by model ID (`packages/opencode/src/tool/registry.ts:291-303`). Token estimation is a single global heuristic, `Math.round(input.length / CHARS_PER_TOKEN)` with `CHARS_PER_TOKEN = 4` (`packages/core/src/util/token.ts:3-5`), used by both compaction implementations; there is no tokenizer anywhere in the session path (a grep for `tiktoken|tokenizer|countTokens` across `packages/` matched only a Shiki syntax-highlight tokenizer in `packages/session-ui/src/components/markdown.worker.ts:21,118-121`, unrelated to LLM accounting). `OUTPUT_TOKEN_MAX = 32_000` (`packages/opencode/src/provider/transform.ts:18`) bounds the requested `maxOutputTokens` and the compaction reserve. The prompt loop in `packages/opencode/src/session/prompt.ts:1088-1336` drives repeated model calls and exits based on finish reasons defined by `FinishReason = Schema.Literals(["stop", "length", "tool-calls", "content-filter", "error", "unknown"])` (`packages/llm/src/schema/ids.ts:39`).

## Mechanism

### Q1. apply_patch gating by model ID

Per-request tool filtering happens in `ToolRegistry.tools(input)` (`packages/opencode/src/tool/registry.ts:291`), char-exact (`packages/opencode/src/tool/registry.ts:297-300`):

```ts
const usePatch =
  input.modelID.includes("gpt-") && !input.modelID.includes("oss") && !input.modelID.includes("gpt-4")
if (tool.id === ApplyPatchTool.id) return usePatch
if (tool.id === EditTool.id || tool.id === WriteTool.id) return !usePatch
```

- `apply_patch` is offered only when the model ID contains `gpt-` and contains neither `oss` nor `gpt-4` (substring tests, case-sensitive, on `input.modelID`, typed `ModelV2.ID` in the `tools()` signature at `packages/opencode/src/tool/registry.ts:81-83`). Tool IDs: `apply_patch` (`packages/opencode/src/tool/apply_patch.ts:22-23`), `edit` (`packages/opencode/src/tool/edit.ts:58-59`), `write` (`packages/opencode/src/tool/write.ts:27-28`).
- Exceptions therefore are IDs containing `oss` (e.g. an OSS-flavored gpt entry) and any ID containing `gpt-4` (including `gpt-4o`), which fall back to `edit`/`write`.
- Interpretation for open models: an Ollama or LM Studio model ID (e.g. `llama3.1`, `qwen2.5-coder`) contains no `gpt-` substring, so `usePatch` is false, `apply_patch` is filtered out, and `edit` plus `write` remain. The open model receives `edit` and `write`. The `edit` tool is a search-and-replace tool with `filePath`, `oldString`, `newString`, `replaceAll` parameters (`packages/opencode/src/tool/edit.ts:47-56`); an empty `oldString` is only allowed for creating a new file (`packages/opencode/src/tool/edit.ts:90-96`).
- The same filter also drops the `websearch` tool for every provider except `opencode`/`opencode-go` unless the `exa`/`parallel` runtime flags are set (`packages/opencode/src/tool/registry.ts:58-65,293-295`), so an open model behind a local provider also loses `websearch` by default.
- All other builtin tools (shell, read, glob, grep, task, fetch, todo, skill, and conditionally question/lsp/plan) pass the filter unconditionally (`packages/opencode/src/tool/registry.ts:231-249,302`).

### Q2. Token accounting for models with unknown limits

Estimator (char-exact, `packages/core/src/util/token.ts:3-5`):

```ts
const CHARS_PER_TOKEN = 4
export const estimate = (input: string) => Math.max(0, Math.round(input.length / CHARS_PER_TOKEN))
```

Re-exported verbatim at `packages/opencode/src/util/token.ts:1`. Use sites, all unconditional (no tokenizer fallback exists):

- v1 session compaction sizing: estimate of serialized model messages per tail turn (`packages/opencode/src/session/compaction.ts:220`), and per tool output during prune (`packages/opencode/src/session/compaction.ts:299`).
- v2 core compaction: request-size estimate `{system, messages, tools}` for the trigger (`packages/core/src/session/compaction.ts:83,237-241`), backward scan of serialized conversation entries for the retained tail (`packages/core/src/session/compaction.ts:149`), and a gate that skips compaction when `Token.estimate(summaryPrompt) > context - summaryOutput` (`packages/core/src/session/compaction.ts:190`).
- Test expectations confirm the arithmetic: 4,000 chars estimates to 1000 tokens, 20,000 chars to 5000, empty string to 0 (`packages/opencode/test/session/compaction.test.ts:1668-1677`).

`OUTPUT_TOKEN_MAX = 32_000` (`packages/opencode/src/provider/transform.ts:18`) is applied through (char-exact, `packages/opencode/src/provider/transform.ts:1418-1420`):

```ts
export function maxOutputTokens(model: Provider.Model, outputTokenMax = OUTPUT_TOKEN_MAX): number {
  return Math.min(model.limit.output, outputTokenMax) || outputTokenMax
}
```

- Request path: `maxOutputTokens: ProviderTransform.maxOutputTokens(input.model, input.flags.outputTokenMax)` at `packages/opencode/src/session/llm/request.ts:129`; `flags.outputTokenMax` is the environment flag `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (`packages/opencode/src/effect/runtime-flags.ts:52`), passed through when positive integer, else `undefined`, which makes the default parameter `OUTPUT_TOKEN_MAX` apply. On the OpenAI-compatible wire this becomes `max_tokens: generation?.maxTokens` (`packages/llm/src/protocols/openai-chat.ts:361`).
- Compaction reserve (v1, char-exact, `packages/opencode/src/session/overflow.ts:8-20`):

```ts
const COMPACTION_BUFFER = 20_000
// ...
const reserved =
  input.cfg.compaction?.reserved ??
  Math.min(COMPACTION_BUFFER, ProviderTransform.maxOutputTokens(input.model, input.outputTokenMax))
return input.model.limit.input
  ? Math.max(0, input.model.limit.input - reserved)
  : Math.max(0, context - ProviderTransform.maxOutputTokens(input.model, input.outputTokenMax))
```

Behavior of `min(20_000, maxOutputTokens)`:
- When `limit.output` is unset (config-defined model default is 0, `packages/opencode/src/provider/provider.ts:1531`): `Math.min(0, 32_000) || 32_000` yields 32,000, so the reserve is `min(20_000, 32_000) = 20_000`.
- When `limit.output` is huge: `maxOutputTokens` caps at 32,000 first, reserve is still 20,000.
- When `limit.output` is small and nonzero (say 8,192): reserve equals 8,192.
- `config.compaction.reserved` overrides the whole computation (`packages/opencode/src/session/overflow.ts:15`).

Overflow detection: `isOverflow` returns false outright when `model.limit.context === 0` (`packages/opencode/src/session/overflow.ts:29`), and `usable()` returns 0 for context 0 (`packages/opencode/src/session/overflow.ts:11-12`). Combined with the config default `limit.context ?? 0` (`packages/opencode/src/provider/provider.ts:1529`), an open model with no declared limits never triggers auto-compaction: the loop's pre-check (`packages/opencode/src/session/prompt.ts:1161-1168`) and the processor's post-step check (`packages/opencode/src/session/processor.ts:477-482`) both route through this `isOverflow`. The same guard exists in the v2 core path: `compactIfNeeded` returns false when `context === undefined || context <= 0` (`packages/core/src/session/compaction.ts:234-235`), with `DEFAULT_BUFFER = 20_000` there too (`packages/core/src/session/compaction.ts:12`); note the v2 trigger reserves `Math.max(output, config.buffer)` rather than a min (`packages/core/src/session/compaction.ts:237-241`).

The overflow count itself prefers real usage from the provider: `input.tokens.total || input.tokens.input + input.tokens.output + input.tokens.cache.read + input.tokens.cache.write` (`packages/opencode/src/session/overflow.ts:31-32`). The chars/4 estimator is for internal sizing (tail selection, prompt gates), not for the overflow count.

### Q3. Streaming and tool-calling assumptions

- The loop does not execute tools based on the finish reason. Tool execution is event-driven on `tool-call` / `tool-result` stream events (`packages/opencode/src/session/processor.ts:331-414`), and each step's finish reason is recorded from the `step-finish` event (`packages/opencode/src/session/processor.ts:435-456`, specifically `ctx.assistantMessage.finish = value.reason` at `packages/opencode/src/session/processor.ts:443`).
- The finish reason controls loop continuation. Loop exit (`packages/opencode/src/session/prompt.ts:1103-1116`):

```ts
// Some providers return "stop" even when the assistant message contains
// tool calls. Keep the loop running so tool results can be sent back to
// the model, but ignore cleanup-marked interrupted orphans.
const hasToolCalls =
  lastAssistantMsg?.parts.some(
    (part) => part.type === "tool" && !part.metadata?.providerExecuted && !isOrphanedInterruptedTool(part),
  ) ?? false

if (
  lastAssistant?.finish &&
  !["tool-calls"].includes(lastAssistant.finish) &&
  !hasToolCalls &&
  lastAssistant.parentID === lastUser.id
) {
```

  So the only finish string that keeps the loop running by itself is `tool-calls`; unfinished tool parts also keep it running regardless of finish.
- Within an iteration, `packages/opencode/src/session/prompt.ts:1295` computes `const finished = handle.message.finish && !["tool-calls", "unknown"].includes(handle.message.finish)`: an unrecognized finish reason (`unknown`) skips the "finished" error surfacing (content-filter handling at `packages/opencode/src/session/prompt.ts:1296-1308`) and falls through to the processor's `"continue"` outcome, then the next iteration's exit check at `packages/opencode/src/session/prompt.ts:1111-1116` breaks the loop once no tool parts remain.
- Recognized reasons are exactly `["stop", "length", "tool-calls", "content-filter", "error", "unknown"]` (`packages/llm/src/schema/ids.ts:39`). The OpenAI-compatible wire parser maps `stop`, `length`, `content_filter`, and `function_call`/`tool_calls`; anything else becomes `unknown` (char-exact, `packages/llm/src/protocols/openai-chat.ts:378-384`). The AI SDK bridge likewise maps any non-matching value to `unknown` (`packages/opencode/src/session/llm/ai-sdk.ts:21-23`).
- Tools are sent unconditionally: `resolveTools` filters only by permission rules and user-disabled tools (`packages/opencode/src/session/llm/request.ts:208-213`), and the prepared request always carries the sorted tool map (`packages/opencode/src/session/llm/request.ts:184`). `capabilities.toolcall` defaults to true (`packages/opencode/src/provider/provider.ts:1263,1494`) but is never read anywhere in `packages/opencode/src` or `packages/core/src` to suppress tools (grep across both trees found only assignments).
- Inference on what breaks for a server with no tool support: the request still contains the `tools` array (plus `stream_options: { include_usage: true }` on the chat wire, `packages/llm/src/protocols/openai-chat.ts:360`); if the server rejects the `tools` field the request fails, and if the model simply never emits tool calls the agent can never modify files and the loop exits at the first `stop` (per the exit condition above). The agent has no model-side fallback for editing without tool calls.

### Q4. Temperature, sampling, and request transforms

- `temperature(model)` returns hard-coded values only for ID substrings `north-mini-code` (1.0), `claude` (undefined), `gemini` (1.0 for the `GEMINI_MODELS_WITH_SAMPLING_DEFAULTS` regexes else undefined), `glm-4.6`, `glm-4.7`, `minimax-m2` (each 1.0), and `kimi-k2` (1.0 or 0.6); any other ID returns `undefined` (`packages/opencode/src/provider/transform.ts:521-545`). An arbitrary open model ID matches none of these and gets no temperature from the transform.
- Temperature is only sent when the capability is on: `temperature: input.model.capabilities.temperature ? (input.agent.temperature ?? ProviderTransform.temperature(input.model)) : undefined` (`packages/opencode/src/session/llm/request.ts:124-126`). Capability defaults are false for config-defined models (`packages/opencode/src/provider/provider.ts:1491`) and `model.temperature ?? false` for catalog models (`packages/opencode/src/provider/provider.ts:1260`). Agent-level `topP` can still override (`packages/opencode/src/session/llm/request.ts:127`), and `topP`/`topK` transforms are ID-gated the same way (`packages/opencode/src/provider/transform.ts:547-572`). Net effect for an open model: no sampling parameters unless the user config sets `temperature: true` on the model and an agent or model `options` supplies values.
- Reasoning effort passthrough: `variants(model)` returns `{}` unless `model.capabilities.reasoning` (`packages/opencode/src/provider/transform.ts:728`). For npm `@ai-sdk/openai-compatible` it emits `low`/`medium`/`high` variants as `{ reasoningEffort: effort }`, plus `max` when the ID contains `deepseek-v4` (`packages/opencode/src/provider/transform.ts:931-939`). Catalog-declared `reasoning_options` take precedence via `reasoningVariants` (`packages/opencode/src/provider/transform.ts:1654-1670`, wired at `packages/opencode/src/provider/provider.ts:1284` and `packages/opencode/src/provider/provider.ts:1538-1541` for config models). The chosen variant is deep-merged into request options (`packages/opencode/src/session/llm/request.ts:80-91`), then nested under a providerOptions key derived from `sdkKey(npm)` or, for `@ai-sdk/openai-compatible`, `model.providerID.split(".")[0]` (`packages/opencode/src/provider/transform.ts:1404-1408,1415`).
- Message transforms relevant to open models on OpenAI-compatible transports: surrogate sanitization of all text (`packages/opencode/src/provider/transform.ts:25-27,121-166`); unsupported media parts are replaced by inline error text based on `capabilities.input[modality]` (`packages/opencode/src/provider/transform.ts:410-446`); interleaved reasoning passback writes the joined reasoning text into `providerOptions.openaiCompatible[field]` when `model.capabilities.interleaved` is a field object (and the SDK is not OpenRouter) (`packages/opencode/src/provider/transform.ts:322-354`). For config-defined openai-compatible models whose ID contains `deepseek`, the default interleaved field is `reasoning_content` (`packages/opencode/src/provider/provider.ts:1515-1517`); otherwise interleaved defaults to false. Anthropic/Bedrock/Mistral/DeepSeek-specific branches (`packages/opencode/src/provider/transform.ts:168-320`) do not fire for a generic open ID.
- `options()` adds almost nothing for an arbitrary providerID: `store: false` is set only for `openai`/`@ai-sdk/openai`/copilot/mantle/xai/azure npm or providerID (`packages/opencode/src/provider/transform.ts:1172-1184`); OpenRouter/llmgateway usage include, baseten/opencode chat_template_args, zai thinking, google thinkingConfig, gpt-5 reasoningEffort blocks all require specific providerIDs or ID substrings (`packages/opencode/src/provider/transform.ts:1186-1322`). An arbitrary local provider gets an empty base options object.

### Q5. Model metadata resolution for an arbitrary provider/model string

- `Provider.getModel` resolves strictly from the in-memory provider map; an unknown provider or model ID fails with `ProviderModelNotFoundError` carrying fuzzysort suggestions (`packages/opencode/src/provider/provider.ts:1842-1863`). The session wrapper turns that into a published `Model not found: <providerID>/<modelID>` error with a "Did you mean" hint and dies (`packages/opencode/src/session/prompt.ts:594-612`); the loop fetches the model each iteration at `packages/opencode/src/session/prompt.ts:1141`.
- A model absent from the hosted/installed catalog can only enter through user config (`provider.<id>.models`), merged at `packages/opencode/src/provider/provider.ts:1452-1550`. Character-exact defaults for the unknown model (`packages/opencode/src/provider/provider.ts:1528-1532`):

```ts
limit: {
  context: model.limit?.context ?? existingModel?.limit?.context ?? 0,
  input: model.limit?.input ?? existingModel?.limit?.input,
  output: model.limit?.output ?? existingModel?.limit?.output ?? 0,
},
```

  plus: npm falls back to `"@ai-sdk/openai-compatible"` (`packages/opencode/src/provider/provider.ts:1466-1474`), `toolcall ?? true` (`packages/opencode/src/provider/provider.ts:1494`), `temperature`/`reasoning`/`attachment ?? false` (`packages/opencode/src/provider/provider.ts:1491-1493`), `input.text ?? true` and `output.text ?? true` (`packages/opencode/src/provider/provider.ts:1496,1503`), all other modalities false, cost fields `?? 0` (`packages/opencode/src/provider/provider.ts:1519-1526`). Catalog models instead take `limit.context`/`limit.output` directly from the models.dev entry (`packages/opencode/src/provider/provider.ts:1254-1258`).
- Consequence chain for an open model with fully unset limits: `limit.context = 0` and `limit.output = 0` (provider.ts defaults above) → `isOverflow` short-circuits false (`packages/opencode/src/session/overflow.ts:29`) so auto-compaction never fires → every request asks for `max_tokens = 32_000` (`transform.ts:1418-1420` fallback) even if the model supports far less → if the server's real context is exceeded, the failure arrives as a provider error whose parse may classify it as `ContextOverflowError` (`packages/opencode/src/session/processor.ts:607-617`). (Classification as overflow depends on the retry/error parser, which I did not trace; see Limitations.)

## Key facts with anchors

- Fact 1 (`packages/opencode/src/tool/registry.ts:297-300`): `apply_patch` replaces `edit`/`write` exactly when `input.modelID.includes("gpt-") && !input.modelID.includes("oss") && !input.modelID.includes("gpt-4")`; open model IDs get `edit` and `write`.
- Fact 2 (`packages/core/src/util/token.ts:3-5`): the only token estimator is `Math.max(0, Math.round(input.length / CHARS_PER_TOKEN))` with `CHARS_PER_TOKEN = 4`; no tokenizer exists in the session path.
- Fact 3 (`packages/opencode/src/provider/transform.ts:18,1418-1420`): `OUTPUT_TOKEN_MAX = 32_000` and `maxOutputTokens` is `Math.min(model.limit.output, outputTokenMax) || outputTokenMax`, so `limit.output = 0` (unknown) yields 32,000.
- Fact 4 (`packages/opencode/src/session/llm/request.ts:129`): that value is sent as every request's `maxOutputTokens` unless `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` overrides (`packages/opencode/src/effect/runtime-flags.ts:52`).
- Fact 5 (`packages/opencode/src/session/overflow.ts:8-20,29`): compaction reserve is `min(20_000, maxOutputTokens(...))` clamped by known `limit.input` or `limit.context`, and `isOverflow` returns false whenever `limit.context === 0`, disabling auto-compaction for limit-unknown models.
- Fact 6 (`packages/opencode/src/provider/provider.ts:1528-1532,1466-1474,1491-1494`): config-defined models missing metadata default to `context: 0`, `output: 0`, `input: undefined`, npm `@ai-sdk/openai-compatible`, `toolcall: true`, `temperature: false`, `reasoning: false`.
- Fact 7 (`packages/opencode/src/session/prompt.ts:1103-1116,1295`): the loop keeps running only for finish `tool-calls` or unfinished tool parts; `unknown` finish reasons are tolerated mid-iteration and unrecognized wire reasons map to `unknown` (`packages/llm/src/protocols/openai-chat.ts:378-384`, `packages/opencode/src/session/llm/ai-sdk.ts:21-23`).
- Fact 8 (`packages/opencode/src/session/llm/request.ts:124-129,208-213`): temperature is sent only when `capabilities.temperature` is true, and the tools array is always sent regardless of the `toolcall` capability.
- Fact 9 (`packages/opencode/src/provider/transform.ts:528-545,931-939`): sampling transforms and reasoning-effort variants are gated on ID substrings or `capabilities.reasoning`; arbitrary open IDs match neither, and `@ai-sdk/openai-compatible` gets `low`/`medium`/`high` effort variants only when reasoning is declared.
- Fact 10 (`packages/opencode/src/session/compaction.ts:28-33`): compaction-adjacent constants on the v1 path are `PRUNE_MINIMUM = 20_000`, `PRUNE_PROTECT = 40_000`, `MIN_PRESERVE_RECENT_TOKENS = 2_000`, `MAX_PRESERVE_RECENT_TOKENS = 15_000`; the v2 core path uses `DEFAULT_BUFFER = 20_000`, `DEFAULT_KEEP_TOKENS = 8_000`, `SUMMARY_OUTPUT_TOKENS = 4_096` (`packages/core/src/session/compaction.ts:12-15`).

## Configuration and defaults

Character-exact values and keys, all at the pinned commit:

- `OUTPUT_TOKEN_MAX = 32_000` (`packages/opencode/src/provider/transform.ts:18`), re-exported at `packages/opencode/src/session/llm.ts:33`.
- `CHARS_PER_TOKEN = 4` (`packages/core/src/util/token.ts:3`).
- `COMPACTION_BUFFER = 20_000` (`packages/opencode/src/session/overflow.ts:8`); `DEFAULT_BUFFER = 20_000`, `DEFAULT_KEEP_TOKENS = 8_000`, `TOOL_OUTPUT_MAX_CHARS = 2_000`, `SUMMARY_OUTPUT_TOKENS = 4_096` (`packages/core/src/session/compaction.ts:12-15`).
- Environment override: `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (positive integer only, `packages/opencode/src/effect/runtime-flags.ts:52`), forwarded to both the request (`packages/opencode/src/session/llm/request.ts:129`) and the overflow reserve via `flags.outputTokenMax` (`packages/opencode/src/session/compaction.ts:203-213`).
- User config knobs: `compaction.reserved`, `compaction.auto`, `compaction.preserve_recent_tokens`, `compaction.prune`, `compaction.tail_turns` (`packages/opencode/src/session/overflow.ts:15,28`, `packages/opencode/src/session/compaction.ts:117,228,275`); per-model config `limit.context`, `limit.input`, `limit.output`, `temperature`, `reasoning`, `tool_call`, `interleaved`, `modalities`, `options`, `variants` (`packages/opencode/src/provider/provider.ts:1463-1547`).
- Wire fields sent for an OpenAI-compatible request include `stream_options: { include_usage: true }` and `max_tokens` (`packages/llm/src/protocols/openai-chat.ts:360-361`). `stream: true` is unconditional in this builder: `fromRequest` hardcodes `stream: true as const` (`packages/llm/src/protocols/openai-chat.ts:359`), the trailing `lowerOptions` spread can only add `store` and `reasoning_effort` (`openai-chat.ts:333-342`), and the body schema accepts no other value (`stream: Schema.Literal(true)`, `openai-chat.ts:487`). Verified against the pinned commit d545d8f on 2026-08-21.

## Limitations and unknowns

- Two compaction implementations coexist at this commit: the v1 path used by the session prompt loop (`packages/opencode/src/session/compaction.ts` + `overflow.ts`) and a v2 core runner path (`packages/core/src/session/compaction.ts`, instantiated in `packages/core/src/session/runner/llm.ts:109` and triggered at `packages/core/src/session/runner/llm.ts:222`). Both paths are wired into the package: `SessionPrompt` (v1, `packages/opencode/src/session/prompt.ts:15,121,1150,1164`) serves the HTTP API session handlers and the GitHub handler, while `SessionExecutionLocal` (v2, `packages/core/src/session/execution/local.ts`) is imported by `packages/opencode/src/session/session.ts:14` and the httpapi server (`packages/opencode/src/server/routes/instance/httpapi/server.ts:67-68`). Which one serves the default `opencode` run at this commit remains unresolved [EVIDENCE NEEDED]; the registry's question about `min(20,000, maxOutputTokens)` matches the v1 `overflow.ts` exactly, and both use a 20,000 default buffer.
- Error classification into `ContextOverflowError` happens in the retry policy parser (`packages/opencode/src/session/processor.ts:606-617` references `parse` and `SessionRetry.policy`), which I did not read; the claim that an over-limit request surfaces as that error type for a local server is unverified.
- The hosted model catalog (models.dev data feeding `fromModelsDevModel`, `packages/opencode/src/provider/provider.ts:1235-1258`) may already contain limit values for popular open models (e.g. Ollama catalog entries); what actual limit data reaches an `ollama/<id>` session belongs to the sibling note `opencodeOssProviders`, which owns `provider.ts` plumbing. This note establishes only the in-code fallbacks.
- Static trace only: no request was executed, so claims about what a given server rejects (e.g. `stream_options`, tool schema keywords) are code-reading plus inference, not observed behavior.
- `capabilities.toolcall` appears write-only in every file searched; if a future commit reads it to gate tools, Fact 8's last clause becomes stale.

## Relevance to the brief

Directly answers RQ3 for OpenCode's model-ID-gated features (the patch-tool gate, character-exact) and its context accounting defaults (chars/4, 32,000 output cap, 20,000 reserve, compaction disabled at context 0). For RQ2 (minimum contract of an OpenAI-compatible server), it contributes the agent-side half: the server must accept a `tools` array and streaming deltas with tool calls in OpenAI shape, must supply usage (requested via `stream_options.include_usage`), and should return `finish_reason: tool_calls` or `stop`; unrecognized reasons degrade to `unknown` and skip the finished-turn handling but do not loop forever. It leaves open the server-side acceptance evidence, which the docs notes (`ollamaCompatDocs`, `lmstudioCompatToolsDocs`, `llamaCppServerDocs`) must supply, and the provider plumbing (baseURL, runtime SDK install, catalog fetch) owned by `opencodeOssProviders`. Practical takeaway I infer for the compatibility matrix: an open model on OpenCode lands on the generic edit/write tool path with hard-coded 32,000-token output requests and no auto-compaction unless the user hand-fills `limit.context` / `limit.output` / `compaction.reserved` in config.

## Quotables for the report

- Gating predicate (`packages/opencode/src/tool/registry.ts:297-300`), frame as "OpenCode selects its patch tool by substring match on the model ID; every non-gpt model is routed to search-and-replace edits":

  ```ts
  const usePatch =
    input.modelID.includes("gpt-") && !input.modelID.includes("oss") && !input.modelID.includes("gpt-4")
  ```

- Token estimator (`packages/core/src/util/token.ts:3-5`), frame as "all internal accounting is a chars/4 heuristic; no tokenizer ships in the session path":

  ```ts
  const CHARS_PER_TOKEN = 4
  export const estimate = (input: string) => Math.max(0, Math.round(input.length / CHARS_PER_TOKEN))
  ```

- Output cap fallback (`packages/opencode/src/provider/transform.ts:1418-1420`), frame as "unknown output limits silently become 32,000 requested tokens":

  ```ts
  export function maxOutputTokens(model: Provider.Model, outputTokenMax = OUTPUT_TOKEN_MAX): number {
    return Math.min(model.limit.output, outputTokenMax) || outputTokenMax
  }
  ```

- Compaction reserve (`packages/opencode/src/session/overflow.ts:14-16`), frame as "the compaction headroom is capped at 20,000 tokens by default":

  ```ts
  const reserved =
    input.cfg.compaction?.reserved ??
    Math.min(COMPACTION_BUFFER, ProviderTransform.maxOutputTokens(input.model, input.outputTokenMax))
  ```

- Finish-reason enum (`packages/llm/src/schema/ids.ts:39`), frame as "the loop's entire finish vocabulary is six literals; anything else from the wire becomes unknown":

  ```ts
  export const FinishReason = Schema.Literals(["stop", "length", "tool-calls", "content-filter", "error", "unknown"])
  ```

- Loop exit (`packages/opencode/src/session/prompt.ts:1111-1114`), frame as "stop does not end the turn if tool parts are still open, a tolerance for servers that omit tool_calls finish reasons":

  ```ts
  if (
    lastAssistant?.finish &&
    !["tool-calls"].includes(lastAssistant.finish) &&
    !hasToolCalls &&
  ```
