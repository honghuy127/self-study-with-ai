---
source_key: "codexInterfaces"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "codex"
commit: "af700180808cce2ce28a31aad0fbad4dc58b857a"
---

# Notes: Codex interfaces: TUI, app-server, exec, CLI (codex)

## Source identification

- Key: `codexInterfaces`
- Repository: `codex` at `af700180808cce2ce28a31aad0fbad4dc58b857a` (see `sources/repos.yaml`)
- Component scope: `codex-rs/tui/`, `codex-rs/app-server/`, `codex-rs/app-server-protocol/`, `codex-rs/app-server-daemon/`, `codex-rs/app-server-transport/`, `codex-rs/exec/`, `codex-rs/exec-server/`, `codex-rs/exec-server-protocol/`, `codex-rs/cli/`, `codex-rs/codex-mcp/`. Two adjacent crates outside the listed component scope are cited where the code cannot be explained without them: `codex-rs/app-server-client/` (shared client facade used by both TUI and exec) and `codex-rs/docs/codex_mcp_interface.md` (repo doc for the `codex mcp-server` surface). Both are flagged as adjacent in the text.
- Tier: codebase

## Purpose and role in the harness

Codex ships one user binary, `codex`, which dispatches to every interface
mode: interactive TUI (the default when no subcommand is given), non-interactive
`exec`, MCP server (`mcp-server`), the IDE-facing `app-server`, a standalone
`exec-server` for remote execution environments, session management verbs
(`resume`, `fork`, `archive`, `delete`, `queue`), and sandbox/update/debug
tooling (`codex-rs/cli/src/main.rs:103-230`). The dispatch table is explicit:
`None | Some(Subcommand::Agents(_))` runs the TUI
(`codex-rs/cli/src/main.rs:1094`), `Subcommand::Exec` calls
`codex_exec::run_main` (`codex-rs/cli/src/main.rs:1144-1159`),
`Subcommand::McpServer` calls `codex_mcp_server::run_main`
(`codex-rs/cli/src/main.rs:1181-1193`), `Subcommand::AppServer` calls
`codex_app_server::run_main_with_transport_options`
(`codex-rs/cli/src/main.rs:1242-1296`), and `Subcommand::ExecServer` calls
`run_exec_server_command` (`codex-rs/cli/src/main.rs:1755-1764`).

The architectural center of gravity is the app-server: a JSON-RPC 2.0 service
whose stated purpose is to "power rich interfaces such as the Codex VS Code
extension" (`codex-rs/app-server/README.md:3`). Every other interface in the
pinned tree is an app-server client rather than a direct driver of the core
agent runtime: the TUI, `codex exec`, and remote control clients all speak the
same `thread/*`, `turn/*`, `item/*` protocol. The protocol's three primitives
are Thread (a conversation), Turn (one round of user input plus agent work),
and Item (user inputs and agent outputs such as messages, shell commands, and
file edits) (`codex-rs/app-server/README.md:66-74`).

## Mechanism

### CLI dispatch

The root parser accepts `codex [OPTIONS] [PROMPT]` or
`codex [OPTIONS] <COMMAND> [ARGS]` with `subcommand_negates_reqs = true`
(`codex-rs/cli/src/main.rs:103-114`). Notable subcommands registered there:
`exec` with visible alias `e` (`codex-rs/cli/src/main.rs:137-139`),
`mcp-server` described as "Start Codex as an MCP server (stdio)"
(`codex-rs/cli/src/main.rs:156-157`), `app-server` labeled `[experimental]`
(`codex-rs/cli/src/main.rs:159-160`), and `exec-server` labeled
`[EXPERIMENTAL]` (`codex-rs/cli/src/main.rs:225-226`). Root-level `--remote`
and `--remote-auth-token-env` connect "the TUI to a remote app server endpoint"
and are rejected for every non-TUI subcommand via
`reject_remote_mode_for_subcommand` (`codex-rs/cli/src/main.rs:973-983`,
`2360-2376`). On exit, the CLI prints token usage plus a `codex resume` hint
from `AppExitInfo` (`codex-rs/cli/src/main.rs:787-838`).

### TUI architecture

The TUI crate depends on `codex-app-server-client` and
`codex-app-server-protocol` and renders with `ratatui` over `crossterm`
(`codex-rs/tui/Cargo.toml:30-31, 72, 83`). It does not embed the core agent
directly. Instead it selects one of three backends expressed by
`AppServerTarget`: `Embedded`, `LocalDaemon { endpoint }`, or
`Remote { endpoint }` (`codex-rs/tui/src/lib.rs:272-277`). Selection logic: an
explicit remote endpoint wins; otherwise the TUI reuses a shared local daemon
over its unix control socket when the invocation carries no CLI `-c` overrides,
default loader overrides, no `strict-config`, and no non-replayable launch
overrides; otherwise it embeds an in-process app-server
(`codex-rs/tui/src/lib.rs:863-873`, `907-918`). The embedded path calls
`InProcessAppServerClient::start` (`codex-rs/tui/src/lib.rs:244-270`), and the
implicit daemon probe has a 50 ms connect timeout
(`codex-rs/tui/src/lib.rs:239-241`).

Remote addresses parse as `ws://host:port`, `wss://host:port`, `unix://`
(defaults to `$CODEX_HOME/app-server-control/app-server-control.sock`), or
`unix://PATH`; websocket URLs require an explicit port, path `/`, and no query
or fragment (`codex-rs/tui/src/lib.rs:369-406`). Bearer tokens are accepted
only for `wss://` or loopback `ws://`
(`codex-rs/tui/src/lib.rs:359-367`, `408-415`).

`run_main` drives startup orchestration, then `run_ratatui_app` starts the
chosen app-server backend inside a `startup_draft` (which keeps rendering
frames while async startup completes) and wraps the connection in
`AppServerSession::new(app_server, app_server_target.thread_params_mode())`
(`codex-rs/tui/src/lib.rs:927-950`, `1015-1035`; `codex-rs/tui/src/app_server_session.rs:344`).
The central state machine is `App` (`codex-rs/tui/src/app.rs:523`) fed by an
`AppEvent` enum of roughly a thousand lines of variants
(`codex-rs/tui/src/app_event.rs:197`). The main loop is a `tokio::select!`
over three sources: the `app_event_rx` channel (internal UI events and RPC
results), `active_thread_rx` (app-server notifications for the focused
thread), and `tui_events` (terminal input), with startup-phase input blocking
while protected events drain (`codex-rs/tui/src/app/startup.rs:620-689`).
Terminal input arrives through `TuiEventStream`, which wraps crossterm's
`EventStream` behind a pausable shared source so the TUI can release stdin
(`codex-rs/tui/src/tui/event_stream.rs:47-58, 118-153`; `TuiEvent` at
`codex-rs/tui/src/tui.rs:559`).

The TUI CLI surface is small: an optional `PROMPT` positional,
`--ask-for-approval`/`-a`, `--search` (enables the Responses `web_search`
tool), and `--no-alt-screen` for inline mode; resume/fork/agents-overview are
internal `#[clap(skip)]` fields set by the top-level wrapper subcommands
(`codex-rs/tui/src/cli.rs:11-79`). The dispatcher refuses to start the TUI on
`TERM=dumb` without a TTY confirmation
(`codex-rs/cli/src/main.rs:2565-2581`). `codex agents` starts the shared local
daemon first via `AppServerLifecycleCommand::Start` and opens a daemon-wide
sessions overview (`codex-rs/cli/src/main.rs:2583-2597`,
`codex-rs/tui/src/app_event.rs:198-230`).

### exec: the non-interactive entrypoint

`codex exec` is a headless app-server client. `run_main` builds config, then
starts an embedded runtime with `InProcessAppServerClient::start` and
`InProcessClientStartArgs` carrying `session_source: SessionSource::Exec`,
`client_name: "codex_exec"`, and `experimental_api: true`
(`codex-rs/exec/src/lib.rs:245, 539-559, 808-812`). Output discipline is
enforced at the lint level: `#![deny(clippy::print_stdout)]`, with the header
comment stating that in default mode only the final message may reach stdout,
in `--json` mode stdout must be valid JSONL, and everything else goes to
stderr (`codex-rs/exec/src/lib.rs:1-5`).

CLI shape (`codex-rs/exec/src/cli.rs`): usage
`codex exec [OPTIONS] [PROMPT]` or `codex exec [OPTIONS] <COMMAND> [ARGS]`
(`codex-rs/exec/src/cli.rs:9-13`); flags `--skip-git-repo-check` (`:26-28`),
`--ephemeral` ("Run without persisting session files to disk", `:30-32`),
`--ignore-user-config` (`:34-36`), `--ignore-rules` (`:38-40`),
`--output-schema FILE` (`:42-44`), `--json` with alias
`experimental-json` (`:53-60`), `--output-last-message`/`-o` (`:62-69`); the
`PROMPT` positional doubles as stdin reader: `-` forces stdin, and piped stdin
alongside a positional prompt is appended as a `<stdin>` block
(`:71-75`). Subcommands are `resume`, `fork`, and `review`
(`codex-rs/exec/src/cli.rs:143-153`). `codex review` at the top level is
desugared into `codex exec review` by the CLI dispatcher
(`codex-rs/cli/src/main.rs:1160-1180`).

Headless safety defaults: the exec override sets
`approval_policy: Some(AskForApproval::Never)` with the comment "Default to
never ask for approvals in headless mode"
(`codex-rs/exec/src/lib.rs:409-411`). A git-repo guard exits with "Not inside
a trusted directory and --skip-git-repo-check was not specified." unless the
cwd is inside a git repo or `--dangerously-bypass-approvals-and-sandbox` is set
(`codex-rs/exec/src/lib.rs:799-805`). Thread creation uses `thread/start` with
`history_mode: ThreadHistoryMode::Paginated` unless `ephemeral`
(`codex-rs/exec/src/lib.rs:1187`), with a retry that drops `history_mode` if
the server answers `-32600` "paginated threads require thread/turns/list and
thread/items/list support" (`codex-rs/exec/src/lib.rs:1146-1165`).

The event loop is a `tokio::select!` between a ctrl-c handler (which sends a
`turn/interrupt` request, `codex-rs/exec/src/lib.rs:1036-1060`) and
`client.next_event()`; server errors and failed or interrupted turns set
`error_seen`, and the process exits with status 1 for "automation-friendly
signaling" (`codex-rs/exec/src/lib.rs:1032-1035, 1066-1089, 1129-1136`).

The `--json` vocabulary is a tagged union `ThreadEvent` with wire names
`thread.started`, `turn.started`, `turn.completed`, `turn.failed`,
`item.started`, `item.updated`, `item.completed`, and `error`
(`codex-rs/exec/src/exec_events.rs:9-37`), including a `Usage` record with
`input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`,
`output_tokens`, `reasoning_output_tokens`
(`codex-rs/exec/src/exec_events.rs:60-73`). In human mode, the final agent
message goes to stdout only when the terminal conditions in
`should_print_final_message_to_stdout` hold; otherwise it renders to stderr
(`codex-rs/exec/src/event_processor_with_human_output.rs:391-415`). The exec
binary also doubles as `codex-linux-sandbox` when invoked under that arg0
name (`codex-rs/exec/src/main.rs:1-11`).

### app-server protocol surface

Wire format: bidirectional JSON-RPC 2.0 messages "with the `\"jsonrpc\":\"2.0\"`
header omitted on the wire", modeled after MCP
(`codex-rs/app-server/README.md:22`). Transports: stdio via `--stdio` or
`--listen stdio://` (default, newline-delimited JSON), websocket via
`--listen ws://IP:PORT` (marked "experimental / unsupported"), unix socket via
`--listen unix://[PATH]` (websocket frames over the HTTP Upgrade handshake,
intended for local control-plane clients), and `--listen off`
(`codex-rs/app-server/README.md:24-29, 37, 41-44`). The enum backing this is
`AppServerTransport { Stdio, UnixSocket, WebSocket, Off }` with
`DEFAULT_LISTEN_URL = "stdio://"`
(`codex-rs/app-server-transport/src/transport/mod.rs:74-80, 113-118`).

Handshake: one `initialize` request plus an `initialized` notification per
connection; any other request first gets a `"Not initialized"` error and a
repeated `initialize` gets `"Already initialized"`
(`codex-rs/app-server/README.md:78, 87`). Clients identify themselves with
`clientInfo`; the README's example is OpenAI's VS Code extension,
`clientInfo.name: "codex_vscode"` (`codex-rs/app-server/README.md:119-139`).
Per-connection opt-out of notifications uses exact method names in
`capabilities.optOutNotificationMethods`
(`codex-rs/app-server/README.md:89, 1542-1554`).

Method surface. Requests are generated by the `client_request_definitions!`
macro into a serde-tagged `ClientRequest` enum
(`codex-rs/app-server-protocol/src/protocol/common.rs:199-232`). Wire names
include `initialize` (`:488`), `thread/start` (`:505`), `thread/resume`
(`:511`), `thread/fork` (`:517`), `thread/list` (`:692`), `thread/read`
(`:778`), `thread/turns/list` (`:784`), `thread/items/list` (`:791`),
`turn/start` (`:961`), `turn/steer` (`:967`), `turn/interrupt` (`:973`),
`review/start` (`:1014`), `model/list` (`:1020`), `environment/add` (`:1103`),
`account/login/start` (`:1164`), `command/exec` (`:1234`), `process/spawn`
(`:1260`), `config/read` (`:1287`), `account/read` (`:1331`). Server-to-client
requests (the approval and elicitation surface) include
`item/commandExecution/requestApproval` (`:1653`),
`item/fileChange/requestApproval` (`:1660`), `item/tool/requestUserInput`
(`:1666`), `mcpServer/elicitation/request` (`:1672`),
`item/permissions/requestApproval` (`:1678`), `item/tool/call` for dynamic
tools (`:1684`), `attestation/generate` (`:1695`), and `currentTime/read`
(`:1702`). Notifications include `thread/started` (`:1807`), `item/started`
(`:1838`), `item/completed` (`:1843`), `item/agentMessage/delta` (`:1848`),
`item/commandExecution/outputDelta` (`:1859`), and
`item/reasoning/summaryTextDelta` (`:1875`). The README documents the full
lifecycle: `item/started`, zero or more deltas, `item/completed`
(`codex-rs/app-server/README.md:1587`). The README's API overview is the most
complete catalog (over 100 methods,
`codex-rs/app-server/README.md:161-291`).

Experimental gating. Experimental methods and fields are annotated
`#[experimental("descriptor")]` and rejected without
`capabilities.experimentalApi: true` with the error
`<descriptor> requires experimentalApi capability`
(`codex-rs/app-server/README.md:2458-2517`;
`codex-rs/app-server-protocol/src/protocol/common.rs:101-106`). The capability
is negotiated once per connection at initialize
(`codex-rs/app-server/README.md:2502-2505`).

Server runtime. `run_main_with_transport_options` wires three bounded mpsc
channels (`TransportEvent`, `OutgoingEnvelope`, `OutboundControlEvent`), each
of `CHANNEL_CAPACITY` (`codex-rs/app-server/src/lib.rs:463-467`), and runs two
documented loops: a "processor loop" for incoming JSON-RPC dispatch and an
"outbound loop" for per-connection writes
(`codex-rs/app-server/src/lib.rs:149-157, 832-915`). One `MessageProcessor`
serves the process; per-connection state lives in a `ConnectionId`-keyed map
(`codex-rs/app-server/src/lib.rs:897-918`). Backpressure: bounded queues feed
back as JSON-RPC error code `-32001`, message
`"Server overloaded; retry later."`
(`codex-rs/app-server/README.md:51-55`; `codex-rs/app-server/src/error_code.rs:7`,
`OVERLOADED_ERROR_CODE` also in
`codex-rs/app-server-transport/src/transport/mod.rs:52`). Schema export:
`codex app-server generate-ts --out DIR` and
`codex app-server generate-json-schema --out DIR`, with `--experimental` to
include the gated surface; outputs are tied to the generating Codex version
(`codex-rs/app-server/README.md:57-64`; `codex-rs/cli/src/main.rs:1351-1370`).

Request serialization. Each request maps to a
`ClientRequestSerializationScope` (global, global shared read, per-thread,
per-process, per-fuzzy-search session, per `fs/watch` id, per MCP OAuth
server), which the server uses to serialize conflicting operations
(`codex-rs/app-server-protocol/src/protocol/common.rs:119-130`).

In-process embed. `codex-rs/app-server/src/in_process.rs` runs the same
`MessageProcessor` and outbound routing "on Tokio tasks, but replaces
socket/stdio transports with bounded in-memory channels"
(`codex-rs/app-server/src/in_process.rs:1-6`). Design intent: "The runtime is
transport-local but not protocol-free. Incoming requests are typed
`ClientRequest` values, yet responses still come back through the same
JSON-RPC result envelope" (`:20-24`). `start` performs the
`initialize`/`initialized` handshake internally (`:11-12`). Server requests
that cannot be queued are failed back with overload or internal errors so
approval flows do not hang (`:26-32`).

### How IDE and external clients attach

- The app-server README states it is the interface behind the Codex VS Code
  extension and asks integrators to identify via `clientInfo.name` for the
  OpenAI Compliance Logs Platform (`codex-rs/app-server/README.md:3, 119-123`).
- The standalone app-server binary defaults `--session-source` to `vscode` and
  analytics off (`codex-rs/app-server/src/main.rs:39-45, 108`); `codex
  app-server` from the main CLI likewise passes `SessionSource::VSCode`
  (`codex-rs/cli/src/main.rs:1284-1295`) and exposes
  `--analytics-default-enabled` for first-party embedders with opt-out via
  `[analytics] enabled = false` (`codex-rs/cli/src/main.rs:576-592`).
- Any client speaks the same protocol over any transport. The shared facade
  (adjacent crate) is `AppServerClient`, an enum of `InProcess` and `Remote`
  (`codex-rs/app-server-client/src/lib.rs:317-320`); its doc states it
  "preserves the server's request/notification/event model instead of
  exposing direct core runtime handles" (`:295-299`). The remote path owns
  the connection lifecycle "including the initialize/initialized" handshake
  and sends `ClientNotification::Initialized` after the response
  (`codex-rs/app-server-client/src/remote.rs:1-6, 168-208, 927-934`).
- A shared local daemon is managed by `codex app-server daemon
  start|restart|stop|version|bootstrap|enable-remote-control|disable-remote-control`
  (`codex-rs/cli/src/main.rs:695-726`); the daemon crate exposes
  `LifecycleCommand::{Start, Restart, Stop, Version}` and a `socket_path` in
  its output (`codex-rs/app-server-daemon/src/lib.rs:38-58, 191-196`), and
  `codex app-server proxy` relays stdio to the control socket for clients that
  cannot open unix sockets (`codex-rs/cli/src/main.rs:1341-1350`).
- The TUI itself attaches remotely with `--remote`/`--remote-auth-token-env`
  (`codex-rs/cli/src/main.rs:973-983`, `2650-2683`).
- Remote execution environments attach via the exec-server. The app-server
  registers them with `environment/add` (`execServerUrl`) and probes them via
  `environment/info`/`environment/status`
  (`codex-rs/app-server/README.md:247-249`). The exec-server protocol is a
  separate JSON-RPC surface with wire methods `initialize`, `initialized`,
  `process/start`, `process/read`, `process/write`, `process/signal`,
  `process/terminate`, `process/output`, `process/exited`, `process/closed`,
  `environment/info`, `environment/status`, `fs/readFile`, `fs/open`,
  `fs/readBlock`, `fs/close`, `fs/writeFile`, `fs/createDirectory`,
  `fs/getMetadata`, `fs/canonicalize`, `fs/readDirectory`, `fs/walk`,
  `fs/remove`, `fs/copy`, `capabilityRoots/discoverV1`, `http/request`, and
  `http/request/bodyDelta`
  (`codex-rs/exec-server-protocol/src/protocol.rs:19-54`), plus
  `environmentConfig/read`
  (`codex-rs/exec-server-protocol/src/environment_config.rs:5`) and
  `network/policyRequest`/`network/policyDecision`
  (`codex-rs/exec-server-protocol/src/network_policy.rs:6-7`). The protocol
  pins `MINIMUM_SUPPORTED_CODEX_VERSION: &str = "0.145.0"`
  (`codex-rs/exec-server-protocol/src/lib.rs:14`). `codex exec-server` serves
  locally with default listen URL `ws://127.0.0.1:0`
  (`codex-rs/exec-server/src/server/transport.rs:32`;
  `codex-rs/cli/src/main.rs:1945-1947`) or registers itself as a remote
  environment with `--remote`/`--environment-id`
  (`codex-rs/cli/src/main.rs:628-640, 1864-1923`); concurrency is
  `--concurrent-requests` with default `1`
  (`codex-rs/cli/src/main.rs:612-618`).
- MCP surface: `codex mcp-server` exposes Codex as an MCP server over stdio.
  The repo doc describes it as "a JSON-RPC API that runs over the Model
  Context Protocol (MCP) transport to control a local Codex engine", status
  "experimental and subject to change without notice", with the v2 thread/turn
  RPCs and approval requests, and notes the types live in
  `app-server-protocol/src/protocol/{common,v1,v2}.rs`
  (`codex-rs/docs/codex_mcp_interface.md:1-12, 15-33`; adjacent to the
  component scope). The dispatch target is `codex_mcp_server::run_main`
  (`codex-rs/cli/src/main.rs:1181-1193`). The `codex-mcp` crate in scope is
  the MCP integration library (bindings, catalog, elicitation, Codex Apps
  connector runtime) consumed by the server side, not the MCP server binary
  itself (`codex-rs/codex-mcp/src/lib.rs:1-112`).

## Key facts with anchors

- One binary, many frontends: the `codex` CLI dispatches TUI, exec, mcp-server,
  app-server, and exec-server from a single `Subcommand` enum
  (`codex-rs/cli/src/main.rs:132-230`).
- Every frontend is an app-server protocol client; the TUI embeds an
  in-process app-server by default, reuses a local daemon when safe, or
  connects remotely (`codex-rs/tui/src/lib.rs:272-277, 863-918`;
  `codex-rs/exec/src/lib.rs:808-812`; `codex-rs/app-server-client/src/lib.rs:317-320`).
- The protocol is JSON-RPC 2.0 without the `jsonrpc` field on the wire,
  generated from a serde-tagged Rust enum; methods are `camelCase`-tagged
  variant names like `thread/start` and `turn/start`
  (`codex-rs/app-server/README.md:22`;
  `codex-rs/app-server-protocol/src/protocol/common.rs:199-232, 488-1331`).
- Approvals are server-to-client JSON-RPC requests
  (`item/commandExecution/requestApproval`, `item/fileChange/requestApproval`,
  `item/permissions/requestApproval`) that the client must answer
  (`codex-rs/app-server-protocol/src/protocol/common.rs:1653-1702`;
  `codex-rs/app-server/README.md:1683-1710`).
- `codex exec` defaults to `AskForApproval::Never` in headless mode and exits
  1 on any server error or failed/interrupted turn
  (`codex-rs/exec/src/lib.rs:409-411, 1129-1136`).
- `codex exec --json` emits a compact JSONL vocabulary
  (`thread.started`, `turn.started`, `turn.completed`, `turn.failed`,
  `item.started`, `item.updated`, `item.completed`, `error`), distinct from
  the richer app-server notification names
  (`codex-rs/exec/src/exec_events.rs:9-37`).
- Exec refuses to run outside a git repository unless
  `--skip-git-repo-check` or the dangerous bypass is set
  (`codex-rs/exec/src/lib.rs:799-805`).
- Backpressure is part of the protocol contract: error code `-32001`, message
  `"Server overloaded; retry later."`
  (`codex-rs/app-server/README.md:51-55`;
  `codex-rs/app-server/src/error_code.rs:7`).
- The same `MessageProcessor` runs unchanged across stdio, websocket, unix
  socket, and in-process transports; the in-process host keeps JSON-RPC result
  envelopes for typed requests ("transport-local but not protocol-free")
  (`codex-rs/app-server/src/lib.rs:897-918`;
  `codex-rs/app-server/src/in_process.rs:20-24`).
- `turn/steer` appends input to an in-flight turn without starting a new one;
  review and manual compaction turns reject it
  (`codex-rs/app-server/README.md:213, 1206-1223`).
- Threads unload 30 minutes after the last subscriber leaves, then run
  `SessionEnd` hooks and emit `thread/closed`
  (`codex-rs/app-server/README.md:201, 547-549`).
- The remote-execution plane is a separate JSON-RPC service (exec-server) over
  WebSocket with process, filesystem, HTTP, and capability-discovery methods
  (`codex-rs/exec-server-protocol/src/protocol.rs:19-54`).
- Schema generation (`generate-ts`, `generate-json-schema`) is version-pinned
  by construction: artifacts always match the generating Codex build
  (`codex-rs/app-server/README.md:57-64`).

The following are my inferences, not code facts: the decision to route every
frontend through one protocol suggests OpenAI treats the interface layer, not
the TUI, as the stable product; and the in-process reuse of the JSON-RPC
envelope implies behavioral parity between `codex exec`, the TUI, and IDE
integrations is obtained by sharing one code path rather than by testing
separate frontends.

## Configuration and defaults

- `AppServerTransport::DEFAULT_LISTEN_URL: &'static str = "stdio://"`
  (`codex-rs/app-server-transport/src/transport/mod.rs:114`).
- `CHANNEL_CAPACITY: usize = 128` with comment "128 messages should be plenty
  for an interactive CLI"
  (`codex-rs/app-server-transport/src/transport/mod.rs:22-25`);
  `DEFAULT_IN_PROCESS_CHANNEL_CAPACITY: usize = CHANNEL_CAPACITY`
  (`codex-rs/app-server/src/in_process.rs:105-106`).
- `OVERLOADED_ERROR_CODE: i64 = -32001`
  (`codex-rs/app-server/src/error_code.rs:7`;
  `codex-rs/app-server-transport/src/transport/mod.rs:52`).
- Control socket defaults to
  `$CODEX_HOME/app-server-control/app-server-control.sock`
  (`codex-rs/app-server-transport/src/transport/mod.rs:54-64`;
  `codex-rs/app-server/README.md:28, 42`).
- Standalone app-server binary: `--session-source` default `vscode`,
  `default_analytics_enabled` passed as `false`
  (`codex-rs/app-server/src/main.rs:39-45, 108`). `codex app-server` analytics
  are "disabled by default for app-server" with opt-in via
  `--analytics-default-enabled` or `[analytics]` config
  (`codex-rs/cli/src/main.rs:576-592`).
- Exec defaults: `DEFAULT_ANALYTICS_ENABLED: bool = true` (otel init,
  `codex-rs/exec/src/lib.rs:167, 478-484`),
  `EXEC_DEFAULT_LOG_FILTER: &str = "error,opentelemetry_sdk=off,opentelemetry_otlp=off"`
  (`codex-rs/exec/src/lib.rs:168`), headless approval policy
  `AskForApproval::Never` (`codex-rs/exec/src/lib.rs:411`),
  `session_source: SessionSource::Exec` and `client_name: "codex_exec"`
  (`codex-rs/exec/src/lib.rs:551-553`), paginated history mode when not
  ephemeral (`codex-rs/exec/src/lib.rs:1187`).
- Exec-server: `DEFAULT_LISTEN_URL: &str = "ws://127.0.0.1:0"`
  (`codex-rs/exec-server/src/server/transport.rs:32`);
  `--concurrent-requests` default `1`
  (`codex-rs/cli/src/main.rs:612-618`); opt-in env
  `CODEX_EXEC_SERVER_EXIT_ON_STDIN_CLOSE`
  (`codex-rs/exec-server/src/lib.rs:46-47`; `codex-rs/cli/src/main.rs:654-661`).
- TUI: implicit daemon connect timeout 50 ms
  (`codex-rs/tui/src/lib.rs:239-241`).
- Env vars observed at the interface layer: `RUST_LOG` and `LOG_FORMAT=json`
  for app-server tracing (`codex-rs/app-server/README.md:48-49`;
  `LOG_FORMAT_ENV_VAR` at `codex-rs/app-server/src/lib.rs:136`);
  `TERM=dumb` guard (`codex-rs/cli/src/main.rs:2565-2581`).
- Protocol-level defaults documented in the pinned README: `command/exec`
  output cap "1 MiB per stream" server default
  (`codex-rs/app-server/README.md:1329`); thread queue limit "up to 100
  messages" (`codex-rs/app-server/README.md:790`); `SessionEnd` default
  timeout one second, capped at three seconds
  (`codex-rs/app-server/README.md:549`); 30-minute idle unload
  (`codex-rs/app-server/README.md:201`). Defaults that depend on config
  resolution (model, sandbox policy) are owned by the config crate and are
  covered by the `codexConfigProviders` note `[EVIDENCE NEEDED]` here only if
  reused: I looked in `codex-rs/app-server/src/lib.rs` and found config loaded
  through `ConfigManager` without interface-layer defaults
  (`codex-rs/app-server/src/lib.rs:483-534`).

## Limitations and unknowns

- The app-server README documents an API far larger than any single note can
  verify line by line (realtime voice, plugins, projects, remote control
  pairing). I verified the method names I cite against
  `codex-rs/app-server-protocol/src/protocol/common.rs`, but methods listed
  only in the README (for example `project/*`, `threadSection/*`,
  `remoteControl/*`) were not each traced into code.
- Large parts of the surface are explicitly experimental or "under
  development; do not call from production clients yet"
  (`codex-rs/app-server/README.md:2458-2517, 258-261`); the pinned snapshot
  may not reflect what shipped clients actually use.
- Websocket transport is labeled "experimental / unsupported"
  (`codex-rs/app-server/README.md:27, 37`), so production IDE attachment in
  the pinned tree is stdio or unix socket only.
- I read the `MessageProcessor` construction, not its full request-routing
  internals; the per-connection vs process-wide split of state (for example,
  initialize gating is "per-connection" per
  `codex-rs/app-server/src/request_processors/initialize_processor.rs:64`) is
  asserted here at the level of the visible wiring only.
- Runtime behavior (actual backpressure thresholds, latency) is from code and
  docs, not execution; the brief permits static traces only.
- The remote-execution data path (how a turn's shell command reaches an
  exec-server environment) is documented by registration-side code and
  protocol constants; I did not trace `EnvironmentManager` internals beyond
  its construction (`codex-rs/app-server/src/lib.rs:568-579`).
- The `codex mcp-server` binary lives in `codex-rs/mcp-server/`, which belongs
  to the `codexExtensibility` component, not this note; the interface facts
  here come from the CLI dispatch and the repo doc
  (`codex-rs/docs/codex_mcp_interface.md`), which is adjacent to, not inside,
  the registered component directories.

## Relevance to the brief

This note answers the interfaces sub-dimension of RQ1 and RQ2 for Codex.
Codex differs structurally from a harness whose interfaces bolt onto the core
loop: the app-server protocol is the harness boundary. The TUI, `codex exec`,
the VS Code extension, remote-control clients, and `codex mcp-server` are all
clients of one JSON-RPC protocol with thread/turn/item primitives
(`codex-rs/app-server/README.md:66-74`), and even the headless mode reuses the
embedded server rather than a lighter path (`codex-rs/exec/src/lib.rs:808`).
For the comparison matrix, Codex's interface stack is: ratatui TUI (client),
app-server (JSON-RPC, stdio/unix/ws, experimental), exec-server (remote
environments), `mcp-server` (MCP transport over the same types), with no LSP
or ACP in this tree.

For RQ3, the interface layer carries safety-relevant facts: approvals are
server-initiated requests the client must answer
(`codex-rs/app-server/README.md:1683-1710`); `command/exec` runs under the
sandbox while `process/spawn` is "intentionally unsandboxed"
(`codex-rs/app-server/README.md:221, 1461`); headless `exec` defaults to
`AskForApproval::Never` (`codex-rs/exec/src/lib.rs:411`). The enforcement
itself lives in the sandbox/permissions components and belongs to the
`codexSandboxPermissions` note.

Open questions for synthesis: how OpenCode's ACP/LSP/HTTP surfaces compare in
stability and scope, whether Claude Code exposes any equivalent programmatic
control plane at all, and how much of the Codex experimental surface (goals,
queues, realtime, remote control) counts as harness versus product.

## Quotables for the report

- "In default output mode, the only thing written to stdout is the final
  message; in `--json` mode, stdout must be valid JSONL" (paraphrase of
  `codex-rs/exec/src/lib.rs:1-5`). Framing: headless output contract as an
  enforced lint (`#![deny(clippy::print_stdout)]`).
- "The runtime is transport-local but not protocol-free."
  (`codex-rs/app-server/src/in_process.rs:20-24`). Framing: in-process
  embedders still get JSON-RPC envelopes, so all frontends share one contract.
- `CHANNEL_CAPACITY: usize = 128`, "a balance between throughput and memory
  usage" (`codex-rs/app-server-transport/src/transport/mod.rs:22-25`) and the
  overload error `"Server overloaded; retry later."` with code `-32001`
  (`codex-rs/app-server/README.md:51-55`). Framing: backpressure as a
  documented protocol feature.
- `AppServerTarget::{Embedded, LocalDaemon, Remote}`
  (`codex-rs/tui/src/lib.rs:272-277`). Framing: the TUI is one client among
  three attachment modes.
- JSONL event names `thread.started` through `item.completed`
  (`codex-rs/exec/src/exec_events.rs:9-37`). Framing: the exec mode exposes a
  deliberately reduced event vocabulary versus the full app-server stream.
- `MINIMUM_SUPPORTED_CODEX_VERSION: &str = "0.145.0"`
  (`codex-rs/exec-server-protocol/src/lib.rs:14`). Framing: the remote
  environment plane has an explicit protocol version floor.
