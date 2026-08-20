---
source_key: opencodeSessionLoop
read_date: "2026-08-20"
confidence: high
relevance: 3
repo: opencode
commit: d545d8fba57283528db69281f59c803c646eb7e9
---

# Notes: OpenCode session run loop, agent runtime, subagents (opencode)

## Source identification

- Key: `opencodeSessionLoop`
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`; branch `dev`, pinned clean tree)
- Component scope: `packages/opencode/src/session/ (processor.ts, run-state.ts, llm.ts, llm/, prompt.ts, prompt/, retry.ts, tools.ts, message.ts, message-v2.ts, revert.ts, status.ts)` and `packages/opencode/src/agent/ (agent.ts, prompt/, subagent-permissions.ts)`. Supporting code outside the listed component is anchored explicitly when used: `packages/opencode/src/tool/task.ts`, `packages/opencode/src/effect/runner.ts`, `packages/opencode/src/effect/runtime-flags.ts`, `packages/opencode/src/session/overflow.ts`, `packages/opencode/src/provider/transform.ts`, `packages/core/src/session/runner/max-steps.ts`, `packages/schema/src/session-status-event.ts`.
- Tier: codebase

## Purpose and role in the harness

- `SessionPrompt` is the entry point for every user-initiated turn. Its public interface is `cancel`, `prompt`, `loop`, `shell`, `command`, `resolvePromptParts` (`packages/opencode/src/session/prompt.ts:102-109`; exported as `SessionPrompt` at `prompt.ts:1631`).
- It owns the outer agent loop (`runLoop`, `prompt.ts:1081-1341`), which repeatedly builds the message list, resolves the agent and tools, and drives one LLM stream per iteration through `SessionProcessor` (`prompt.ts:1213-1286`, `processor.ts:627-683`).
- `SessionProcessor` owns one assistant message: it consumes the normalized `LLMEvent` stream, persists text/reasoning/tool parts, records tokens and cost, detects doom loops and overflow, and classifies the step as `"compact" | "stop" | "continue"` (`processor.ts:30`, `processor.ts:98-693`).
- `LLM` (`session/llm.ts`) is the single seam between the session and provider calls. It resolves auth, config, provider, and model, prepares the request (`llm/request.ts`), and streams either through the Vercel AI SDK (`streamText`) or an opt-in native runtime, normalizing both to one `LLMEvent` stream (`llm.ts:85-381`, `llm/AGENTS.md:34-83`).
- `SessionRunState` serializes runs per session with a per-session `Runner` state machine and implements cancel (`run-state.ts:52-105`).
- `Agent` defines the built-in agents (`build`, `plan`, `general`, `explore`, plus hidden `compaction`, `title`, `summary`), their permission rulesets and per-agent overrides (`agent/agent.ts:140-310`).
- Subagent delegation is invoked from the loop via `task` tool parts (`SubtaskPart`) handled in `handleSubtask` (`prompt.ts:255-449`, `prompt.ts:1142-1147`), which executes the `task` tool defined in `packages/opencode/src/tool/task.ts:81-360`.
- Inference about role: this component is OpenCode's equivalent of Codex's agent/thread turn loop. It is the central object of RQ1 for the OpenCode side.

## Mechanism

Code facts below; items marked "(interpretation)" describe intent I attribute to the code based on its structure and comments.

### Entry and message creation

1. `prompt(input)` loads the session, calls `revert.cleanup(session)` to drop messages past any pending revert point (`prompt.ts:1055-1056`, `revert.ts:101-136`), creates the user message, and touches the session (`prompt.ts:1057-1058`).
2. The deprecated `input.tools` map (`prompt.ts:1505-1508`) is converted to permission rules `{ permission: t, action: enabled ? "allow" : "deny", pattern: "*" }` and stored on the session (`prompt.ts:1060-1067`).
3. `noReply === true` returns the message without running the loop (`prompt.ts:1069`).
4. `createUserMessage` resolves the agent (`agents.get(agentName)` or `agents.defaultInfo()`, `prompt.ts:636-637`), resolves the model as `input.model ?? ag.model ?? currentModel(sessionID)` (`prompt.ts:646`), persists the user message, and resolves parts: `file` parts are read through the `read` tool with `bypassCwdCheck: true` (`prompt.ts:808-970`), MCP resource attachments are size/mime-checked (`prompt.ts:702-784`), and `agent` parts append a synthetic instruction ending in "call the task tool with subagent: " plus the agent name (`prompt.ts:974-990`).
5. `loop({ sessionID })` delegates to `state.ensureRunning(sessionID, lastAssistant(...), runLoop(sessionID))` (`prompt.ts:1343-1347`). `ensureRunning` returns the existing fiber's result if a run is already in flight, queues a run after an in-flight shell, or starts a new run from `Idle` (`effect/runner.ts:115-138`).

### Turn loop state machine

Each iteration of `runLoop` (`prompt.ts:1088-1336`):

1. Sets session status `busy` (`prompt.ts:1089`; status values are the schema union `idle | retry | busy`, `packages/schema/src/session-status-event.ts:9-32`).
2. Rebuilds the working message list with `MessageV2.filterCompactedEffect` (`prompt.ts:1092`), which walks messages newest-first and, when a completed compaction exists, reorders context to `[compaction-user "What did we do so far?", summary, ...retained tail..., continue]` (`message-v2.ts:521-576`, reorder comment at `message-v2.ts:578-581`; compaction part renders as text "What did we do so far?" at `message-v2.ts:228-233`).
3. `MessageV2.latest(msgs)` extracts the latest user, assistant, finished assistant, and any pending `compaction`/`subtask` parts that appear after the last finished assistant message (`message-v2.ts:582-598`).
4. Exit condition: the loop breaks when the last assistant message has a `finish` other than `tool-calls`, has no pending tool parts (ignoring provider-executed and cleanup-marked interrupted orphans), and parents to the last user message (`prompt.ts:1106-1130`). (Interpretation: some providers return `"stop"` while leaving tool calls, so opencode re-enters the loop until tool results are sent back; the comment at `prompt.ts:1103-1105` states this.)
5. On the first iteration only, title generation is forked into the session scope using the hidden `title` agent (step 1, `prompt.ts:1133-1139`, `prompt.ts:193-253`; title capped at 100 chars with `"..."` suffix at `prompt.ts:249`).
6. Pending tasks are popped LIFO: a `subtask` part runs `handleSubtask` (`prompt.ts:1142-1147`), a `compaction` part runs `compaction.process` and breaks if it returns `"stop"` (`prompt.ts:1149-1159`). (Compaction internals belong to the `opencodeContextCompaction` note.)
7. Overflow guard: if the last finished assistant turn exceeds `compaction.isOverflow` and was not itself a summary, a compaction is created with `auto: true` and the loop continues (`prompt.ts:1161-1168`). Overflow threshold logic is in `session/overflow.ts:22-34` with `COMPACTION_BUFFER = 20_000` (`overflow.ts:8`) and `compaction.auto === false` disabling it (`overflow.ts:28`).
8. The step budget is `agent.steps ?? Infinity` (`prompt.ts:1178`); when `step >= maxSteps` an assistant-role `MAX_STEPS_PROMPT` message is appended to the request (`prompt.ts:1279-1282`). The prompt text instructs the model that tools are disabled and only text is allowed (`packages/core/src/session/runner/max-steps.ts:1-16`), but the tool set itself is not removed from the request (no `tools = {}` branch exists in `runLoop`; see Limitations).
9. A fresh assistant message is created with zeroed tokens/cost (`prompt.ts:1186-1201`), a `SessionProcessor` handle is created pre-capturing a git snapshot (`prompt.ts:1213-1219`, `processor.ts:98-102`), and `handle.process(...)` runs one provider step.
10. After `process` returns: structured output ends the loop (`prompt.ts:1288-1293`); `content-filter` finish becomes a surfaced error and breaks (`prompt.ts:1301-1308`); a `json_schema` format without structured output becomes `StructuredOutputError` (`prompt.ts:1309-1316`); `"stop"` breaks; `"compact"` creates a compaction (with `overflow: !handle.message.finish`) and continues (`prompt.ts:1319-1329`).
11. After the loop, `compaction.prune` is forked and the last assistant message is returned (`prompt.ts:1338-1339`).

### One provider step (processor + LLM stream)

- `process(streamInput)` resets compaction state, sets `ctx.shouldBreak = config.experimental?.continue_loop_on_deny !== true` (`processor.ts:632-633`), sets status `busy`, and drains `llm.stream(streamInput)` event by event (`processor.ts:639-646`).
- The stream is cut short when `ctx.needsCompaction` flips (`processor.ts:644`), set either at `step-finish` when `isOverflow` of the accumulated usage holds (`processor.ts:477-482`) or in `halt()` on a `ContextOverflowError` (`processor.ts:607-618`).
- Event handling (`processor.ts:278-537`): `reasoning-start/delta/end` maintain `reasoningMap` parts; `text-start/delta/end` maintain a single `currentText` part with delta updates (`processor.ts:499-510`); `tool-call` moves a tool part from `pending` to `running` with parsed input (`processor.ts:331-351`); `tool-result` completes or fails the tool part (`processor.ts:383-414`); `step-start` records a `step-start` part with the snapshot hash (`processor.ts:424-433`); `step-finish` records usage/cost into the assistant message, writes a `step-finish` part with `tokens` and `cost`, computes the `patch` part from the tracked snapshot when files changed, and forks a summary pass (`processor.ts:435-484`).
- Doom loop detection: on every `tool-call`, the last `DOOM_LOOP_THRESHOLD` (= 3, `processor.ts:29`) tool parts of the assistant message are checked; if all three are the same tool with byte-identical `JSON.stringify(input)` and are not pending, a permission ask with `permission: "doom_loop"` is raised against the agent ruleset (`processor.ts:353-380`).
- Denied permissions stop the loop: `failToolCall` sets `ctx.blocked = ctx.shouldBreak` for `PermissionV1.RejectedError` or `Question.RejectedError` (`processor.ts:200-202`), and `process` returns `"stop"` when blocked or when the assistant message has an error (`processor.ts:679-681`).
- Return classification (`processor.ts:679-681`): `"compact"` if `needsCompaction`, `"stop"` if blocked/errored, else `"continue"`.

### Streaming, abort, and retries

- `LLM.stream` acquires an `AbortController` per request and aborts it when the stream scope closes (`llm.ts:357-381`).
- Default runtime is the AI SDK: `streamText({ ... maxRetries: input.retries ?? 0 ... })` (`llm.ts:280-323`), so SDK-level retries default to zero; retries happen at the session level instead (below). The native `@opencode-ai/llm` runtime is opt-in behind `OPENCODE_EXPERIMENTAL_NATIVE_LLM` (or the umbrella `OPENCODE_EXPERIMENTAL`) (`llm.ts:226-269`, `effect/runtime-flags.ts:10,54`, `llm/AGENTS.md:88-90`).
- Failed tool calls are repaired by `experimental_repairToolCall`: a case mismatch reties the lowercased name; otherwise the call is rerouted to a tool named `invalid` carrying the error message as input (`llm.ts:296-312`); `activeTools` excludes `invalid` (`llm.ts:317`).
- Session-level retry wraps the stream drain: `Effect.retry(SessionRetry.policy(...))` (`processor.ts:660-674`). The policy publishes a `retry` status (with `attempt`, `message`, `action`, `next` timestamp) between attempts (`processor.ts:664-673`, `status.ts:39-48`).
- Retry constants (`session/retry.ts:26-31`): `RETRY_INITIAL_DELAY = 2000`, `RETRY_BACKOFF_FACTOR = 2`, `RETRY_JITTER_FACTOR = 0.25`, `RETRY_MAX_DELAY_NO_HEADERS = 30_000`, `RETRY_MAX_DELAY = 2_147_483_647`, `RETRY_MAX_RETRIES = 5`.
- Retryability: context overflow is never retried (`retry.ts:86`); 5xx always retries even when not SDK-marked (`retry.ts:89-97`); a regex bank (`RETRYABLE_MESSAGE_PATTERNS`, `retry.ts:33-40`) matches rate-limit/overload/network/timeout phrasing; `retry-after-ms` and `retry-after` (seconds or HTTP date) headers are honored (`retry.ts:46-77`); attempts beyond 5 stop the schedule (`retry.ts:192`).
- Error normalization is `MessageV2.fromError` (`message-v2.ts:606-733`): `AbortError` DOMException maps to `AbortedError` (`message-v2.ts:611-617`), `APICallError` parses into `ContextOverflowError` or `APIError` (`message-v2.ts:679-704`).
- Cancellation: `cancel(sessionID)` cancels background jobs for the session and its descendants, then interrupts the session runner (`prompt.ts:152-155`, `run-state.ts:77-86`, recursive job cancellation at `run-state.ts:111-143`). Runner cancel interrupts the fiber and fails waiters with `RunnerCancelled` (`effect/runner.ts:171-202`).
- On interrupt mid-stream, the processor calls `halt(new DOMException("Aborted", "AbortError"))` (`processor.ts:648-655`) which records the `AbortedError` on the assistant message and sets status `idle` (`processor.ts:619-624`). `cleanup()` then awaits each in-flight tool's completion deferred for `"250 millis"` and marks any still-running tool with `status: "error"`, `error: "Tool execution aborted"`, `metadata.interrupted = true` (`processor.ts:571-594`). Those orphans are later ignored by the loop exit check via `isOrphanedInterruptedTool` (`prompt.ts:96-100`, `prompt.ts:1106-1127`) and replayed to the provider as `output-error` parts `"[Tool execution was interrupted]"` (`message-v2.ts:349-360`).

### Tool resolution and execution

- `SessionTools.resolve` wraps every registry tool as an AI SDK `tool()` whose `execute` builds a `Tool.Context` carrying `sessionID`, `abort` (the SDK `abortSignal`), `messageID`, `callID`, `agent`, `messages`, a `metadata` updater that writes back into the tool part, and an `ask` function that merges `agent.permission` with `session.permission` (`tools.ts:59-90`, `tools.ts:92-134`).
- Every tool execution fires plugin hooks `tool.execute.before` and `tool.execute.after` (`tools.ts:106-125`); if the abort signal fired before the result returned, the tool part is still completed with the produced output (`tools.ts:126-128`).
- Permission filtering happens twice: statically at request prep, where `Permission.disabled` removes tools denied by the merged agent+session ruleset and `user.tools` disables specific tools (`llm/request.ts:208-214`), and dynamically per-call via `ctx.ask` (`tools.ts:81-89`).
- MCP tools are converted and wrapped with a permission ask of `permission: key, patterns: ["*"], always: ["*"]` (`tools.ts:390-490`); MCP resource tools (`list_mcp_resources`, `list_mcp_resource_templates`, `read_mcp_resource`) are injected only when some connected server advertises the `resources` capability (`tools.ts:27-31`, `tools.ts:136-386`). Under `experimentalCodeMode` MCP tools are skipped (`tools.ts:388`).
- A `StructuredOutput` tool is injected when the last user message has `format.type === "json_schema"`, with `toolChoice: "required"` and a dedicated system prompt (`prompt.ts:74-82`, `prompt.ts:1243-1250`, `prompt.ts:1270-1271`, `prompt.ts:1285`).

### Request assembly

- System prompt is `[agent.prompt ?? SystemPrompt.provider(model), ...session system parts..., user.system]` joined with newlines (`llm/request.ts:58-66`); plugin hook `experimental.chat.system.transform` may rewrite it (`request.ts:69-78`). The session contributes environment, instructions, MCP instructions, and skills blocks (`prompt.ts:1257-1269`); messages pass through `experimental.chat.messages.transform` (`prompt.ts:1255`).
- Sampling parameters default per model via `ProviderTransform`, are overridable per agent (`agent.temperature`, `agent.topP`) and are exposed to the `chat.params` plugin hook (`request.ts:114-132`); `maxOutputTokens` uses `OUTPUT_TOKEN_MAX = 32_000` as default cap (`session/llm.ts:33`, `provider/transform.ts:18`, `transform.ts:1418`).
- Options merge order: provider base options, then `model.options`, then `agent.options`, then the selected variant options (`request.ts:84-91`).
- OpenAI Responses-family providers (`@ai-sdk/openai`, `@ai-sdk/azure`, `@ai-sdk/amazon-bedrock/mantle`) get `strict: false` forced on every function tool ("Codex parity" comment, `request.ts:149-157`).
- History is converted by `MessageV2.toModelMessagesEffect` (`message-v2.ts:131-415`): assistant messages with errors are dropped except aborted turns that have visible content (`message-v2.ts:248-256`); completed tool parts carry a `[Old tool result content cleared]` placeholder when compacted or truncation per `toolOutputMaxChars` (`message-v2.ts:292-296`, truncator at `message-v2.ts:49-53`); media unsupported in tool results is extracted into a synthetic user message prefixed `"Attached media from tool result:"` (`message-v2.ts:46`, `message-v2.ts:147-159`, `message-v2.ts:380-394`).
- Outbound requests carry identifying headers: `User-Agent: opencode/${InstallationVersion}` plus `x-opencode-*` headers for opencode providers or `x-session-affinity`/`X-Session-Id`/`x-parent-session-id` otherwise (`request.ts:18`, `request.ts:181-204`).

### Subagents and task delegation

- A `SubtaskPart` queued by an `agent` prompt part or a subagent-mode command is executed in-loop by `handleSubtask` (`prompt.ts:1142-1147`, `prompt.ts:255-449`). It creates an assistant message plus a running `task` tool part, then calls the `task` tool directly with `extra: { bypassAgentCheck: true, promptOps }`, so no permission ask gates the user-scheduled subtask (`prompt.ts:283-349`; bypass check at `tool/task.ts:119-129`). Permission asks inside the child run merge the subagent's own ruleset with the parent session rules (`prompt.ts:341-348`).
- If the requested agent does not exist, an `Agent not found: "<name>". Available agents: ...` error is published and thrown (`prompt.ts:313-320`). Interrupting the subtask aborts its `AbortController` and marks the part `Cancelled` (`prompt.ts:360-379`).
- The `task` tool (outside this component's file list but the delegation target) creates a child session with `parentID: ctx.sessionID` and title `<description> (@<name> subagent)` (`tool/task.ts:156-172`), enforces depth `cfg.subagent_depth ?? 1` by walking `parentID` links (`tool/task.ts:104-117`), and reuses an existing child session when `task_id` is passed (`tool/task.ts:136-138`).
- Child permission derivation is `deriveSubagentSessionPermission`: only the parent session's deny rules and `external_directory` rules propagate; `todowrite` and `task` are denied unless the subagent's own ruleset mentions them (`agent/subagent-permissions.ts:14-27`, mirrored as `childToolDenies` at `tool/task.ts:143-155` plus `experimental.primary_tools` denies).
- The child runs through the same `promptOps.prompt` machinery (`tool/task.ts:200-214`), i.e. full recursion into this loop in a new session. Foreground tasks race completion against promotion to background (`tool/task.ts:317-347`); background mode requires `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS` (or `OPENCODE_EXPERIMENTAL`) and otherwise fails with "Background subagents require OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=true" (`tool/task.ts:97-101`, `effect/runtime-flags.ts:43`). On completion the result is re-injected into the parent session as a synthetic user message wrapped in `<task id=... state=...>` XML (`tool/task.ts:64-79`, `tool/task.ts:216-243`).
- User-invoked `command`s whose resolved agent has `mode === "subagent"` are rewritten into a `subtask` part instead of inline text (`prompt.ts:1439-1451`).

### Shell passthrough (no LLM)

- `shell(input)` runs a user-executed command outside the model loop: it records a synthetic user text "The following tool was executed by the user" (`prompt.ts:484`) and a running `tool` part, spawns via `ChildProcess` with `stdin: "ignore"`, `forceKillAfter: "3 seconds"`, `TERM: "dumb"` (`prompt.ts:559-565`), streams output into the part metadata, and on interrupt appends `<metadata>\nUser aborted the command\n</metadata>` to the output (`prompt.ts:530-532`). It is guarded by the same runner state machine and fails with `Session.BusyError` when not idle (`prompt.ts:1349-1354`, `run-state.ts:96-105`, `effect/runner.ts:140-169`).

## Key facts with anchors

- Outer loop is an unbounded `while (true)` over provider steps; the only per-run step cap is `agent.steps ?? Infinity` (`packages/opencode/src/session/prompt.ts:1088`, `prompt.ts:1178`).
- Turn exit requires a non-`tool-calls` finish, no pending tool parts, and assistant parented to the last user message (`prompt.ts:1111-1130`).
- One `streamText` call per loop iteration; AI SDK `maxRetries` defaults to 0 and session-level retry supplies up to 5 retries (`session/llm.ts:323`, `session/retry.ts:31,192`).
- Step result vocabulary is `"compact" | "stop" | "continue"` (`session/processor.ts:30`); compaction is triggered both proactively (`prompt.ts:1161-1168`) and reactively on provider `ContextOverflowError` (`processor.ts:607-618`).
- Doom loop guard: 3 consecutive identical tool calls raise a `doom_loop` permission ask (`processor.ts:29,353-380`); default action is `ask` (`agent/agent.ts:121`).
- Interrupted tools are settled after a `250 millis` grace period and marked `metadata: { ..., interrupted: true }` (`processor.ts:573,583-592`).
- Per-session runner state machine is `Idle | Running | Shell | ShellThenRun` (`packages/opencode/src/effect/runner.ts:33-37`); a prompt during a running run awaits the same fiber, a prompt during a shell queues behind it (`runner.ts:115-138`).
- Built-in agents: `build` (default primary), `plan` (edits denied except `.opencode/plans/*.md` and global plans dir), `general` (subagent, `todowrite` denied), `explore` (subagent, everything denied except `grep`, `glob`, `list`, `bash`, `webfetch`, `websearch`, `read`), plus hidden `compaction`, `title` (temperature 0.5), `summary` (`agent/agent.ts:140-265`).
- `explore` has `bash: "allow"` (`agent/agent.ts:205`). (Interpretation: the read-only exploration agent can still execute shell commands; safety relies on model/provider behavior and on `bash` tool policy elsewhere.)
- Subagent child sessions deny `task` and `todowrite` unless their own ruleset allows them, and inherit only deny + `external_directory` rules from the parent session (`agent/subagent-permissions.ts:14-27`).
- Subagent nesting depth defaults to 1 (`tool/task.ts:111`); background subagents are behind an experimental flag (`tool/task.ts:97-101`).
- Tool denial is enforced both ahead of the request (`Permission.disabled` filter, `llm/request.ts:208-214`) and at call time (`ctx.ask`, `session/tools.ts:81-89`).
- MCP-originated tool calls always pass through an ask with `patterns: ["*"]` (`session/tools.ts:408`); tool outputs from MCP are truncated by the shared `Truncate` service (`tools.ts:464-469`).

## Configuration and defaults

All values copied character-exact from the pinned tree.

- Permission defaults for every agent before user config merge (`agent/agent.ts:119-136`): `"*": "allow"`, `doom_loop: "ask"`, `question: "deny"`, `plan_enter: "deny"`, `plan_exit: "deny"`, `external_directory: { "*": "ask", ...whitelisted dirs: "allow" }`, `read: { "*": "allow", "*.env": "ask", "*.env.*": "ask", "*.env.example": "allow" }`. Whitelisted dirs are the truncate glob, `Global.Path.tmp` children, skill dirs, and reference dirs (`agent/agent.ts:108-117`).
- User config can override per agent via `cfg.agent[key]` including `disable: true` which deletes the agent, and `steps` which sets the per-agent step cap (`agent/agent.ts:267-294`). Default agent is `cfg.default_agent`, else the first non-subagent, non-hidden agent, which in the default set is `build` (`agent/agent.ts:316-340`).
- Retry knobs are compile-time constants, not config (`retry.ts:26-31`): initial 2000 ms, factor 2, jitter 0.25, headerless cap `30_000` ms, hard cap `2_147_483_647` ms, max 5 retries.
- `compaction.auto === false` disables both proactive overflow compaction and reactive recovery (in which case the error is surfaced and the session goes idle) (`session/overflow.ts:28`, `session/processor.ts:608-613`). `compaction.reserved` overrides the default `COMPACTION_BUFFER = 20_000` tokens (`overflow.ts:8,14-16`).
- Output token default cap `OUTPUT_TOKEN_MAX = 32_000`, overridable via env `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (`provider/transform.ts:18`, `effect/runtime-flags.ts:52`).
- Environment flags relevant to this component (`effect/runtime-flags.ts:10-56`): `OPENCODE_EXPERIMENTAL` (umbrella), `OPENCODE_EXPERIMENTAL_NATIVE_LLM`, `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS`, `OPENCODE_EXPERIMENTAL_CODE_MODE`, `OPENCODE_CLIENT` (default `"cli"`).
- Runtime config keys read directly by the loop machinery: `experimental.continue_loop_on_deny` (`processor.ts:633`), `experimental.openTelemetry` (`llm.ts:208,345`), `subagent_depth` (`tool/task.ts:111`), `experimental.primary_tools` (`tool/task.ts:150`), `default_agent` (`agent/agent.ts:322,330`), `shell` (`prompt.ts:523`).
- MCP resource attachment cap `MAX_MCP_RESOURCE_BLOB_BYTES = 10 * 1024 * 1024` with allowed MIME set `application/pdf`, `image/gif`, `image/jpeg`, `image/png`, `image/webp` (`prompt.ts:65-72`, duplicated in `tools.ts:32-39`).
- Title generation runs with `retries: 2` against the AI SDK (`prompt.ts:234`); agent `title` temperature 0.5 (`agent/agent.ts:240`). Agent generation (`Agent.generate`) uses temperature 0.3 (`agent/agent.ts:396`).
- Whether the native LLM runtime supports a given provider is documented (repo-internal) as OpenAI, opencode-managed OpenAI-compatible, and Anthropic API-key paths only (`session/llm/AGENTS.md:89`); runtime confirmation of provider coverage beyond this file is `[EVIDENCE NEEDED]` (I did not read `llm/native-runtime.ts` gate internals for this note).

## Limitations and unknowns

- AI SDK step semantics are not verifiable in the pinned tree. `streamText` is imported from the `ai` package (`llm.ts:9`) and its internal `stopWhen`/multi-step behavior was not inspected (no vendored copy examined). The loop structure and the `hasToolCalls` re-entry check (`prompt.ts:1106-1116`) suggest opencode assumes the SDK executes tools within one call and returns, but the exact contract lives in the dependency.
- The `invalid` repair tool is referenced (`llm.ts:310-317`) but defined elsewhere (tool registry, covered by the `opencodeTools` note); its behavior here is only the rerouting contract.
- `Permission.evaluate`/`Permission.ask` internals, `Snapshot.track/patch/revert` git mechanics, and storage persistence (`SessionTable`, drizzle) belong to other components (`opencodePermissions`, `opencodeStateSnapshots`); this note treats them as called services.
- Compaction and summary prompt contents (`agent/prompt/compaction.txt`, `summary.txt`, plus `session/system.ts` system assembly) live in the `opencodeContextCompaction` component; I did not quote their text.
- The `prompt/` directory of model-specific system prompt files (`anthropic.txt`, `beast.txt`, `codex.txt`, `copilot-gpt-5.txt`, `default.txt`, `gemini.txt`, `gpt.txt`, `kimi.txt`, `meta.txt`, `plan-mode.txt`, `plan-reminder-anthropic.txt`, `plan.txt`, `trinity.txt`, `build-switch.txt`) is selected by `SystemPrompt.provider` (`llm/request.ts:60`), whose selection logic is in `session/system.ts` (other component); I list the files but did not analyze selection.
- `MAX_STEPS_PROMPT` enforcement is advisory: tools remain in the request at the last step; only the injected assistant text forbids tool calls (`prompt.ts:1279-1282`, `core/src/session/runner/max-steps.ts:1-16`). Whether the provider complies is runtime behavior I cannot observe statically.
- Retry classification leans on regex matching of provider error text (`retry.ts:33-40`); behavior on unlisted error strings is "no retry", which is only observable empirically.
- Static analysis only: no live runs were made (per brief constraints), so queueing timing, actual token accounting, and plugin hook ordering under real providers are unobserved.
- Full-depth gap flags for the literature gate: no source-level blockers found for this component. The unverifiable items above are cross-package facts, not missing evidence for the turn loop itself.

## Relevance to the brief

My own inference, separated from code facts.

- RQ1/RQ2 (turn loop dimension): OpenCode's loop is a thin TypeScript outer `while` over single AI SDK `streamText` steps, with persistence-driven continuation: the loop condition is computed from stored message parts (`prompt.ts:1106-1130`) rather than from in-memory step state. This contrasts with Codex's Rust thread/turn machinery (see `codexTurnLoop` note) and is the key structural difference to verify in synthesis. The Effect-based runtime supplies structured cancellation, per-session serialization, and retry as schedulers rather than ad-hoc control flow.
- RQ3 (capability vs safety): the default agent runs with `"*": "allow"` (`agent/agent.ts:120`); safety is carried by per-tool `ask` prompts, the doom-loop ask, env-file read asks, and plan-mode edit denies, not by any OS sandbox (consistent with the registry's `[CLOSED]` note on opencode OS-sandbox). The subagent permission derivation deliberately not inheriting parent allow-rules is a design choice worth quoting (`subagent-permissions.ts:4-13` docstring).
- RQ4 is not addressed by this source (Claude Code).
- Left open for other notes: compaction prompts and context window policy details (`opencodeContextCompaction`), tool implementations and apply_patch (`opencodeTools`), permission evaluation semantics (`opencodePermissions`).

## Quotables for the report

- Loop exit condition, paraphrase-ready: the loop continues while the last assistant message has pending tool parts or `finish === "tool-calls"` ("Some providers return 'stop' even when the assistant message contains tool calls", `packages/opencode/src/session/prompt.ts:1103-1109`). Frame as: OpenCode trusts stored parts, not provider stop reasons.
- `Result = "compact" | "stop" | "continue"` (`packages/opencode/src/session/processor.ts:30`). Frame as the three-way step verdict, with compaction as a first-class loop outcome.
- Doom loop guard constants: `DOOM_LOOP_THRESHOLD = 3` and `permission.ask({ permission: "doom_loop", ... })` (`processor.ts:29,372-379`). Frame as an explicit anti-loop device absent from the Claude Code surface and different from Codex's approach (verify in synthesis).
- Retry defaults block: `RETRY_INITIAL_DELAY = 2000`, `RETRY_BACKOFF_FACTOR = 2`, `RETRY_JITTER_FACTOR = 0.25`, `RETRY_MAX_RETRIES = 5` (`session/retry.ts:26-31`).
- Runner state union `Idle | Running | Shell | ShellThenRun` (`packages/opencode/src/effect/runner.ts:33-37`). Frame as the session-level concurrency state machine: user shell commands interleave with, and can delay, agent runs.
- MAX_STEPS enforcement is prompt-only: "Tools are disabled until next user input. Respond with text only." (`packages/core/src/session/runner/max-steps.ts:1-16`) while tools stay in the request (`prompt.ts:1279-1282`). Frame as soft guardrail.
- Subagent rule derivation docstring: "Parent agent restrictions only govern that agent; the subagent's own permissions determine its capabilities." (`agent/subagent-permissions.ts:4-13`). Frame as OpenCode's delegation security model: deny-inheritance plus per-agent capability defaults.
