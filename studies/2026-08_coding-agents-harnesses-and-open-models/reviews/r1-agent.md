# r1: agent review of `report/main.tex`

Reviewer: adversarial agent (read-only except this file). Date: 2026-08-20.
Basis: 11 notes + `_synthesis.md`, `sources/registry.yaml`, `sources/repos.yaml`,
pinned checkouts at `/Users/hong.huy.nguyen/Work/Code/references/coding-agents/{codex,opencode,claude-code}`,
doc snapshots under `sources/docs/`, `brief.md`, skill playbooks
(`paper-review-and-rebuttal.md`, `ethics-integrity-and-policy.md`).

Tool runs:

- `python3 tools/lint_report.py .../main.tex` -> `lint clean`.
- `python3 tools/verify_pins.py studies/2026-08_open-source-model-compat` -> PASS x3
  (codex af70018, opencode d545d8fb dev, claude-code c3d2e35).
- `python3 tools/research/audit_research.py --root studies/2026-08_open-source-model-compat`
  -> 4 errors: no `.research/` dossier, no evidence/claims/experiments ledgers
  (see finding F-min-10).

## Verdict: CONDITIONAL

No fabrication detected. Every draft claim I traced lands on a note with a
spot-checkable anchor, every bib entry matches a registry entry, no rejected
source is cited, and no `[CITATION NEEDED]`/`[EVIDENCE NEEDED]`/`[RESULT PENDING]`
markers leaked into the draft. One major finding (a load-bearing Codex claim
stated unconditionally where the note and the synthesis gap register flag it as
conditional/open) plus ~13 minors block a clean PASS. All fixes are wording or
one-sentence additions; none requires new evidence gathering.

Verdicts per review dimension (skill vocabulary):

| Dimension | Verdict | Basis |
|---|---|---|
| Claim traceability | CONDITIONAL | F-maj-1: fallback-metadata claim unstated condition; two gap-register items absent from Limitations; remaining ~20 traced claims anchor cleanly |
| Quote fidelity | CONDITIONAL | 7 of 8 checked quotes char-exact; F-min-11 is a near-verbatim quote |
| Number fidelity | CONDITIONAL | all substantive numbers match char-exact; pin date contradicts this study's `repos.yaml` (F-min-1) |
| Overclaiming | CONDITIONAL | F-maj-1 plus minors listed below; no behavioral claims beyond static traces otherwise |
| Scope vs brief | PASS | three surfaces covered; vLLM exclusion documented; blog-tier router hedged and fills no matrix cell |
| Style and formatting | PASS | no em-dashes, no untied cites, single-space `&`, American spellings, consistent `32{,}000` phrasing |
| Structure | CONDITIONAL | abstract vs body mismatch (F-min-9); Limitations miss two gap-register items (F-maj-1, F-min-12) |
| Experiment gate | NOT_ASSESSED | briefing depth; no experiments, `experiments_approved: false`, `experiments/` empty; nothing promoted |
| Dossier audit | BLOCKED (human action) | `audit_research.py` errors, no `audit_waiver`; needs human waiver or minimal dossier |

## Findings

Severity: `blocker` must be fixed before sign-off, `major` should be fixed
before sign-off, `minor` fix at writer's discretion.

| id | sev | location | issue | suggested fix |
|---|---|---|---|---|
| F-maj-1 | major | main.tex:173-177 ("Those default slugs are absent from the bundled catalog, so they resolve to a fallback model description..."); also 184-185 (272,000); absence in Limitations 309-339 | States fallback metadata as unconditional, but `codexOssProviders.md` Limitations (lines 377-385) records `[EVIDENCE NEEDED]`: whether fallback applies at runtime depends on the models-catalog refresh decoding against a plain `/v1/models` listing (rich Codex `ModelsResponse` schema expected), and `_synthesis.md` gap register item 1 explicitly carries this into the report Limitations, where it does not appear. The Codex patch-tool-loss and 272k findings both rest on this caveat. | Add one clause hedging "resolve to a fallback model description" (e.g., "provided the catalog refresh does not decode a richer listing from the server") and one sentence in Limitations naming the open cell, per `_synthesis.md`. |
| F-min-1 | minor | main.tex:85 ("Three local checkouts were pinned on 2026-08-19"); refs.bib:9,17,25 notes "(2026-08-19)" | This study's `sources/repos.yaml` records `pinned_at: 2026-08-20T05:33:50+00:00` for all three repos. 2026-08-19 is the pin date of the harness study's repos.yaml; `pin_repos.py` was re-run for this study on 2026-08-20 (registry provenance line 20). Commits are correct; the date is inconsistent with the study's own manifest. | Say "pinned at the harness study's commits (re-pinned 2026-08-20)" or change to 2026-08-20 in both main.tex and refs.bib notes. |
| F-min-2 | minor | main.tex:161-162 ("refuses servers older than 0.13.4"); matrix cell line 275 ("refuses below 0.13.4"); abstract line 39 | Code-verified gate has two exceptions the note states and the draft omits: version 0.0.0 (dev builds) is treated as supported, and a missing/unparsable `GET /api/version` returns `Ok(())` (`codex-rs/ollama/src/lib.rs:50-60`, verified). Flat "refuses below 0.13.4" is thus an oversimplification. | "refuses servers reporting a version older than 0.13.4" and footnote the two exceptions, or add "(dev builds and unreported versions pass)" once. |
| F-min-3 | minor | main.tex:176-177 ("open models on Codex lose the patch tool and keep the rest of the registry") | Stronger than the anchor. `codexOssProviders.md` line 236-238 says tool calling remains available, but its Limitations (lines 390-392) explicitly says the rest of `spec_plan.rs` was not characterized. | "lose the patch tool; the rest of the registry is gated by features and environment, not provider," matching the note's own wording. |
| F-min-4 | minor | main.tex:216-218 ("a server without tool support is not discovered until the request fails") | Collapses the note's two failure modes. `opencodeModelGating.md` Q3 line 117: if the server rejects the `tools` field the request fails, but if the model simply never emits tool calls the agent silently loses file editing. The draft states only the first. | "...is not discovered until the request fails or the model simply never calls a tool." |
| F-min-5 | minor | main.tex:171 ("open-weight models by intent") | Intent is not anchored anywhere in `codexOssProviders.md`; the note only records the default slugs. | "open-weight model slugs" or "gpt-oss, an open-weight family." |
| F-min-6 | minor | main.tex:276, matrix OpenCode x Ollama cell ("generic path plus catalog") | Misleading for Ollama: the pinned fixture catalog has `ollama-cloud` but no bare local `ollama` entry (`opencodeOssProviders.md` F7; draft body lines 204-206 gets this right). "plus catalog" fits the LM Studio cell, not Ollama. | "generic path, config-defined; in-repo example `localhost:11434/v1`". |
| F-min-7 | minor | main.tex:220-221 ("The one open-model-specific choice is the edit path") | `opencodeModelGating.md` line 41 records a second traced filter that hits every local-provider model: `websearch` is dropped for all providers except `opencode`/`opencode-go` (`registry.ts:293-295`). It is provider-keyed rather than model-ID-keyed, but the flat "the one" understates what the note traced. | "the one model-ID-keyed choice" or add half a clause on the websearch filter. |
| F-min-8 | minor | main.tex:130, Table 1 Ollama row ("listed as future work at post time") | Snapshot line 555 says "Future improvements under consideration"; `ollamaCompatDocs.md` interpretation (lines 102-103) flags "under consideration" as a hedge, not a roadmap commitment. "future work" hardens it. | "listed as a possible future improvement at post time". |
| F-min-9 | minor | main.tex:52-53 abstract ("an Anthropic messages endpoint exists in both reference servers") vs body 144-145 ("the llama.cpp reference server also exposes an Anthropic-shaped `/v1/messages` route, and LM Studio documents an Anthropic-compatible surface") | For LM Studio the snapshot only names "Anthropic-compatible endpoints" as a link (`lmstudioServer.md:11,33`); no route or shape is documented (`lmstudioServerDocs.md` Limitations). "exists in both" overstates LM Studio relative to both the note and the body. | Mirror the body: "an Anthropic messages route documented by llama.cpp and an Anthropic-compatible surface named by LM Studio, both unverified against Claude Code". |
| F-min-10 | minor | study directory (`audit_research.py` output); not a draft defect | No `.research/` dossier; audit reports 4 errors and `study.yaml` lists `dossier: .research/` while `audit_waiver` is empty. The sibling briefing study (2026-08_coding-agent-harnesses) also has no dossier, so this matches briefing practice, but `check_all.py` will fail until a human decides. | Human: set `audit_waiver` with the documented reason (briefing depth, evidence chain in notes/registry/repos), or initialize a minimal dossier. Agent must not set it. |
| F-min-11 | minor | main.tex:244 (quote "for any string your API endpoint accepts") | Not char-exact. Snapshot `claudeCodeModelConfig.md:684` reads "so you can use any string your API endpoint accepts" (grep: 0 hits for "for any string"). The draft's own preposition was quoted as if part of the source. | `adds an unvalidated picker entry: ``you can use any string your API endpoint accepts''`. |
| F-min-12 | minor | main.tex:245-246 ("`CLAUDE_CODE_MAX_CONTEXT_TOKENS` applies precisely to model IDs that do not start with `claude-`") | The documented condition is conjunctive (`claudeCodeModelConfig.md:657`): the ID must also not contain `[1m]` and must not resolve to a Claude model; IDs starting with `claude-` can still be affected via `DISABLE_COMPACT` (snapshot 659, note lines 240-242). "precisely" is false as written. Also note: `_synthesis.md` does not carry the OpenCode compaction-path ambiguity (v1 min vs v2 max reserve, unresolved which runs by default, `opencodeModelGating.md` lines 117-119/169) into Limitations either; the draft's flat `min(20,000, maxOutputTokens)` at line 214-215 is v1-only. | Drop "precisely" and state the full condition briefly; for the reserve, attribute to the v1 overflow path or hedge. |
| F-min-13 | minor | main.tex:233-235 ("model IDs in the `anthropic.*` namespace only") | Contradicted by this study's own notes: the Bedrock page documents ARN-shaped model IDs (`arn:aws:bedrock:...inference-profile...`, `claudeCodeBedrockDocs.md` L313; also ARNs at modelDoc L773) and cross-region IDs prefixed `us.`/`eu.`/`apac.`. The "only" and the namespace wording overstate the note's own flagged inference. | "every documented example is an Anthropic model (IDs prefixed or namespaced `anthropic.`, inference-profile ARNs)". |

Blockers: none. Majors: F-maj-1. Minors: 13.

## Verified-anchor log

Code anchors opened at the pinned commits (verify_pins: PASS x3; HEAD
`af70018` main, `d545d8fb` dev, `c3d2e35` main).

1. `codex-rs/model-provider-info/src/lib.rs:~508-521`: `built_in_model_providers` registers `OLLAMA_OSS_PROVIDER_ID` and `LMSTUDIO_OSS_PROVIDER_ID` via `create_oss_provider(..., WireApi::Responses)`. Matches note F1 and draft main.tex:150-153.
2. `codex-rs/model-provider-info/src/lib.rs:56-90`: `CHAT_WIRE_API_REMOVED_ERROR` const; single-variant `WireApi` enum; `"chat"` arm returns `serde::de::Error`. Matches note F2 and draft main.tex:157-158.
3. `codex-rs/ollama/src/lib.rs:46-70`: `Version::new(0, 13, 4)`; `supports_responses` admits `0.0.0`; error string "Ollama {version} is too old...". Matches note F4 (and grounds F-min-2).
4. `codex-rs/ollama/src/client.rs:158-181`: `GET {host}/api/version`, strips leading `v`. Matches note and draft main.tex:160-161.
5. `codex-rs/codex-api/src/endpoint/responses.rs:100-102`: `fn path() -> "responses"`. Matches note F3 and draft main.tex:152-156.
6. `codex-rs/ollama/src/lib.rs:16` `DEFAULT_OSS_MODEL = "gpt-oss:20b"`; `codex-rs/lmstudio/src/lib.rs:7` `"openai/gpt-oss-20b"`. Matches draft main.tex:169-171 and matrix 275.
7. `codex-rs/lmstudio/src/client.rs:70-77`: warm-up POST `{base}/responses` body `{"model", "input": "", "max_output_tokens": 1}`; `:178` `lms ["get", "--yes", model]`. Matches note F11 and draft main.tex:164-167.
8. `opencode packages/opencode/src/tool/registry.ts:297-300`: `usePatch` predicate char-exact (`gpt-`, not `oss`, not `gpt-4`). Matches note Fact 1 and draft main.tex:221-223.
9. `opencode packages/opencode/src/provider/transform.ts:18,1418-1420`: `OUTPUT_TOKEN_MAX = 32_000`; `Math.min(model.limit.output, outputTokenMax) || outputTokenMax`. Matches note Fact 3 and draft main.tex:209-210.
10. `opencode packages/opencode/src/session/overflow.ts:8-31`: `COMPACTION_BUFFER = 20_000`; reserve `min(buffer, maxOutputTokens)`; `usable`/`isOverflow` return 0/false when `limit.context === 0`. Matches note Fact 5 and draft main.tex:210-215.
11. `opencode packages/opencode/test/provider/provider.test.ts:874-891`: `local-llm` provider, `baseURL "http://localhost:11434/v1"`, `limit: { context: 8192, output: 2048 }`. Matches note F13 and draft main.tex:198-200.
12. `opencode packages/opencode/src/provider/provider.ts:106-133`: `BUNDLED_PROVIDERS` has exactly 24 keys including `@ai-sdk/openai-compatible`. Matches draft main.tex:193-194.
13. `opencode packages/core/src/models-dev.ts:160,165`: source `models.opencode.ai`, `ttl = Duration.minutes(5)`. Matches draft main.tex:202.
14. `claude-code` checkout at `c3d2e35` contains only plugins/examples/docs (no harness core), consistent with the `claudeCodeSurface` bib note and the "loader is closed" framing.

Doc-anchor spot checks (grep against `sources/docs/`):

15. `claudeCodeModelConfig.md`: zero case-insensitive hits for ollama/lmstudio/open-weight/openai-compatible/vllm/litellm, supporting the verified-absence claim at main.tex:235-237; `claudeCodeBedrock.md` likewise zero hits.
16. `lmstudioServer.md:11,33`: "Anthropic-compatible endpoints" named as links (feeds F-min-9).
17. `llamaCppServer.md:1563`: `POST /v1/messages` documented as Anthropic-compatible.
18. `lmstudioTools.md`: 0 hits for `tool_choice` and `parallel`; `tc.index` at lines 1090-1096. Supports Table 1 row 131.
19. `lmstudioResponses.md`: 0 hits for `tool_choice`/`parallel_tool_calls`/`include`/`reasoning.summary`; line 3 feature summary char-exact. Supports Table 1 row 131.
20. `shared/knowledge/coding-agent-harnesses.md:6-8`: eight-dimension decomposition claim in Related Work (main.tex:294-296) is real.

## Quote check log

| # | draft quote | location | source | result |
|---|---|---|---|---|
| 1 | "required, but unused" | main.tex:130 | ollamaOpenaiCompat.html | exact (1 hit) |
| 2 | "no strong claims of compatibility" | main.tex:132 | llamaCppServer.md:1272,1303 | exact |
| 3 | "only supported on some models" | main.tex:132 | llamaCppServer.md:1323 | exact |
| 4 | "changes where requests are sent, not which model answers them" | main.tex:241 | claudeCodeModelConfig.md:23 | exact |
| 5 | "passes any string through without checking it" | main.tex:242-243 | claudeCodeModelConfig.md:131 | exact |
| 6 | "for any string your API endpoint accepts" | main.tex:244 | claudeCodeModelConfig.md:684 | FAIL, source is "so you can use any string your API endpoint accepts" (F-min-11) |
| 7 | "when a gateway rewrites the error" | main.tex:249-250 | claudeCodeModelConfig.md:661 | exact after markdown-link strip (note's stated convention) |
| 8 | "This endpoint works by converting Responses request into Chat Completions request" | _synthesis/llamaCppServerDocs note; paraphrased in draft 132 | llamaCppServer.md:1494 | exact in snapshot; draft paraphrases honestly |

## Number check log

| number in draft | grounding | result |
|---|---|---|
| 0.13.4 (main.tex:39,162,275,354) | `codex-rs/ollama/src/lib.rs:47`, note F4 | exact (but see F-min-2 exceptions) |
| 11434 (multiple) | codex `DEFAULT_OLLAMA_PORT`; ollama snapshot:425; opencode test:886 | exact |
| 1234 (multiple) | codex `DEFAULT_LMSTUDIO_PORT`; lmstudioChatCompletions.md:19; lmstudioResponses.md | exact |
| 272,000 (main.tex:184) | note: `context_window: Some(272_000)` (model_info.rs:169) | exact |
| 32,000 (main.tex:46,209) | `transform.ts:18` `OUTPUT_TOKEN_MAX = 32_000` | exact, phrased `32{,}000` consistently |
| 20,000 (main.tex:214) | `overflow.ts:8` `COMPACTION_BUFFER = 20_000` | exact (v1 path only; F-min-12) |
| 8192 / 2048 (main.tex:200) | `provider.test.ts:885` | exact |
| 24 bundled packages (main.tex:194) | `BUNDLED_PROVIDERS` key count = 24 | exact |
| five-minute cache (main.tex:202) | `models-dev.ts:165` `Duration.minutes(5)` | exact |
| one-token warm-up (main.tex:166) | `lmstudio/client.rs:70-77` `max_output_tokens: 1` | exact |
| "3 codebase notes, 7 documentation notes, 1 context note" (main.tex:107) | notes/ listing: 11 notes | exact |
| 2024 post (main.tex:97,130,321) | ollama post dated February 8, 2024 | exact |
| commits af700180808c.../d545d8fba572.../c3d2e35e5540... (main.tex:86-89) | repos.yaml | exact |
| 2026-08-20 snapshots (main.tex:55,93,320,357) | registry evidence_cutoff and provenance | exact |
| 2026-08-19 pin date (main.tex:85; refs.bib:9,17,25) | this study's repos.yaml `pinned_at: 2026-08-20` | MISMATCH (F-min-1) |

## Scope, structure, style notes (non-finding)

- All three brief surfaces covered in the matrix with per-cell evidence tiers;
  vLLM exclusion and LM Studio mirror provenance both disclosed (brief
  definition-of-done items 1-2 satisfied).
- Blog-tier router (`claudeCodeRouterContext`) appears only hedged
  (main.tex:101-103, 255-257, 304-307) and fills no matrix cell, per brief
  and registry inclusion rule.
- No em-dashes; no untied `\citep`/`\ref` (lint clean, spot-grep agrees);
  table `&` separators are single-spaced; American spellings throughout
  ("behavior", "gray"); `32{,}000` phrased identically in both uses.
- Abstract agrees with body except F-min-9; conclusion introduces no new
  factual claims (its advice paragraph paraphrases findings already cited).
- Limitations cover: no behavior measured, field-acceptance cell, version and
  provenance bounds (Ollama 2024 post, LM Studio mirror, llama.cpp master,
  vLLM), closed Claude Code loader, fixture-scoped catalog. Missing: Codex
  catalog-refresh cell (F-maj-1) and OpenCode compaction-path ambiguity
  (F-min-12).
- Citations: all 9 bib keys exist and match registry entries 1:1 (URLs, years,
  tiers); codebase entries carry repo key + pinned commit in `note`; no
  `rejected` source cited; claude-code checkout confirmed to carry no harness
  code, so the `claudeCodeSurface` framing is honest.

## Next decisive action

1. Writer fixes F-maj-1 (hedge at main.tex:173-177 + sentence in Limitations).
2. Writer fixes F-min-11 (quote), F-min-13 (`anthropic.*` "only"), F-min-1
   (pin date, main.tex and refs.bib), and whichever minors the human keeps.
3. Human decides F-min-10: set `audit_waiver` documenting briefing-depth
   practice, or initialize `.research/` before sign-off.
4. Re-run `tools/lint_report.py` after edits; then the human may consider
   `review_signed_off`.
