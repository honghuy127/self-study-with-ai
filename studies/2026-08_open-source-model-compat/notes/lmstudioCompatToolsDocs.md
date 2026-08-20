---
source_key: lmstudioCompatToolsDocs
read_date: 2026-08-20
confidence: high
relevance: 3
---

# Notes: LM Studio docs: OpenAI-compatible tool calling

## Source identification

- Key: lmstudioCompatToolsDocs
- Authors, year, venue: LM Studio (lmstudio-ai), 2026, docs.lmstudio.ai
  (snapshotted via github.com/lmstudio-ai/docs)
- Tier: docs
- URL / DOI: https://docs.lmstudio.ai/developers/openai-compat/tools
  (snapshot: `sources/docs/lmstudioTools.md`, 1194-line mdx file, frontmatter
  `title: Tool Use`, `sidebar_title: Tools and Function Calling`, line 2-3).
  All anchors below are line numbers in the snapshot.

## Problem and motivation

The page documents how to make models served by LM Studio request external
function calls. Frontmatter description: "Enable LLMs to interact with
external functions and APIs" (line 4). The opening states the scope: "Tool
use enables LLMs to request calls to external functions and APIs through the
`/v1/chat/completions` and `v1/responses` endpoints ... via LM Studio's REST
API (or via any OpenAI client). This expands their functionality far beyond
text output" (line 10). The doc is structured as quick start, conceptual
flow, supported-model taxonomy, then curl and Python examples (lines 14-1191).

Repeated emphasis: the model only emits text; execution is the client's job.
"LLMs output text requesting functions to be called (LLMs cannot directly
execute code)" (line 61), restated in bold at line 155.

## Method or core idea

**Tool-use loop (lines 55-238).** Setup provides the model plus tool list; on
each turn the model either calls one or more tools or responds normally; the
client executes and appends results back to `messages` (flow diagram lines
67-99, steps 1-6 at lines 109-236). The doc labels this the "`pedantic` flow
for tool use" and says you can "experiment with this flow to best fit your
use case" (line 238).

**Request shape (lines 103-131).** "LM Studio supports tool use through the
`/v1/chat/completions` endpoint when given function definitions in the
`tools` parameter of the request body" (line 103). Tools are "an array of
function definitions that describe their parameters and usage", each entry
`{"type": "function", "function": {"name": ..., "description": ...,
"parameters": {...}}}` with a JSON-schema-style `parameters` object (lines
112-131). "It follows the same format as OpenAI's Function Calling API and is
expected to work via the OpenAI client SDKs" (line 105). "All parameters
recognized by `/v1/chat/completions` will be honored, and the array of
available tools should be provided in the `tools` field" (line 405).

**Template injection (lines 134-153).** The tool list "will be injected into
the `system` prompt of the model depending on the model's chat template",
with a worked Qwen2.5-Instruct example placing tool signatures in
`<tools></tools>` XML tags (lines 134-147).

**Response parsing (lines 174-185).** "LM Studio parses the text output from
the model into an OpenAI-compliant `chat.completion` response object" (line
174). When `tools` were offered, LM Studio "will attempt to parse the tool
calls into the `response.choices[0].message.tool_calls` field" (line 175);
unparsable text goes to `response.choices[0].message.content` (line 176).

**Two support levels (lines 240-359).** Native requires both a tool-capable
chat template and LM Studio support for that model's tool format (lines
250-256). Default mode, applied to "All models that don't have native tool
use support" (line 359), works by "Giving models a custom system prompt and a
default tool call format to use", "Converting `tool` role messages to the
`user` role so that chat templates without the `tool` role are compatible",
and "Converting `assistant` role `tool_calls` into the default tool call
format" (lines 277-281). The default format uses
`[TOOL_REQUEST]...[END_TOOL_REQUEST]` blocks inside a "You are a tool-calling
AI" system prompt (lines 299-342); the format is "subject to change" (line
285). If the model follows it exactly, "LM Studio will be able to parse those
tool calls into the `chat.completions` object, just like for natively
supported models" (line 355).

**Streaming (lines 1027-1044).** Covered in Key claims; chunks carry partial
`tool_calls` deltas that the client accumulates (line 1042).

## Key claims with anchors

Answers to the five assigned questions, using only the snapshot.

**Q1. Endpoints and request/response shapes.**

- Endpoints (char-exact): "the `/v1/chat/completions` and `v1/responses`
  endpoints" (line 10; note the snapshot writes `/v1/chat/completions` with a
  leading slash and `v1/responses` without one). The remainder of the page
  documents `/v1/chat/completions` only; the `v1/responses` claim appears
  exactly once. Example curl call hits
  `http://localhost:1234/v1/chat/completions` (line 368).
- Request shape: `tools` is an array of `{"type": "function", "function":
  {name, description, parameters}}` objects, `parameters` using JSON-schema
  fields `type`, `properties`, `required` (plus `additionalProperties: false`
  in the curl example) (lines 112-131, 373-401).
- Response shape: "an array of tool call request objects will be provided in
  the response field, `choices[0].message.tool_calls`" (line 407); "The
  `finish_reason` field of the top-level response object will also be
  populated with `\"tool_calls\"`" (line 409). Full example response (lines
  413-446): `object: "chat.completion"` with `id`, `created`, `model`,
  `choices[0].index`, `logprobs: null`, `finish_reason: "tool_calls"`,
  `message.role: "assistant"`, per-call `id`, `type: "function"`,
  `function.name`, `function.arguments` (a JSON string), plus `usage`
  (`prompt_tokens`, `completion_tokens`, `total_tokens`) and
  `system_fingerprint` (lines 439-444).
- Fallback: unparseable output lands in
  `response.choices[0].message.content` instead of `tool_calls` (line 176).
- Tool results return as messages with `role: "tool"` and `tool_call_id`
  (lines 225, 633-642); the multi-turn examples send the final follow-up
  request without `tools` (lines 214-231, 652-657), framed as flow advice
  ("The LLM is then prompted again with the updated messages array, but
  without access to tools", line 214), not as a server restriction.

**Q2. Parallel tool calls.**

- No `tool_choice` parameter and no parallel-tool-calls flag appear anywhere
  in the snapshot. Searched the full file: no occurrence of "parallel",
  "tool_choice", or any analogous flag. `[CITATION NEEDED]` for an explicit
  parallel-tool-calls flag in LM Studio's documented contract.
- Multiple calls per turn are nonetheless documented as supported behavior:
  the model "can ... (a) Call one or more tools" (lines 157-158, 142, 332);
  the default-format rules say "Use one [TOOL_REQUEST] block per tool" and
  the worked example shows two blocks in one message (`send_email` then
  `open_browser`) (lines 330, 338-340); the advanced example loops over all
  entries of `response.choices[0].message.tool_calls` (lines 857-907); and
  the streaming accumulator indexes calls by `tc.index`, implying multiple
  interleaved tool calls in one stream (lines 1088-1102).

**Q3. Structured output / JSON schema.**

- JSON schema vocabulary appears only inside tool `parameters` definitions
  (`"type": "object"`, `properties`, `required`, `additionalProperties`,
  `enum`) (lines 120-128, 379-398, 389).
- No `response_format`, no constrained/structured-output endpoint, and no
  JSON-schema enforcement on model output is documented in this snapshot.
  Searched the full file: no occurrence of "response_format",
  "structured", or "json_schema". `[CITATION NEEDED]` for structured-output
  support on LM Studio's OpenAI-compatible endpoints (looked across the
  entire tool-calling page; it may be documented on another page not read
  here).

**Q4. Model families with tool support, prompt-template caveats.**

- Universal claim: "Through LM Studio, **all** models support at least some
  degree of tool use" (line 242), split into Native and Default levels (line
  244).
- Native list ("subject to change", line 258), char-exact (lines 260-268):
  - Qwen: `GGUF` lmstudio-community/Qwen2.5-7B-Instruct-GGUF (4.68 GB);
    `MLX` mlx-community/Qwen2.5-7B-Instruct-4bit (4.30 GB)
  - Llama-3.1, Llama-3.2: `GGUF`
    lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF (4.92 GB); `MLX`
    mlx-community/Meta-Llama-3.1-8B-Instruct-8bit (8.54 GB)
  - Mistral: `GGUF` bartowski/Ministral-8B-Instruct-2410-GGUF (4.67 GB);
    `MLX` mlx-community/Ministral-8B-Instruct-2410-4bit (4.67 GB GB)
    ("GB GB" appears in the source, line 268)
  - Note the heading family is "Llama-3.1, Llama-3.2" but both listed
    artifacts are Llama-3.1-8B-Instruct (lines 263-265).
- Template caveats: tools are injected per the model's chat template (line
  134); Native requires both a tool-use chat template and LM Studio support
  for that format (lines 250-256); Default mode rewrites roles and injects a
  custom tool-calling system prompt (lines 277-283, 299-342). "Smaller
  models and models that were not trained for tool use may output improperly
  formatted tool calls, resulting in LM Studio being unable to parse them
  into the `tool_calls` field" (line 177).

**Q5. Streaming with tool calls.**

- Supported, documented, and exemplified. "When streaming through
  `/v1/chat/completions` (`stream=true`), tool calls are sent in chunks.
  Function names and arguments are sent in pieces via
  `chunk.choices[0].delta.tool_calls.function.name` and
  `chunk.choices[0].delta.tool_calls.function.arguments`" (line 1029).
- Client obligation: "These chunks must be accumulated throughout the stream
  to form the complete function signature for execution" (line 1042). Worked
  delta sequence for `get_current_weather(location="San Francisco")` shows
  the first `ChoiceDeltaToolCall` carrying `id` and `name` with empty
  arguments, then argument fragments with `id=None` (lines 1031-1040). A
  complete streaming chatbot example follows (lines 1049-1169).

Inference vs claim, separated per house rules: everything above is the
source's own statement. My inference about what this means for the brief is
isolated in "Relevance to the brief".

## Evaluation and evidence

This is a product documentation page, not an evaluation. Its evidence is
worked examples, all illustrative rather than benchmarked:

- curl request to `http://localhost:1234/v1/chat/completions` (lines
  368-403); example response (lines 413-446) with copied values:
  `"id": "chatcmpl-gb1t1uqzefudice8ntxd9i"`, `"created": 1730913210`,
  `"finish_reason": "tool_calls"`, tool call `"id": "365174485"`,
  `"arguments": "{\"query\":\"dell\",\"category\":\"electronics\",\"max_price\":50}"`,
  and `"usage": {"prompt_tokens": 263, "completion_tokens": 34,
  "total_tokens": 297}`.
- Python examples using `OpenAI(base_url="http://localhost:1234/v1",
  api_key="lm-studio")` (lines 474, 552, 706, 1053): single-turn (lines
  470-516), multi-turn (lines 545-662) with printed output
  `completion_tokens=24, prompt_tokens=223, total_tokens=247` and
  `created=1730916196` (line 673), advanced agent (lines 697-984), and
  streaming chatbot (lines 1049-1169). All examples use model ID
  `lmstudio-community/qwen2.5-7b-instruct` (lines 228, 503, 553, 707, 1054).
- A log-stream excerpt dated `11/13/2024, 9:35:15 AM` shows the default tool
  prompt injected for model `gemma-2-2b-it` (lines 294-296), i.e., the
  Default path is demonstrated on a non-native Gemma model.
- No metrics, baselines, or success rates are reported anywhere in the page.
  Any quantitative claim about parse success or tool-call quality per model
  would be `[CITATION NEEDED]` (looked: entire snapshot, lines 240-359 in
  particular).

## Limitations

- **Single-mention responses coverage.** `v1/responses` is asserted once
  (line 10); the entire mechanism section, all request/response shapes, and
  all examples describe `/v1/chat/completions` only (lines 103, 368, 405,
  1029, 1044). The responses-side contract must come from the separate
  snapshot (lmstudioCompatResponsesDocs).
- **No tool-selection controls documented.** No `tool_choice`, no
  "required"/"none"/"auto" modes, no parallel-tool-calls flag anywhere in
  the snapshot (full-file search). Silent on whether unsupported request
  fields error or are ignored.
- **Fragility is admitted, not measured.** Parse fallback to `content` (line
  176) and malformed-call examples for Qwen2.5-Instruct (lines 179-185) give
  no frequency; "Results will vary by model" is the only guidance for
  Default mode (line 283). The Default-format system prompt and its rule list
  are explicitly "subject to change" (line 285), and so is the Native model
  list (line 258).
- **Native list is thin and partly mislabeled.** Three families, six
  artifacts, all 7-8B instruct models; the "Llama-3.1, Llama-3.2" heading is
  backed only by Llama-3.1 artifacts (lines 263-265).
- **Example hygiene.** The single-turn example parses arguments with
  `eval(tool_call.function.arguments)` (line 511) and assumes a tool call
  occurred (line 509); example outputs are curated transcripts, not reproducible
  runs.
- **Snapshot provenance.** The page was mirrored from the public docs repo at
  main HEAD on 2026-08-20 because docs.lmstudio.ai was unreachable in the
  gathering environment (registry `coverage_limits`); drift between this
  mirror and the shipped LM Studio app is not assessed. The page itself shows
  no version or release date; internal artifacts date to November 2024 (lines
  294, 417, 997).
- **No context-window or model-capability reporting** is documented, though
  per-request `usage` token counts are shown in example responses (lines
  439-443).

## Relevance to the brief

My inference, separated from source claims. This note bears directly on
RQ2 (the minimum contract an OpenAI-compatible server must satisfy) for the
LM Studio cells of the compatibility matrix.

- The tool-calling contract LM Studio claims is the OpenAI chat-completions
  shape: `tools` array in, `choices[0].message.tool_calls` out, `finish_reason:
  "tool_calls"`, streaming deltas under `chunk.choices[0].delta.tool_calls`
  (lines 105, 407-409, 1029). Any agent that speaks OpenAI chat-completions
  tool calling can, on paper, interoperate. This is exactly the wire shape
  the brief asks about for the generic-endpoint bar.
- The one-line `v1/responses` attestation (line 10) is load-bearing for the
  Codex question: the brief records that Codex pins its wire protocol to the
  Responses API, leaving open how its lmstudio provider entry fits. If LM
  Studio's `v1/responses` endpoint carries tool use, a Responses-wired agent
  has a documented LM Studio path. The details live in the
  lmstudioCompatResponsesDocs snapshot and this note cannot confirm them.
- For RQ3 (where support degrades), two documented degradation modes matter:
  silent fallback of unparsed tool calls to `content` (line 176), and the
  Default-mode rewrite of `tool`/`assistant` messages for models without
  native templates (lines 277-283). Both can make tool calls look "missing"
  to an agent expecting structured `tool_calls`.
- Not documented here, still open for the matrix: `tool_choice`,
  structured-output enforcement, context-window reporting, error behavior on
  unsupported parameters.

## Quotables for the report

- Endpoint scope (line 10): "Tool use enables LLMs to request calls to
  external functions and APIs through the `/v1/chat/completions` and
  `v1/responses` endpoints". Suggested framing: LM Studio's docs attest tool
  use on both the chat-completions and responses surfaces.
- Compatibility claim (line 105): "It follows the same format as OpenAI's
  Function Calling API and is expected to work via the OpenAI client SDKs."
  Note the hedge in "expected to"; useful for marking documentation-tier
  evidence in matrix cells.
- Parse fallback (line 176): "If LM Studio cannot parse any correctly
  formatted tool calls, it will simply return the response to the standard
  `response.choices[0].message.content` field." Framing: silent degradation
  mode agents must tolerate or detect.
- Universal support (line 242): "Through LM Studio, **all** models support at
  least some degree of tool use." Framing: availability is total, quality is
  tiered (Native vs Default, lines 244-246).
- Default-mode caveat (line 283): "Results will vary by model." Framing: the
  docs themselves bound the quality claim for non-native models.
- Streaming contract (line 1029): "When streaming through
  `/v1/chat/completions` (`stream=true`), tool calls are sent in chunks."
  Framing: streaming tool calls are part of the documented contract, with
  client-side accumulation required (line 1042).
