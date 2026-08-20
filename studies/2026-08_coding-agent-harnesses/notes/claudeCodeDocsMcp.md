---
# Note for the official Claude Code MCP reference page, docs tier. All claims
# anchor to the committed snapshot sources/docs/claudeCodeDocsMcp.md by section
# heading (in quotes) and line number at access date 2026-08-20. The page is a
# floating docs-site copy: it is not pinned to a Claude Code release commit,
# and the Claude Code core it describes is closed source.
source_key: "claudeCodeDocsMcp"
read_date: "2026-08-20"           # snapshot accessed 2026-08-20 per its header; note written same day
confidence: "high"                # full snapshot read directly, start to end
relevance: "3"                    # central to RQ4 and the Claude Code extensibility dimension
---

# Notes: Connect Claude Code to tools via MCP

## Source identification

- Key: claudeCodeDocsMcp
- Authors, year, venue: Anthropic, 2026, Claude Code official docs
  (code.claude.com/docs/en/mcp)
- Tier: docs
- URL / DOI: https://docs.claude.com/en/docs/claude-code/mcp (no DOI). The
  registry records the redirect target code.claude.com/docs/en/mcp
  (`sources/registry.yaml:337-347`).
- Access record: the committed snapshot
  `sources/docs/claudeCodeDocsMcp.md`, whose header states
  "snapshot: https://code.claude.com/docs/en/mcp.md accessed 2026-08-20
  (registry URL: https://docs.claude.com/en/docs/claude-code/mcp)"
  (snapshot line 1). Full page read directly for this note. All anchors below
  cite section headings of the snapshot plus line numbers.

## Problem and motivation

The page is the full reference for Claude Code's Model Context Protocol (MCP)
subsystem, the mechanism by which the agent reaches external tools,
databases, and APIs. The stated motivation: "Claude Code can connect to
hundreds of external tools and data sources through the Model Context
Protocol (MCP), an open source standard for AI-tool integrations" (intro,
snapshot line 10), and the trigger is workflow friction, "Connect a server
when you find yourself copying data into chat from another tool" (snapshot
line 12). The page positions itself as the reference counterpart to a
quickstart: "This page is the full reference" (snapshot line 14).

The page also states the safety premise of the subsystem up front: a warning
box says "Verify you trust each server before connecting it. Servers that
fetch external content can expose you to prompt injection risk" (section
"Find and build MCP servers", snapshot lines 31-33). That warning, plus the
workspace-trust machinery documented later, is the page's only explicit
capability-versus-safety framing.

Enumerated use cases include issue trackers, monitoring, databases, design
tools, workflows, and reactive events: "an MCP server can also act as a
channel that pushes messages into your session, so Claude reacts to Telegram
messages, Discord chats, or webhook events while you're away" (section "What
you can do with MCP", snapshot line 25).

## Method or core idea

The page documents a client-side MCP runtime with five interacting layers.
Mechanisms and architecture, each anchored:

1. **Transport layer (sections under "Installing MCP servers", snapshot
   lines 64-155).** Four transports: HTTP (recommended, the "most widely
   supported transport for cloud-based services", snapshot line 70), SSE
   (explicitly deprecated: "The SSE (Server-Sent Events) transport is
   deprecated. Use HTTP servers instead, where available", snapshot lines
   92-94), stdio (local child processes, snapshot lines 110-112), and
   WebSocket ("persistent bidirectional connection", for servers that push
   events unprompted; supports neither OAuth nor the `--transport` flag,
   snapshot lines 144-146). In JSON configs, `type` accepts `streamable-http`
   as an alias for `http` because "The MCP specification uses the name
   `streamable-http`" (snapshot line 84); an entry with a `url` but no
   `type` is a configuration error because Claude Code reads a typeless entry
   as stdio (snapshot line 86).
2. **Configuration-scope layer (section "MCP installation scopes", snapshot
   lines 430-556).** Three user-facing scopes (local, project, user) plus
   plugin-provided servers and claude.ai connectors, resolved by a fixed
   five-level precedence with whole-entry replacement, no field merging
   (snapshot lines 508-518). Project scope lives in a checkable-in
   `.mcp.json` and is gated by an interactive approval prompt and a workspace
   trust model (snapshot lines 495-497, 243-255). `.mcp.json` supports
   `${VAR}` and `${VAR:-default}` expansion in five fields (snapshot lines
   522-556).
3. **Lifecycle layer (sections under "Managing your servers", snapshot lines
   217-341).** Health statuses and a `/mcp` panel (snapshot lines 235-241);
   dynamic tool updates via MCP `list_changed` notifications (snapshot lines
   298-302); automatic reconnection for HTTP/SSE with exponential backoff
   (snapshot lines 304-312); a discovery cache with `cached` status so
   previously seen servers "connect on first use" (snapshot lines 257-259);
   channels for server-pushed messages (snapshot lines 314-316); the timeout
   stack (snapshot lines 327-341); and automatic backgrounding of long tool
   calls (snapshot lines 343-357).
4. **Scale layer (section "Scale with MCP tool search", snapshot lines
   1209-1300).** Tool search defers MCP tool definitions out of context and
   lets Claude discover them with a search tool; it is on by default, has an
   `ENABLE_TOOL_SEARCH` knob with threshold mode, per-server and per-tool
   `alwaysLoad` exemptions, and provider-specific fallbacks (snapshot lines
   1217-1300). When requested tools belong to servers still connecting,
   Claude waits either inside `ToolSearch` or via the `WaitForMcpServers`
   tool (section "Tool availability", snapshot lines 273-283).
5. **Policy and trust layer.** Per-tool and per-org controls surfaced
   through tool-list annotations (`anthropic/maxResultSizeChars`,
   `anthropic/requiresUserInteraction`, `anthropic/alwaysLoad`, snapshot
   lines 1092-1112, 1127-1153, 1298), claude.ai organization controls
   (`ask`, `blocked`, snapshot lines 985-990), managed configuration
   (`managed-mcp.json`, `allowedMcpServers`, `deniedMcpServers`, snapshot
   lines 1341-1343), and output limits (snapshot lines 1076-1090).

Source-level framing (the page's own interpretation, not independently
established): stdio servers are "ideal for tools that need direct system
access or custom scripts" (snapshot line 112); WebSocket suits servers that
push events unprompted (snapshot line 146); tool search gives "minimal impact
on your context window" (snapshot line 1211). These are vendor characterizations
of intent, used here only as such.

## Key claims with anchors

Established by the page as stated. Snapshot line numbers refer to
`sources/docs/claudeCodeDocsMcp.md`.

**Transports.**

- Claim 1 (section "Option 1: Add a remote HTTP server", lines 68-88): HTTP
  is the recommended remote transport; added with
  `claude mcp add --transport http <name> <url>`; `--header` supports static
  auth headers (e.g. `"Authorization: Bearer your-token"`); JSON `type`
  accepts `streamable-http` as an alias for `http`; a JSON entry with `url`
  but no `type` is skipped with the message
  `MCP server "<name>" has a "url" but no "type"; add "type": "http" (or "sse" / "ws") to this entry`,
  where versions before v2.1.202 reported `command: expected string, received undefined`;
  in `--output-format stream-json` runs, skipped `--mcp-config` entries appear
  in the `system/init` event's `mcp_server_errors` field (requires v2.1.219 or later).
- Claim 2 (section "Option 2: Add a remote SSE server", lines 90-108): the
  SSE transport is deprecated in favor of HTTP; it remains addable via
  `claude mcp add --transport sse <name> <url>` because "Some services still
  expose only an SSE endpoint".
- Claim 3 (section "Option 3: Add a local stdio server", lines 110-142):
  stdio servers run as local processes; added with
  `claude mcp add [options] <name> -- <command> [args...]` where `--`
  separates CLI options from the server command; Claude Code sets
  `CLAUDE_PROJECT_DIR` in the spawned server's environment to the stable
  project root (same directory hooks receive), and servers needing directory
  scoping should implement the MCP `roots/list` request, which Claude Code
  answers with the launch directory plus every additional working directory
  granted via `--add-dir`, `/add-dir`, or `additionalDirectories`, sending
  `notifications/roots/list_changed` on change (before v2.1.203, only the
  launch directory was returned and no change notification was sent).
- Claim 4 (section "Option 4: Add a remote WebSocket server", lines 144-155):
  WebSocket is configured only via `.mcp.json` or `claude mcp add-json` style
  JSON (`type: "ws"`), since `claude mcp add --transport` does not accept
  `ws`; `ws` accepts the same `url`, `headers`, `headersHelper`, `timeout`,
  and `alwaysLoad` fields as `http`; authentication is header-only; WebSocket
  servers are not shown in `claude mcp list` output (section "Server status",
  line 241).

**Scopes and precedence.**

- Claim 5 (section "MCP installation scopes", table lines 434-438): three
  scopes with storage and sharing semantics quoted from the table: Local
  ("Current project only", not shared, stored in
  `~/.claude.json`); Project ("Current project only", "Shared with team …
  Yes, via version control", stored in `.mcp.json` in project root); User
  ("All your projects", not shared, stored in `~/.claude.json`).
- Claim 6 (section "Local scope", lines 440-471): local scope is the
  default; the server is written under the project's path key inside
  `~/.claude.json`. A note distinguishes this from general settings: "MCP
  local-scoped servers are stored in `~/.claude.json` (your home directory),
  while general local settings use `.claude/settings.local.json` (in the
  project directory)" (lines 444-446).
- Claim 7 (section "Scope hierarchy and precedence", lines 508-520): for
  duplicate definitions Claude Code "connects to it once, using the
  definition from the highest-precedence source. The entire server entry
  from that source is used; fields are not merged across scopes." Precedence
  order: 1. Local scope, 2. Project scope, 3. User scope, 4. Plugin-provided
  servers, 5. claude.ai connectors. Scopes match duplicates by name; plugins
  and connectors match by endpoint (same URL or command). A special case:
  the Desktop app's Code tab uses the `~/.claude.json` definition over a
  same-named `.mcp.json` entry for stdio servers.

**`.mcp.json` approval and workspace trust.**

- Claim 8 (section "Project scope", lines 473-497): "For security reasons,
  Claude Code prompts for approval in interactive sessions before using
  project-scoped servers from `.mcp.json` files"; `claude mcp reset-project-choices`
  resets approvals. `claude -p`, Agent SDK, and cloud sessions cannot show
  the prompt and "load project-scoped servers there without asking"; a
  session started in `bypassPermissions` with `skipDangerousModePermissionPrompt`
  set also skips it. `disabledMcpjsonServers` blocks a server in every mode;
  `--setting-sources` or the SDK's `settingSources` excludes project settings
  entirely.
- Claim 9 (section "Project server approvals and workspace trust", lines
  243-255): as of v2.1.196, `claude mcp list` and `claude mcp get` read
  `.mcp.json` approvals only from settings files not checked into the
  repository until the user trusts the workspace by running `claude` and
  accepting the trust dialog. Verbatim: "A cloned repository can't approve
  its own servers", so `enableAllProjectMcpServers` or `enabledMcpjsonServers`
  committed to `.claude/settings.json` is ignored in an untrusted folder and
  the server stays at `⏸ Pending approval`. In untrusted folders, approvals
  still apply from the user `~/.claude/settings.json`, managed settings, and
  `--settings`. An untracked `.claude/settings.local.json` is honored only
  after a git tracking check that itself runs only in trusted folders
  (before v2.1.207 it applied even in never-trusted folders), with an
  exception for the user's own configuration home. A `disabledMcpjsonServers`
  entry in any settings file still rejects.
- Claim 10 (section "Disable a server without removing it", lines 285-296):
  per-project opt-out/opt-in recorded in `~/.claude.json` as
  `disabledMcpServers` (opt-out for user-configured, plugin, connector, and
  default-on built-in servers) and `enabledMcpServers` (opt-in for
  default-off built-ins such as `computer-use`); exactly one list is
  consulted per server, so neither overrides the other, and both are
  unrelated to `enabledMcpjsonServers`/`disabledMcpjsonServers`.

**Environment variable expansion.**

- Claim 11 (section "Environment variable expansion in `.mcp.json`", lines
  522-556): supported syntax is `${VAR}` and `${VAR:-default}`; expansion
  locations are `command`, `args`, `env`, `url` (HTTP types), and `headers`.
  Missing variable behavior: "the config still loads: Claude Code reports a
  missing-variable warning for that server in `claude mcp list` output and
  uses the unexpanded `${VAR}` text as-is" (line 556). For plugin-provided
  servers, `${CLAUDE_PROJECT_DIR}` is substituted directly without needing a
  default, unlike user-scoped entries (section "Option 3", line 118).

**Tool search and `WaitForMcpServers`.**

- Claim 12 (section "Tool availability", lines 273-283): when a request needs
  tools from a still-connecting server, Claude waits, and the mechanism
  depends on configuration: "With tool search, the default: the wait happens
  inside the `ToolSearch` call. Without tool search: Claude uses the
  `WaitForMcpServers` tool instead", where tool-search-less configurations
  include a custom `ANTHROPIC_BASE_URL`, `ENABLE_TOOL_SEARCH=false`, and
  pre-Claude-4.5-generation models on Google Cloud's Agent Platform. On
  Microsoft Foundry deployments hosted on Azure, Claude starts on the
  tool-search path because the deployment's server-side rejection is only
  discovered from the API, then switches to upfront loading.
- Claim 13 (section "Scale with MCP tool search", lines 1209-1221): "Tool
  search keeps MCP context usage low by deferring tool definitions until
  Claude needs them. Only tool names and server instructions load at session
  start"; "Claude Code doesn't impose a fixed per-server tool cap; the
  practical limit is your context window budget"; it is enabled by default,
  and "Only the tools Claude actually uses enter context." Server
  instructions become more important under tool search, "similar to how
  skills work" (section "For MCP server authors", line 1225).
- Claim 14 (section "Configure tool search", lines 1235-1268): tool search
  is disabled when `ANTHROPIC_BASE_URL` is a non-first-party host;
  `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` keeps it off without override,
  while managed settings can keep it on (v2.1.227 or later). It requires a
  model supporting `tool_reference` blocks: "Claude Sonnet 4.5, Claude
  Haiku 4.5, Claude Opus 4.5, and later models". `ENABLE_TOOL_SEARCH`
  accepts `(unset)`, `true`, `auto`, `auto:N` (threshold percent, e.g.
  `auto:5` for 5%, N is 0-100), and `false`; `auto` mode loads deferred
  definitions upfront while they total less than 10% of the context window
  and defers all of them once they reach 10%. `ToolSearch` itself is
  deniable via `permissions.deny`. Before v2.1.221, tool search was disabled
  for all models on Google Cloud's Agent Platform unless forced on.
- Claim 15 (section "For MCP server authors", line 1233): "Claude Code
  truncates tool descriptions and server instructions at 2KB each."
- Claim 16 (section "Exempt a server from deferral", lines 1280-1300):
  `alwaysLoad: true` on any server type loads all its tools at session start
  regardless of `ENABLE_TOOL_SEARCH`; a server can mark individual tools
  always-loaded with `"anthropic/alwaysLoad": true` in the tool's `_meta`;
  `alwaysLoad: true` makes startup wait for that server's tools, "capped at
  the standard 5-second connect timeout"; other servers connect in the
  background by default (`MCP_CONNECTION_NONBLOCKING=0` makes startup wait
  for them).

**Timeouts.**

- Claim 17 (Tip box under "Push messages with channels", lines 327-329):
  `MCP_TIMEOUT` sets the MCP server startup timeout (e.g.
  `MCP_TIMEOUT=10000 claude` sets a 10-second timeout); a per-server
  `timeout` field in milliseconds in `.mcp.json` sets that server's tool
  execution timeout (e.g. `"timeout": 600000` for ten minutes) and overrides
  `MCP_TOOL_TIMEOUT` for that server only.
- Claim 18 (same section, line 333): the per-server `timeout` is "a hard
  wall-clock limit per tool call, and progress notifications from the server
  don't extend it"; values below 1000 are ignored and fall through to
  `MCP_TOOL_TIMEOUT` "or to its default of about 28 hours when that variable
  is unset". For HTTP, SSE, and claude.ai connector servers there is a
  second per-request timer to the server's first response byte: "That timer
  is 60 seconds unless you set the per-server `timeout` or
  `MCP_TOOL_TIMEOUT`; setting either to 60 seconds or higher raises the
  per-request timer to that value, a lower value doesn't shorten it, and the
  28-hour default of an unset `MCP_TOOL_TIMEOUT` never feeds it." Stdio and
  WebSocket servers have no per-request timer. Before v2.1.162, sub-1000
  values were floored to one second. A per-server `timeout` of at least 1000
  also floors the idle timeout (line 335, requires v2.1.203 or later).
- Claim 19 (same section, lines 337-339): the idle timeout aborts a call
  that sends "no response and no progress notification for the idle window"
  (requires v2.1.187 or later); it applies to every server type except IDE
  servers and SDK in-process servers; the idle window defaults to five
  minutes for HTTP, SSE, WebSocket, and claude.ai connector servers and 30
  minutes for stdio servers (before v2.1.203, stdio was exempt);
  `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` in milliseconds changes it, `0`
  disables it.

**Automatic backgrounding.**

- Claim 20 (section "Automatic backgrounding of long tool calls", lines
  343-357): "An MCP tool call in the main conversation that is still running
  after two minutes moves to a background task instead of blocking the
  session"; Claude receives the task ID immediately and the result arrives
  as a task notification; requires v2.1.212 or later. Tasks appear in
  `/tasks`, can be stopped there, and don't survive exiting the session;
  per-call limits still apply in the background. `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`
  changes the threshold (`0` turns it off); `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`
  disables it plus all background task features. Never backgrounded: calls
  from subagents, calls to IDE servers, and calls in non-interactive mode
  unless `CLAUDE_AUTO_BACKGROUND_TASKS=1`. A call waiting on an open
  elicitation dialog is deferred until the dialog closes.

**OAuth.**

- Claim 21 (section "Authenticate with remote MCP servers", lines 610-629):
  OAuth 2.0 is supported; a remote server is marked as needing
  authentication on `401 Unauthorized` or `403 Forbidden`. On a 401 from a
  signed-in OAuth server, Claude Code "refreshes the stored token,
  reconnects, and retries the request once", flagging the server only if the
  retry fails (before v2.1.206 a transient refresh failure flagged the
  server for the rest of the session). A `WWW-Authenticate` header pointing
  at the authorization server gets automatic discovery. In non-interactive
  mode (no `/mcp` panel), as of v2.1.196, with tool search enabled Claude
  Code tells Claude the server's tools are unavailable until authorization.
  A rejected configured `headers.Authorization` is reported as failed, not
  fallen back to OAuth.
- Claim 22 (sections "Authenticate from the command line" through "Use
  pre-configured OAuth credentials", lines 661-760): `claude mcp login <name>`
  runs the OAuth flow from the shell (from v2.1.186), `claude mcp logout <name>`
  clears credentials; from v2.1.191 the login command detects no local
  browser (SSH, Linux without a display server) and prints the authorization
  URL, with `--no-browser` forcing the prompt and `ssh -t` required for the
  paste step. Dynamic Client Registration is the default path; Client ID
  Metadata Document (CIMD) servers are discovered automatically; the error
  "Incompatible auth server: does not support dynamic client registration"
  signals pre-configured credentials are required; `--client-id`,
  `--client-secret`, `--callback-port`, an `oauth` JSON object, and the
  `MCP_CLIENT_SECRET` env var are supported; client secrets are stored "in
  your system keychain (macOS) or a credentials file". Version note: v2.1.229
  sent `http://127.0.0.1:PORT/callback` and broke exact-match redirect URIs;
  v2.1.231 restored the `localhost` form. OAuth flags apply only to HTTP and
  SSE transports.
- Claim 23 (sections "Override OAuth metadata discovery" and "Restrict OAuth
  scopes", lines 762-808): default discovery checks RFC 9728 Protected
  Resource Metadata at `/.well-known/oauth-protected-resource` first, then
  falls back to RFC 8414 at `/.well-known/oauth-authorization-server`;
  `oauth.authServerMetadataUrl` (must be `https://`) overrides the chain.
  `oauth.scopes` pins the requested scope set as a space-separated string
  "matching the `scope` parameter format in RFC 6749 §3.3" and takes
  precedence over both `authServerMetadataUrl` and `.well-known` scopes. As
  of v2.1.196, with `oauth.scopes` unset, Claude Code requests scopes from
  `WWW-Authenticate` or protected resource metadata and no longer requests
  the full `scopes_supported` catalog. If the server advertises
  `offline_access`, Claude Code appends it; a 403 `insufficient_scope`
  triggers re-authentication with the same pinned scopes.
- Claim 24 (section "Use dynamic headers for custom authentication", lines
  810-866): `headersHelper` runs a shell command at connection time for
  non-OAuth auth (Kerberos, short-lived tokens, internal SSO); the command
  must print a JSON object of string pairs, "runs in a shell with a 10-second
  timeout, from the session's current working directory", and its output
  overrides static `headers` of the same name; it runs fresh per connection
  with no caching; on a 401/403 tool call it re-runs, reconnects, and retries
  once. The helper receives `CLAUDE_CODE_MCP_SERVER_NAME`,
  `CLAUDE_CODE_MCP_SERVER_URL`, and, for plugin servers, `CLAUDE_PLUGIN_ROOT`.
  Security note in the source: "`headersHelper` executes arbitrary shell
  commands. When defined at project or local scope, Claude Code runs it
  under the same workspace trust rule as hooks in settings files, so it runs
  in a `-p` session in a folder you've never trusted" (lines 864-866).

**Channels.**

- Claim 25 (section "Push messages with channels", lines 314-316): an MCP
  server can push messages into the session for event-driven reactions; the
  server declares the `claude/channel` capability and the user opts in with
  the `--channels` flag at startup. Details are deferred to the Channels and
  Channels reference pages, which are not part of this snapshot.

**Plugin-provided servers and scoped tool names.**

- Claim 26 (section "Plugin-provided MCP servers", lines 359-368): plugins
  define servers in `.mcp.json` at the plugin root or inline in
  `plugin.json`; enabling a plugin starts its servers automatically;
  "Plugin MCP servers work identically to user-configured servers"; they are
  added and removed by installing or uninstalling the plugin, though they
  can be toggled off in `/mcp`.
- Claim 27 (same section, lines 402-414): lifecycle: enabled-plugin servers
  connect at session startup (or show `cached` status and connect on first
  use); `/reload-plugins` applies mid-session enable/disable and preserves
  live connections of unchanged configs; in web sessions an MCP call to an
  unconnected plugin server starts it on demand and waits. Path
  placeholders: `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's
  installation directory, `${CLAUDE_PLUGIN_DATA}` to its persistent state
  directory, `${CLAUDE_PROJECT_DIR}` to the stable project root; substitution
  covers `command`, `args`, `env` for stdio and `url`, `headers`,
  `headersHelper` for http/sse/ws (before v2.1.195, `headersHelper` passed
  the placeholder through literally).
- Claim 28 (same section, lines 416-426): plugin MCP tool names are scoped.
  "The full form is `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`,
  where any character outside `A-Z`, `a-z`, `0-9`, `_`, and `-` is replaced
  with `_`" (worked example `mcp__plugin_my-plugin_database-tools__query`).
  Hook matchers written against the bare server key "never fire for a
  plugin-bundled server". The server registers under the scoped name
  `plugin:<plugin-name>:<server-name>` for surfaces that expect a configured
  server name.

**Supporting machinery (also anchored).**

- Claim 29 (section "Automatic reconnection", lines 304-312): HTTP/SSE
  mid-session disconnects reconnect "with exponential backoff: up to five
  attempts, starting at a one-second delay and doubling each time"; after
  five failures the server is marked failed. Initial-connection failures
  retry up to three times on transient errors (5xx, connection refused,
  timeout), never on authentication or not-found errors. Capability
  discovery requests (`tools/list`, `prompts/list`, `resources/list`) retry
  transient errors up to three times. With tool search enabled, connection
  failures are reported to Claude, including inside empty `ToolSearch`
  results; without tool search, they are not.
- Claim 30 (section "Server status detail", lines 257-271, plus "Configuration
  warnings", lines 265-271): discovery cache with `cached` status requires
  v2.1.221 or later and is disabled with `MCP_DISCOVERY_CACHE=0`; reserved
  built-in server names are `workspace`, `claude-in-chrome`, `computer-use`,
  `Claude Preview`, and `Claude Browser`, and configurations using them are
  skipped with a warning at load.
- Claim 31 (section "MCP output limits and warnings", lines 1076-1112):
  warning at 10,000 tokens, default maximum 25,000 tokens, raised via
  `MAX_MCP_OUTPUT_TOKENS`; per-tool `_meta["anthropic/maxResultSizeChars"]`
  raises the persist-to-disk threshold "up to a hard ceiling of 500,000
  characters"; oversized text results "are persisted to disk and replaced
  with a file reference in the conversation".
- Claim 32 (section "Require approval for a specific tool", lines 1127-1153):
  `_meta["anthropic/requiresUserInteraction"] = true` forces the permission
  prompt on every call "even in `acceptEdits`, `auto`, and `bypassPermissions`
  permission modes", with no "don't ask again" and no skip via allow rules;
  in `dontAsk` mode the call is denied; via `--permission-prompt-tool` an
  `allow` is converted to a deny with the message
  `MCP tool requires user interaction; not supported via --permission-prompt-tool`;
  requires v2.1.199 or later.
- Claim 33 (sections "Use Claude Code as an MCP server", lines 1016-1074,
  and "Use MCP servers from claude.ai", lines 939-1014): `claude mcp serve`
  exposes Claude Code itself as a stdio MCP server, and "This MCP server
  only exposes Claude Code's tools to your MCP client, so your own client is
  responsible for implementing user confirmation for individual tool calls".
  claude.ai connectors are available only under a claude.ai subscription
  login and are the lowest-precedence source; organizations can enforce
  per-tool `ask` (prompts even in `bypassPermissions`, denies in `dontAsk`)
  and `blocked` (filtered out before Claude sees it) controls;
  `disableClaudeAiConnectors` uses any-source-true semantics.

## Evaluation and evidence

Docs source; there are no datasets, baselines, or experimental metrics. The
character-exact tunable values and constants the page states, each anchored:

- Startup timeout knob: `MCP_TIMEOUT`, example "MCP_TIMEOUT=10000 claude
  sets a 10-second timeout" (Tip box, line 327).
- Per-server tool execution timeout: `timeout` in `.mcp.json` in
  milliseconds, example "`\"timeout\": 600000` for ten minutes"; overrides
  `MCP_TOOL_TIMEOUT` for that server only (line 328).
- Default tool execution timeout: "about 28 hours" when `MCP_TOOL_TIMEOUT`
  is unset (line 333). Note the hedge "about": no exact figure is given.
- Per-request timer (HTTP/SSE/claude.ai connector only): 60 seconds to first
  response byte by default (line 333).
- Idle window defaults: five minutes for HTTP, SSE, WebSocket, claude.ai
  connectors; 30 minutes for stdio (line 337). Env knob
  `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`.
- Automatic backgrounding threshold: two minutes (line 345). Env knob
  `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`.
- Reconnection backoff: five attempts, one-second start, doubling (line 306);
  initial-connect retries: three (line 308); discovery retries: three (line 312).
- Output limits: warning at 10,000 tokens; default limit 25,000 tokens;
  example override `MAX_MCP_OUTPUT_TOKENS=50000`; per-tool annotation ceiling
  500,000 characters (lines 1080-1094).
- Tool search threshold: 10% of context window in `auto` mode; custom
  `auto:N` with N 0-100; tool description and server-instruction truncation
  at 2KB each (lines 1221, 1256-1257, 1233).
- Connect timeout for `alwaysLoad` servers: 5 seconds (line 1300).
- `headersHelper` shell timeout: 10 seconds (line 843).
- Version-gated behavior changes cited by exact version numbers: v2.1.162,
  v2.1.186, v2.1.187, v2.1.191, v2.1.193, v2.1.195, v2.1.196, v2.1.199,
  v2.1.202, v2.1.203, v2.1.205, v2.1.206, v2.1.207, v2.1.208, v2.1.212,
  v2.1.214, v2.1.219, v2.1.221, v2.1.222, v2.1.227, v2.1.229, v2.1.231
  (passim, as anchored in the claims above).
- Model requirements for tool search: "Claude Sonnet 4.5, Claude Haiku 4.5,
  Claude Opus 4.5, and later models" (line 1241).

Not located, with where I looked (all within the full snapshot): an exact
value for the `MCP_TOOL_TIMEOUT` default (only "about 28 hours", line 333);
the default value of `MCP_TIMEOUT` itself (the page gives an example of
setting it, not its default) `[CITATION NEEDED]`; channel protocol details
(deferred to /docs/en/channels, not in scope); managed-policy semantics
(deferred to /docs/en/managed-mcp, not in scope).

## Limitations

- Floating docs, unpinned to any artifact. The snapshot header records
  access on 2026-08-20 (`sources/docs/claudeCodeDocsMcp.md` line 1), and the
  registry's coverage limits state that docs sites "are not pinned" and "can
  drift from the pinned commits" (`sources/registry.yaml:57`). Claude Code's
  core is closed source (`sources/registry.yaml:55`), so no claim on this
  page can be checked against code, only against the page itself. The dense
  version churn notes (twenty-plus v2.1.x callouts) show the behavior
  described is specific to a narrow release window, and this snapshot does
  not record which Claude Code version it was rendered for. `[CITATION NEEDED]`
  Where I looked: full snapshot text and header; the page states no version.
- Self-reported and normative. Every mechanism claim is the vendor's
  description of intended behavior. Nothing on the page is evaluated: no
  benchmarks, no failure-rate data, no measurements of context savings from
  tool search ("minimal impact on your context window", line 1211, is an
  unquantified characterization).
- Hedges in the constants. The default tool execution timeout is given only
  as "about 28 hours" (line 333), and several constants are stated
  conditionally on version ("Before v2.1.x …"), so reuse of any number
  requires carrying its version qualifier.
- Deferred scope. Several behaviors are documented only by pointer on this
  page: channels (Lines 314-316), managed configuration (lines 1341-1343),
  the env-var reference (/docs/en/env-vars), plugin component reference
  (/docs/en/plugins-reference), and workspace-trust interaction rules
  (/docs/en/permissions). Claims about those surfaces should cite those
  pages, not this note.
- Asymmetric verifiability with the pinned checkout. The pinned
  claude-code repository (commit c3d2e35) contains only plugins, examples,
  and scripts (`sources/registry.yaml:259-270`), none of which exercises the
  client runtime described here (transports, timeouts, tool search). This
  note therefore has no code-side corroboration for any mechanism claim.
- Gate note for the literature gate (`study.yaml: depth: full`): no blocking
  gap for this entry. The snapshot is complete and claim-checkable in full.
  The only source-level gaps are the deferred pages listed above, which are
  out of this entry's registered scope, and the absent version identifier
  for the snapshot, which should be resolved before the report quotes
  version-gated behavior as current.

## Relevance to the brief

My inference, separated from the anchored material above.

- RQ4 (Claude Code's closed core through its docs) is the primary payoff.
  This page is unusually mechanism-rich for a closed product: it documents
  the transport set, the scope/precedence resolution order, the
  trust-then-approval model for checked-in MCP config, the full timeout
  stack, the backgrounding policy, and the tool-search deferral scheme.
  Together with `notes/claudeCodePluginSurface.md` (the verifiable plugin
  manifests), it lets the report state how Claude Code is designed to be
  extended even though the core is unobservable.
- RQ2 (general harness components) gets a concrete Claude Code instance of
  extensibility-as-MCP plus two turn-loop-adjacent behaviors the docs expose:
  tool-call backgrounding after two minutes (claim 20) and idle/timeout
  aborts (claims 18-19). These are harness machinery normally invisible in
  docs; worth a dedicated cell in the comparison matrix because the other
  systems' docs/code may treat long tool calls differently.
- RQ1 (genuine differences) is sharpened by three Claude Code design bets
  that can be tested against the Codex and OpenCode notes: deferred tool
  loading via tool search (claim 13) rather than upfront tool registration;
  whole-entry precedence across five config sources (claim 7) rather than
  merge; and trust-gated adoption of repo-committed MCP config (claims 8-9),
  i.e. the repo cannot authorize its own servers. Each has a plausible
  contrasting implementation to hunt for in the pinned codebases.
- RQ3 (capability vs safety) is addressed through the prompt-injection
  warning (intro section), the workspace-trust approval flow, the
  `headersHelper` trust note, the `ask`/`blocked` org controls, and
  `anthropic/requiresUserInteraction` prompting even in `bypassPermissions`.
  The pattern: Claude Code relocates safety decisions from static config to
  interactive, trust-gated moments.
- Left open: the channels mechanism (separate page), what tool search costs
  in latency or accuracy, and whether documented defaults match any
  shipped binary. The report should quote this source as "documented
  behavior" rather than verified behavior.

## Quotables for the report

Short verified excerpts with snapshot anchors, and suggested framing.

- Recommended transport: "HTTP servers are the recommended option for
  connecting to remote MCP servers. This is the most widely-supported
  transport for cloud-based services." (section "Option 1", line 70), and
  the deprecation: "The SSE (Server-Sent Events) transport is deprecated.
  Use HTTP servers instead, where available." (section "Option 2", line 93).
  Framing: Claude Code is consolidating on streamable HTTP for remote MCP.
- Precedence: "The entire server entry from that source is used; fields are
  not merged across scopes", with the five-level order local, project, user,
  plugin, claude.ai connector (section "Scope hierarchy and precedence",
  lines 510-516). Framing: config resolution is replacement, not merge.
- Workspace trust: "A cloned repository can't approve its own servers"
  (section "Project server approvals and workspace trust", line 245).
  Framing: repo-committed MCP config is inert until the user trusts the
  folder, a prompt-injection countermeasure at the harness level.
- Tool search: "Only tool names and server instructions load at session
  start, so adding more MCP servers has minimal impact on your context
  window" (section "Scale with MCP tool search", line 1211). Framing: Claude
  Code buys MCP scale by deferring tool schemas behind a search tool
  (context-budget framing, no fixed per-server cap).
- Waiting for servers: "Without tool search: Claude uses the `WaitForMcpServers`
  tool instead" (section "Tool availability", line 280). Framing: the
  harness turns server readiness into an explicit tool the model can call.
- Backgrounding: "An MCP tool call in the main conversation that is still
  running after two minutes moves to a background task instead of blocking
  the session" (section "Automatic backgrounding", line 345). Framing: a
  documented, threshold-based decoupling of long tool calls from the turn.
- Timeout stack: "The idle window defaults to five minutes for HTTP, SSE,
  WebSocket, and claude.ai connector servers, and to 30 minutes for stdio
  servers" (Tip box section, line 337); `MCP_TOOL_TIMEOUT` default "about 28
  hours" (line 333). Framing: three nested timers (startup, per-request,
  wall-clock) plus an idle abort bound every MCP call.
- Plugin naming: "The full form is `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`"
  (section "Plugin-provided MCP servers", line 418). Framing: plugin MCP
  tools are namespaced, and hook matchers must use the scoped name.
