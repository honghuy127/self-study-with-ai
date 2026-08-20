---
source_key: codexOssProviders
read_date: 2026-08-20
confidence: high
relevance: 3
repo: codex
commit: af700180808cce2ce28a31aad0fbad4dc58b857a
---

# Notes: Codex, Ollama and LM Studio providers and the Responses-wire mapping (codex)

## Source identification

- Key: `codexOssProviders`
- Repository: `codex` at `af700180808cce2ce28a31aad0fbad4dc58b857a` (see `sources/repos.yaml`;
  verified via `.git/HEAD` -> `refs/heads/main` -> `af700180808cce2ce28a31aad0fbad4dc58b857a`)
- Component scope: `codex-rs/ollama/` (lib.rs, client.rs, url.rs, pull.rs, parser.rs,
  line_buffer.rs), `codex-rs/lmstudio/` (lib.rs, client.rs),
  `codex-rs/model-provider-info/src/lib.rs` (oss provider entries, wire types). Consulted
  in support: `codex-rs/core/src/client.rs` (model request building),
  `codex-rs/codex-api/src/endpoint/responses.rs`, `codex-rs/codex-api/src/endpoint/session.rs`,
  `codex-rs/codex-api/src/provider.rs`, `codex-rs/codex-api/src/common.rs`,
  `codex-rs/config/src/config_toml.rs`, `codex-rs/utils/oss/src/lib.rs`,
  `codex-rs/utils/cli/src/shared_options.rs`, `codex-rs/exec/src/lib.rs`,
  `codex-rs/models-manager/src/model_info.rs`, `codex-rs/models-manager/src/manager.rs`,
  `codex-rs/models-manager/models.json`, `codex-rs/model-provider/src/models_endpoint.rs`,
  `codex-rs/codex-api/src/endpoint/models.rs`, `codex-rs/core/src/tools/spec_plan.rs`,
  `codex-rs/protocol/src/openai_models.rs`, `codex-rs/core/src/session/turn_context.rs`,
  `codex-rs/tui/src/oss_selection.rs`, `codex-rs/tui/src/startup_orchestration.rs`,
  `codex-rs/core/src/config/mod.rs`.
- Tier: codebase

## Purpose and role in the harness

Codex ships two built-in "oss" provider entries, `ollama` and `lmstudio`
(`codex-rs/model-provider-info/src/lib.rs:490-491`), registered alongside `openai`,
`amazon-bedrock`, and `amazon-bedrock-runtime` in `built_in_model_providers`
(`codex-rs/model-provider-info/src/lib.rs:494-526`). They are the integration surface for
running Codex against a local open-model server: selecting `--oss` on the CLI resolves one
of the two providers, ensures the server is reachable, pulls/downloads the default model if
missing, and then runs the normal Codex session against the provider's base URL
(`codex-rs/exec/src/lib.rs:361-404`, `codex-rs/exec/src/lib.rs:685-700`,
`codex-rs/utils/oss/src/lib.rs:17-39`).

The decisive design fact: both oss providers are created with `WireApi::Responses`
(`codex-rs/model-provider-info/src/lib.rs:514-521`), so Ollama and LM Studio are spoken to
with the same Responses-API wire used for OpenAI. The Ollama client crate and LM Studio
client crate never carry model inference traffic. They do housekeeping: server probes,
model listing, version gating (Ollama), model pulling/downloading, and model preloading.
Model requests themselves go through the shared Responses client (Mechanism, below).

## Mechanism

### Provider registration and the Responses-only wire

`WireApi` is a single-variant enum, `Responses`
(`codex-rs/model-provider-info/src/lib.rs:61-67`); its `Display` is `"responses"`
(`codex-rs/model-provider-info/src/lib.rs:69-76`). The custom deserializer accepts only
`"responses"`; `"chat"` produces a hard error with the message
`` `wire_api = \"chat\"` is no longer supported. `` plus a fix instruction
(`codex-rs/model-provider-info/src/lib.rs:56`,
`codex-rs/model-provider-info/src/lib.rs:78-90`). The former `ollama-chat` provider ID is
likewise rejected: `LEGACY_OLLAMA_CHAT_PROVIDER_ID` is `"ollama-chat"` and
`validate_oss_provider` returns `OLLAMA_CHAT_PROVIDER_REMOVED_ERROR` for it
(`codex-rs/model-provider-info/src/lib.rs:57-58`,
`codex-rs/config/src/config_toml.rs:946-960`). There is no chat-completions path anywhere
in the wire layer at this commit.

The oss provider entry is built by `create_oss_provider` /
`create_oss_provider_with_base_url`: name `"gpt-oss"`, a base URL of
`http://localhost:{port}/v1`, `env_key: None`, no auth fields,
`requires_openai_auth: false`, `supports_websockets: false`,
`supports_standalone_web_search: false`
(`codex-rs/model-provider-info/src/lib.rs:575-615`). Both oss providers are registered with
`WireApi::Responses` (`codex-rs/model-provider-info/src/lib.rs:514-521`), and both IDs are
reserved against user override in config.toml
(`codex-rs/config/src/config_toml.rs:63-69`, `codex-rs/config/src/config_toml.rs:283-286`).

At turn time the transport selection matches on the provider's `wire_api`, and the match has
a single arm, `WireApi::Responses` (`codex-rs/core/src/client.rs:1872-1911`). Within that
arm, the WebSocket transport is taken only when `info().supports_websockets` is true
(`codex-rs/core/src/client.rs:955-963`); the oss entries set it false
(`codex-rs/model-provider-info/src/lib.rs:612`), so oss sessions use the HTTP streaming
path `stream_responses_api` (`codex-rs/core/src/client.rs:1899-1909`,
`codex-rs/core/src/client.rs:1440-1564`). Net effect: the Responses-only wire is not
translated, downgraded, or bypassed for ollama/lmstudio. It is applied unchanged, and the
local server must implement it.

### Request building and endpoint path (Q1)

`build_responses_request` assembles a `ResponsesApiRequest` regardless of provider:
`model`, `instructions`, `input`, `tools` (raw JSON from
`create_tools_raw_json_for_responses_api`), `tool_choice: "auto"`,
`parallel_tool_calls`, `reasoning: Some(...)`, `store: false`, `stream: true`,
`include: ["reasoning.encrypted_content"]`, `text`, `client_metadata`
(`codex-rs/core/src/client.rs:845-940`; request struct at
`codex-rs/codex-api/src/common.rs:251-275`). The only provider-keyed adjustment in request
building is `is_openai()` (name == `"OpenAI"`,
`codex-rs/model-provider-info/src/lib.rs:459-461`); for non-OpenAI providers, which
includes the `"gpt-oss"` oss entries (`codex-rs/model-provider-info/src/lib.rs:596`),
Codex strips internal chat message metadata and clears `encrypted_function_args` on
function-call input items (`codex-rs/core/src/client.rs:855-867`).

The request is POSTed by `ResponsesClient::stream_request`
(`codex-rs/codex-api/src/endpoint/responses.rs:70-98`), whose path is the literal
`"responses"` (`codex-rs/codex-api/src/endpoint/responses.rs:100-102`), joined to the
provider base URL by `Provider::url_for_path` (`codex-rs/codex-api/src/provider.rs:53-75`),
with `Accept: text/event-stream` and SSE parsing of the response
(`codex-rs/codex-api/src/endpoint/responses.rs:140-155`,
`codex-rs/core/src/client.rs:1440-1523`). The base URLs are
`http://localhost:11434/v1` (ollama) and `http://localhost:1234/v1` (lmstudio)
(`codex-rs/model-provider-info/src/lib.rs:578-591`,
`codex-rs/model-provider-info/src/lib.rs:487-488`), so model traffic goes to
`POST http://localhost:11434/v1/responses` and `POST http://localhost:1234/v1/responses`.
Streaming is always on (`stream: true`, `codex-rs/core/src/client.rs:933`).

The LM Studio client confirms the responses path is the local contract Codex assumes: its
`load_model` helper warms a model by POSTing to `{base_url}/responses` with body
`{"model": model, "input": "", "max_output_tokens": 1}`
(`codex-rs/lmstudio/src/client.rs:70-77`).

### The `--oss` bootstrap path

CLI surface: `--oss` (`codex-rs/utils/cli/src/shared_options.rs:25-27`),
`--local-provider` mapped to the `oss_provider` field
(`codex-rs/utils/cli/src/shared_options.rs:29-32`), and `-m/--model`
(`codex-rs/utils/cli/src/shared_options.rs:21-23`). Under `--oss`, exec resolves the
provider via `resolve_oss_provider`: explicit `--local-provider` wins, else the
`oss_provider` key in config.toml (`codex-rs/core/src/config/mod.rs:2541-2553`). With
neither, it errors: "No default OSS provider configured. Use --local-provider=provider or
set oss_provider to one of: lmstudio, ollama in config.toml"
(`codex-rs/exec/src/lib.rs:381-389`). Without `-m`, the model defaults per provider
(`codex-rs/exec/src/lib.rs:395-404`, `codex-rs/utils/oss/src/lib.rs:8-14`).

Before the session runs, `ensure_oss_provider_ready` per provider
(`codex-rs/utils/oss/src/lib.rs:17-39`, `codex-rs/exec/src/lib.rs:685-700`):

- Ollama: construct `OllamaClient` from the config's provider entry, which probes the
  server (`codex-rs/ollama/src/client.rs:43-58`, `codex-rs/ollama/src/client.rs:71-95`,
  `codex-rs/ollama/src/client.rs:98-129`); check Responses support from the server version
  (`codex-rs/utils/oss/src/lib.rs:27-33`, `codex-rs/ollama/src/lib.rs:57-70`); then pull the
  model if missing (`codex-rs/ollama/src/lib.rs:22-44`).
- LM Studio: construct `LMStudioClient` (probe `GET {base_url}/models`,
  `codex-rs/lmstudio/src/client.rs:19-67`), download the model via the `lms` CLI if missing
  (`codex-rs/lmstudio/src/lib.rs:22-27`, `codex-rs/lmstudio/src/client.rs:173-195`), then
  spawn a background task that warms the model through `load_model`
  (`codex-rs/lmstudio/src/lib.rs:34-43`).

Also under `--oss`, exec forces raw agent reasoning display on
(`codex-rs/exec/src/lib.rs:429`).

### Ollama version gate

`ensure_responses_supported` requires the Ollama server to report version >= `0.13.4`
(`codex-rs/ollama/src/lib.rs:46-52`, `codex-rs/ollama/src/lib.rs:57-70`); version `0.0.0`
is treated as supported (dev builds, `codex-rs/ollama/src/lib.rs:50-52`). The version comes
from `GET {host}/api/version` (`codex-rs/ollama/src/client.rs:158-181`). Too-old servers
fail with "Ollama {version} is too old. Codex requires Ollama {min} or newer."
(`codex-rs/ollama/src/lib.rs:66-69`). If the version endpoint is missing or unparsable, the
check returns `Ok(())` (`codex-rs/ollama/src/lib.rs:57-60`,
`codex-rs/ollama/src/client.rs:166-180`).

### Ollama housekeeping and pull machinery (Q5)

The Ollama client talks to Ollama's *native* API only for logistics, never for inference:

- Server probe: `GET {host}/v1/models` when the configured `base_url` ends with `/v1`,
  else `GET {host}/api/tags` (`codex-rs/ollama/src/client.rs:98-103`,
  `codex-rs/ollama/src/url.rs:2-4`). Connect timeout is `OLLAMA_CONNECTION_TIMEOUT =
  Duration::from_secs(5)` (`codex-rs/ollama/src/client.rs:30`); on failure the user sees
  "No running Ollama server detected. Start it with: `ollama serve` ..."
  (`codex-rs/ollama/src/client.rs:29`).
- Model listing: `GET {host}/api/tags`, extracting `models[].name`
  (`codex-rs/ollama/src/client.rs:132-155`).
- Version: `GET {host}/api/version`, stripping a leading `v` before semver parsing
  (`codex-rs/ollama/src/client.rs:158-181`).
- Pull: `POST {host}/api/pull` with body `{"model": model, "stream": true}`
  (`codex-rs/ollama/src/client.rs:185-196`). The response is an NDJSON byte stream fed
  through `LineBuffer`, a memchr-based incremental line splitter
  (`codex-rs/ollama/src/line_buffer.rs:6-28`); each JSON line becomes events via
  `pull_events_from_value`, reading keys `status`, `digest`, `total`, `completed`
  (`codex-rs/ollama/src/parser.rs:6-29`). Events are `PullEvent::{Status, ChunkProgress,
  Success, Error}` (`codex-rs/ollama/src/pull.rs:6-21`). Success or failure is read from
  the event stream, not the HTTP status, because "ollama returns a 200 OK response even
  when the output stream includes an error message" (`codex-rs/ollama/src/client.rs:255-263`).
- Progress rendering: `CliProgressReporter` writes inline stderr progress, suppresses the
  "pulling manifest" status (`codex-rs/ollama/src/pull.rs:60-70`), prints a header
  `Downloading model: total {gb:.2} GB` (`codex-rs/ollama/src/pull.rs:94-100`), then a
  per-chunk line `{done_gb:.2}/{total_gb:.2} GB ({pct:.1}%) {speed_mb_s:.1} MB/s`
  (`codex-rs/ollama/src/pull.rs:111-120`). `TuiProgressReporter` delegates to the CLI
  reporter (`codex-rs/ollama/src/pull.rs:138-147`).

Base URL handling stitches the two surfaces together: `base_url_to_host_root` strips a
trailing `/v1` so the OpenAI-style base URL `http://localhost:11434/v1` yields the native
root `http://localhost:11434` for `/api/*` calls (doc example and implementation at
`codex-rs/ollama/src/url.rs:6-18`).

### LM Studio housekeeping

- Probe and listing: `GET {base_url}/models`; listing parses `data[].id`
  (`codex-rs/lmstudio/src/client.rs:51-67`, `codex-rs/lmstudio/src/client.rs:100-129`).
  Connect timeout 5 s (`codex-rs/lmstudio/src/client.rs:16`); error text: "LM Studio is not
  responding. Install from https://lmstudio.ai/download and run 'lms server start'."
  (`codex-rs/lmstudio/src/client.rs:15`).
- Download: shells out to `lms get --yes {model}`, locating `lms` on PATH or at
  `{home}/.lmstudio/bin/lms` (`.exe` on Windows) (`codex-rs/lmstudio/src/client.rs:132-171`,
  `codex-rs/lmstudio/src/client.rs:173-195`).
- Preload: background `POST {base_url}/responses` with empty input and
  `max_output_tokens: 1` (`codex-rs/lmstudio/src/lib.rs:34-43`,
  `codex-rs/lmstudio/src/client.rs:70-77`).
- Default model: `DEFAULT_OSS_MODEL = "openai/gpt-oss-20b"`
  (`codex-rs/lmstudio/src/lib.rs:7`), versus Ollama's `"gpt-oss:20b"`
  (`codex-rs/ollama/src/lib.rs:16`).

### Model metadata and feature gating (Q4)

Feature differentiation is keyed by model metadata (`ModelInfo`), not by provider ID. The
bundled catalog at this commit contains only gpt-5.x family and review models (slugs at
`codex-rs/models-manager/models.json:4`, `:118`, `:230`, `:338`, `:444`, `:548`, `:647`,
`:743`). `construct_model_info_from_candidates` tries longest-prefix slug match, then a
single-segment namespace-stripped suffix match, and otherwise falls back to
`model_info_from_slug` (`codex-rs/models-manager/src/manager.rs:654-672`,
`codex-rs/models-manager/src/manager.rs:617-652`). Neither `gpt-oss:20b` nor
`openai/gpt-oss-20b` (suffix `gpt-oss-20b`) matches a bundled slug, so both default oss
models resolve to fallback metadata (`codex-rs/models-manager/src/model_info.rs:139-186`),
with warning "Unknown model {slug} is used. This will use fallback model metadata."
(`codex-rs/models-manager/src/model_info.rs:141`).

Fallback metadata values relevant to compatibility:

- `apply_patch_tool_type: None` (`codex-rs/models-manager/src/model_info.rs:165`). The
  apply_patch handler is registered only when
  `turn_context.model_info.apply_patch_tool_type.is_some()`
  (`codex-rs/core/src/tools/spec_plan.rs:1112-1116`), and the only tool type that exists is
  `Freeform` (`codex-rs/protocol/src/openai_models.rs:307-311`). So the apply_patch tool is
  not offered to the default oss models. I found no provider-ID check in the tool plan;
  the rest of the tool registry is gated by features and environment, so tool calling
  itself remains available (inference; see Relevance).
- Tool calling is always sent on the wire: serialized tool definitions, `tool_choice:
  "auto"`, `parallel_tool_calls: true` for unknown/fallback models (non-responses-lite)
  (`codex-rs/core/src/client.rs:892-897`, `codex-rs/core/src/client.rs:929-930`).
- Structured output: an output schema becomes `text.format` of type `json_schema` with
  `strict` and `name: "codex_output_schema"`, with no provider gate; the `text` field is
  omitted entirely when there is neither verbosity nor schema
  (`codex-rs/core/src/client.rs:917-921`, `codex-rs/codex-api/src/common.rs:361-379`,
  `codex-rs/codex-api/src/common.rs:176-196`). Fallback metadata sets
  `support_verbosity: false` (`codex-rs/models-manager/src/model_info.rs:163`), so no
  verbosity field is emitted for oss models unless user config sets one, in which case a
  warning logs (`codex-rs/core/src/client.rs:906-916`).
- Reasoning: `build_reasoning` emits `effort` only when a per-turn effort or
  `model_info.default_reasoning_level` is present (fallback has `None`, so effort is
  omitted by serde skip), and emits `summary` only when
  `supports_reasoning_summary_parameter` is true (fallback: `true`) and summary is not
  `None` (`codex-rs/core/src/client.rs:825-843`,
  `codex-rs/models-manager/src/model_info.rs:146-147`,
  `codex-rs/models-manager/src/model_info.rs:161-162`,
  `codex-rs/codex-api/src/common.rs:148-156`). The default summary is
  `ReasoningSummary::Auto` applied from `model_info.default_reasoning_summary`
  (`codex-rs/models-manager/src/model_info.rs:162`,
  `codex-rs/core/src/session/turn_context.rs:608-610`). `include:
  ["reasoning.encrypted_content"]` is always present
  (`codex-rs/core/src/client.rs:905`); `stream_options` (sequential reasoning summary
  delivery) is only built for OpenAI (`codex-rs/core/src/client.rs:899-904`).
  `use_responses_lite: false` in fallback metadata
  (`codex-rs/models-manager/src/model_info.rs:178`), so the responses-lite header and tool
  prefixing do not apply (`codex-rs/core/src/client.rs:868-897`).
- Context accounting: fallback `context_window: Some(272_000)` and
  `max_context_window: Some(272_000)` (`codex-rs/models-manager/src/model_info.rs:169-170`),
  `effective_context_window_percent: 95` (`codex-rs/models-manager/src/model_info.rs:173`),
  `auto_compact_token_limit: None` (`codex-rs/models-manager/src/model_info.rs:171`), which
  core derives as 90% of the context window, i.e. `(context_window * 9) / 10`
  (`codex-rs/protocol/src/openai_models.rs:436-440`,
  `codex-rs/protocol/src/openai_models.rs:488-499`; 272,000 * 9 / 10 = 244,800). Tool
  output truncation defaults to 10,000-byte budgets
  (`codex-rs/models-manager/src/model_info.rs:167`).
- Search: `supports_search_tool: false`, `web_search_tool_type: Text`
  (`codex-rs/models-manager/src/model_info.rs:166`,
  `codex-rs/models-manager/src/model_info.rs:177`); provider entries set
  `supports_standalone_web_search: false`
  (`codex-rs/model-provider-info/src/lib.rs:613`).

## Key facts with anchors

- F1 (`codex-rs/model-provider-info/src/lib.rs:514-521`): the built-in `ollama` and
  `lmstudio` providers are both registered as `WireApi::Responses`.
- F2 (`codex-rs/core/src/client.rs:1872-1911`): the streaming transport match on
  `wire_api` has exactly one arm, `WireApi::Responses`; there is no chat path.
  `wire_api = "chat"` in config fails deserialization with a removal error
  (`codex-rs/model-provider-info/src/lib.rs:56`, `codex-rs/model-provider-info/src/lib.rs:86`),
  and the legacy `ollama-chat` provider ID is rejected
  (`codex-rs/config/src/config_toml.rs:946-952`).
- F3 (`codex-rs/codex-api/src/endpoint/responses.rs:100-102`,
  `codex-rs/codex-api/src/provider.rs:53-75`): model requests are
  `POST {base_url}/responses` with `Accept: text/event-stream`, i.e.
  `http://localhost:11434/v1/responses` (ollama) and
  `http://localhost:1234/v1/responses` (lmstudio), streamed via SSE.
- F4 (`codex-rs/ollama/src/lib.rs:46-70`): Ollama servers older than `0.13.4` (except
  version `0.0.0`) are rejected before use with "Ollama {version} is too old. Codex
  requires Ollama {min} or newer."
- F5 (`codex-rs/model-provider-info/src/lib.rs:575-615`): oss provider entries have
  `env_key: None`, no auth, `requires_openai_auth: false`, `supports_websockets: false`;
  the base URL overrides come from `CODEX_OSS_BASE_URL` and `CODEX_OSS_PORT`
  (`codex-rs/model-provider-info/src/lib.rs:578-591`).
- F6 (`codex-rs/models-manager/src/model_info.rs:139-186`): unknown slugs (both oss
  defaults are absent from the bundled catalog, `codex-rs/models-manager/models.json:4-743`)
  get fallback metadata with `apply_patch_tool_type: None` and
  `context_window: Some(272_000)`.
- F7 (`codex-rs/core/src/tools/spec_plan.rs:1112-1116`): the apply_patch tool is registered
  only when `apply_patch_tool_type.is_some()`, so it is absent for the default oss models.
- F8 (`codex-rs/core/src/client.rs:825-843`, `codex-rs/core/src/session/turn_context.rs:608-610`):
  oss requests carry `reasoning.summary` (default `auto`) but no `reasoning.effort` unless
  the user sets one; `include: ["reasoning.encrypted_content"]` is always sent
  (`codex-rs/core/src/client.rs:905`).
- F9 (`codex-rs/core/src/client.rs:855-867`): for non-OpenAI providers (the oss entries'
  name is `"gpt-oss"`), internal chat metadata and encrypted function args are stripped
  from input items before sending.
- F10 (`codex-rs/ollama/src/client.rs:185-196`, `codex-rs/ollama/src/client.rs:255-263`):
  model pulls use `POST /api/pull` with NDJSON progress; success/failure is decoded from
  the stream because Ollama returns 200 even on in-stream errors.
- F11 (`codex-rs/lmstudio/src/client.rs:70-77`, `codex-rs/lmstudio/src/client.rs:173-195`):
  LM Studio models are warmed via `POST {base}/responses` with `max_output_tokens: 1` and
  downloaded by shelling out to `lms get --yes {model}`.
- F12 (`codex-rs/model-provider/src/models_endpoint.rs:38-39`,
  `codex-rs/model-provider/src/models_endpoint.rs:84-87`): model catalog refresh queries
  the active provider's `/models` with a 5 s timeout and expects the rich Codex
  `ModelsResponse` schema (`codex-rs/codex-api/src/endpoint/models.rs:70-76`).

## Configuration and defaults

Character-exact keys, env vars, and defaults:

- Provider IDs: `OLLAMA_OSS_PROVIDER_ID = "ollama"`, `LMSTUDIO_OSS_PROVIDER_ID =
  "lmstudio"` (`codex-rs/model-provider-info/src/lib.rs:490-491`); legacy rejected ID
  `"ollama-chat"` (`codex-rs/model-provider-info/src/lib.rs:57`).
- Ports: `DEFAULT_LMSTUDIO_PORT: u16 = 1234`, `DEFAULT_OLLAMA_PORT: u16 = 11434`
  (`codex-rs/model-provider-info/src/lib.rs:487-488`). Built-in base URLs are
  `http://localhost:11434/v1` and `http://localhost:1234/v1`
  (`codex-rs/model-provider-info/src/lib.rs:578-591`).
- Env vars: `CODEX_OSS_PORT` (parsed as u16, overrides the port), `CODEX_OSS_BASE_URL`
  (overrides the whole base URL); both documented in-code as experimental
  (`codex-rs/model-provider-info/src/lib.rs:576-591`).
- config.toml keys: `model` (`codex-rs/config/src/config_toml.rs:154-155`),
  `model_provider` ("Provider to use from the model_providers map.",
  `codex-rs/config/src/config_toml.rs:159-160`), `model_context_window`
  (`codex-rs/config/src/config_toml.rs:162-163`), `model_auto_compact_token_limit`
  (`codex-rs/config/src/config_toml.rs:165-166`), `model_providers` (user entries; built-in
  IDs cannot be overridden, `codex-rs/config/src/config_toml.rs:283-286`),
  `model_reasoning_effort` (`codex-rs/config/src/config_toml.rs:347`),
  `model_reasoning_summary` (`codex-rs/config/src/config_toml.rs:349`), `model_verbosity`
  (`codex-rs/config/src/config_toml.rs:351`), and `oss_provider` ("Preferred OSS provider
  for local models, e.g. \"lmstudio\" or \"ollama\".",
  `codex-rs/config/src/config_toml.rs:511-512`). `oss_provider` accepts only `lmstudio` and
  `ollama` (`codex-rs/config/src/config_toml.rs:946-960`).
- CLI flags: `--oss`, `--local-provider` (lmstudio or ollama), `-m/--model`
  (`codex-rs/utils/cli/src/shared_options.rs:21-32`).
- Default models: ollama `"gpt-oss:20b"` (`codex-rs/ollama/src/lib.rs:16`); lmstudio
  `"openai/gpt-oss-20b"` (`codex-rs/lmstudio/src/lib.rs:7`).
- Timeouts: Ollama client connect `Duration::from_secs(5)`
  (`codex-rs/ollama/src/client.rs:30`); LM Studio client connect `Duration::from_secs(5)`
  (`codex-rs/lmstudio/src/client.rs:16`); models refresh timeout `Duration::from_secs(5)`
  (`codex-rs/model-provider/src/models_endpoint.rs:38`); TUI localhost probes timeout after
  `Duration::from_secs(2)` (`codex-rs/tui/src/oss_selection.rs:422-434`).
- Persistence: the TUI writes the chosen provider back as `oss_provider = "..."` via
  `set_default_oss_provider` (`codex-rs/core/src/config/mod.rs:2256-2270`,
  `codex-rs/tui/src/config_update.rs:154-156`).
- No API key material is configured for the oss providers (`env_key: None`,
  `codex-rs/model-provider-info/src/lib.rs:598`; `api_key()` returns `Ok(None)` when
  `env_key` is `None`, `codex-rs/model-provider-info/src/lib.rs:331-347`).

## Limitations and unknowns

- Static trace only. Whether Ollama >= 0.13.4 or LM Studio actually accept the full
  request shape (tools JSON, `parallel_tool_calls`, `reasoning.summary`,
  `include: ["reasoning.encrypted_content"]`, `prompt_cache_key`, `client_metadata`) is not
  decidable from this checkout; that belongs to the doc snapshots of the servers'
  OpenAI/Responses compatibility in this study's registry.
- Whether fallback metadata really applies at runtime depends on the models-catalog
  refresh, which queries the active provider's `/models` endpoint and expects the rich
  Codex `ModelsResponse` schema (`codex-rs/model-provider/src/models_endpoint.rs:75-115`,
  `codex-rs/codex-api/src/endpoint/models.rs:70-76`). A plain OpenAI-style models list from
  a local server may fail to decode, in which case the bundled catalog stands and fallback
  metadata applies; but a server that serves the rich schema could override it.
  [EVIDENCE NEEDED: no fixture in the pinned tree exercises this refresh against an oss
  provider. Looked at `codex-rs/models-manager/src/manager.rs:186-199` and
  `codex-rs/models-manager/src/manager.rs:271-284`.]
- The TUI status list still shows an "Ollama (Chat)" entry
  (`codex-rs/tui/src/oss_selection.rs:122-125`), but the selection options are only LM
  Studio and Ollama/Responses (`codex-rs/tui/src/oss_selection.rs:68-83`). I read this as a
  display leftover from the chat-wire removal (interpretation, not a code fact).
- I traced the apply_patch gate but did not enumerate every other tool handler in
  `codex-rs/core/src/tools/spec_plan.rs`; shell/edit tool availability for oss models
  beyond the apply_patch gate is not characterized here.
- Auto-compaction and context accounting numbers for oss models derive from fallback
  metadata (272,000 window, 90% compaction threshold); user overrides via
  `model_context_window` and `model_auto_compact_token_limit` are applied afterward
  (`codex-rs/models-manager/src/model_info.rs:25-50`), but typical user behavior is out of
  scope for a static trace.

## Relevance to the brief

This component answers the brief's named open question on Codex (prior understanding: "how
the ollama/lmstudio provider entries fit that constraint"): they fit by making the local
servers speak the Responses API. Codex's Codex-side contract is (Q1, Q2): native provider
code registers `ollama`/`lmstudio` as Responses-wire providers at
`http://localhost:{11434,1234}/v1`, POSTs SSE-streamed `/responses` requests built by the
same code path used for OpenAI, and hard-errors on any chat-wire configuration. The oss
crates themselves are logistics (probes, version gate, pull/download, preload), not wire
translation. For the compatibility matrix, Codex's Ollama and LM Studio cells are native
provider code, and the minimum server contract is "Responses API at /v1/responses",
with an Ollama version floor of 0.13.4 enforced client-side.

For RQ2 (minimum contract) and RQ3 (degradation), the fallback-metadata facts are the
sharpest findings: open models get tool calling and JSON-schema structured output on the
wire but no apply_patch tool (`apply_patch_tool_type: None`), a 272,000-token context
assumption, and an always-present `reasoning.summary: auto` unless configured otherwise.
These are candidate degradation points to cross-check against the server-side doc notes in
this study before the matrix cells are filled.

## Quotables for the report

- Single-arm wire match (framing: Codex has no chat fallback; open-model providers inherit
  the Responses wire verbatim): `match wire_api { WireApi::Responses => { ... } }`
  (`codex-rs/core/src/client.rs:1873-1874`).
- Ollama version floor (framing: client-side capability gate on the Responses surface):
  `Version::new(0, 13, 4)` in `min_responses_version` (`codex-rs/ollama/src/lib.rs:46-48`)
  and the error "Codex requires Ollama {min} or newer." (`codex-rs/ollama/src/lib.rs:67-69`).
- OSS base URL construction (framing: the local contract is /v1/responses):
  `format!("http://localhost:{codex_oss_port}/v1", ...)`
  (`codex-rs/model-provider-info/src/lib.rs:578-585`).
- apply_patch gating (framing: patch-tool absence comes from model metadata, not provider
  config): `turn_context.model_info.apply_patch_tool_type.is_some()`
  (`codex-rs/core/src/tools/spec_plan.rs:1112`).
- Fallback context window (framing: unknown open models are assumed to have 272k context):
  `context_window: Some(272_000)` (`codex-rs/models-manager/src/model_info.rs:169`).
- Ollama error semantics on pulls (framing: the client distrusts HTTP status and parses
  the NDJSON stream): comment "Empirically, ollama returns a 200 OK response even when the
  output stream includes an error message." (`codex-rs/ollama/src/client.rs:256-263`).
