---
source_key: "claudeCodeRouterContext"
read_date: "2026-08-20"
confidence: "high"
relevance: "1"
---

<!-- Confidence gloss: high = I read the full 567-line snapshot and every claim
below is locatable by line number; it says nothing about whether the project's
own claims are true. This is unverified community material admitted only as
hedged context per the brief (brief.md lines 35-36) and the registry inclusion
rule (registry.yaml line 26): it never carries a compatibility-matrix cell alone. -->

# Notes: claude-code-router: community router bridging Claude Code to other providers (context only)

## Source identification

- Key: `claudeCodeRouterContext`
- Authors, year, venue: musistudio, 2026 (year per registry entry; the snapshot itself carries no date), `github.com/musistudio/claude-code-router`
- Tier: blog (unverified community project; hedged context only, per register)
- URL / DOI: https://github.com/musistudio/claude-code-router; local snapshot `sources/docs/claudeCodeRouterReadme.md` (README.md raw, fetched 2026-08-20 at gathering time per `registry.yaml` provenance query, line 22)

## Problem and motivation

The README presents Claude Code Router (CCR) as "a local model gateway and control plane for coding agents" that gives a list of agents "one stable local endpoint" so users can "manage the providers, models, accounts, routing rules, and tools behind it from one place" (line 62). The stated motivations are managing all agents and providers together, switching providers or models without editing agent configuration files, keeping requests running through retries and fallbacks, adding capabilities to models, and observing requests (lines 66-70). It frames itself with the tagline "Manage every agent and provider from one place" (line 37).

All of this is the project's self-description. The snapshot establishes only that these claims are made, not that the software implements them.

## Method or core idea

Mechanism as the README describes it, all as claims:

- **Interception point.** CCR runs a local HTTP gateway. The README states "The local model gateway listens on `http://127.0.0.1:3456` by default" (line 207), repeated in the CLI section ("The model gateway remains at `http://127.0.0.1:3456`", line 222) and in the ASCII architecture diagram ("Claude Code Router :3456", line 249). A management UI listens on `http://127.0.0.1:3458` for the npm CLI (line 222) and for Docker (line 230).
- **Agents it fronts.** The README claims profiles for "Claude Code, Claude Design, Codex, Grok CLI, Kimi CLI, Kilo Code, OpenCode, Pi, ZCode, WorkBuddy" as both supported agents (line 39) and as profile targets with "model overrides; scopes; environment settings; CLI and app launch entries; multi-instance workflows" (line 260). Codex and OpenCode, two of this study's three agents, appear in that list.
- **Protocol surface.** The README claims "CCR supports OpenAI Chat / Responses, Anthropic Messages, Gemini Generate Content / Interactions, OpenRouter, DeepSeek, SiliconFlow, Moonshot, Kimi Code, Mistral, Z.AI, Bailian, and custom compatible providers" (line 72). The only per-provider protocol remark is the Kimi sponsor text: "The subscription endpoint passes through natively without protocol conversion, API endpoints are adapted automatically" (line 22). The snapshot does not describe a request-format translation layer in any more mechanical detail; the word "conversion" appears only in that Kimi sentence.
- **How Claude Code is pointed at it.** The README's flow is: "Open **Agent Config**, choose Claude Code, ... select a model, and apply the profile. Start using your agent." (lines 208-209), after which "Your agent is now connected to CCR." (line 211). The agent-profile feature list mentions "environment settings" (line 260). The snapshot never prints the proxy environment variables this implies: `[CITATION NEEDED]`. I searched the Quick Start (lines 160-230), the "How it works" diagram (lines 243-254), and the Core capabilities table (lines 256-266); no variable such as an Anthropic base-URL or HTTP proxy var appears anywhere in the 567-line snapshot. The claim that CCR configures Claude Code is made, but the env-var mechanism is not shown in this README.
- **Reliability and routing machinery claimed.** "retries, credential pools, key rotation, and ordered fallback models" (line 68); routing by "conditions on headers and bodies; prefixes; rewrites; retries; ordered fallbacks" plus "model descriptions for task selection" (line 262).
- **Extension machinery claimed.** "Fusion vision, web search, MCP tools, and ToolHub" (line 69); "Fusion models; ToolHub; built-in browser automation; Chrome login-state import; wrapper and core gateway plugins; local routes and virtual models" (line 263).
- **Distribution.** Desktop app for macOS, Windows, Linux at release `v3.0.21` (lines 172-197); npm CLI `npm install -g @musistudio/claude-code-router` then `ccr ui`, "requires Node.js 22 or newer" (lines 215-219); Docker via `docker compose up -d --build` (line 227).

The snapshot also interprets its own positioning commercially: the page opens with a Kimi sponsor banner stating "Thanks to Kimi for sponsoring this project!" (line 22), and it lists twelve corporate sponsors plus community sponsors (lines 321-561). The Kimi block contains vendor marketing claims ("Kimi K3 is Moonshot AI's most capable model and the world's first open 3T-class model. With 2.8 trillion parameters, native vision, and a 1-million-token context window", line 22) which I record as promotional assertions inside the README and do not adopt as findings.

## Key claims with anchors

Every item below is the README's claim, not a verified fact.

- Claim 1 (line 62): The README claims CCR is "a local model gateway and control plane for coding agents" giving ten named agents "one stable local endpoint".
- Claim 2 (line 207): The README states the gateway "listens on `http://127.0.0.1:3456` by default"; the management UI is on `http://127.0.0.1:3458` (line 222).
- Claim 3 (line 72): The README claims protocol/provider support for "OpenAI Chat / Responses, Anthropic Messages, Gemini Generate Content / Interactions, OpenRouter, DeepSeek, SiliconFlow, Moonshot, Kimi Code, Mistral, Z.AI, Bailian, and custom compatible providers".
- Claim 4 (lines 82-152, line 260): The README claims agent profiles for Claude Code (CLI & APP), Codex (CLI & APP), Grok CLI, Kimi CLI, Kilo Code, OpenCode (CLI & APP), Pi, ZCode, Claude Design, and WorkBuddy; profiles include "environment settings".
- Claim 5 (line 262): The README claims routing capabilities including "model descriptions for task selection; conditions on headers and bodies; prefixes; rewrites; retries; ordered fallbacks".
- Claim 6 (lines 208-211): The README claims Claude Code is connected by choosing it in "Agent Config", selecting a model, and applying a profile; it never shows proxy environment variables (`[CITATION NEEDED]`, see Method section for where I looked).
- Claim 7 (line 567): The README states "This project is licensed under the [MIT License](LICENSE)."
- Claim 8 (absence, verified across lines 1-567): The snapshot nowhere names Ollama, LM Studio, vLLM, or llama.cpp, and nowhere claims context management, compaction, or context-window handling as a feature.

### Providers and backends, as claimed (task question 2)

The claimed provider/protocol list is line 72's, quoted above. Mapping onto the study's open-model concern:

- **DeepSeek**: named in the claimed support list (line 72). DeepSeek serves open-weight models via a hosted API under this README's framing; the README gives no further detail in the snapshot.
- **Ollama and LM Studio**: not named anywhere in the snapshot. The only route to a local server the README claims is the catch-all "custom compatible providers" (line 72) plus "Presets and custom endpoints; protocol probing; model discovery; connectivity checks" (line 261). Whether that covers an OpenAI-compatible local server is not specified.
- **Moonshot / Kimi Code**: named (line 72) and heavily promoted in the sponsor block (lines 6-29); Kimi K3 is advertised as "the world's first open 3T-class model" with "2.8 trillion parameters" (line 22), a promotional claim I do not treat as evidence.

### Features claimed (task question 3)

- Task-oriented model selection: "model descriptions for task selection" and condition-based routing on "headers and bodies" (line 262). The snapshot does not claim named task modes (no background/think/long-context categories appear).
- Reliability: retries, credential pools, key rotation, ordered fallback models (line 68).
- Capability injection: Fusion vision, web search, MCP tools, ToolHub (line 69).
- Access control and quotas: "Separate CCR client keys with expiration and local request, token, and image limits" (line 264).
- Observability: "request logs, resolved routes, latency, token usage, cost estimates, and account status" (line 70); "resolved provider, model, and credential; status; latency; tokens; estimated cost; tool calls; agent traces" (line 265).
- Messenging relay (AgentClaw): "Agent relay through Weixin iLink, WeCom, Slack, Discord, Telegram, LINE, Feishu, and DingTalk" (line 266).
- Context management: **not claimed** in this snapshot. I checked "Why use Claude Code Router?" (lines 60-72) and "Core capabilities" (lines 256-266); the only occurrence of "context" in the whole file is in the Kimi ad ("1-million-token context window", line 22).

### Admitted non-support (task question 4)

The README has no "limitations" or "not supported" section. The closest admissions in the snapshot:

- "local login import where supported" (line 261): concedes login import is not universal across providers.
- "The npm CLI requires Node.js 22 or newer." (line 215) and "Install Node.js 22+, then run `npm ci`." (line 234): environment prerequisites.
- "Windows app packaging must run on Windows x64 because `better-sqlite3` ships a native Electron module." (line 241): build constraint.
- "Read the Docker deployment guide before exposing CCR remotely." (line 230): implies remote exposure is not turnkey.
- A "Troubleshoot common issues" doc link (line 277) implies known issues, none enumerated in the snapshot.

Nothing here admits a missing agent, protocol, or open-model-server path; the Ollama/LM Studio silence (Claim 8 above) is an absence in the text, not an admission by the authors.

### License, authorship, maintenance signals (task question 5)

- License: the README states MIT (line 567); a license badge links to the repo's LICENSE file (line 51). The license text itself is not in the snapshot.
- Authorship: everything points to a single handle, musistudio: repo URL (line 4 of registry; README title area), npm package `@musistudio/claude-code-router` (line 218), X badge `@musistudio2026` (line 50), PayPal `paypal.me/musistudio1999` (line 295). No organization or contributor list appears in the snapshot.
- Maintenance signals, all weak because the snapshot undated: desktop release `v3.0.21` in the download URLs (lines 172-197); a release workflow that "builds macOS on macOS runners and Windows on `windows-latest` when a `v*` tag is pushed" (line 241); an external documentation site ccrdesk.top (line 270); a Discord community link (line 49); active sponsorship income (lines 22, 283-301, 321-418) with 2026-dated affiliate campaign links ("claudecoderouter_2026", line 374).
- Commercial entanglements worth flagging: the top of the README is a paid Kimi placement ("Thanks to Kimi for sponsoring this project!", line 22), and several sponsor links carry affiliate parameters (lines 6, 330, 374, 381, 397, 404, 411). The README's provider claims should be read with that incentive in view.

## Evaluation and evidence

There is no evaluation. The README provides no benchmarks, no test suite, no compatibility matrix, and no verification that any named agent actually works through the gateway. No numbers characterize compatibility; the only quantitative strings in the snapshot are ports (`http://127.0.0.1:3456`, line 207; `http://127.0.0.1:3458`, line 222), the release tag `v3.0.21` (line 172), "Node.js 22" (line 215), and the Kimi sponsor's "2.8 trillion parameters" and "1-million-token context window" (line 22). Behavioral evidence for the study's questions (tool calling through the router, context-window reporting, streaming) is `[CITATION NEEDED]` from any source; nothing in this snapshot supplies it. No agents were executed in this study (brief.md line 33), so none of these claims could be tested here either.

## Limitations

Own section, per protocol; these are weaknesses of the source as evidence, not of any experiment:

1. **Self-reported only.** Every capability is a README assertion by the project's author; the snapshot contains no code, tests, or third-party confirmation.
2. **Mechanism gap for the study's central question.** The snapshot never shows how Claude Code is redirected (no environment variables, no config file, no hook), which is exactly the surface RQ1 asks about; the README's "apply the profile" wording (line 208) is opaque about what is written where.
3. **Undated snapshot.** No publish or commit date appears in the file; recency rests on circumstantial signs (`v3.0.21`, "2026" in sponsor links, X handle `musistudio2026`).
4. **Promotional contamination.** A paid sponsor block opens the document and advertises one provider's model with unverified capability numbers (line 22); provider "support" claims cannot be read as neutral coverage statements.
5. **Silence on local open-model servers.** Ollama, LM Studio, vLLM, and llama.cpp are never named; whether "custom compatible providers" (line 72) actually serves a local OpenAI-compatible endpoint is left entirely to external docs (ccrdesk.top), which are not snapshotted in this study.
6. **No admitted limitations.** The absence of a limitations section in a community README is itself a reliability caveat; only indirect admissions exist (see task question 4 above).

## Relevance to the brief

My inference, separated from source claims:

- **It cannot fill a compatibility-matrix cell alone.** Per the registry inclusion rule ("never carries a compatibility cell alone", registry.yaml line 26) and the brief's scope decision (brief.md lines 35-36), this note is hedged context only. Nothing above may appear in the matrix as evidence that Claude Code works with an open model through any surface.
- **What it does show, hedged:** a community bridging pattern exists around Claude Code's closed loader. The Claude Code column of RQ1 is otherwise documentation-attested only (registry.yaml coverage limit, line 33: "loader and fallback logic are not inspectable"); this README, if its claims were true, would indicate that third parties route Claude Code by pointing it at a local gateway (`http://127.0.0.1:3456`, line 207) through agent-side configuration the README calls "Agent Config ... apply the profile" (line 208) but does not expose. That is a claim that a workaround exists, not evidence of compatibility.
- **It also claims to front Codex and OpenCode** (line 39, line 260), the study's other two agents. Since this study has pinned-code evidence for both, the router's claims about them are checkable context, not needed evidence.
- **It leaves open everything RQ2/RQ3 asks:** whether tool calling, context-window reporting, streaming, or compaction survive the router's translation. The snapshot claims none of these except token/cost logging (line 70).
- **One framing worth carrying to the report:** the existence of an MIT-licensed gateway project claiming to give Claude Code "one stable local endpoint" (line 62) is a data point that the closed loader is a real friction point users route around, stated as community behavior, not as a measured finding.

## Quotables for the report

Use only with explicit hedging ("the community project's README claims ..."). Suggested framing in brackets.

- "one stable local endpoint" (line 62) [what the router claims to offer agents].
- "The local model gateway listens on `http://127.0.0.1:3456` by default." (line 207) [the claimed interception point].
- "OpenAI Chat / Responses, Anthropic Messages, Gemini Generate Content / Interactions, OpenRouter, DeepSeek, SiliconFlow, Moonshot, Kimi Code, Mistral, Z.AI, Bailian, and custom compatible providers" (line 72) [the claimed provider surface].
- "model descriptions for task selection; conditions on headers and bodies; prefixes; rewrites; retries; ordered fallbacks" (line 262) [the claimed routing feature set].
- "This project is licensed under the [MIT License](LICENSE)." (line 567) [license, if cited in refs.bib].
- Negative quotable for the report's limitation note: the README never names Ollama or LM Studio (verified across lines 1-567), so it does not even claim the specific local servers this study traces.
