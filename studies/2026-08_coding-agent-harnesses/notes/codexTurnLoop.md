---
source_key: codexTurnLoop
read_date: "2026-08-20"
confidence: high
relevance: 3
repo: codex
commit: af700180808cce2ce28a31aad0fbad4dc58b857a
---

# Notes: Codex: turn loop, thread manager, and turn state machine (codex)

## Source identification

- Key: `codexTurnLoop`
- Repository: `codex` at `af700180808cce2ce28a31aad0fbad4dc58b857a` (see `sources/repos.yaml`; branch `main`, pinned clean tree, remote `https://github.com/openai/codex`)
- Component scope: `codex-rs/core/src/agent/` (`mod.rs`, `control.rs`, `registry.rs`, `role.rs`, `status.rs`, `builtins/explorer.toml`, `builtins/awaiter.toml`); `codex-rs/core/src/codex_thread.rs`; `codex-rs/core/src/thread_manager.rs`; `codex-rs/core/src/turn_metadata.rs`; `codex-rs/core/src/turn_diff_tracker.rs`; `codex-rs/core/src/turn_timing.rs`; `codex-rs/core/src/state/` (`session.rs`, `turn.rs`, `service.rs`, `auto_compact_window.rs`); `codex-rs/core/src/tasks/` (`regular.rs`, `lifecycle.rs`, `compact.rs`, `review.rs`, `user_shell.rs`); `codex-rs/core/src/session/` (notably `turn.rs`, `turn_input.rs`, `handlers.rs`, `mod.rs`, `input_queue.rs`, `turn_context.rs`); `codex-rs/protocol/` (notably `protocol.rs`, `turn_input.rs`, `items.rs`, `models.rs`). Supporting code outside the listed component is anchored explicitly when used: `codex-rs/core/src/stream_events_utils.rs`, `codex-rs/core/src/responses_retry.rs`, `codex-rs/core/src/util.rs`, `codex-rs/model-provider-info/src/lib.rs`.
- Tier: codebase

## Purpose and role in the harness

- `CodexThread` is the per-thread handle that clients use to drive a thread; its docs call it the "Conduit for the bidirectional stream of messages that compose a thread (formerly called a conversation) in Codex" (`codex-rs/core/src/codex_thread.rs:190-191`). It wraps an `Arc<Session>` and a `SessionIo` pair of channels (`codex_thread.rs:166-174`).
- `ThreadManager` creates, resumes, and forks threads (`codex-rs/core/src/thread_manager.rs:218` struct, `thread_manager.rs:417` impl; `resume_thread_from_rollout` at `thread_manager.rs:970`, `resume_thread_with_history` at `thread_manager.rs:990`, `fork_thread` at `thread_manager.rs:1150`, `fork_thread_from_history` at `thread_manager.rs:1195`, `fork_prepared_thread` at `thread_manager.rs:1224`).
- Client requests are `Submission` values carrying an `Op` over a channel; a per-session `submission_loop` dispatches them (`codex-rs/core/src/session/handlers.rs:515-522`, spawned from `codex-rs/core/src/session/mod.rs:780`).
- A "turn" is one background Tokio task implementing `SessionTask` (`codex-rs/core/src/tasks/mod.rs:179-211`). Regular user turns spawn a `RegularTask` (`codex-rs/core/src/tasks/regular.rs:22`), whose `run` calls `run_turn` (`codex-rs/core/src/session/turn.rs:153`) in a loop until no pending input remains (`regular.rs:74-90`).
- `run_turn` is Codex's agent loop: it seeds context, runs user-prompt hooks, then iterates sampling requests against the model; each sampling request streams model events, executes tool calls concurrently, and decides whether the model needs follow-up (`turn.rs:281-302`, `turn.rs:363-405`).
- Per-turn mutable state lives in `ActiveTurn`/`TurnState` (`codex-rs/core/src/state/turn.rs:31-35`, `state/turn.rs:88-103`); persistent session state (history (`ContextManager`), auto-compact window) is `SessionState` (`codex-rs/core/src/state/session.rs:27-50`).
- Inference about role: this component is the Codex counterpart of OpenCode's `SessionPrompt`/`SessionProcessor` loop covered in `notes/opencodeSessionLoop.md`, and is central to RQ1/RQ2 for the Codex side. Stated as inference; the code facts above are what the source establishes.

## Mechanism

Code facts below; items marked "(interpretation)" describe intent I attribute to the code based on its structure and comments. Inferences about the brief are deferred to "Relevance to the brief".

### Submission entry and dispatch

- `CodexThread::submit(op)` forwards into `SessionIo::submit` (`codex_thread.rs:211-213`). Typed turn entry points: `start_or_steer_turn` (`codex_thread.rs:283-289`), `start_turn_if_idle` (`codex_thread.rs:295-298`); both delegate to `submit_turn_input_with_mode` with a `TurnInputMode` (`codex_thread.rs:287`, `codex_thread.rs:299-300`).
- Each submission is `Submission { id, op, trace, parent_turn_id, root_turn_id }` (`codex-rs/protocol/src/protocol.rs:184-199`); `parent_turn_id`/`root_turn_id` are documented as used only for inter-agent communication (`protocol.rs:193-198`).
- `submission_loop` receives `Submission`s until `Op::Shutdown` ("To break out of this loop, send Op::Shutdown", `codex-rs/core/src/session/handlers.rs:520`) and matches on `sub.op` (`handlers.rs:522-526`):
  - `Op::Interrupt` calls `interrupt(&sess)` (`handlers.rs:527-530`). The protocol documents `Interrupt` as "Abort current task without terminating background terminal processes. This server sends `EventMsg::TurnAborted` in response." (`protocol.rs:544-546`).
  - `Op::TurnInput { request, mode, reply }` calls `turn_input::handle` and replies through a oneshot (`handlers.rs:570-578`; variant at `protocol.rs:570-575`).
  - `Op::RecoverTurn` resumes an interrupted regular turn through `turn_input::handle_recovery` (`handlers.rs:579-587`; variant at `protocol.rs:577-581`).
  - `Op::InterAgentCommunication` forwards inter-agent mail with `sub.parent_turn_id`/`sub.root_turn_id` (`handlers.rs:592-602`).
  - Approvals and user-input answers route to turn-local waiters (`handlers.rs:603-618`; waiter tables in `TurnState`, `state/turn.rs:89-99`).

### Start / steer / reject decision

- `turn_input.rs` is self-described as "the one place Core decides whether submitted input starts a turn, steers an active turn, or is rejected. It replies after that decision; it does not wait for user-prompt hooks, updating the in-memory model context, rollout persistence, or sampling." (`codex-rs/core/src/session/turn_input.rs:3-6`).
- Routing modes: `TurnInputMode::StartOrSteer`, `StartIfIdle`, and `Steer { expected_turn_id }` (`codex-rs/protocol/src/turn_input.rs:117-124`).
- Submitted input is the protocol `TurnInput` enum with variants `UserInput { content: Vec<UserInput>, client_id }`, `ResponseItem(ResponseItem)`, `InterAgentCommunication(InterAgentCommunication)` (`protocol/src/turn_input.rs:16-25`).
- `handle` dispatches by mode (`turn_input.rs:141-156`); `handle_recovery` builds an empty-input `start_if_idle` with `is_recovery = true` (`turn_input.rs:158-165`).
- Thread settings are validated up front but applied only after acceptance: "Thread settings are validated up front but only applied after Core accepts the input. Start-only options are only consumed by `apply_started`." (`turn_input.rs:48-52`). Persistent settings apply on both Started and Steered; turn start options only on Started (`turn_input.rs:8-9`, `protocol/src/turn_input.rs:73-88`).
- `start_or_steer` accepts only `UserInput` for steering ("only user input can steer a turn", `turn_input.rs:180-188`), then tries `session.steer_input(...)` (`turn_input.rs:195-205`). On success it returns `TurnInputSubmission::Steered { turn_id }` (`turn_input.rs:207-210`).
- On `NotSubmittedReason::NoActiveTurn`, `start_or_steer` applies start settings via `apply_started` (which calls `Session::new_turn_with_sub_id`, `turn_input.rs:95-127`), records root-turn lineage, merges additional context, and spawns the turn with `session.spawn_task(turn_context, task_input, RegularTask::new())` (`turn_input.rs:211-243`), returning `Started { turn_id: submission_id }` (`turn_input.rs:244-246`). Any other rejection reason becomes `NotSubmitted { reason }` (`turn_input.rs:248`).
- `start_if_idle` rejects with `PendingTriggerTurn` when trigger-turn mailbox mail exists (`turn_input.rs:269-273`), refuses automatic (non-user, non-recovery) idle work when the collaboration mode is Plan (`turn_input.rs:274-280`), and reserves the `active_turn` slot under the session lock, returning `NotIdle` if occupied (`turn_input.rs:282-291`).
- `NotSubmittedReason` variants: `NotIdle`, `PendingTriggerTurn`, `PlanMode`, `NoActiveTurn`, `ExpectedTurnMismatch { expected, actual }`, `ActiveTurnNotSteerable { turn_kind }`, `ActiveTurnOutputSchemaMismatch`, `EmptyInput` (`protocol/src/turn_input.rs:180-208`).
- The reply only means acceptance: "Started and Steered only mean Core accepted the input for turn processing. They do not wait for user-prompt hooks, updating the in-memory model context, rollout persistence, or sampling." (`protocol/src/turn_input.rs:143-147`).

### Task spawn, task kinds, lifecycle events

- `Session::spawn_task` first aborts any running task with `TurnAbortReason::Replaced`, then starts the new one: `self.abort_all_tasks(TurnAbortReason::Replaced).await` (`codex-rs/core/src/tasks/mod.rs:279-288`).
- The `SessionTask` trait has `kind`, `span_name`, `run`, and a default no-op `abort`; docs state a task runs "on a background Tokio task", that returning `Some` "yields a final message that `Session::on_task_finished` will emit to the client", and returning `CodexErr::TurnAborted` "completes the task through the aborted-turn lifecycle" (`tasks/mod.rs:179-227`, quotes at `tasks/mod.rs:181-185` and `tasks/mod.rs:200-204`).
- `TaskKind` has exactly three variants: `Regular`, `Review`, `Compact` (`codex-rs/core/src/state/turn.rs:67-72`). Implementations: `RegularTask` (`regular.rs:30-33`), plus compact (`codex-rs/core/src/tasks/compact.rs:28`), review (`codex-rs/core/src/tasks/review.rs:54`), and `UserShellCommandTask` which reports `TaskKind::Regular` with span name `"session_task.user_shell"` (`tasks/user_shell.rs:72-79`, timeout `USER_SHELL_TIMEOUT_MS: u64 = 60 * 60 * 1000; // 1 hour` at `tasks/user_shell.rs:49`).
- `UserShellCommandMode` distinguishes `StandaloneTurn` ("Executes as an independent turn lifecycle (emits TurnStarted/TurnComplete via task lifecycle plumbing)") from `ActiveTurnAuxiliary`, which "must not emit a second TurnStarted/TurnComplete pair for the same active turn" (`tasks/user_shell.rs:51-58`); standalone mode emits `EventMsg::TurnStarted` itself (`tasks/user_shell.rs:112-122`), with a comment explaining that `/compact` is an intentional exception to emitting model-visible turn context diffs (`tasks/user_shell.rs:116-119`).
- `RegularTask::run` emits `EventMsg::TurnStarted` inline "so first-turn lifecycle does not wait on startup prewarm resolution" (`regular.rs:46-57`), resolves a startup-prewarmed client session (`regular.rs:58-73`), then loops: `run_turn(...)` and return `Ok(last_agent_message)` when `sess.input_queue.has_pending_input(&sess.active_turn)` is false (`regular.rs:76-90`).
- `Session::on_task_finished` (`tasks/mod.rs:571`) finalizes a turn: with an abort reason it emits `EventMsg::TurnAborted(TurnAbortedEvent { turn_id: Some(..), reason, started_at, completed_at, duration_ms })` (`tasks/mod.rs:788-797`); otherwise `EventMsg::TurnComplete(TurnCompleteEvent { turn_id, last_agent_message, error, started_at, completed_at, duration_ms, time_to_first_token_ms })` (`tasks/mod.rs:798-815`); the event is sent through `send_event` (`tasks/mod.rs:816`) and the `active_turn` slot is cleared (`tasks/mod.rs:823-829`). It also computes `TurnProfile` timing and token-usage telemetry before emission (`tasks/mod.rs:700-777`).
- Extension lifecycle hooks fire around turn boundaries via `emit_turn_start_lifecycle`, `emit_turn_stop_lifecycle`, `emit_turn_abort_lifecycle`, `emit_turn_error_lifecycle`, and thread-idle notifications (`codex-rs/core/src/tasks/lifecycle.rs:11-29`, `lifecycle.rs:31-41`, `lifecycle.rs:70-85`, `lifecycle.rs:87-100`, `lifecycle.rs:43-68`).
- (Interpretation) the design cleanly separates "input accepted" (reply from `turn_input::handle`) from "turn actually ran" (task-level events), so clients can enqueue steers into a busy turn without blocking.

### run_turn: the outer sampling loop

- `run_turn(sess, turn_context, input, prewarmed_client_session, cancellation_token)` (`turn.rs:153-159`):
  1. Drains async hook results that finished after the previous turn (`turn.rs:160-161`).
  2. Reuses the prewarmed `ModelClientSession` or creates one with `sess.services.model_client.new_session()` (`turn.rs:163-164`); a TODO notes pre-turn compaction currently runs before context updates/user input are recorded (`turn.rs:165-168`).
  3. Runs `run_pre_sampling_compact` (`turn.rs:169-176`); a `TurnAborted` error records inputs and propagates, `ToolCollision` propagates, other errors emit a turn error lifecycle and return `Ok(None)` (`turn.rs:177-190`).
  4. Resolves `required_mcp_servers_for_input` (`turn.rs:192-204`).
  5. Captures the first step context: "`run_turn` owns the step used to seed context and make the first sampling request." (`turn.rs:206-222`), via `Session::capture_step_context_with_required_mcp_servers` (`codex-rs/core/src/session/mod.rs:3131`) with a plain-step fallback `capture_step_context` (`session/mod.rs:3118`).
  6. Snapshots model-visible state: "Keep the exact model-visible state used by this turn and its inline compactions." (`turn.rs:223-228`), via `record_context_updates_and_set_reference_context_item` joined with `turn_diff_display_roots`.
  7. Builds skills/plugins injection (`turn.rs:230-240`), runs pending session-start hooks (`turn.rs:242-244`), and records inputs with hooks via `run_hooks_and_record_inputs(.., PersistContext::TurnStart)`; a hook block returns `Ok(None)` (`turn.rs:245-248`).
  8. Records injected skill/plugin items into the conversation history one by one (`turn.rs:258-261`).
  9. Creates a per-turn `TurnDiffTracker`; a comment notes that although it lives across many `run_turn` calls, "from the perspective of the user, it is a single turn" (`turn.rs:267-271`).
- The sampling loop (`turn.rs:281` onward) then iterates:
  - Pending input is drained from the input queue only when `can_drain_pending_input` (`turn.rs:285-292`); the comment explains pending input is input submitted through the UI while the model was running, which "the model might not" support (`turn.rs:282-284`).
  - Pending input is recorded through hooks; a block breaks the loop (`turn.rs:294-302`).
  - A step context is captured once per sampling iteration: "Capture once so context, advertised tools, and tool calls share one request view." (`turn.rs:313-336`).
  - The model request input is built from history: `sess.clone_history().await.for_prompt(&step_context.model_info.input_modalities)` (`turn.rs:349-356`).
  - `run_sampling_request(...)` executes the request (`turn.rs:363-374`).
  - On success, `model_needs_follow_up` from `SamplingRequestResult` gates mailbox delivery acceptance for the current turn (`turn.rs:376-389`), `can_drain_pending_input = true` (`turn.rs:390`), async hooks drain after sampling (`turn.rs:391-392`), and the loop computes `needs_follow_up = model_needs_follow_up || has_pending_input` plus a token status (`turn.rs:393-406`).
  - Rollover: `should_roll_over = needs_follow_up && (sess.take_new_context_window_request().await || token_limit_reached)` (`turn.rs:440-441`). With a comment, "as long as compaction works well in getting us way below the token limit, we shouldn't worry about being in an infinite loop." (`turn.rs:451`), it runs `run_auto_compact(.., CompactionReason::ContextLimit, CompactionPhase::MidTurn)` and `continue`s, deferring input drain when the model still needs follow-up: `can_drain_pending_input = !model_needs_follow_up` (`turn.rs:452-479`). (Compaction internals belong to the `codexContextCompaction` note.)
  - When no follow-up is needed, stop hooks run via `run_turn_stop_hooks`; a blocking stop hook can inject a continuation prompt and `continue` the loop (`turn.rs:482-507`; stop hook runner in `codex-rs/core/src/hook_runtime.rs:306`).
- `run_hooks_and_record_inputs` returns true (block) only when hooks blocked input and no user input was accepted: for each item it runs `inspect_pending_input`, records additional contexts on block, otherwise `record_pending_input`, and returns `blocked_input && !accepted_user_input` (`turn.rs:597-625`).
- Input consumed by turns is the core-local `TurnInput` enum (`codex-rs/core/src/session/input_queue.rs:19-30`) with the same three variant shapes as the protocol enum but carrying `ResponseItemEnvelope` for history items (`input_queue.rs:28`).

### run_sampling_request: retries and request construction

- `run_sampling_request` (`turn.rs:1322-1331`) creates a `ToolCallRuntime` (`turn.rs:1335-1339`), starts a code-mode turn worker (`turn.rs:1340-1344`), sets `max_retries = turn_context.provider.info().stream_max_retries()` (`turn.rs:1345`) and a fresh `ResponsesStreamRetryState::default()` (`turn.rs:1346`).
- Its loop (`turn.rs:1350`): prompt input is the initial input or re-cloned history (`turn.rs:1351-1357`); pending executed tool calls are attached (`turn.rs:1359-1364`); the prompt is built by `build_prompt` (`turn.rs:1365-1369`).
- `build_prompt` sets `tools: step_context.tool_router.model_visible_specs()`, `parallel_tool_calls: true`, `base_instructions`, `output_schema: turn_context.final_output_json_schema.clone()`, and `output_schema_strict: !crate::guardian::is_guardian_reviewer_source(&turn_context.session_source)` (`turn.rs:1294-1310`).
- Retry policy: on `ContextWindowExceeded` it records the full context and returns the error (`turn.rs:1387-1390`); on `UsageLimitReached` it updates rate limits and returns (`turn.rs:1391-1397`); non-retryable errors return (`turn.rs:1406-1408`); retryable errors go to `handle_retryable_response_stream_error(.., ResponsesStreamRequest::Sampling)` then `turn_context.turn_timing_state.record_sampling_retry()` and loop again (`turn.rs:1410-1420`).
- `handle_retryable_response_stream_error` (`codex-rs/core/src/responses_retry.rs:44-52`):
  - With feature `UnboundedConnectionRetries`, for sampling `ConnectionFailed` errors from non-internal, non-Bedrock sessions, it sleeps for the current delay, doubles it, and caps at `MAX_CONNECTION_RETRY_DELAY`, retrying without bound (`responses_retry.rs:58-83`).
  - When `retries >= max_retries` and the client can switch fallback transport, it falls back (WebSocket to HTTPS), emits a warning "Falling back from WebSockets to HTTPS transport.", and resets `retries = 0` (`responses_retry.rs:85-100`).
  - Otherwise while `retries < max_retries` it increments, computes `delay = err.retry_delay().unwrap_or_else(|| backoff(retry_count))`, notifies the UI with "Reconnecting... {retry_count}/{max_retries}" (first websocket retry hidden in release builds), sleeps, and returns `Ok(())` to retry (`responses_retry.rs:102-126`); exhausted retries return `Err(err)` (`responses_retry.rs:128`).
- `backoff` is exponential with jitter: `200 ms * 2^(attempt-1)` times a `0.9..1.1` jitter factor (`codex-rs/core/src/util.rs:86-91` with `INITIAL_DELAY_MS: u64 = 200` and `BACKOFF_FACTOR: f64 = 2.0` at `util.rs:6-7`).

### Streaming: model event handling and tool concurrency

- `try_run_sampling_request` (`turn.rs:2161-2171`) starts the stream via `client_session.stream(prompt, &step_context.model_info, ...)` with `or_cancel(&cancellation_token)` (`turn.rs:2192-2205`), creates an `in_flight: FuturesOrdered<BoxFuture<'static, CodexResult<ResponseInputItem>>>` (`turn.rs:2206-2207`), and loops over stream events (`turn.rs:2232-2258`).
- Cancellation while receiving yields `CodexErr::TurnAborted` (`turn.rs:2255-2257`); a stream error breaks with `Err(err)` (`turn.rs:2260-2262`); an exhausted stream before completion is itself an error: `CodexErr::Stream("stream closed before response.completed")` (`turn.rs:2263-2267`).
- Per-event handling (`turn.rs:2275` match): `OutputItemDone(mut item)` is the main item boundary (`turn.rs:2277`); analytics collects up to `MAX_ANALYTICS_TOOL_CALL_IDS_PER_RESPONSE: usize = 256` tool call ids per response (`turn.rs:2217`, `turn.rs:2279-2294`).
- For each completed output item, `handle_output_item_done` (`codex-rs/core/src/stream_events_utils.rs:288-292`) is called (`turn.rs:2365-2372`); its doc: "Handle a completed output item from the model stream, recording it and queuing any tool execution futures. This records items immediately so history and rollout stay in sync even if the turn is later cancelled." (`stream_events_utils.rs:189-191`).
- Tool branch (`stream_events_utils.rs:296-327`): `ToolRouter::build_tool_call` recognizes the call; Core accepts mailbox delivery for the current turn, logs the call, persists the item via `record_completed_response_item`, then queues `tool_runtime.handle_tool_call(call, cancellation_token)` as `tool_future` and sets `needs_follow_up = true`.
- Non-tool branch (`stream_events_utils.rs:329-360`): messages/reasoning are finalized into `TurnItem`s, `ItemStarted`/`ItemCompleted` events are emitted, the item is recorded into history, and `last_agent_message` is extracted.
- Error branches: `FunctionCallError::RespondToModel` pushes a synthetic `FunctionCallOutput` into the transcript and sets `needs_follow_up = true` (`stream_events_utils.rs:362-382`); `FunctionCallError::Fatal` aborts with `CodexErr::Fatal` (`stream_events_utils.rs:384-386`).
- Back in `try_run_sampling_request`: returned `tool_future`s are `push_back`ed into `in_flight` (`turn.rs:2373-2374`); `needs_follow_up |= output_result.needs_follow_up` (`turn.rs:2379`).
- `ResponseEvent::Completed { response_id, token_usage, end_turn }` records token usage, emits `RawResponseCompleted`, and: `if let Some(false) = end_turn { needs_follow_up = true; }`, then breaks with `SamplingRequestResult { needs_follow_up, last_agent_message }` (`turn.rs:2521-2565`). (Interpretation: the model's `end_turn: false` flag is the server signal that more sampling steps are expected.)
- After the event loop: in-flight tool futures are drained (`turn.rs:2726-2731`, `drain_in_flight` at `turn.rs:2112-2117`), token counts are emitted after tools resolve (`turn.rs:2734-2740`), a still-cancelled token becomes `CodexErr::TurnAborted` (`turn.rs:2742-2743`), and the accumulated unified diff is emitted as `EventMsg::TurnDiff` (`turn.rs:2746-2755`).
- The prompt always advertises `parallel_tool_calls: true` (`turn.rs:1303`), and the `FuturesOrdered` queue is how concurrent tool calls execute and return in order (`turn.rs:2206-2207`, `turn.rs:2373-2374`). (Tool implementations, approval policies, and `ToolRouter` belong to the `codexToolsPatch` and `codexSandboxPermissions` notes.)

### Interruption, events, and agent status

- `Session::interrupt_task` logs "interrupt received: abort current task, if any", records whether a turn was active, and calls `self.abort_all_tasks(TurnAbortReason::Interrupted)`; if no turn was active it also cancels MCP startup (`codex-rs/core/src/session/mod.rs:4091-4098`).
- `TurnAbortReason` variants: `Interrupted`, `Replaced`, `ReviewEnded`, `BudgetLimited` (`codex-rs/protocol/src/protocol.rs:3986-3993`). `Replaced` is what `spawn_task` uses to stop a running turn when new work starts (`tasks/mod.rs:285`).
- `abort_all_tasks` is at `tasks/mod.rs:494`.
- Every protocol event flows through `send_event_raw_with_persistence`: MCP runtime observes it, it is persisted as `RolloutItem::EventMsg` into rollout storage when `persist` is set, recorded in the rollout trace, then delivered (`session/mod.rs:2132-2143`). `deliver_event_raw` derives and stores the agent status (`session/mod.rs:2145-2153`).
- Status is derived event-by-event by `agent_status_from_event` (`codex-rs/core/src/agent/status.rs:6-21`): `TurnStarted` → `Running`; `TurnComplete` → `Completed(ev.last_agent_message)`; `TurnAborted` → `Interrupted` for `Interrupted | BudgetLimited` reasons and `Errored(format!("{:?}", reason))` otherwise; `Error` → `Errored(message)`; `ShutdownComplete` → `Shutdown`; all other events yield `None` (`status.rs:8-19`). Non-final statuses are `PendingInit | Running | Interrupted` (`status.rs:23-28`).
- `TurnStartedEvent` carries `turn_id`, optional `trace_id`, `started_at`, `model_context_window`, and `collaboration_mode_kind` (`protocol.rs:2027-2042`); `TurnCompleteEvent` carries timing fields including `time_to_first_token_ms` (`protocol.rs:2001-2025`); `TurnAbortedEvent` carries `turn_id: Option<String>` and `reason` (`protocol.rs:3968-3984`).

### Turn state structures

- `ActiveTurn { task: Option<RunningTask>, turn_state: Arc<Mutex<TurnState>> }` (`state/turn.rs:31-35`); `RunningTask` holds the `CancellationToken`, an `AbortOnDropHandle`, the task object, kind, `turn_context`, an optional `AgentExecutionGuard`, and a completion timer (`state/turn.rs:74-85`).
- `TurnState` holds pending approvals/permissions/user-input/elicitations/dynamic-tool waiters, `pending_input: TurnInputQueue`, `mailbox_delivery_phase`, granted permissions, `tool_calls: u64`, `has_memory_citation`, and `token_usage_at_turn_start` (`state/turn.rs:87-103`).
- `MailboxDeliveryPhase` is a two-state machine documented at `state/turn.rs:37-56`: a turn starts in `CurrentTurn` so queued child mail can join the next model request; after user-visible terminal output it switches to `NextTurn` so late child mail stays queued; explicit same-turn work (a steered prompt or a tool call after an untagged preamble) reopens `CurrentTurn`.
- `SessionState` holds `history: ContextManager` (`state/session.rs:32`), the `auto_compact_window` (`state/session.rs:42`; `AutoCompactWindow`/`AutoCompactWindowIds` at `codex-rs/core/src/state/auto_compact_window.rs:34` and `auto_compact_window.rs:5`), `previous_turn_settings` (`state/session.rs:37-40`), and `next_turn_is_first` (`state/session.rs:49`). Session-wide services are `SessionServices` (`codex-rs/core/src/state/service.rs:46`).
- `TurnContext` is the turn-scoped immutable context: `sub_id` (the turn id), `mode: ModeKind`, `config: Arc<Config>`, `provider`, `final_output_json_schema`, `turn_metadata_state`, `turn_timing_state`, `terminal_error`, etc. (`codex-rs/core/src/session/turn_context.rs:142-190`); created by `new_turn_with_sub_id` (`turn_context.rs:703`) with defaults at `new_default_turn`/`new_default_turn_with_sub_id` (`turn_context.rs:970`, `turn_context.rs:975`).
- Per-turn bookkeeping helpers: `TurnTimingState` (`codex-rs/core/src/turn_timing.rs:44-47`) records start, first token (`record_turn_ttfm_metric` at `turn_timing.rs:30-41`), per-item start times, and a phase profile with phases `Sampling`, `Compaction`, `ToolBlocking` (`turn_timing.rs:75-80`); `TurnDiffTracker` (`codex-rs/core/src/turn_diff_tracker.rs:49`) accumulates applied-patch deltas capped by `DIFF_TIMEOUT: Duration = Duration::from_millis(100)` before falling back to a coarse content-exact diff (`turn_diff_tracker.rs:15-17`); `TurnMetadataState` (`codex-rs/core/src/turn_metadata.rs:100`) holds turn lineage metadata (parent/root turn ids set in `turn_input.rs:116-125`).

### Agent registry and execution limits

- Sub-agent spawn accounting lives in `codex-rs/core/src/agent/registry.rs`: `reserve_spawn_slot` fails with `CodexErrorDetails::AgentLimitReached { max_threads }` when `try_increment_spawned` hits the cap (`registry.rs:81-101`, `registry.rs:278-281`; asserted in `agent/registry_tests.rs:102-105`); spawn depth is bounded via `exceeds_thread_spawn_depth_limit` (`registry.rs:72-76`).
- Concurrent v2 sub-agent turns are limited by `AgentExecutionLimiter` (`codex-rs/core/src/agent/control/execution.rs:14-16`) with `ensure_execution_capacity_for_turn_start` (`execution.rs:30`) and `max_threads()` defaulting to `usize::MAX` when uninitialized (`execution.rs:77-78`).
- The default agent role name is `DEFAULT_ROLE_NAME: &str = "default"` (`codex-rs/core/src/agent/role.rs:33`).
- Built-in agent roles are TOML files; `builtins/awaiter.toml` sets `background_terminal_max_timeout = 3600000` and `model_reasoning_effort = "low"` plus a developer instruction to await a command's terminal state (`codex-rs/core/src/agent/builtins/awaiter.toml:1-35`); `builtins/explorer.toml` is empty (0 lines).
- Agent-to-agent input arrives as `Op::InterAgentCommunication` with parent/root turn ids (`handlers.rs:592-602`) and queues through the mailbox described by `MailboxDeliveryPhase` (`state/turn.rs:37-56`).

## Key facts with anchors

- One submission channel per thread; `submission_loop` matches `Op` variants until `Op::Shutdown` (`codex-rs/core/src/session/handlers.rs:515-522`).
- Start vs steer vs reject is decided in one place, `turn_input.rs`, with an explicit 8-variant `NotSubmittedReason` enum (`codex-rs/core/src/session/turn_input.rs:1-9`; `codex-rs/protocol/src/turn_input.rs:180-208`).
- A turn is a background Tokio `SessionTask`; spawning replaces any running task with `TurnAbortReason::Replaced` (`codex-rs/core/src/tasks/mod.rs:279-288`).
- `RegularTask::run` emits `TurnStarted` inline and loops `run_turn` while `input_queue.has_pending_input` is true (`codex-rs/core/src/tasks/regular.rs:46-90`).
- `run_turn` = pre-sampling compact, MCP requirement resolution, step-context capture, hooks/input recording, then an outer loop of sampling requests, mid-turn compaction rollover, and stop hooks (`codex-rs/core/src/session/turn.rs:153-507`).
- Follow-up decision: `needs_follow_up = model_needs_follow_up || has_pending_input`, where `model_needs_follow_up` comes from queued tool calls or `Completed.end_turn == Some(false)` (`turn.rs:405`, `turn.rs:2559-2561`).
- Tool calls execute concurrently through `FuturesOrdered` in-flight futures built in `handle_output_item_done` (`turn.rs:2206-2207`, `turn.rs:2373-2379`; `stream_events_utils.rs:296-327`).
- `parallel_tool_calls: true` is hard-coded in `build_prompt` (`turn.rs:1303`).
- Stream retries: provider-configured `stream_max_retries` (default 5), retryable-error filtering, bounded retries with exponential backoff (`200 ms * 2^(n-1)`, jitter 0.9-1.1x), unbounded connection retries behind a feature flag, and a WebSocket-to-HTTPS transport fallback that resets retries (`turn.rs:1345`, `turn.rs:1406-1420`; `responses_retry.rs:44-128`; `util.rs:6-7`, `util.rs:86-91`; `codex-rs/model-provider-info/src/lib.rs:357-361`).
- Interruption is `abort_all_tasks(TurnAbortReason::Interrupted)` and surfaces as `EventMsg::TurnAborted` mapped to `AgentStatus::Interrupted` (`session/mod.rs:4091-4098`; `tasks/mod.rs:788-797`; `agent/status.rs:10-14`).
- Events persist to rollout as `RolloutItem::EventMsg` on the way to clients (`session/mod.rs:2132-2143`).
- Item surface: model `ResponseItem`s (`codex-rs/protocol/src/models.rs:940`) are converted into client-visible `TurnItem`s (18 variants: `UserMessage`, `HookPrompt`, `AgentMessage`, `Plan`, `Reasoning`, `CommandExecution`, `DynamicToolCall`, `CollabAgentToolCall`, `SubAgentActivity`, `WebSearch`, `ImageView`, `Extension`, `ImageGeneration`, `EnteredReviewMode`, `ExitedReviewMode`, `FileChange`, `McpToolCall`, `ContextCompaction`) (`codex-rs/protocol/src/items.rs:44-75`; `stream_events_utils.rs:329-360`).

## Configuration and defaults

Character-exact values and their code locations at the pinned commit:

- `DEFAULT_STREAM_MAX_RETRIES: u64 = 5` (`codex-rs/model-provider-info/src/lib.rs:27`), effective value capped: `stream_max_retries()` returns `self.stream_max_retries.unwrap_or(DEFAULT_STREAM_MAX_RETRIES).min(MAX_STREAM_MAX_RETRIES)` (`lib.rs:357-361`) with `MAX_STREAM_MAX_RETRIES: u64 = 100` (`lib.rs:32`).
- `DEFAULT_REQUEST_MAX_RETRIES: u64 = 4` (`lib.rs:28`), capped by `MAX_REQUEST_MAX_RETRIES: u64 = 100` (`lib.rs:34`) in `request_max_retries()` (`lib.rs:350-354`).
- `DEFAULT_STREAM_IDLE_TIMEOUT_MS: u64 = 300_000` (`lib.rs:26`), applied by `stream_idle_timeout()` (`lib.rs:364-368`).
- `DEFAULT_WEBSOCKET_CONNECT_TIMEOUT_MS: u64 = 15_000` (`lib.rs:30`).
- `INITIAL_CONNECTION_RETRY_DELAY: Duration = Duration::from_secs(5)` and `MAX_CONNECTION_RETRY_DELAY: Duration = Duration::from_secs(60)` (`codex-rs/core/src/responses_retry.rs:17-18`); connection retry delay doubles each attempt and is capped at the max (`responses_retry.rs:79-81`).
- `INITIAL_DELAY_MS: u64 = 200`, `BACKOFF_FACTOR: f64 = 2.0`, jitter range `0.9..1.1` (`codex-rs/core/src/util.rs:6-7`, `util.rs:89`).
- `DIFF_TIMEOUT: Duration = Duration::from_millis(100)` for turn diff tracking (`codex-rs/core/src/turn_diff_tracker.rs:17`).
- `USER_SHELL_TIMEOUT_MS: u64 = 60 * 60 * 1000; // 1 hour` (`codex-rs/core/src/tasks/user_shell.rs:49`).
- `MAX_ANALYTICS_TOOL_CALL_IDS_PER_RESPONSE: usize = 256` (`codex-rs/core/src/session/turn.rs:2217`).
- `THREAD_CREATED_CHANNEL_CAPACITY: usize = 1024` and `MAX_TURN_ENVIRONMENT_CWD_BYTES: usize = 8 * 1024` (`codex-rs/core/src/thread_manager.rs:100-102`).
- Built-in agent role `awaiter.toml`: `background_terminal_max_timeout = 3600000`, `model_reasoning_effort = "low"` (`codex-rs/core/src/agent/builtins/awaiter.toml:1-2`).
- `DEFAULT_ROLE_NAME: &str = "default"` (`codex-rs/core/src/agent/role.rs:33`).
- `parallel_tool_calls: true` (hard-coded per sampling request, `codex-rs/core/src/session/turn.rs:1303`).
- Feature-gated behavior: `Feature::UnboundedConnectionRetries` enables unbounded connection retries for sampling (`codex-rs/core/src/responses_retry.rs:58-83`).
- Retry caps and idle timeouts are per-provider TOML config fields surfaced through `ModelProviderInfo` (e.g., `stream_max_retries`, `stream_idle_timeout_ms` fields at `lib.rs:134`); the defaults above apply when unset. Provider-config values set by the user in `config.toml` are loaded through the `codexConfigProviders` component and not re-verified here.

## Limitations and unknowns

- This note covers control flow only. What tools exist, their schemas, approval gating, and sandbox enforcement are in `codex-rs/core/src/tools/` (`codexToolsPatch`, `codexSandboxPermissions` notes) and were only observed indirectly through `ToolRouter::build_tool_call` and `ToolCallRuntime::handle_tool_call` (`stream_events_utils.rs:296`, `stream_events_utils.rs:319-322`).
- Compaction triggers are visible here (`run_pre_sampling_compact` at `turn.rs:169`, `run_auto_compact` with `CompactionReason::ContextLimit, CompactionPhase::MidTurn` at `turn.rs:452-464`), but compaction mechanics are out of this component's scope (see `codexContextCompaction`).
- `compact.rs` and `review.rs` task bodies were only inspected at entry-point level (`codex-rs/core/src/tasks/compact.rs:28`, `codex-rs/core/src/tasks/review.rs:54`); their internal loops are not described here.
- Realtime (voice) ops and plan-mode stream handling are present in the dispatch and streaming paths (`handlers.rs:535-568`; `turn.rs:2225-2227`) but not analyzed in depth.
- The model-side meaning of `end_turn` in `ResponseEvent::Completed` and of phases like `MessagePhase::Commentary` is a Responses API contract not defined in this repo (`turn.rs:2521-2524`, `turn.rs:2343-2346`). [EVIDENCE NEEDED: checked `codex-rs/protocol/src/protocol.rs` around `ResponseEvent` and `codex-rs/model-provider-info`; no local spec.]
- Whether `TurnContext.mode == ModeKind::Plan` changes the advertised tool set (vs only stream parsing at `turn.rs:2225-2227`) was not verified in this component.
- `agent/control.rs` (spawn/resume/communication APIs, `AgentControl`) was inventoried but not fully traced; this note relies on the execution limiter and registry for concurrency limits.
- All anchors are at commit `af70018`; behavior can drift on `main` (the brief prohibits claims outside pinned commits).
- Prior scratch notes from an earlier session misnamed the sampling function `run_sampling_match`; the correct symbol at the pinned commit is `run_sampling_request` (`turn.rs:1322`).

## Relevance to the brief

My inference, separated from code facts:

- RQ1/RQ2 (harness components, turn loop): Codex implements the canonical LLM tool-use loop with a distinctly "session-server" architecture: a persistent submission/event channel pair per thread, a dispatch loop, and turns as abortable background tasks (`handlers.rs:515-522`; `tasks/mod.rs:179-211`). This contrasts with OpenCode's fiber-scoped `runLoop` in `notes/opencodeSessionLoop.md`, and is directly comparable in the synthesis matrix.
- Two features stand out as genuine harness differentiators worth testing against OpenCode/Claude Code: (1) steerable active turns with an explicit `StartOrSteer` routing mode and a structured `NotSubmittedReason` taxonomy (`turn_input.rs:1-9`; `protocol/src/turn_input.rs:117-208`), and (2) transport-level resilience inside the sampling loop: bounded retries, transport fallback WebSocket-to-HTTPS, and unbounded connection retries behind a feature flag (`responses_retry.rs:44-128`).
- The prompt hard-codes `parallel_tool_calls: true` and executes tool calls concurrently while the stream continues (`turn.rs:1303`, `turn.rs:2373-2379`); whether OpenCode or Claude Code pipeline tool calls the same way is an open comparison point.
- Safety-relevant seams visible from the loop: every `ResponseItem` is recorded to history/rollout immediately ("history and rollout stay in sync even if the turn is later cancelled", `stream_events_utils.rs:189-191`), approvals are turn-local oneshot waiters (`state/turn.rs:89-95`), and interrupts leave background terminal processes running by design (`protocol.rs:544-546`). These feed RQ3 via the permissions/sandbox notes.
- Leaves open: TUI/app-server presentation of these events (codexInterfaces), tool policy enforcement, and compaction quality (codexContextCompaction); the note marks those seams explicitly for the writer.

## Quotables for the report

- "This is the one place Core decides whether submitted input starts a turn, steers an active turn, or is rejected." (`codex-rs/core/src/session/turn_input.rs:3-4`; framing: Codex centralizes start/steer routing.)
- "Abort current task without terminating background terminal processes. This server sends `EventMsg::TurnAborted` in response." (`codex-rs/protocol/src/protocol.rs:544-546`; framing: interruption is scoped to the task, not the spawned processes.)
- `parallel_tool_calls: true` (`codex-rs/core/src/session/turn.rs:1303`; framing: concurrent tool execution is a per-request default.)
- "This records items immediately so history and rollout stay in sync even if the turn is later cancelled." (`codex-rs/core/src/stream_events_utils.rs:190-191`; framing: transcript durability under interruption.)
- "as long as compaction works well in getting us way below the token limit, we shouldn't worry about being in an infinite loop." (`codex-rs/core/src/session/turn.rs:451`; framing: mid-turn compaction as the loop's escape valve.)
- `TurnAbortReason::{Interrupted, Replaced, ReviewEnded, BudgetLimited}` (`codex-rs/protocol/src/protocol.rs:3988-3993`; framing: turn abort is a taxonomy, not a single interrupt.)
- `DEFAULT_STREAM_MAX_RETRIES: u64 = 5`, `DEFAULT_REQUEST_MAX_RETRIES: u64 = 4`, `DEFAULT_STREAM_IDLE_TIMEOUT_MS: u64 = 300_000` (`codex-rs/model-provider-info/src/lib.rs:26-28`; framing: concrete retry/timeout defaults for the comparison matrix.)
- `SamplingRequestResult { needs_follow_up, last_agent_message }` (`codex-rs/core/src/session/turn.rs:1556-1559`; framing: the follow-up bit is the loop's continuation condition.)
