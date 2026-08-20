---
source_key: lmstudioServerDocs
read_date: 2026-08-20
confidence: high
relevance: 3
---

# Notes: LM Studio docs: running the local LLM API server

## Source identification

- Key: lmstudioServerDocs
- Authors, year, venue: LM Studio (lmstudio-ai), 2026, docs.lmstudio.ai (snapshotted via github.com/lmstudio-ai/docs)
- Tier: docs
- URL / DOI: https://docs.lmstudio.ai/developers/local-server
- Evidence files read:
  - `sources/docs/lmstudioServer.md` (primary, 33 lines; registry key `lmstudioServerDocs`, snapshot field).
  - `sources/docs/lmstudioChatCompletions.md` (51 lines, skimmed because the primary page lists "OpenAI-compatible" endpoints at lmstudioServer.md:11 and lmstudioServer.md:32; the registry provenance query identifies this snapshot as the openai-compat chat-completions page, sources/registry.yaml:22).
- Anchors below are `<snapshot>:<line>` in these files. Provenance caveat: the snapshots come from the lmstudio-ai docs-repo mirror at main HEAD on 2026-08-20, not the live docs site, which was unreachable from the gathering environment (sources/registry.yaml:34).

## Problem and motivation

The page is the landing page for LM Studio's developer server docs (frontmatter `index: 1`, lmstudioServer.md:6) and states the product capability bluntly: "Run an LLM API server on localhost with LM Studio" (lmstudioServer.md:4). Its stated scope is serving "local LLMs from LM Studio's Developer tab, either on `localhost` or on the network" (lmstudioServer.md:9). The page exists to route developers to the API families (REST API, SDKs, compatibility endpoints), each linked and enumerated (lmstudioServer.md:11, lmstudioServer.md:29-33).

## Method or core idea

How the server starts, per the source:

1. GUI path: "go to the Developer tab in LM Studio, and toggle the \"Start server\" switch to start the API server" (lmstudioServer.md:17). An accompanying screenshot caption reads "Load and serve LLMs from LM Studio" (lmstudioServer.md:13).
2. CLI path: "you can use `lms` ([LM Studio's CLI](/docs/cli)) to start the server from your terminal" (lmstudioServer.md:21), command `lms server start` (lmstudioServer.md:24).

API surface, per the source. The page states: "LM Studio's APIs can be used through [REST API](/docs/developer/rest), client libraries like [lmstudio-js](/docs/typescript) and [lmstudio-python](/docs/python), and compatibility endpoints like [OpenAI-compatible](/docs/developer/openai-compat) and [Anthropic-compatible](/docs/developer/anthropic-compat)." (lmstudioServer.md:11). The "API options" list repeats these five entries (lmstudioServer.md:29-33): "LM Studio REST API", "TypeScript SDK ... `lmstudio-js`", "Python SDK ... `lmstudio-python`", "OpenAI-compatible endpoints", "Anthropic-compatible endpoints". Paths mentioned are documentation page paths (`/docs/developer/rest`, `/docs/typescript`, `/docs/python`, `/docs/developer/openai-compat`, `/docs/developer/anthropic-compat`, `/docs/cli`), not HTTP endpoint paths (lmstudioServer.md:11, lmstudioServer.md:29-33).

OpenAI-compatible chat completions detail (skimmed snapshot):

- "Method: `POST`" and "Prompt template is applied automatically for chat‑tuned models" (lmstudioChatCompletions.md:9-10).
- The Python example constructs the OpenAI SDK client against the local server: `client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")` and calls `client.chat.completions.create` with `model="model-identifier"` (lmstudioChatCompletions.md:18-22).
- Inference parameters are supplied in the payload (lmstudioChatCompletions.md:11); the example sets `temperature=0.7` (lmstudioChatCompletions.md:27). Parameter semantics defer to OpenAI's reference: "See https://platform.openai.com/docs/api-reference/chat/create for parameter semantics." (lmstudioChatCompletions.md:35; also lmstudioChatCompletions.md:12).
- Supported payload parameters, listed character-exact (lmstudioChatCompletions.md:38-50): `model`, `top_p`, `top_k`, `messages`, `temperature`, `max_tokens`, `stream`, `stop`, `presence_penalty`, `frequency_penalty`, `logit_bias`, `repeat_penalty`, `seed`.
- Debugging aid: "keep a terminal open with [`lms log stream`](/docs/cli/serve/log-stream) to inspect model input" (lmstudioChatCompletions.md:13).

## Key claims with anchors

Source claims, quoted character-exact:

- Claim 1 (lmstudioServer.md:9): "You can serve local LLMs from LM Studio's Developer tab, either on `localhost` or on the network." Local and network serving are both first-class.
- Claim 2 (lmstudioServer.md:17): the server starts from a "Start server" switch in the Developer tab; the CLI alternative is `lms server start` (lmstudioServer.md:21, lmstudioServer.md:24).
- Claim 3 (lmstudioServer.md:11): three API families plus two client libraries: "REST API", "OpenAI-compatible" and "Anthropic-compatible" endpoints, "lmstudio-js" and "lmstudio-python". Anthropic compatibility is a named, documented surface of the local server.
- Claim 4 (lmstudioChatCompletions.md:19): the OpenAI-compatible example uses base URL `http://localhost:1234/v1` and API key `lm-studio` (both character-exact). This is the only port reference in either snapshot: `1234` appears solely inside this example URL; lmstudioServer.md names no port.
- Claim 5 (lmstudioChatCompletions.md:10): "Prompt template is applied automatically for chat‑tuned models", i.e. the server handles chat templating.
- Claim 6 (lmstudioChatCompletions.md:38-50): the chat completions payload accepts 13 parameters, including `stream`, `max_tokens`, `top_k`, `repeat_penalty`, `seed`.
- Claim 7 (lmstudioChatCompletions.md:12, lmstudioChatCompletions.md:35): the surface is defined by reference to OpenAI's chat API documentation.

Inferences I draw, not stated in the snapshots, marked as such:

- Inference: the endpoint path is `/v1/chat/completions` under the base URL. The snapshots never spell out an HTTP path; this follows only from combining `base_url="http://localhost:1234/v1"` with the SDK call `client.chat.completions.create` (lmstudioChatCompletions.md:19, lmstudioChatCompletions.md:21).
- Inference: `top_k` and `repeat_penalty` extend the OpenAI chat parameter set (the snapshot defers parameter semantics to OpenAI's reference at lmstudioChatCompletions.md:35 without contrasting the lists).
- Inference: models must be loaded into LM Studio before serving. The only support is the caption "Load and serve LLMs from LM Studio" (lmstudioServer.md:13) and serving "from LM Studio's Developer tab" (lmstudioServer.md:9); no explicit loading requirement is stated. Model-loading requirement as a contract term: `[CITATION NEEDED]` (looked: both snapshots, full text).
- Inference: whether the server enforces the API key is unknown from these snapshots; `api_key="lm-studio"` appears only as an example value (lmstudioChatCompletions.md:19). Auth enforcement: `[CITATION NEEDED]` (looked: both snapshots; lmstudioServer.md contains no auth text).

## Evaluation and evidence

This is product documentation, so there are no datasets, metrics, baselines, or benchmarks. Every number located, character-exact:

- Port: `1234`, inside `http://localhost:1234/v1` (lmstudioChatCompletions.md:19).
- Example key string: `lm-studio` (lmstudioChatCompletions.md:19).
- Example temperature: `0.7` (lmstudioChatCompletions.md:27).
- Payload parameter count: 13 (lmstudioChatCompletions.md:38-50).

Context-window reporting by the server: `[CITATION NEEDED]`. Looked: full text of both snapshots; neither mentions context length, context window, or token limits. Tool calling: not covered in these two snapshots; the registry tracks a separate entry `lmstudioCompatToolsDocs` for it (sources/registry.yaml:129-139).

## Limitations

- Port behavior is attested only by one example URL (lmstudioChatCompletions.md:19). Whether `1234` is the default, configurable, or the network-serving port is not stated; lmstudioServer.md:9 asserts network serving without any configuration detail.
- Auth is attested only by the example string `lm-studio` (lmstudioChatCompletions.md:19). No statement of whether the key is required, validated, or ignored, locally or on the network.
- The Anthropic-compatible surface is named but not described anywhere in the read snapshots (lmstudioServer.md:11, lmstudioServer.md:33): no paths, request shape, or auth for it. The anthropic-compat snapshot was not in this entry's reading set and is not cited here.
- The OpenAI-compatible HTTP endpoint path is never spelled out literally; only the base URL plus an SDK call exists as evidence (lmstudioChatCompletions.md:19-21).
- Model-loading requirements before serving are not stated as requirements (see inference above, lmstudioServer.md:13).
- Screenshots referenced at lmstudioServer.md:13 and lmstudioServer.md:19 are image assets not present in the snapshot, so any UI detail they carry is unavailable.
- Snapshot provenance: mirror of the docs repo at main HEAD on 2026-08-20, not the live docs site; drift between this mirror and the shipped LM Studio app is not assessed (sources/registry.yaml:34).

## Relevance to the brief

My inference, separated from source claims:

- RQ1, LM Studio column: LM Studio documents two distinct compat surfaces, OpenAI-compatible and Anthropic-compatible, from a single local server (lmstudioServer.md:11). This means the LM Studio cell of the compatibility matrix should be split by protocol: agents speaking the OpenAI chat protocol (Codex, OpenCode) attach to `http://localhost:1234/v1`, while an Anthropic-protocol client (Claude Code speaks Anthropic's API per the brief's prior understanding) has a documented Anthropic-compatible surface to point at, named on the same page. The Anthropic surface's actual contract cannot be confirmed from this entry's snapshots, so any Claude Code cell built on it stays documentation-attested at best, with a `[CITATION NEEDED]` until the anthropic-compat page is read.
- RQ2, minimum server contract: the documented chat completions surface covers wire shape (POST, OpenAI-referenced parameters, lmstudioChatCompletions.md:9, lmstudioChatCompletions.md:35) and streaming (`stream` in the parameter list, lmstudioChatCompletions.md:44). Context-window reporting is absent from these snapshots, which matters because OpenCode falls back to a chars/4 estimate for unknown models (brief, brief.md:63-64). Tool calling lives in a separate registry entry (sources/registry.yaml:129-139) and is out of scope here.
- RQ3, degradation points: automatic prompt templating for "chat‑tuned models" (lmstudioChatCompletions.md:10) suggests the server, not the agent, owns prompt formatting, which is one fewer integration assumption an agent must satisfy. The server-side `seed` and `repeat_penalty` parameters (lmstudioChatCompletions.md:50, lmstudioChatCompletions.md:49) are knobs no studied agent is known to expose, but checking that against the provider notes belongs to those notes, not this one.
- Open question left: whether the documented port and key match what Codex's built-in lmstudio provider assumes (brief.md:52-54) is answerable only by cross-checking against notes/codexOssProviders.md, not from this source.

## Quotables for the report

- "You can serve local LLMs from LM Studio's Developer tab, either on `localhost` or on the network." (lmstudioServer.md:9). Framing: one sentence covering both local and network serving.
- "LM Studio's APIs can be used through [REST API] ... client libraries like [lmstudio-js] and [lmstudio-python], and compatibility endpoints like [OpenAI-compatible] ... and [Anthropic-compatible]" (lmstudioServer.md:11, links elided in prose). Framing: evidence that LM Studio ships a native REST API plus two compatibility surfaces.
- `lms server start` (lmstudioServer.md:24). Framing: headless startup path.
- `client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")` (lmstudioChatCompletions.md:19). Framing: the documented OpenAI-compatible base URL and the placeholder key.
- "Prompt template is applied automatically for chat‑tuned models" (lmstudioChatCompletions.md:10). Framing: server-side chat templating.
