---
source_key: ollamaCompatDocs
read_date: 2026-08-20
confidence: high
relevance: 3
---

# Notes: Ollama: OpenAI compatibility (chat completions surface)

All anchors are line numbers in the HTML snapshot
`sources/docs/ollamaOpenaiCompat.html` (640 lines, fetched 2026-08-20).
Quotes are character-exact after stripping HTML tags and decoding
`&rsquo;` to a plain apostrophe.

## Source identification

- Key: `ollamaCompatDocs`
- Authors, year, venue: Ollama team, 2024, ollama.com/blog
- Tier: docs
- URL / DOI: https://ollama.com/blog/openai-compatibility (registry URL).
  The snapshot's own canonical link is `https://ollama.com/public/OpenAI compatibility`
  (line 20). Page title: "OpenAI compatibility · Ollama Blog" (line 13).
  Published date printed in the page: "February 8, 2024" (line 309).

## Problem and motivation

The post announces that Ollama exposes an OpenAI-compatible surface so that
existing OpenAI tooling can drive local models. Body statement: "Ollama now
has built-in compatibility with the OpenAI Chat Completions API, making it
possible to use more tooling and applications with Ollama locally." (line
412). The meta description frames it as partial: "Ollama now has initial
compatibility with the OpenAI Chat Completions API, making it possible to use
existing tooling built for OpenAI with local models via Ollama." (line 16).

## Method or core idea

The post is a how-to, not a specification. Its mechanism description:

- Setup is `ollama pull llama2`, with Llama 2 and Mistral named as example
  models (lines 416, 418).
- The compatibility instruction: "To invoke Ollama's OpenAI compatible API
  endpoint, use the same OpenAI format and change the hostname to
  `http://localhost:11434`" (line 425).
- cURL calls `http://localhost:11434/v1/chat/completions` with a
  `model`/`messages` body using `system`, `user` roles (lines 427, 431-440).
- The OpenAI Python and JavaScript clients point `base_url` / `baseURL` at
  `http://localhost:11434/v1` with `api_key='ollama', # required, but unused`
  (lines 449-450, 470-471).
- Two integration examples carry the evidence: Vercel AI SDK with
  `stream: true` on `openai.chat.completions.create` (lines 486, 500-505),
  and Autogen configured against `http://localhost:11434/v1` with model
  `codellama` (lines 520, 534-540).
- Full contract details are delegated to a linked doc,
  `https://github.com/ollama/ollama/blob/main/docs/openai.md` (lines 412,
  564), which is outside this snapshot.

## Key claims with anchors

Source claims (what the post establishes):

- Claim 1 (line 412): Ollama has built-in compatibility with the OpenAI Chat
  Completions API.
- Claim 2 (lines 425, 427): the compatible endpoint demonstrated is
  `/v1/chat/completions` at base URL `http://localhost:11434` (port 11434).
- Claim 3 (lines 449, 470, 495, 537): SDK clients use base URL
  `http://localhost:11434/v1`.
- Claim 4 (lines 450, 471): the API key is `ollama`, "required, but unused".
- Claim 5 (line 555): "This is initial experimental support for the OpenAI
  API." The meta description says "initial compatibility with the OpenAI Chat
  Completions API" (line 16).
- Claim 6 (lines 555-562): embeddings, function calling, vision, and logprobs
  were not supported at post time. "Future improvements under consideration
  include: Embeddings API, Function calling, Vision support, Logprobs."
- Claim 7 (line 486, lines 500-505): streaming is demonstrated via the Vercel
  AI SDK example, described as "an open-source library for building
  conversational streaming applications", with `"stream": true` (line 502)
  passed to chat completions. This is a working example, not a written
  capability statement.
- Claim 8 (line 309): the post is dated "February 8, 2024".
- Claim 9 (line 564): further contract detail lives in
  `https://github.com/ollama/ollama/blob/main/docs/openai.md`.

Negatives located by exhaustive search of the snapshot (lines 1-640):

- Responses API: not mentioned anywhere. The only surface named is Chat
  Completions (lines 16, 412). Any statement about a Responses endpoint in
  Ollama cannot be drawn from this snapshot. `[CITATION NEEDED]` if required;
  looked: full snapshot text, headings, code blocks.
- Tool/function calling: absent as a feature. The only occurrence is the
  "Function calling" roadmap bullet (line 559). No model list, no request or
  response shape exists in the snapshot. `[CITATION NEEDED]` for current
  tool-calling behavior; looked: full snapshot.
- Structured output / `response_format`: not mentioned. `[CITATION NEEDED]`;
  looked: full snapshot.
- Vision: only the roadmap bullet "Vision support" (line 560).
- Embeddings: only the roadmap bullet "Embeddings API" (line 558).
- Ollama release version that introduced compatibility: not stated.
  `[CITATION NEEDED]`; looked: full snapshot, including metadata (lines 10-60).

Interpretation (mine, not the post's):

- The phrasing "under consideration" (line 555) is a hedge, not a roadmap
  commitment; the post commits to nothing beyond chat completions.
- The silence on endpoints other than `/v1/chat/completions` is absence of
  evidence in this post, not evidence that no other endpoints exist; the
  linked `docs/openai.md` (line 564) is the enumerated contract and is not in
  the snapshot.

## Evaluation and evidence

No benchmarks, metrics, baselines, or datasets. The post's evidence is two
integration walkthroughs (Vercel AI SDK, Autogen), each shown only as code
plus prose, with no measured outputs (lines 482-551). Character-exact values
found: port `11434`, base path `/v1`, endpoint `/v1/chat/completions`, date
`February 8, 2024`, API key literal `ollama`, example models `llama2`,
`mistral` (library link, line 416), `codellama` (line 520). No latency,
throughput, or conformance numbers exist in the snapshot.

## Limitations

- Dated evidence. The post is February 8, 2024 (line 309) and describes the
  feature as "initial experimental support" (line 555). The registry's
  coverage limits already record that "versioned Ollama behavior (current
  release notes) is not snapshot-pinned" (`sources/registry.yaml`,
  coverage_limits). Anything Ollama shipped after this post (tool calling,
  embeddings, vision, which later upstream releases did add) is not attested
  here and must not be claimed from this note.
- Single endpoint documented. Only `/v1/chat/completions` is shown (line
  427). The complete compatible surface is delegated to `docs/openai.md`
  (line 564), which is outside the snapshot.
- Streaming is only exemplified, not specified: no SSE detail, no
  termination semantics, no guarantee statement (lines 500-505).
- No tool-calling contract exists at all in the snapshot, which is the
  largest gap for the brief's RQ2 (minimum contract for agents that rely on
  tools).
- No version pin: the post names no Ollama release version
  (`[CITATION NEEDED]`), so the snapshot cannot be tied to a specific binary
  behavior.

## Relevance to the brief

My inferences, separated from source claims:

- RQ1 (Ollama surface): this note is the documentation-tier attestation for
  the Ollama column of the compatibility matrix. The attested surface is an
  OpenAI-compatible Chat Completions endpoint at `http://localhost:11434/v1`
  with a dummy API key (lines 425, 449-450). As of the snapshot date, Ollama
  was "documentation only" compatible with tool-using agents, because
  function calling was explicitly unimplemented (line 559).
- RQ2 (minimum contract): the snapshot fixes four contract items for Ollama:
  chat-completions wire shape (`model` + `messages` with `system`/`user`/
  `assistant` roles, lines 427-441), port 11434 (line 425), base path `/v1`
  (line 449), and a required-but-unused API key (line 450). It provides no
  tool-calling shape, no embeddings, no structured output, and no
  context-window reporting, leaving those contract cells open for this
  source.
- RQ3 (degradation): Codex's pinned Responses-API wire (brief, prior
  understanding) confronts a Chat-Completions-only Ollama surface per this
  snapshot (lines 16, 412). Whether Codex's `ollama` provider entry remaps
  the wire is a code question for the `codexOssProviders` note, not
  answerable here.
- Left open by this note: current Ollama tool-calling support and shapes,
  Responses API status, structured output, and any version-tagged behavior.
  Closing those cells needs a snapshot newer than 2024-02-08 or the pinned
  `docs/openai.md`; without it they stay `[CITATION NEEDED]` in the matrix.

## Quotables for the report

- "Ollama now has built-in compatibility with the OpenAI Chat Completions
  API, making it possible to use more tooling and applications with Ollama
  locally." (line 412). Framing: open the Ollama surface cell.
- "change the hostname to `http://localhost:11434`" (line 425) and endpoint
  `/v1/chat/completions` (line 427). Framing: the base URL and path agents
  must target.
- "`api_key='ollama', # required, but unused`" (line 450). Framing: the
  auth contract is a placeholder, so agents that demand a real key still
  pass.
- "This is initial experimental support for the OpenAI API. Future
  improvements under consideration include: Embeddings API, Function calling,
  Vision support, Logprobs" (lines 555-562). Framing: quote when arguing the
  2024 surface cannot carry tool-using agents, and to date-stamp the
  "initial" status.
