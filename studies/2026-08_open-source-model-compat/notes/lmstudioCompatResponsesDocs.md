---
source_key: "lmstudioCompatResponsesDocs"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
---

# Notes: LM Studio docs: OpenAI Responses API compatibility

## Source identification

- Key: lmstudioCompatResponsesDocs
- Authors, year, venue: LM Studio (lmstudio-ai), 2026, docs.lmstudio.ai
  (snapshotted via github.com/lmstudio-ai/docs). Metadata from
  `sources/registry.yaml` lines 141-151.
- Tier: docs
- URL / DOI: https://docs.lmstudio.ai/developers/openai-compat/responses.
  Local evidence: `sources/docs/lmstudioResponses.md` (73 lines, read in
  full). Snapshot provenance: fetched 2026-08-20 as a raw file from the
  lmstudio-ai docs repo at `main` HEAD, because docs.lmstudio.ai was
  unreachable from the gathering environment
  (`sources/registry.yaml` lines 22, 34).
- All anchors below are line numbers of `sources/docs/lmstudioResponses.md`.
  Quotes are character-exact, including the non-breaking hyphens the page
  uses in headings.

## Problem and motivation

The page is LM Studio's API reference page for its OpenAI Responses API
compatibility surface. Its own one-line statement of what it covers (line 3):
"Create responses with support for streaming, reasoning, prior response
state, and optional Remote MCP tools." It explicitly aligns itself with the
OpenAI reference (line 10): "See OpenAI docs:
https://platform.openai.com/docs/api-reference/responses". The page's method
is to establish the endpoint and demonstrate it with four cURL recipes
against a local server, rather than to enumerate a full request schema.

## Method or core idea

The page documents one endpoint through four sequential cURL examples, all
`POST http://localhost:1234/v1/responses`:

1. Non-streaming request with a reasoning effort (lines 12-22), heading
   "##### cURL (non‑streaming)" (line 12).
2. Stateful follow-up keyed on a previous response id (lines 24-36), heading
   "##### Stateful follow‑up" (line 24).
3. Streaming request returning SSE events (lines 38-50), heading
   "##### Streaming" (line 38).
4. Tools via Remote MCP (lines 52-73), heading
   "##### Tools and Remote MCP (opt‑in)" (line 52).

The frontmatter records only the method (`api_info: method: POST`, lines
5-6; repeated at line 9 as "Method: `POST`"). The path `/v1/responses` is
attested only through the example URLs (lines 15, 29, 41, 57), not through a
route table.

## Key claims with anchors

What the source establishes (claims stated by the page):

- Claim 1, endpoint and method (line 6, line 9, line 15): LM Studio serves
  the Responses API as `POST` at `http://localhost:1234/v1/responses`.
- Claim 2, supported-feature summary (line 3): support covers "streaming,
  reasoning, prior response state, and optional Remote MCP tools".
- Claim 3, reasoning (line 20): the request accepts
  `"reasoning": { "effort": "low" }`. No other reasoning fields appear.
- Claim 4, stateful follow-up (lines 26, 34): "Use the `id` from a previous
  response as `previous_response_id`." Example value `"previous_response_id":
  "resp_123"`.
- Claim 5, streaming (lines 46, 50): `"stream": true` is accepted, and "You
  will receive SSE events such as `response.created`,
  `response.output_text.delta`, and `response.completed`." The phrase "such
  as" marks this event list as non-exhaustive.
- Claim 6, tools are remote MCP only on this page, and opt-in (lines 52, 54,
  62-71): "Enable Remote MCP in the app (Developer → Settings)." The only
  tool schema shown is `"type": "mcp"` with fields `server_label`
  (`"huggingface"`), `server_url` (`https://huggingface.co/mcp`), and
  `allowed_tools` (`["model_search"]`, lines 63-69).
- Claim 7, example model IDs, character-exact: `"openai/gpt-oss-20b"`
  (lines 18, 32, 44) and `"ibm/granite-4-micro"` (line 60).

What the source interprets (its own framing):

- It presents itself as a compatibility layer over OpenAI's Responses API by
  pointing to the OpenAI reference instead of restating semantics (line 10).
- It frames MCP tools as not on by default: the section heading says
  "(opt‑in)" (line 52) and enablement happens in the app UI, not the request
  (line 54).

What is not locatable (searched the full snapshot, lines 1-73):

- Function-type local tools on the Responses route: [CITATION NEEDED]. The
  only `tools` entry in the snapshot has `"type": "mcp"` (line 64). A sibling
  page for tool calling exists in the registry
  (`lmstudioCompatToolsDocs`, `sources/registry.yaml` lines 129-139) but is a
  separate source outside this note.
- `tool_choice`, `parallel_tool_calls`, `include`, `reasoning.summary`,
  `reasoning.encrypted_content`, `truncation`, `store`, `metadata`:
  [CITATION NEEDED] for each. None of these strings appears anywhere in the
  snapshot.

My inference about relevance is separated below under "Relevance to the
brief".

## Evaluation and evidence

This is an API doc, not an evaluation. There are no datasets, metrics,
baselines, or quantitative results ([CITATION NEEDED]; looked at every line,
1-73, and there is no evaluation content). All evidence is example-based:

- Endpoint: `http://localhost:1234/v1/responses` (lines 15, 29, 41, 57),
  i.e. default port `1234`.
- Model IDs: `openai/gpt-oss-20b` (lines 18, 32, 44),
  `ibm/granite-4-micro` (line 60).
- Reasoning effort value: `"low"` (line 20).
- SSE event names: `response.created`, `response.output_text.delta`,
  `response.completed` (line 50).
- MCP example: server label `huggingface`, server URL
  `https://huggingface.co/mcp`, allowed tool `model_search` (lines 65-69).
- Placeholder response id in the stateful example: `resp_123` (line 34).
- All four examples send `input` as a plain string (lines 19, 33, 45, 61).

## Limitations

Document-level omissions and weakness, kept separate from prose claims:

- No request-schema reference. Every feature is attested only by a cURL
  example (lines 14-73); absence of a field from the examples is weak
  evidence of non-support but not a stated contract.
- None of the fields Codex posts on the Responses wire appear anywhere in
  the snapshot: function-type `tools`, `tool_choice`, `parallel_tool_calls`,
  `reasoning.summary`, `include` with `reasoning.encrypted_content`
  ([CITATION NEEDED], searched lines 1-73). From this page alone there is no
  evidence LM Studio accepts the request body Codex actually sends.
- Array-form or item-list `input` is never shown; every example uses a
  string input (lines 19, 33, 45, 61). Support for non-string input:
  [CITATION NEEDED].
- No version or date on the page: no LM Studio app version, no docs
  revision. The snapshot is the docs-repo mirror at `main` HEAD fetched
  2026-08-20 because the live site was unreachable; drift between the mirror
  and the shipped app is not assessed (`sources/registry.yaml` lines 22,
  34).
- The SSE event list is explicitly incomplete ("such as", line 50), and the
  terminal/error event behavior is undocumented.
- The stateful example uses placeholder `resp_123` (line 34); actual
  response-id format and retention semantics are not stated.
- MCP capability is gated behind a manual app UI setting
  (Developer → Settings, line 54), so it is not discoverable from the API
  alone.

## Relevance to the brief

My inference, separated from source claims.

- RQ1 and RQ2, LM Studio surface: this snapshot is the direct evidence that
  LM Studio serves the Responses API at all. It establishes `POST
  /v1/responses` on port 1234, streaming via SSE, `reasoning.effort`, and
  `previous_response_id` (Claims 1, 3, 4, 5 above). That matters because the
  brief records that Codex's wire protocol is pinned to the Responses API
  with the chat path rejected (brief.md lines 55-57), and this is the page
  that would carry a Codex-style client.
- The gap that matters for the compatibility matrix: the only tool surface
  documented here is remote MCP, opt-in (Claim 6), while Codex sends
  function-type `tools`, `tool_choice`, `parallel_tool_calls`,
  `reasoning.summary`, and `include` (task context; to be verified against
  the `codexOssProviders` code trace). This snapshot cannot confirm that LM
  Studio accepts those fields, so the "Codex x LM Studio" cell should not
  rest on this doc alone. It stays evidence-pending for function tools and
  reasoning fields until `notes/codexOssProviders.md` shows what Codex's
  lmstudio provider entry actually posts and whether it transforms the
  request.
- RQ3, model-ID gating: the example model IDs `openai/gpt-oss-20b` and
  `ibm/granite-4-micro` show LM Studio's own ID namespace on the Responses
  route (lines 18, 60). Any agent hardcoding OpenAI model IDs must resolve
  to this namespace first.
- Left open here: function-tool schema support on this route, `include` and
  reasoning-detail fields, input array shape, error and terminal SSE
  events, and any version statement.

## Quotables for the report

- Feature summary (line 3), frame as LM Studio's self-description of the
  surface: "Create responses with support for streaming, reasoning, prior
  response state, and optional Remote MCP tools."
- Statefulness (line 26): "Use the `id` from a previous response as
  `previous_response_id`."
- Streaming contract (line 50): "You will receive SSE events such as
  `response.created`, `response.output_text.delta`, and
  `response.completed`."
- MCP gating (line 54): "Enable Remote MCP in the app (Developer →
  Settings)." Frame as: MCP tools are the only tool type shown on the
  Responses page, and they are opt-in.
- Endpoint attestation (line 15): `http://localhost:1234/v1/responses`,
  frame as the local-server route Codex's lmstudio provider would target.
