---
source_key: "opencodeInterfaces"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "opencode"
commit: "d545d8fba57283528db69281f59c803c646eb7e9"
---

# Notes: OpenCode interfaces: ACP, LSP, IDE server, HTTP server, TUI, CLI (opencode)

## Source identification

- Key: opencodeInterfaces
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`)
- Component scope: `packages/opencode/src/acp/` (agent.ts, session.ts, permission.ts, service.ts, event.ts, plus content.ts, config-option.ts, directory.ts, tool.ts, usage.ts, error.ts), `packages/opencode/src/lsp/` (client.ts, server.ts, launch.ts, diagnostic.ts, language.ts, lsp.ts), `packages/opencode/src/ide/index.ts`, `packages/opencode/src/server/` (server.ts, auth.ts, mdns.ts, routes/instance/httpapi/), TUI split (`packages/tui/package.json`, `packages/opencode/src/cli/cmd/tui.ts`, `packages/opencode/src/cli/tui/worker.ts`), CLI split (`packages/opencode/src/index.ts`, `packages/opencode/src/cli/cmd/{acp,serve,attach,run}.ts`, `packages/cli/`). Scoped to architecture, not UI polish.
- Tier: codebase

## Purpose and role in the harness

OpenCode separates one agent runtime (the "server", an in-process or headless
Effect/HttpApi app) from many frontends that all speak to it. The interface
layer is the collection of adapters that expose that runtime: a stdio ACP
server for editors (`packages/opencode/src/acp/`), an LSP client farm that gives
tools language intelligence (`packages/opencode/src/lsp/`), a thin IDE-detection
shim (`packages/opencode/src/ide/`), an HTTP/SSE server that is the actual
runtime surface (`packages/opencode/src/server/`), a terminal UI that mounts the
server in a worker (`packages/tui/` + `packages/opencode/src/cli/cmd/tui.ts`),
and a yargs CLI that wires every command together (`packages/opencode/src/index.ts`).

Architecturally the decisive fact is that ACP, TUI, and the headless `run`/`serve`
commands do not embed the agent loop. They construct an HTTP SDK client
(`createOpencodeClient` from `@opencode-ai/sdk/v2`, `packages/sdk/js/src/v2/client.ts:50`)
pointed at a local or remote server and translate a protocol into HTTP calls
(`packages/opencode/src/acp/service.ts:76`, `packages/opencode/src/cli/cmd/acp.ts:27`).
The runtime is reachable identically whether the caller is a terminal UI, an IDE
over ACP, or a script over HTTP.

## Mechanism

**ACP (Agent Client Protocol).** `acp/agent.ts#Agent` (line 32) implements the
`Agent` interface of `@agentclientprotocol/sdk` (version `0.21.0`,
`packages/opencode/package.json:57`) as a thin pass-through: every method
(`initialize`, `newSession`, `loadSession`, `prompt`, `cancel`,
`unstable_forkSession`, `unstable_setSessionModel`) delegates to a private
`service` and returns `run(service.method(params))` (`acp/agent.ts:35-93`). The
real logic lives in `acp/service.ts#make` (line 75), which holds an
`sdk: OpencodeClient` and a `connection` for server-push notifications. All ACP
requests become SDK calls on the HTTP server: `newSession` ->
`sdk.session.create` (`acp/service.ts:169-182`), `prompt` -> `sdk.session.prompt`
or `sdk.session.command`/`sdk.session.summarize` (`acp/service.ts:506-574`), MCP
servers from the editor -> `sdk.mcp.add` (`acp/service.ts:958-1007`).

The ACP side of the process is started by `opencode acp`
(`packages/opencode/src/cli/cmd/acp.ts`). It first boots the same HTTP server
(`Server.listen`, line 25), points an SDK client at
`http://${server.hostname}:${server.port}` with `ServerAuth.headers()` (lines
27-30), then binds an `AgentSideConnection` over an ndJsonStream on
stdin/stdout (lines 55-61). So a single `opencode acp` process hosts both the
HTTP runtime and the ACP stdio bridge, and the bridge is a client of its own
server.

`initialize` advertises `protocolVersion: 1` and agent capabilities
`loadSession`, `mcpCapabilities {http, sse}`, `promptCapabilities
{embeddedContext, image}`, `sessionCapabilities {close, fork, list, resume}`,
plus an `authMethods` entry whose id is `opencode-login`
(`acp/service.ts:112-136`); when the client declares a `terminal-auth`
capability, the method gains `_meta` with `command: "opencode"`, `args: ["auth",
"login"]` (`acp/service.ts:102-110`).

Streaming from the harness back to the editor is done by `acp/event.ts`
`Subscription` (line 39). It consumes the server's global SSE stream via
`sdk.global.event()` in a reconnect loop (1000 ms backoff,
`acp/event.ts:144-165`) and translates OpenCode events into ACP
`sessionUpdate`s: `message.part.delta` text -> `agent_message_chunk`,
reasoning -> `agent_thought_chunk` (`acp/event.ts:214-258`); tool-part
pending/running/completed/error -> `tool_call` / `tool_call_update`
(`acp/event.ts:295-339`), with bash output snapshot de-dup (`acp/event.ts:341-377`).
`runUntilIdle` awaits the prompt request and then resolves only on a
`session.status` idle event, so the PromptResponse returns after the turn's
events have flushed (`acp/event.ts:74-91`). Permissions surface through
`acp/permission.ts#Handler` which calls `connection.requestPermission` with
options `once`/`always`/`reject` (kinds `allow_once`/`allow_always`/
`reject_once`, `acp/permission.ts:20-24`), answers via `sdk.permission.reply`
(`acp/permission.ts:91-97`), and for `edit` permissions pushes the proposed file
content back over `connection.writeTextFile` using `applyPatch` from `diff`
(`acp/permission.ts:99-115`). ACP session identity is held in an in-memory `Map`
(`acp/session.ts:95-100`); ACP "modes" are OpenCode agents filtered to non-
subagent, non-hidden entries with a `defaultModeID` fallback of `"build"`
(`acp/service.ts:754-778`).

**LSP (Language Server Protocol).** `lsp/lsp.ts` is a service that owns a pool
of LSP *clients* (a client per `{server, root}`), not servers. It builds the
built-in server registry from `lsp/server.ts`, honors the `lsp` config, swaps
`ty`/`pyright` behind the experimental flag (`lsp/lsp.ts:98-108`), and lazily
spawns/dedups clients on file access, marking failures in a `broken` set
(`lsp/lsp.ts:208-297`). Its `Interface` exposes `hover`, `definition`,
`references`, `implementation`, `documentSymbol`, `workspaceSymbol`,
call-hierarchy ops, plus `touchFile` and `diagnostics`
(`lsp/lsp.ts:119-134`). `touchFile` sends `didOpen`/`didChange` and optionally
blocks until fresh diagnostics arrive (`lsp/lsp.ts:344-362`).
`lsp/client.ts#create` speaks JSON-RPC via `vscode-jsonrpc`
(`lsp/client.ts:132-135`), runs the `initialize`/`initialized` handshake
(`lsp/client.ts:211-260`), and merges push and pull diagnostics with timeouts
(`INITIALIZE_TIMEOUT_MS = 45_000`, `DIAGNOSTICS_FULL_WAIT_TIMEOUT_MS = 10_000`,
`lsp/client.ts:13-18`). `lsp/server.ts` declares ~38 built-in servers; examples:
TypeScript uses `typescript-language-server --stdio` with `tsserver.path`
initialization (`lsp/server.ts:115-142`), gopls auto-installs
`golang.org/x/tools/gopls@latest` (`lsp/server.ts:358-390`), clangd runs with
`--background-index --clang-tidy` and self-downloads from GitHub releases
(`lsp/server.ts:935-1067`), jdtls requires Java >= 21 (`lsp/server.ts:1197`).

Why the harness uses LSP: it is the feedback channel that lets edit tools check
their own work. After applying an edit, the `edit` tool calls
`lsp.touchFile(filePath, "document")` then `lsp.diagnostics()`, and appends the
errors back into the tool output with the literal text `LSP errors detected in
this file, please fix:` (`packages/opencode/src/tool/edit.ts:197-201`). The same
pattern is in `write` (`tool/write.ts:75-76`) and `apply_patch`
(`tool/apply_patch.ts:269-271`); `read` touches files so the LSP warms up
(`tool/read.ts:119`). A dedicated `lsp` tool exposes navigation ops to the model
(`tool/lsp.ts:11-21,37-113`) and routes through the `lsp` permission with
`patterns: ["*"], always: ["*"]` (`tool/lsp.ts:56-61`). The `lsp` status is also
surfaced over HTTP (`server/routes/instance/httpapi/handlers/instance.ts:88-90,107`).

**IDE attachment.** `ide/index.ts` is minimal. `SUPPORTED_IDES` lists Windsurf,
Visual Studio Code - Insiders, Visual Studio Code, Cursor, VSCodium with shell
commands (`ide/index.ts:6-12`). `ide()` infers the host IDE from
`TERM_PROGRAM === "vscode"` plus the `GIT_ASKPASS` value containing the IDE name
(`ide/index.ts:22-30`); `alreadyInstalled()` checks
`OPENCODE_CALLER === "vscode"|"vscode-insiders"` (`ide/index.ts:32-34`; install
runs `<cmd> --install-extension sst-dev.opencode`, `ide/index.ts:40`). IDE
integration in practice rides on ACP (editor is the ACP client) and on mDNS for
discovery, rather than on a bespoke IDE server.

**Server/HTTP surface.** `server/server.ts#listen` (line 73) boots the Effect
HttpApi app. With `port === 0` it prefers `4096` then any free port
(`server/server.ts:117-122`). The composed API is `OpenCodeHttpApi` in
`server/routes/instance/httpapi/api.ts` (lines 54-94): a root group (Control,
ControlPlane, Global), an instance group (Config, Experimental, File, Instance,
Mcp, Project, ProjectCopy, Pty, Question, Permission, Provider, Session, Sync,
Tui, Workspace), plus Event and a pty-connect group. The instance event stream
is SSE at `/event` (`server/routes/instance/httpapi/groups/event.ts:7-28`);
global health/event/config/dispose/upgrade live under `/global/*`
(`server/routes/instance/httpapi/groups/global.ts:65-136`). The session surface
is a large route table including `prompt`, `prompt_async`, `command`, `shell`,
`summarize`, `fork`, `abort`, `share`, `revert`
(`server/routes/instance/httpapi/groups/session.ts:78-105`). Instances are
resolved per-request via the `x-opencode-directory` header/query
(`packages/opencode/src/cli/cmd/serve.ts:10-11`; SDK sets the header
in `packages/sdk/js/src/v2/client.ts:63-68`). Auth is optional Basic auth: when
`OPENCODE_SERVER_PASSWORD` is set, `Authorization` middleware checks
`ServerAuth.authorized` and otherwise returns 401 with
`WWW-Authenticate: Basic realm="Secure Area"`
(`server/routes/instance/httpapi/middleware/authorization.ts:13-14,40-99`;
credential config in `server/auth.ts:17-42`). mDNS publication is opt-in and is
skipped for loopback hostnames (`server/server.ts:155-170`), publishing a
`bonjour` `http` service on domain `opencode.local` by default
(`server/mdns.ts:11`).

**TUI/CLI split.** The default yargs command `$0 [project]` is the TUI
(`TuiThreadCommand`, `cli/cmd/tui.ts:72-74`). It spawns a Bun `Worker`
(`cli/cmd/tui.ts:210`) whose RPC surface (`cli/tui/worker.ts:30-79`) hosts the
*server in the worker*: `fetch` calls go straight to
`Server.Default().app.fetch` in-process (`cli/tui/worker.ts:30-49`) and global
bus events are forwarded as `global.event` RPC events
(`cli/tui/worker.ts:24-26`). By default the TUI uses an in-memory transport with
base URL `http://opencode.internal` (`cli/cmd/tui.ts:238-249`); if `--port`/
`--hostname`/`--mdns` is passed it switches to a real HTTP URL plus Basic-auth
headers (`cli/cmd/tui.ts:233-244`). The TUI renderer is a separate package
`@opencode-ai/tui` built on `@opentui/core`, `@opentui/solid`, and `solid-js`
(`packages/tui/package.json:50-66`). The same server underlies headless use:
`serve` starts a headless server and warns when `OPENCODE_SERVER_PASSWORD` is
unset (`cli/cmd/serve.ts:6-24`); `attach <url>` connects a TUI to a running
server with Basic auth (`cli/cmd/attach.ts:7-148`); `run [message..]` is the
non-interactive form with `--format default|json` and `--attach`
(`cli/cmd/run.ts:126-229`). The top-level yargs binary registers the ACP, MCP,
TUI, Attach, Run, Serve (and other) commands
(`packages/opencode/src/index.ts:81-103`). A second, separate preview CLI
package exists (`packages/cli`, `bin: lildax`, self-described "OpenCode 2.0
preview command line interface") exposing `api`/`debug`/`migrate`/`service`/
`serve` (`packages/cli/src/commands/commands.ts:6-51`; `packages/cli/package.json:7-9`).

## Key facts with anchors

- The ACP `Agent` class is a one-line-per-method delegation shim over an Effect
  service; protocol-level errors are mapped via `ACPError.toRequestError`
  (`packages/opencode/src/acp/agent.ts:32-93`).
- ACP `initialize` returns `protocolVersion: 1` and declares exactly one auth
  method id `opencode-login`; `LoadAPIKeyError`/`ProviderAuthError` are mapped to
  an ACP `AuthRequiredError` (`packages/opencode/src/acp/service.ts:94-146`,
  `packages/opencode/src/acp/service.ts:1065-1097`).
- `opencode acp` hosts the HTTP server and the stdio ACP bridge in one process;
  the bridge is a client of its own server via `createOpencodeClient`
  (`packages/opencode/src/cli/cmd/acp.ts:19-72`).
- ACP `listSessions` pages at a hard-coded `limit = 100`
  (`packages/opencode/src/acp/service.ts:246-290`).
- ACP prompt detects leading-`/` slash commands from the prompt text
  (`detectSlashCommand`, `packages/opencode/src/acp/service.ts:811-822`) and maps
  known ones to `sdk.session.command`; `compact` maps to `sdk.session.summarize`
  (`packages/opencode/src/acp/service.ts:506-574`).
- ACP PromptResponse stop reasons are `end_turn`, `cancelled` (MessageAbortedError),
  `max_tokens` (MessageOutputLengthError), `refusal` (ContentFilterError)
  (`packages/opencode/src/acp/service.ts:824-873`).
- The ACP event subscription reconnects after 1000 ms on stream loss and turns
  OpenCode `session.status` idle events into the `runUntilIdle` resolve that ends a
  prompt (`packages/opencode/src/acp/event.ts:144-165`, `event.ts:74-91`).
- ACP permission replies are limited to `once`/`always`/`reject`; anything else is
  treated as reject (`packages/opencode/src/acp/permission.ts:20-24`,
  `permission.ts:219-223`). Edit permissions also push the full post-edit file via
  `connection.writeTextFile` after applying the diff locally with `diff.applyPatch`
  (`permission.ts:99-115`).
- The LSP service lazy-spawns and memoizes clients keyed by `{root, serverID}`,
  and never re-spawns a `broken` pair (`packages/opencode/src/lsp/lsp.ts:208-297`).
- LSP `workspaceSymbol` filters to 8 symbol kinds and slices to the first 10 per
  client (`packages/opencode/src/lsp/lsp.ts:87-96`, `lsp.ts:437`).
- Edit/write/apply_patch tools feed LSP diagnostics back into tool output with
  the string `LSP errors detected in this file, please fix:`; this is the primary
  "why LSP" mechanism (`packages/opencode/src/tool/edit.ts:197-201`,
  `tool/write.ts:75-76`, `tool/apply_patch.ts:269-271`).
- LSP diagnostic reporting keeps only severity 1 (errors) and caps at
  `MAX_PER_FILE = 20` per file (`packages/opencode/src/lsp/diagnostic.ts:3,20-27`).
- IDE `install` shells to `<editor-cmd> --install-extension sst-dev.opencode`
  (`packages/opencode/src/ide/index.ts:36-52`).
- The HTTP session route table includes `prompt_async`, `command`, `shell`,
  `summarize`, `fork`, `abort`, `share`, `revert`, `unrevert`
  (`packages/opencode/src/server/routes/instance/httpapi/groups/session.ts:78-105`).
- Server port `0` means "prefer 4096, then any free port"
  (`packages/opencode/src/server/server.ts:117-122`).
- Server authentication is off unless `OPENCODE_SERVER_PASSWORD` is set; the
  default Basic-auth username is `opencode`
  (`packages/opencode/src/server/auth.ts:17-26`).
- The default TUI runs the server in a worker and calls via an in-process fetch
  pointed at fake base URL `http://opencode.internal`
  (`packages/opencode/src/cli/cmd/tui.ts:238-249`,
  `packages/opencode/src/cli/tui/worker.ts:30-49`).

## Configuration and defaults

- `@agentclientprotocol/sdk` is pinned to `0.21.0`
  (`packages/opencode/package.json:57`).
- LSP control lives under the `lsp` config key: `false` disables all, `true`
  enables built-ins, or an object enables built-ins with per-server overrides; an
  entry `{disabled: true}` disables one server, and a custom server entry has
  `command[]`, `extensions[]`, optional `env`, `initialization`
  (`packages/core/src/v1/config/config.ts:120-123`,
  `packages/core/src/v1/config/lsp.ts:5-78`). Custom (non-builtin) servers must
  declare `extensions` or the config fails validation
  (`packages/core/src/v1/config/lsp.ts:63-74`).
- Built-in LSP server ids list (38) is in
  `packages/core/src/v1/config/lsp.ts:22-61`: deno, typescript, vue, eslint,
  oxlint, biome, gopls, ruby-lsp, ty, pyright, elixir-ls, zls, csharp, razor,
  fsharp, sourcekit-lsp, rust, clangd, svelte, astro, jdtls, kotlin-ls, yaml-ls,
  lua-ls, "php intelephense", prisma, dart, ocaml-lsp, bash, terraform, texlab,
  dockerfile, gleam, clojure-lsp, nixd, tinymist, haskell-language-server,
  julials.
- Runtime flags: `OPENCODE_DISABLE_LSP_DOWNLOAD` -> `disableLspDownload` and
  `OPENCODE_EXPERIMENTAL_LSP_TY` -> `experimentalLspTy`
  (`packages/opencode/src/effect/runtime-flags.ts:22,44`). The latter switches the
  Python server between `ty` and `pyright` (`packages/opencode/src/lsp/lsp.ts:98-108`).
- Server auth env: `OPENCODE_SERVER_PASSWORD` (optional), `OPENCODE_SERVER_USERNAME`
  (default `"opencode"`) (`packages/opencode/src/server/auth.ts:18-19`).
- Serve/attach network defaults: `--port` default `0`, `--hostname` default
  `127.0.0.1`, `--mdns` default `false`, `--mdns-domain` default `opencode.local`
  (`packages/opencode/src/cli/network.ts:6-33`). When mDNS is set and no explicit
  hostname is given, hostname defaults to `0.0.0.0`
  (`packages/opencode/src/cli/network.ts:70-74`).
- LSP client timing constants: `DIAGNOSTICS_DEBOUNCE_MS = 150`,
  `DIAGNOSTICS_DOCUMENT_WAIT_TIMEOUT_MS = 5_000`,
  `DIAGNOSTICS_FULL_WAIT_TIMEOUT_MS = 10_000`,
  `DIAGNOSTICS_REQUEST_TIMEOUT_MS = 3_000`, `INITIALIZE_TIMEOUT_MS = 45_000`
  (`packages/opencode/src/lsp/client.ts:13-18`).
- ACP usage updates report cost currency `"USD"` and read the context limit from
  `sdk.config.providers` (`packages/opencode/src/acp/service.ts:653-661`,
  `service.ts:602-622`).
- Several LSP servers self-install binaries when missing (gopls via `go install`,
  eslint via a fetched `vscode-eslint` zip, clangd/zls/lua-language-server/
  terraform-ls/tinymist from release archives, jdtls requires Java >= 21)
  (`packages/opencode/src/lsp/server.ts:358-390,173-222,935-1067,585-685,
  1387-1513,1622-1693,1867-1949,1147-1271`).

## Limitations and unknowns

- I read the ACP, LSP service/client/diagnostic, IDE, server wiring, and CLI
  command handlers directly. `lsp/server.ts` is very large (~1983 lines) and I
  verified only a representative sample of built-in servers (typescript, gopls,
  clangd, eslint, jdtls, pyright). The full per-server spawn behavior for the
  remaining ~30 entries is asserted from structure and the shared
  `builtinServerIds` list, not each line-verified.
- The TUI renderer (`packages/tui/src/*`) and the separate preview CLI
  (`packages/cli/src/*`) were characterized from `package.json`, exports, and
  command specs only; no UI/component-level behavior is claimed here (out of scope
  per the brief's architecture focus).
- Runtime behavior that cannot be observed statically is not claimed: whether a
  given LSP server actually starts depends on host toolchain presence, the
  `disableLspDownload` flag, and network fetches at runtime.
- ACP `session` state is an in-memory `Map` (`acp/session.ts:95-100`). I did not
  verify how ACP sessions survive server restarts or map durably to stored
  sessions; `loadSession`/`resumeSession` reconstruct model/mode from message
  history (`acp/service.ts:211-398`) but persistence semantics are governed by the
  storage layer, which is a separate component (opencodeStateSnapshots).
- The OpenCode->ACP protocol mapping (e.g. exact `ToolKind` or event taxonomy
  accepted by the `@agentclientprotocol/sdk` contract) is only as verifiable as the
  adapter code; correctness against an external ACP spec was not checked against
  the spec text itself (web access not used).
- Default model resolution prefers, in order, the configured model, the `opencode`
  provider's best model, then the global best-sorted model
  (`acp/service.ts:785-802`). I could not observe what `Provider.sort`'s ordering
  is here (defined in the provider component), so "best" is the code's term, not a
  verified ranking metric.

## Relevance to the brief

(Inference, separated from code facts above.)

This component is central to RQ1/RQ2 because it shows OpenCode's most distinctive
harness choice: the agent runtime is a network service, and every "interface" is a
client of it. That contrasts with a single in-process CLI loop. Concretely for the
cross-system comparison the brief asks for, the interfaces dimension yields:

- **One runtime, many frontends.** TUI, ACP, `run`, and `attach` all speak the
  HTTP SDK, so capability is defined once (server side) and the editor/terminal
  boundary is thin. ACP is explicitly an adapter, not a second agent.
- **LSP as the self-correction channel.** OpenCode wires diagnostics back into
  edit tool output, meaning the harness uses language servers as an automatic
  verifier of file edits. This is a genuine architectural point for the
  "apply-patch and repair" story (complements the tools note).
- **IDE support rides on ACP.** There is no bespoke IDE server; editors attach via
  ACP, and discovery can use mDNS. This shapes how to compare "IDE attachment"
  across the three systems.
- **Permission surfacing is protocol-native.** ACP maps OpenCode permission events
  to editor-native permission prompts (once/always/reject), including pushing
  proposed edit contents to the editor. This is OpenCode's answer to the
  capability-vs-safety question at the interface layer.

What it leaves open and must come from sibling notes: the turn loop/compaction
(opencodeSessionLoop, opencodeContextCompaction), storage persistence
(opencodeStateSnapshots), permission *rulesets* (opencodePermissions), and the
provider/auth machinery (opencodeConfigProviders). The interfaces note deliberately
does not re-derive those.

## Quotables for the report

- ACP is a client of the same HTTP server it hosts: `const sdk =
  createOpencodeClient({ baseUrl: \`http://${server.hostname}:${server.port}\`,
  headers: ServerAuth.headers() })` (`packages/opencode/src/cli/cmd/acp.ts:27-30`).
  Framing: "OpenCode's ACP endpoint does not embed the agent; it dials the runtime
  over its own HTTP API."
- LSP-as-verifier string: `if (block) output += \`\n\nLSP errors detected in this
  file, please fix:\n${block}\`` (`packages/opencode/src/tool/edit.ts:201`).
  Framing: "After each edit, OpenCode re-runs the language server and appends
  diagnostics to the tool result, closing the edit-and-check loop."
- Default TUI transport: `url: "http://opencode.internal"` with an in-process
  worker fetch (`packages/opencode/src/cli/cmd/tui.ts:246`,
  `packages/opencode/src/cli/tui/worker.ts:30-49`). Framing: "Even the terminal UI
  is structured as a client over an in-memory transport, so local and remote
  attachment share one code path."
- Auth boundary: `Basic realm="Secure Area"` and `OPENCODE_SERVER_PASSWORD` gate
  (`packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts:14`,
  `packages/opencode/src/server/auth.ts:18`). Framing: "The server is unauthenticated
  by default; a single password env var enables Basic auth."
- Server port default: prefer `4096` then any port
  (`packages/opencode/src/server/server.ts:117-122`). Framing: conventional local
  port for headless serve/attach.
