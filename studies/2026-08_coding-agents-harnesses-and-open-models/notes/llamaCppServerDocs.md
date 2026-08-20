---
source_key: llamaCppServerDocs
read_date: 2026-08-20
confidence: high
relevance: 3
---

# Notes: llama.cpp: reference server OpenAI-compatible contract

Anchor convention: `L<n>` is a line number in the local snapshot
`sources/docs/llamaCppServer.md` (the `snapshot:` field of this registry
entry), a 2,131-line copy of `tools/server/README.md` from
`github.com/ggml-org/llama.cpp` master, fetched 2026-08-20 per the registry
provenance. All quotes are character-exact from that file. Claims are marked
as `states` (documented fact), `interprets` (maintainer judgment without
cited evidence), or `infers` (my reading, only in the final sections).

## Source identification

- Key: llamaCppServerDocs
- Authors, year, venue: ggml-org, 2026, github.com/ggml-org/llama.cpp
  (per registry)
- Tier: docs
- URL / DOI: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Snapshot: `sources/docs/llamaCppServer.md`; no commit hash is embedded in
  the snapshot itself (see Limitations)

## Problem and motivation

The README documents `llama-server`, described as a "Fast, lightweight, pure
C/C++ HTTP server based on httplib, nlohmann::json and **llama.cpp**" that
provides a "Set of LLM REST APIs and a web UI to interact with llama.cpp"
(L3, L5). Its stated compatibility surface is the point of this note: it
lists as features "[OpenAI API](https://github.com/openai/openai-openapi)
compatible chat completions, responses, and embeddings routes" (L9),
"[Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
compatible chat completions" (L10), "Schema-constrained JSON response
format" (L16), and "Function calling / tool use for ~any model" (L18). It
positions itself as the reference OpenAI-compatible server for GGUF models,
which makes it the natural "generic OpenAI-compatible endpoint" bar in the
brief's compatibility matrix.

## Method or core idea

Mechanisms relevant to a compatibility contract (all `states`):

- One HTTP server, two modes: single-model, or a "router mode" started
  without a model that dynamically loads/unloads model instances and
  forwards requests by the `"model"` field in POST bodies
  ("(`/v1/chat/completions`, `/v1/completions`, `/infill`, etc.)") (L1642-L1646,
  L1764-L1768).
- Chat requests are rendered through a Jinja chat template engine:
  "`--jinja, --no-jinja` | whether to use jinja template engine for chat
  (default: enabled)" (L226). Custom templates come from model metadata, a
  built-in list (bailing ... zephyr, including `gpt-oss`, `llama3`,
  `chatml`), or `--chat-template-file` (L233-L234).
- Constrained decoding is grammar-based: `--grammar GRAMMAR` ("BNF-like
  grammar to constrain generations") and `-j, --json-schema SCHEMA` (L151,
  L153); per-request fields `grammar` (L562) and `json_schema` (L564).
- `/v1/responses` is not a native implementation: "This endpoint works by
  converting Responses request into Chat Completions request." (L1494).
- Concurrency via slots: "`-np, --parallel N` | number of server slots
  (default: -1, -1 = auto)" (L175) with continuous batching "default:
  enabled" (L176).
- Streaming uses Server-Sent Events (L600, quoted in Key claims below).

## Key claims with anchors

### Q1. OpenAI-compatible endpoints exposed (paths character-exact)

Under the heading "## OpenAI-compatible API Endpoints" (L1236), the snapshot
documents, in order:

1. GET `/v1/models` ("OpenAI-compatible Model Info API", L1238)
2. POST `/v1/completions` (L1270)
3. POST `/v1/chat/completions` (L1301)
4. POST `/v1/chat/completions/control` (L1438; real-time control of a
   running completion, only action is `reasoning_end`, L1446)
5. POST `/v1/responses` ("OpenAI-compatible Responses API", L1454)
6. POST `/v1/embeddings` (L1497)
7. POST `/v1/responses/input_tokens` ("Token Counting", L1533)
8. POST `/v1/chat/completions/input_tokens` (L1546), flagged "Note: This is
   not an official OAI endpoint, but is added for completeness and
   convenience." (L1550)

Other documented endpoints outside that section:

- GET `/health`: "This endpoint is public (no API key check). `/v1/health`
  also works." (L463, L465). Returns 503 `{"error": {"code": 503, "message":
  "Loading model", "type": "unavailable_error"}}` while loading, 200
  `{"status": "ok" }` when ready (L469-L474).
- GET `/props` (L823); POST `/props` only "if you need to start server with
  `--props`" (L825, L919-L921). Response includes `total_slots`,
  `model_path`, `chat_template`, `chat_template_caps`, `modalities`,
  `is_sleeping` (L911-L917).
- GET `/metrics`: "This endpoint is only accessible if `--metrics` is set."
  (L1115, L1117). Prometheus metric names such as
  `llamacpp:prompt_tokens_total` (L1125).
- GET `/slots`: "enabled by default and can be disabled with `--no-slots`"
  (L967, L969); POST `/slots/{id_slot}?action=save` / `restore` / `erase`
  (L1141, L1161, L1181).
- GET `/lora-adapters` and POST `/lora-adapters` (L1192, L1219).
- POST `/reranking` with "*Aliases:* `/rerank`, `/v1/rerank`,
  `/v1/reranking`" (L756, L767-L770); requires `--rerank, --reranking`
  (L206) and a reranker model with `--embedding --pooling rank` (L759).
- Native, explicitly non-OAI routes: POST `/completion` ("This endpoint is
  **not** OAI-compatible. For OAI-compatible client, use `/v1/completions`
  instead.", L476-L480), POST `/tokenize` (L670), POST `/detokenize` (L715),
  POST `/apply-template` (L721), POST `/embedding` (same not-OAI warning
  pointing to `/v1/embeddings`, L733-L737), POST `/embeddings`
  ("non-OpenAI-compatible embeddings API", L927), POST `/infill` (L789).
- Anthropic-compatible: POST `/v1/messages` (L1563) and POST
  `/v1/messages/count_tokens` (L1609).
- Router-mode model management: GET `/models` (L1790), POST `/models/load`
  (L1875), POST `/models/unload` (L1897), GET `/models/sse` (L1917), POST
  `/models` for downloads (L1990), DELETE `/models` (L2030).
- Server-tools REST under `/tools` (L1636), with the warning "**Please do
  NOT use this endpoint in a downstream application**" (L1638). Unrelated to
  LLM tool calling; it exposes filesystem tools to the Web UI (L342).

### Q2. Streaming and SSE status; Responses API presence

- `/completion` `stream` option: "Allows receiving each predicted token in
  real-time instead of waiting for the completion to finish (uses a
  different response format). To enable this, set to `true`." (L527).
- Wire format: "Responses are sent using the
  [Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
  standard. Note: the browser's `EventSource` interface cannot be used due
  to its lack of `POST` request support." (L600). In streaming mode "only
  `content`, `tokens` and `stop` will be returned until end of completion"
  (L600).
- Keep-alive: "`--sse-ping-interval N` | server SSE ping interval in
  seconds (-1 = disabled, default: 30)" (L213); per-request override
  `sse_ping_interval` keeps "the connection observable during long prompt
  processing" (L590).
- `/v1/completions`: "Streaming mode is also supported." (L1272).
- `/v1/chat/completions`: "Both synchronous and streaming mode are
  supported, so scripted and interactive applications work fine." (L1303).
- `/v1/messages` (Anthropic route): "Streaming is supported via Server-Sent
  Events." (L1565).
- Responses API: PRESENT. Heading "### POST `/v1/responses`:
  OpenAI-compatible Responses API" (L1454), with Python and curl examples
  (L1462-L1492) and the mechanism note "This endpoint works by converting
  Responses request into Chat Completions request." (L1494). Verified
  absence in the snapshot: there is no statement of whether `/v1/responses`
  supports streaming, no options table (only "See [OpenAI Responses API
  documentation]", L1456-L1458), and no mention of tools, `reasoning`, or
  `previous_response_id` on that endpoint. I searched L1454-L1496 and the
  rest of the file; the only other `/v1/responses` mention is the token
  counting route (L1533).

### Q3. Tool / function calling

Supported, via the chat template:

- "[OpenAI-style function
  calling](https://platform.openai.com/docs/guides/function-calling) is
  supported with the `--jinja` flag (and may require a `--chat-template-file`
  override to get the right tool-use compatible Jinja template; worst case,
  `--chat-template chatml` may also work)." (L1384).
- `--jinja` is on by default: "(default: enabled)" (L226).
- Feature-level claim: "Function calling / tool use for ~any model" (L18),
  with detail deferred to external docs: "supported native tool call styles
  (generic tool call style is used as fallback)" (L1386).
- Request-level options on `/v1/chat/completions`: `parse_tool_calls`:
  "Whether to parse the generated tool call." (L1321); `parallel_tool_calls`:
  "Whether to enable parallel/multiple tool calls (only supported on some
  models, verification is based on jinja template)." (L1323).
- Caveats about model-specific templates are explicit: "Only models with a
  [supported chat
  template](https://github.com/ggml-org/llama.cpp/wiki/Templates-supported-by-llama_chat_apply_template)
  can be used optimally with this endpoint. By default, the ChatML template
  will be used." (L1303).
- Escape hatch: `--skip-chat-parsing` will "force a pure content parser,
  even if a Jinja template is specified; model will output everything in the
  content section, including any reasoning and/or tool calls (default:
  disabled)" (L235).
- Anthropic route mirrors the requirement: "Tool use requires `--jinja`
  flag." (L1569); `tools`: "Array of tool definitions (requires `--jinja`)"
  (L1589).
- Structured-output features (grammar, `response_format`) are separate from
  tool parsing; see Q4.

### Q4. Structured output / JSON mode

Three mechanisms documented:

- `response_format` on `/v1/chat/completions`: "supports both plain JSON
  output (e.g. `{"type": "json_object"}`) and schema-constrained JSON (e.g.
  `{"type": "json_object", "schema": {...}}` or `{"type": "json_schema",
  "schema": {...}}`), similar to other OpenAI-inspired API providers."
  (L1309; JSON bodies elided here are inline in the snapshot).
- Request fields on non-OAI routes: `grammar`: "Set grammar for
  grammar-based sampling." (L562); `json_schema`: "Set a JSON schema for
  grammar-based sampling (e.g. `{"items": {"type": "string"}, "minItems":
  10, "maxItems": 100}` of a list of strings, or `{}` for any JSON)."
  (L564).
- Server startup flags: `--grammar`, `--grammar-file`, `-j, --json-schema`,
  `-jf, --json-schema-file` (L151-L154), including the limitation "For
  schemas w/ external $refs, use --grammar + example/json_schema_to_grammar.py
  instead" (L153-L154).
- Feature bullet: "Schema-constrained JSON response format" (L16).
- Invalid grammar surfaces an OAI-shaped 400 error `"message": "Failed to
  parse grammar"` (L2109-L2118).

### Q5. Key flags that affect compatibility

- `--jinja, --no-jinja`: "(default: enabled)" (L226). Gate for tool calling
  (L1384) and Anthropic tool use (L1569).
- `-a, --alias STRING`: "set model name aliases, comma-separated (to be used
  by API)" (L184). "By default, model `id` field is the path to model file,
  specified via `-m`. You can set a custom value for model `id` field via
  `--alias` argument. For example, `--alias gpt-4o-mini`." (L1244).
- `-c, --ctx-size N`: "size of the prompt context (default: 0, 0 = loaded
  from model)" (L50).
- `--api-key KEY`: "API key to use for authentication, multiple keys can be
  provided as a comma-separated list (default: none)" (L207); also
  `--api-key-file` (L208).
- `--host HOST`: "ip address to listen, or bind to an UNIX socket if the
  address ends with .sock (default: 127.0.0.1)" (L187).
- `--port PORT`: "port to listen (default: 8080)" (L188).
- `-np, --parallel N`: "number of server slots (default: -1, -1 = auto)"
  (L175); continuous batching default enabled (L176).
- Compatibility-adjacent: `--api-prefix PREFIX` changes the URL prefix the
  server serves from (L195); `--reasoning-format` controls thought-tag
  extraction into `message.reasoning_content` (L227); `--reasoning-effort`
  passes a level such as "'minimal', 'low', 'medium', 'high', 'xhigh' or
  'max'" to the chat template (L229); `--prefill-assistant` "(default:
  prefill enabled)" (L236) supports assistant prefilling "similar to the
  Claude API" (L17); `--metrics` and `--props` gate their endpoints and are
  both "(default: disabled)" (L217-L218); `--sse-ping-interval` (L213).

### Q6. Explicit statements about OpenAI compatibility scope

- The strongest scope statement is a disclaimer, repeated for both core
  routes: "While no strong claims of compatibility with OpenAI API spec is
  being made, in our experience it suffices to support many apps." (L1272
  for `/v1/completions`; L1303 for `/v1/chat/completions`).
- Same disclaimer for the Anthropic route: "While no strong claims of
  compatibility with the Anthropic API spec are made, in our experience it
  suffices to support many apps." (L1565).
- Feature list limits stated OpenAI compatibility to "chat completions,
  responses, and embeddings routes" (L9).
- Errors: "`llama-server` returns errors in the same format as OAI:
  https://github.com/openai/openai-openapi" (L2048), example body carries
  `"code": 401, "message": "Invalid API Key", "type":
  "authentication_error"` (L2052-L2059). llama.cpp-specific error types are
  added on top, e.g. 501 `"This server does not support metrics endpoint."`
  when `/metrics` or `/slots` is disabled (L2095-L2107).
- Preconditions: `/v1/embeddings` "requires that the model uses a pooling
  different than type `none`" (L1499); `/v1/models` "The returned list
  always has one single element." (L1242); chat completions is template
  bounded (L1303, see Q3).

## Evaluation and evidence

This is reference documentation, not an empirical study: there are no
datasets, baselines, or conformance metrics. The snapshot nowhere reports a
test of llama.cpp against the OpenAI specification [CITATION NEEDED; looked:
full snapshot L1-L2131, especially the "OpenAI-compatible API Endpoints"
section L1236-L1559]. Documented values, character-exact:

- Defaults: ctx size "(default: 0, 0 = loaded from model)" (L50); port
  "(default: 8080)" (L188); host "(default: 127.0.0.1)" (L187); slots
  "(default: -1, -1 = auto)" (L175); SSE ping "(-1 = disabled, default:
  30)" (L213); server read/write timeout "(default: 3600)" seconds (L212).
- `/v1/models` example `meta`: `"n_vocab": 128256`, `"n_ctx_train":
  131072`, `"n_embd": 4096`, `"n_params": 8030261312` (L1258-L1263);
  `"owned_by": "llamacpp"` (L1256).
- `usage` object example on chat completions: `"completion_tokens": 48,
  "prompt_tokens": 44, "total_tokens": 92`, `"prompt_tokens_details":
  {"cached_tokens": 0}` (L1421-L1428).
- Context accounting: "The total number of tokens in context is equal to
  `prompt_n + cache_n + predicted_n`" (L1414), from the `timings` object
  (L1390-L1410).
- Token counting responses: `{"object": "response.input_tokens",
  "input_tokens": 11}` (L1540-L1543, L1554-L1558); Anthropic variant
  `{"input_tokens": 10}` (L1631).

## Limitations

These are weaknesses of the source as evidence, kept separate from its
claims:

- The compatibility claim is explicitly soft: "no strong claims of
  compatibility with OpenAI API spec is being made" (L1272, L1303), and the
  positive half, "in our experience it suffices to support many apps"
  (L1272), is maintainer interpretation with no cited evidence.
- `/v1/responses` is thinly documented (L1454-L1494): no options reference
  beyond a link to OpenAI's docs, no streaming statement, no tool or
  reasoning documentation, and the implementation is a translation layer
  ("converting Responses request into Chat Completions request", L1494), so
  any Responses-specific semantics (statefulness, `previous_response_id`,
  structured outputs on the Responses path) are undocumented here.
- Tool calling is model-dependent by the source's own admission: template
  overrides "may" be needed (L1384), `parallel_tool_calls` works "only [on]
  some models" (L1323), and the advertised "tool use for ~any model" (L18)
  rests on `docs/function-calling.md`, which is outside this snapshot, so
  that breadth claim is unverifiable here.
- The snapshot is not pinned to a commit; it is master at fetch time
  (registry provenance, 2026-08-20). Drift to newer master is possible.
- Several behaviors are marked experimental and "subject to change", e.g.
  the `/tools` REST API (L1636-L1638) and server tools/MCP flags
  (L199-L202); multimodal is "currently an experimental feature" (L332).
- Typo-level fidelity note: "/v1/embeddings" normalizes "using the Eucledian
  norm" (L1499, sic).

## Relevance to the brief

My inference only, tied to the brief's questions; none of this is stated by
the source:

- This note defines the study's "generic OpenAI-compatible endpoint" bar
  (brief RQ1 column three, RQ2 contract). The reference server's contract is
  chat completions with SSE streaming (L1303, L600), `/v1/models` with
  `n_ctx_train` metadata (L1238-L1268), `usage` plus `timings` for context
  accounting (L1390-L1430), token counting endpoints (L1533, L1546),
  template-gated tool calling (L1384), and schema-constrained JSON (L1309).
- For Codex, whose wire protocol is pinned to the Responses API (brief
  prior understanding), the load-bearing fact is that llama.cpp exposes
  POST `/v1/responses` (L1454) implemented as a translating shim over chat
  completions (L1494). Whether that shim satisfies Codex's streaming and
  tool expectations is not answerable from this snapshot (no streaming or
  tool documentation for the route) and must come from the Codex notes.
- For OpenCode's AI-SDK openai-compatible path, the documented surface
  (`/v1/chat/completions`, streaming, `response_format`, tools) appears to
  match, but the match is my inference from the two snapshots, not a claim
  of either source.
- The default model `id` being a GGUF file path (L1244) is a concrete
  interop hazard for agents that echo the model ID back in requests;
  `--alias` is the documented fix (L184, L1244).
- Open items this note leaves for synthesis: streaming behavior of
  `/v1/responses`; whether `parallel_tool_calls` holds for typical coding
  models; and context-window reporting under `--ctx-size` overrides (the
  server reports `n_ctx` in `/props` and slot state, L834, L983, but the
  interaction with model metadata `n_ctx_train` is not spelled out).

## Quotables for the report

- Scope disclaimer, for the generic-endpoint bar: "While no strong claims of
  compatibility with OpenAI API spec is being made, in our experience it
  suffices to support many apps." (L1272, L1303). Frame as: the reference
  server self-describes as best-effort compatible.
- Responses API presence and mechanism: "This endpoint works by converting
  Responses request into Chat Completions request." (L1494), heading "###
  POST `/v1/responses`: OpenAI-compatible Responses API" (L1454). Frame as:
  a generic server can answer Codex's Responses-wire requirement with a
  shim, at least for the non-streaming unknowns.
- Tool calling: "is supported with the `--jinja` flag (and may require a
  `--chat-template-file` override to get the right tool-use compatible
  Jinja template; worst case, `--chat-template chatml` may also work)."
  (L1384). Frame as: tool support is template-dependent, not guaranteed per
  model.
- Streaming wire format: "Responses are sent using the Server-sent events
  standard." (L600). Frame as: SSE is the contract for the streaming cell.
- Model ID default: "By default, model `id` field is the path to model
  file" (L1244). Frame as: aliasing is required for clean model-ID
  interop.
