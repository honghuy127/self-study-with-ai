---
source_key: "opencodeContextCompaction"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "opencode"
commit: "d545d8fba57283528db69281f59c803c646eb7e9"
---

# Notes: OpenCode context assembly, compaction, and summaries (opencode)

## Source identification

- Key: opencodeContextCompaction
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`; branch `dev`, pinned clean tree; verified via `.git/HEAD` and `.git/refs/heads/dev` of the checkout)
- Component scope: `packages/opencode/src/session/compaction.ts`, `summary.ts`, `overflow.ts`, `reminders.ts`, `instruction.ts`, `system.ts`, `todo.ts` (registry entry scope), plus the support files they depend on, read to anchor the mechanism: `packages/core/src/session/compaction.ts` (summarization prompt, imported by the v1 service at `packages/opencode/src/session/compaction.ts:23`), `packages/core/src/util/token.ts`, `packages/opencode/src/session/processor.ts`, `packages/opencode/src/session/prompt.ts` (call sites only), `packages/opencode/src/session/message-v2.ts` (compacted-history reconstruction), `packages/opencode/src/session/llm/request.ts` (system-prompt join point), `packages/opencode/src/agent/agent.ts` and `packages/opencode/src/agent/prompt/compaction.txt` (built-in compaction agent), `packages/opencode/src/provider/transform.ts` (`OUTPUT_TOKEN_MAX`), `packages/core/src/v1/config/config.ts` (config schema), `packages/opencode/src/effect/runtime-flags.ts` (env flags).
- Tier: codebase

## Purpose and role in the harness

OpenCode's context layer does four jobs in the session runtime:

1. Assembles the system prompt for every request from a model-family base prompt, an environment block, AGENTS.md-style instruction files, MCP server instructions, and skill listings (`packages/opencode/src/session/llm/request.ts:56-66`, `packages/opencode/src/session/prompt.ts:1257-1269`, `packages/opencode/src/session/system.ts:66-136`).
2. Detects when the conversation approaches the model context limit, either from reported token usage or from a provider context-overflow error, and triggers compaction (`packages/opencode/src/session/overflow.ts:22-34`, `packages/opencode/src/session/processor.ts:477-482`, `packages/opencode/src/session/processor.ts:606-618`).
3. Runs compaction as a dedicated hidden agent that produces a structured summary, then reconstructs subsequent requests from summary plus a verbatim recent tail (`packages/opencode/src/session/compaction.ts:319-557`, `packages/opencode/src/session/message-v2.ts:521-572`).
4. Optionally prunes old tool outputs to reclaim tokens (`packages/opencode/src/session/compaction.ts:273-317`).

The summarization prompt and template live in the core package and are shared with a newer v2 session runner (`packages/core/src/session/compaction.ts:16-55`, `packages/core/src/session/runner/llm.ts:222-223`); see Limitations.

## Mechanism

### Context assembly

Per loop iteration the run loop loads the stored message history through `MessageV2.filterCompactedEffect` and derives `lastUser`, `lastAssistant`, `lastFinished`, and pending `tasks` (compaction/subtask parts) via `MessageV2.latest` (`packages/opencode/src/session/prompt.ts:1092-1096`). Plan/build reminders are injected into the last user message (`packages/opencode/src/session/prompt.ts:1180-1184`). The per-request system array is built as `[env, instructions, mcpInstructions, skills]` plus an optional structured-output prompt (`packages/opencode/src/session/prompt.ts:1257-1271`), then joined in `LLMRequestPrep.prepare`:

- Order: `agent.prompt` if the agent defines one, else the model-family base prompt from `SystemPrompt.provider(model)`; then the session `system` blocks; then `user.system` (`packages/opencode/src/session/llm/request.ts:58-65`).
- `SystemPrompt.provider` picks a base prompt by substring-matching `model.api.id`: `muse` to PROMPT_META, `gpt-4`/`o1`/`o3` to PROMPT_BEAST, `gpt`+`codex` to PROMPT_CODEX, `gpt` to PROMPT_GPT, `gemini-` to PROMPT_GEMINI, `claude` to PROMPT_ANTHROPIC, `trinity` to PROMPT_TRINITY, `kimi` to PROMPT_KIMI, fallback PROMPT_DEFAULT (`packages/opencode/src/session/system.ts:27-49`).
- The joined single system string can be mutated by the `experimental.chat.system.transform` plugin hook (`packages/opencode/src/session/llm/request.ts:68-78`). System content is sent as `role: "system"` messages, except OpenAI OAuth where it goes into `options.instructions` (`packages/opencode/src/session/llm/request.ts:99-112`).

Environment block contents: model name and exact model ID, working directory, workspace root, whether the directory is a git repo, `process.platform`, and `new Date().toDateString()`, wrapped in `<env>` tags (`packages/opencode/src/session/system.ts:72-83`), followed by an optional `<available_references>` block (`packages/opencode/src/session/system.ts:84-101`). Skills are described verbosely in the system prompt and omitted entirely when the `skill` permission is disabled (`packages/opencode/src/session/system.ts:105-117`). MCP instructions render inside `<mcp_instructions>` and only for servers with at least one enabled tool (`packages/opencode/src/session/system.ts:119-135`).

Instruction files (AGENTS.md layer, `packages/opencode/src/session/instruction.ts`):

- Global candidates: `<global config>/AGENTS.md`, then `~/.claude/CLAUDE.md` unless `OPENCODE_DISABLE_CLAUDE_CODE`/`OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` is set; first existing one wins (`instruction.ts:60-63`, `instruction.ts:115-120`, `packages/opencode/src/effect/runtime-flags.ts:23-26`).
- Project candidates, searched with `findUp` from the working directory to the worktree root: `AGENTS.md`, then `CLAUDE.md` (same flag gate), then `CONTEXT.md` (marked deprecated); the first filename with matches wins so ancestor files do not stack (`instruction.ts:64-68`, `instruction.ts:122-133`).
- Additional entries from config `instructions`, supporting glob patterns and `~/` paths; `http://`/`https://` entries are fetched with a 5000 ms timeout (`instruction.ts:95-103`, `instruction.ts:135-150`, `instruction.ts:158-163`).
- Everything renders as blocks prefixed `Instructions from: <path or url>` (`instruction.ts:165-168`), which is the exact framing visible in this study's own pipeline prompts.
- Nested discovery: when the `read` tool reads a file, parent directories between that file and the project root are scanned for instruction files and attached once per assistant message via an in-memory `claims` map (`instruction.ts:179-221`, cleared at `packages/opencode/src/session/prompt.ts:1331`). Files whose `read` part was pruned are not counted as loaded (`instruction.ts:17-32`).

Reminders (`packages/opencode/src/session/reminders.ts#apply`): on every iteration, synthetic `<system-reminder>` text parts are pushed onto the last user message. Non-experimental path: `PROMPT_PLAN` when the agent is `plan`, and `BUILD_SWITCH` text when switching from a plan agent to `build` (`reminders.ts:26-47`); these parts are built in memory without `sessions.updatePart` (`reminders.ts:28-46`). The `experimentalPlanMode` path persists the reminder parts and tracks a plan file, substituting `${planInfo}` in `PLAN_MODE` (`reminders.ts:51-89`, `packages/opencode/src/session/prompt/plan-mode.txt:1-9`).

Todo state (`packages/opencode/src/session/todo.ts`): `update` deletes all `TodoTable` rows for the session and re-inserts with positions (a full replace), publishing `Event.Updated`; `get` returns rows ordered by `position` (`todo.ts:29-66`). Backed by `TodoTable` (`packages/core/src/session/sql.ts:100`) and driven by the todowrite tool (`packages/opencode/src/tool/todo.ts:14-17`). Todos are persistent scratch state, not injected into model input by this component.

`SessionSummary` (`summary.ts`) is not an LLM summarizer despite the name: `summarize` resets the session diff summary to `{additions: 0, deletions: 0, files: 0}`, publishes an empty diff event, returns early when config `snapshot === false`, then computes a git snapshot diff between the first `step-start` and last `step-finish` snapshots of the target user message and stores it on `target.info.summary.diffs` (`summary.ts:102-127`, `summary.ts:82-100`). It is forked from the processor after each step finish and from the run loop at step 1 (`packages/opencode/src/session/processor.ts:471-476`, `packages/opencode/src/session/prompt.ts:1252-1253`).

### Overflow detection

`usable()` computes the token ceiling: if `model.limit.input` exists it is `max(0, limit.input - reserved)`, otherwise `max(0, limit.context - maxOutputTokens)`; `reserved` defaults to `min(COMPACTION_BUFFER, maxOutputTokens)` with `COMPACTION_BUFFER = 20_000`, overridable via `cfg.compaction.reserved` (`packages/opencode/src/session/overflow.ts:8-20`). `maxOutputTokens` is `min(model.limit.output, outputTokenMax) || outputTokenMax` with `OUTPUT_TOKEN_MAX = 32_000` and an env override `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (`packages/opencode/src/provider/transform.ts:18`, `transform.ts:1418-1420`, `packages/opencode/src/effect/runtime-flags.ts:52`).

`isOverflow()` returns false when `cfg.compaction.auto === false` or `model.limit.context === 0`; otherwise it compares `tokens.total || input + output + cache.read + cache.write` against `usable` (`overflow.ts:22-34`). Token counts come from provider usage recorded at step finish (`packages/opencode/src/session/session.ts:338-369`, `packages/opencode/src/session/processor.ts:438-445`).

Three trigger paths:

1. Mid-step: at each `step-finish`, if the assistant message is not itself a summary and usage overflows, `ctx.needsCompaction = true` (`processor.ts:477-482`). The event stream is cut with `Stream.takeUntil(() => ctx.needsCompaction)` and `process` returns `"compact"` (`processor.ts:642-646`, `processor.ts:679-681`).
2. Provider error: a parsed `SessionV1.ContextOverflowError` in `halt` sets `needsCompaction`, unless `compaction.auto === false` on a non-summary message, in which case the error is surfaced and the session goes idle (`processor.ts:606-618`).
3. Between steps: after a finished assistant step the run loop re-checks `compaction.isOverflow` and creates an auto compaction (`prompt.ts:1161-1168`). When the processor returns `"compact"`, the loop calls `compaction.create` with `overflow: !handle.message.finish` (true when the step never finished, i.e. hard overflow) and continues (`prompt.ts:1319-1328`).

### Compaction execution

`create` appends a user message carrying a `compaction` part with `auto` and `overflow` flags (`compaction.ts:559-582`). The run loop treats pending compaction parts as tasks (`packages/opencode/src/session/message-v2.ts:592-597`) and dispatches them to `compaction.process` before normal steps (`prompt.ts:1149-1158`). Manual compaction is exposed as the `session.summarize` HTTP endpoint, which calls `compactSvc.create` with `auto: payload.auto ?? false` and then `promptSvc.loop` (`packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts:273-293`, route defined at `packages/opencode/src/server/routes/instance/httpapi/groups/session.ts:94`, `groups/session.ts:303-313`).

`processCompaction` (`compaction.ts:319-557`):

- Requires the parent to be a user message (`compaction.ts:326-329`).
- On overflow-triggered compaction, it finds the most recent non-compaction user message before the compaction marker and replays it after compaction; media file parts are converted to `[Attached <mime>: <filename>]` text in the replay (`compaction.ts:340-356`, `compaction.ts:482-494`).
- Runs as the built-in `compaction` agent: hidden, `mode: "primary"`, `permission` deny-all (`"*": "deny"`), prompt PROMPT_COMPACTION (`packages/opencode/src/agent/agent.ts:219-233`, `packages/opencode/src/agent/prompt/compaction.txt:1-5`). The compaction call passes `tools: {}` and `system: []` (`compaction.ts:425-448`). The model is `agent.compaction.model` if configured, else the model of the triggering user message (`compaction.ts:358-361`).
- Prior completed compaction pairs (user with compaction part + assistant with `summary`, `finish`, no `error`) are hidden from the serialized history, and only the newest prior summary text is passed as `previousSummary` (`compaction.ts:97-113`, `compaction.ts:363-366`).
- Splits history into head (to summarize) and tail (to keep verbatim) via `select` (`compaction.ts:223-269`).
- Plugins may inject extra context or replace the prompt via `experimental.session.compacting`, and `experimental.chat.messages.transform` may mutate the head before serialization (`compaction.ts:372-379`).
- Serializes the head to plain text with role prefixes `[User]`, `[Assistant]`, `[Assistant reasoning]`, `[Assistant tool call]`, `[Tool result]`, `[Tool error]`; tool outputs are truncated to `TOOL_OUTPUT_MAX_CHARS = 2_000` characters with a `[truncated]` suffix, and previously pruned outputs render as `[Old tool result content cleared]` (`compaction.ts:30`, `compaction.ts:51-85`).
- The prompt is `buildPrompt({previousSummary, context})` from core: without a prior summary it asks to "Create a new anchored summary" and appends `SUMMARY_TEMPLATE`; with a prior summary it wraps the old text in `<prior-summary>` and appends `SUMMARY_UPDATE_INSTRUCTIONS` plus the template (`packages/core/src/session/compaction.ts:160-174`, `core/src/session/compaction.ts:16-55`, used at `compaction.ts:381-391`).
- The summary is produced by running the compaction agent on a single user message containing that prompt (`compaction.ts:392-448`). The assistant result message is flagged `summary: true`, `mode: "compaction"`, `agent: "compaction"` (`compaction.ts:393-418`).
- If the summarization call itself reports overflow (`result === "compact"`), the compaction fails with error "Conversation history too large to compact - exceeds model context limit" (replay case) or "Session too large to compact - context exceeds model limit even after stripping media", and the loop stops (`compaction.ts:450-459`).
- After success, the compaction part records `tail_start_id` marking the first retained tail message (`compaction.ts:461-466`).
- Auto compaction continuation: without replay, a synthetic user message is appended: "Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed." (prefixed with a media-removal explanation on overflow), marked `synthetic: true` with `metadata: { compaction_continue: true }` (`compaction.ts:497-548`), gated by the `experimental.compaction.autocontinue` plugin hook which defaults to `enabled: true` (`compaction.ts:500-517`). On success it publishes `Event.Compacted` (`compaction.ts:553-555`).

### What compaction preserves and how history is reconstructed

- Retained tail budget: `preserve_recent_tokens` if set, else `min(15_000, max(2_000, floor(usable * 0.25)))` (`compaction.ts:32-33`, `compaction.ts:115-120`).
- Turn accounting: each non-compaction user message starts a turn extending to the next user message (`compaction.ts:122-138`). `select` walks turns newest-first while they fit the budget; `tail_turns` caps how many turns are even considered and `tail_turns: 0` disables tail retention entirely (`compaction.ts:228-233`). A turn that does not fit may be split mid-way by `splitTurn`, which scans forward inside the turn for the first suffix that fits the remaining budget (`compaction.ts:140-163`, `compaction.ts:249-257`). When nothing fits, the whole history is summarized (`compaction.ts:264`).
- Reconstruction for subsequent requests happens in `MessageV2.filterCompacted`: it scans newest-first and stops at the boundary of a completed compaction (assistant `summary` + finished + no error marking its parent user completed), honoring `tail_start_id` to include the retained tail; it then reorders output so the model sees `[compaction user message, summary assistant message, ...retained tail..., post-compaction messages]` (`message-v2.ts:521-572`, reorder comment at `message-v2.ts:578-581`). The compaction user message becomes the literal question "What did we do so far?" in model input and the summary message answers it (`message-v2.ts:228-233`).

### Pruning of stale tool outputs

`prune` runs only when `cfg.compaction.prune` is truthy (`compaction.ts:274-275`; schema default false at `packages/core/src/v1/config/config.ts:154-156`). It is forked with `Effect.ignore` after the run loop exits (`prompt.ts:1338`). Walking messages newest-first it counts user boundaries and skips everything newer than the second user message from the end, so the latest turn is always protected (`compaction.ts:288-291`). It stops entirely at a prior summary assistant message or at a part already marked compacted (`compaction.ts:292`, `compaction.ts:298`). Completed tool parts are considered except tools in `PRUNE_PROTECTED_TOOLS = ["skill"]` (`compaction.ts:295-297`, `compaction.ts:31`). Using the character-based token estimator, the newest `PRUNE_PROTECT = 40_000` estimated tokens of tool output are kept; older output is eligible (`compaction.ts:299-303`). Eligible parts are actually cleared only when the estimated savings exceed `PRUNE_MINIMUM = 20_000` tokens; clearing sets `part.state.time.compacted = Date.now()` and persists the part (`compaction.ts:308-315`). Cleared outputs render as `[Old tool result content cleared]` in both model messages (`message-v2.ts:292-296`) and compaction serialization (`compaction.ts:76-78`).

## Key facts with anchors

- Token estimation is a character heuristic: `Token.estimate = Math.max(0, Math.round(input.length / 4))` with `CHARS_PER_TOKEN = 4` (`packages/core/src/util/token.ts:3-5`, re-exported at `packages/opencode/src/util/token.ts:1`). Compaction sizing estimates `JSON.stringify` of model messages (`compaction.ts:215-221`); prune estimates raw output strings (`compaction.ts:299`).
- Overflow threshold: reported token count `>= usable`, where `usable = max(0, limit.input - reserved)` or `max(0, limit.context - maxOutputTokens)`, `reserved = cfg.compaction.reserved ?? min(20_000, maxOutputTokens)` (`overflow.ts:8-34`).
- Auto-compaction opt-out is `compaction.auto: false` in config; the schema documents "Enable automatic compaction when context is full (default: true)" (`packages/core/src/v1/config/config.ts:149-153`, checked at `overflow.ts:28`, `processor.ts:608`, `packages/core/src/session/compaction.ts:233`).
- Summary format is a fixed six-section Markdown template: `## Objective`, `## Important Details`, `## Work State` (`### Completed`, `### Active`, `### Blocked`), `## Next Move`, `## Relevant Files`, with rules to preserve exact file paths, symbols, commands, error strings, URLs, and identifiers, and "Do not mention the summary process or that context was compacted" (`core/src/session/compaction.ts:16-46`).
- Incremental summaries: prior summary is merged, not stacked; "anything you do not carry into the new summary is lost", conversation wins on conflict, completed work moves from Active to Completed (`core/src/session/compaction.ts:47-55`).
- The summarizer agent has no tools and no system prompt; its system prompt comes only from its agent prompt text, and it is invoked with `tools: {}`, `system: []` (`compaction.ts:425-430`, `agent.ts:219-233`).
- Compaction history keeps reasoning parts (`[Assistant reasoning]`) and tool call inputs (`[Assistant tool call]: <tool>(JSON input)`) but truncates tool outputs to 2000 chars (`compaction.ts:66-84`).
- Compacted conversations are not deleted: all messages stay in storage; `filterCompacted` only changes what is sent to the model and reorders messages for consumption (`message-v2.ts:521-581`).
- Nested compaction guard: a compaction whose own summarization step overflows fails with a typed `ContextOverflowError` and stops the loop instead of recursing (`compaction.ts:450-459`).
- Prune is off by default and works in token units of the char/4 estimator, with protect window 40_000, minimum savings 20_000, protected tool list `["skill"]`, latest turn always spared, and hard stop at prior summary boundaries (`compaction.ts:28-32`, `compaction.ts:273-316`).
- Instruction discovery is breadth-limited: within the project tree only the first matching filename class is used (AGENTS.md preferred over CLAUDE.md preferred over CONTEXT.md; comment "The first project-level match wins so we don't stack AGENTS.md/CLAUDE.md from every ancestor") (`instruction.ts:64-68`, `instruction.ts:122-133`).
- AGENTS.md and CLAUDE.md interop with Claude Code is explicit: `~/.claude/CLAUDE.md` is read as a global instruction candidate and project `CLAUDE.md` as a fallback candidate, both gated by `OPENCODE_DISABLE_CLAUDE_CODE`/`OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` (`instruction.ts:60-68`, `runtime-flags.ts:23-26`).
- The v1 pipeline also runs two cheaper auxiliary LLM tasks on the context: a session title generated on step 1 by the hidden `title` agent with the small model (`prompt.ts:216-236`, `agent.ts:234-249`), and per-message git diff summaries stored by `SessionSummary` (non-LLM) (`summary.ts:102-127`).
- A second, newer compaction module exists in core and is used by the v2 `SessionRunner`: `compactIfNeeded` estimates the whole request (system + messages + tools) against `context - max(output, buffer)` with `DEFAULT_BUFFER = 20_000`, then `compactAfterOverflow` keeps the most recent `DEFAULT_KEEP_TOKENS = 8_000` tokens verbatim (`core/src/session/compaction.ts:12-13`, `core/src/session/compaction.ts:123-158`, `core/src/session/compaction.ts:178-243`), caps summary output at `SUMMARY_OUTPUT_TOKENS = 4_096` (`core/src/session/compaction.ts:15`, `:189`), and the runner retries once after overflow-driven compaction (`packages/core/src/session/runner/llm.ts:222-223`, `packages/core/src/session/runner/llm.ts:289-295`, `packages/core/src/session/runner/llm.ts:362-388`).

## Configuration and defaults

Config keys under `compaction` (schema descriptions character-exact from `packages/core/src/v1/config/config.ts:149-168`):

- `auto` (boolean): "Enable automatic compaction when context is full (default: true)" (`config.ts:151-153`).
- `prune` (boolean): "Enable pruning of old tool outputs (default: false)" (`config.ts:154-156`).
- `tail_turns` (non-negative int): "Maximum number of recent user turns, including their following assistant/tool responses, to keep verbatim during compaction. By default retention is limited only by the preserved token budget." (`config.ts:157-160`); `0` disables tail retention (`compaction.ts:228-229`).
- `preserve_recent_tokens` (non-negative int): "Maximum number of tokens from recent turns to preserve verbatim after compaction" (`config.ts:161-163`); default `min(MAX_PRESERVE_RECENT_TOKENS=15_000, max(MIN_PRESERVE_RECENT_TOKENS=2_000, floor(usable * 0.25)))` (`compaction.ts:32-33`, `compaction.ts:115-120`).
- `reserved` (non-negative int): "Token buffer for compaction. Leaves enough window to avoid overflow during compaction." (`config.ts:164-166`); default `min(COMPACTION_BUFFER=20_000, maxOutputTokens)` (`overflow.ts:8-16`).
- `instructions` (string[]): "Additional instruction files or patterns to include" (`config.ts:124-126`); URLs in this list are fetched per request with a 5000 ms timeout (`instruction.ts:96-99`, `instruction.ts:158-163`).
- `agent.compaction` accepts `ConfigAgentV1.Info`, so the summarizer model and prompt are user-overridable (`config.ts:105`, applied at `agent.ts:267-294` and read at `compaction.ts:358-361`).
- `snapshot: false` disables the diff-summary machinery (`summary.ts:115`).
- `tool_output.max_lines` / `tool_output.max_bytes`, documented defaults 2000 / 51200, truncate tool output to disk at capture time (`config.ts:136-148`); this is capture-time truncation in the tools layer, distinct from compaction-time truncation.

Environment variables (all default false or unset unless noted, `packages/opencode/src/effect/runtime-flags.ts:10-57`):

- `OPENCODE_DISABLE_CLAUDE_CODE`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT`: exclude CLAUDE.md candidates (`runtime-flags.ts:23-26`).
- `OPENCODE_EXPERIMENTAL_PLAN_MODE` (or umbrella `OPENCODE_EXPERIMENTAL`): persistent plan-file reminders (`runtime-flags.ts:47`).
- `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX`: overrides the 32_000 output cap used in `usable` and request params (`runtime-flags.ts:52`, `transform.ts:1418-1420`, `compaction.ts:203-213`).
- `OPENCODE_DISABLE_PROJECT_CONFIG` (core `Flag`): restricts instruction search to the global config directory (`instruction.ts:81-88`, `instruction.ts:123`).

Hard-coded constants (character-exact):

- v1 service: `PRUNE_MINIMUM = 20_000`, `PRUNE_PROTECT = 40_000`, `TOOL_OUTPUT_MAX_CHARS = 2_000`, `PRUNE_PROTECTED_TOOLS = ["skill"]`, `MIN_PRESERVE_RECENT_TOKENS = 2_000`, `MAX_PRESERVE_RECENT_TOKENS = 15_000` (`compaction.ts:28-33`).
- Overflow: `COMPACTION_BUFFER = 20_000` (`overflow.ts:8`); provider output cap `OUTPUT_TOKEN_MAX = 32_000` (`transform.ts:18`).
- Core compaction module: `DEFAULT_BUFFER = 20_000`, `DEFAULT_KEEP_TOKENS = 8_000`, `TOOL_OUTPUT_MAX_CHARS = 2_000`, `SUMMARY_OUTPUT_TOKENS = 4_096` (`core/src/session/compaction.ts:12-15`), tail selection at `select` (`core/src/session/compaction.ts:137-158`).
- Token heuristic: `CHARS_PER_TOKEN = 4` (`core/src/util/token.ts:3`).

Plugin hooks (not stable contracts unless documented otherwise): `experimental.session.compacting` (inject context or replace the compaction prompt) (`compaction.ts:372-377`), `experimental.chat.messages.transform` (mutate message list before summarization and before normal steps) (`compaction.ts:378-379`, `prompt.ts:1255`), `experimental.compaction.autocontinue` (default `enabled: true`) (`compaction.ts:500-517`), `experimental.chat.system.transform` (mutate the system array) (`request.ts:69-73`). The `compaction_continue` metadata marker on the auto-continue message is explicitly documented in code as "not a stable plugin contract and may change or disappear" (`compaction.ts:537-540`).

## Limitations and unknowns

- Two compaction pipelines coexist at this commit. The component described here is the v1 session pipeline (`SessionPrompt` + `SessionCompaction` + `SessionProcessor`), wired into the app runtime and the HTTP session group (manual `session.summarize` endpoint maps to it: `packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts:273-293`). A v2 core `SessionRunner` with its own compaction module (`compactIfNeeded`/`compactAfterOverflow`) is also built and provided to the instance server via `SessionExecutionLocal` (`packages/opencode/src/server/routes/instance/httpapi/server.ts:243-302`, `packages/core/src/session/execution/local.ts:16-29`, `packages/core/src/session/runner/llm.ts:222-223`). I did not exhaustively trace which client entry points (TUI vs SDK vs web) reach v1 vs v2 at this commit, so I cannot state which pipeline serves interactive sessions by default. This is the one gap that could matter for the literature gate if a report claim says "OpenCode compacts by summarization" without qualifying the pipeline; both pipelines do summarize, but with different retention defaults (15_000/25% tail vs 8_000 tokens).
- `Session.getUsage` `total` comes from `usage.totalTokens` reported by the provider (`packages/opencode/src/session/session.ts:366-369`); I did not verify what providers report for `total` versus the fallback sum in `overflow.ts:31-32`, so exact overflow timing on specific providers is runtime-dependent.
- The effective context limits (`model.limit.context`, `limit.input`, `limit.output`) come from model catalogs resolved at runtime (`Provider.getModel`, ModelsDev data); they are not derivable from this component's code, so concrete trigger thresholds for real models are `[EVIDENCE NEEDED]` (looked at `overflow.ts`, `transform.ts`, `compaction.ts`; the values live in provider/model catalog data, not in the pinned harness code).
- Prune only touches persisted parts when savings exceed `PRUNE_MINIMUM`; I did not observe a runtime session, so I cannot say how often pruning fires in practice or how `Date.now()` compacted timestamps interact with sharing/export.
- `reminders.ts` non-experimental path mutates the in-memory message parts without persisting them (`reminders.ts:27-47`); I infer they are re-derived each iteration, but I did not verify that no other consumer persists that mutated array.
- The nested-instruction attachment (`instruction.ts:179-221`) depends on the `read` tool recording `metadata.loaded`; I did not re-verify the read tool implementation in this note (it belongs to the opencodeTools component).
- Core v2 module behavior (e.g. `SessionContextEpoch` baseline, `SessionHistory.entriesForRunner`) was read only as far as compaction; the v2 history/context machinery is otherwise out of this component's scope.

## Relevance to the brief

Inferences, separated from code facts above:

- RQ1/RQ2 (harness components, genuine differences): this component shows OpenCode implements context management as an explicit, inspectable stack: a deterministic window trigger (reported tokens vs `usable`), a provider-error fallback trigger, an LLM summarizer with a fixed output contract, verbatim tail retention with a token budget, and optional tool-output pruning. The fixed six-section summary template (`core/src/session/compaction.ts:16-46`) and the "What did we do so far?" Q/A reconstruction (`message-v2.ts:228-233`) are concrete design choices to compare against Codex's compaction entries (see `notes/codexContextCompaction.md`) and Claude Code's documented behavior.
- The AGENTS.md-first discovery order with CLAUDE.md fallback and `~/.claude/CLAUDE.md` global ingestion (`instruction.ts:60-68`) is direct evidence that OpenCode deliberately interoperates with Claude Code's memory-file ecosystem, a genuine harness-level difference/similarity datapoint.
- The prune mechanism (`PRUNE_PROTECT`/`PRUNE_MINIMUM`, protect-list `["skill"]`) is OpenCode's answer to "stale tool output accumulation" and is off by default; comparing its defaults to Claude Code's described context editing would answer part of RQ1, but Claude Code's core is closed, so the comparison can only cite docs/teardowns for that side.
- The parallel v1/v2 pipelines suggest the repo was mid-migration at the pinned commit; any cross-system comparison should pin claims to the v1 pipeline (the one the registered component covers) and flag v2 as in-flux.
- Left open for synthesis: how Codex and OpenCode differ in what survives compaction (structured summary vs raw prefix retention), and whether OpenCode's plugin-overridable compaction prompt is unique among the three.

## Quotables for the report

- Overflow gate, character-exact thresholds: `COMPACTION_BUFFER = 20_000` (`packages/opencode/src/session/overflow.ts:8`), `OUTPUT_TOKEN_MAX = 32_000` (`packages/opencode/src/provider/transform.ts:18`), trigger `count >= usable` (`overflow.ts:31-33`). Framing: "OpenCode treats the provider-reported token count against a conservative usable window, reserved by a 20k token buffer, as the compaction signal, with provider overflow errors as a second trigger" (`processor.ts:606-618`).
- Tail-retention budget formula: `Math.min(15_000, Math.max(2_000, Math.floor(usable * 0.25)))` (`packages/opencode/src/session/compaction.ts:32-33`, `compaction.ts:115-120`). Framing: "compaction keeps at most 25% of the usable window (clamped to 2k to 15k tokens) verbatim and folds everything older into the summary."
- Summary template sections: `## Objective`, `## Important Details`, `## Work State` (Completed/Active/Blocked), `## Next Move`, `## Relevant Files` with rule "Preserve exact file paths, symbols, commands, error strings, URLs, and identifiers when known" (`packages/core/src/session/compaction.ts:16-46`). Framing: "OpenCode fixes the summary schema so a successor model can resume work, and instructs the summarizer never to reveal that compaction happened."
- Reconstruction: compaction user message renders as "What did we do so far?" (`packages/opencode/src/session/message-v2.ts:228-233`); reordered window `[compaction-user, summary, ...retained tail..., continue-user]` (`message-v2.ts:578-581`).
- Prune constants: `PRUNE_PROTECT = 40_000`, `PRUNE_MINIMUM = 20_000`, `PRUNE_PROTECTED_TOOLS = ["skill"]`, marker `[Old tool result content cleared]` (`compaction.ts:28-32`, `message-v2.ts:292-296`). Framing: "tool outputs are treated as reclaimable memory once the newest 40k tokens of them are protected, but only when reclamation exceeds 20k tokens, and pruning is disabled by default."
- Instruction interop: candidate order `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md` with `~/.claude/CLAUDE.md` global fallback (`packages/opencode/src/session/instruction.ts:60-68`); rendered as `Instructions from: <path>` (`instruction.ts:165-168`).
- Auto-continue nudge after compaction: "Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed." (`compaction.ts:527-531`).
