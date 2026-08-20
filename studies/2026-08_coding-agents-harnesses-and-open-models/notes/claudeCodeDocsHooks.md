---
# Note for the Claude Code Hooks reference page. Full snapshot read directly:
# sources/docs/claudeCodeDocsHooks.md (page captured 2026-08-20). Every claim
# carries a section anchor of that snapshot. No code cross-check is possible:
# the Claude Code core is closed source (sources/registry.yaml:55).
source_key: "claudeCodeDocsHooks"
read_date: "2026-08-20"
confidence: "high"    # full snapshot read directly, same day as capture
relevance: "3"        # central: Claude Code extensibility (hooks) plus lifecycle and permission evidence for RQ1-RQ4
---

# Notes: Claude Code Hooks reference

## Source identification

- Key: claudeCodeDocsHooks
- Authors, year, venue: Anthropic, 2026, Claude Code official docs (code.claude.com/docs/en/hooks)
- Tier: docs
- URL / DOI: https://docs.claude.com/en/docs/claude-code/hooks (registry URL;
  the snapshot header records the fetched endpoint
  `https://code.claude.com/docs/en/hooks.md`, accessed 2026-08-20,
  `sources/docs/claudeCodeDocsHooks.md:1`)
- Snapshot: `sources/docs/claudeCodeDocsHooks.md`, 3,488 lines, read in full.
  Anchors below cite section headings of the snapshot page, e.g. (Section
  "Hook lifecycle"). The page itself prints no product version stamp; which
  CLI version the text targets is `[CITATION NEEDED]` (looked: snapshot header
  line 1 and the entire page body; the page only references version-gated
  changes in the v2.1.x series, from v2.1.145 through v2.1.234).

## Problem and motivation

The page is the normative reference for Claude Code's hook system. Its stated
scope: "Reference for Claude Code hook events, configuration schema, JSON
input/output formats, exit codes, async hooks, HTTP hooks, prompt hooks, and
MCP tool hooks" (Section "Hooks reference", page summary line). The docs
define hooks as "user-defined shell commands, HTTP endpoints, or LLM prompts
that execute automatically at specific points in Claude Code's lifecycle" and
claim they run identically across every client surface: "sessions in the
terminal, IDE extensions, the Desktop app, and Claude Code on the web all
fire the same hook events" (Section "Hooks reference", introduction).

The docs also frame what hooks are and are not for. They repeatedly steer the
reader away from treating hooks as a security boundary: "Because the `if`
filter is best-effort, use the permission system rather than a hook to
enforce a hard allow or deny" (Section "Common fields") and "don't count on a
stalled hook to act as a gate" (Section "Timeouts"). That framing is itself
evidence about the harness: hooks are positioned as an automation and
observability layer, with enforcement delegated to a separate permission
system documented on other pages.

## Method or core idea

The hook system is specified as three nested configuration levels (Section
"Configuration"): (1) a hook event to respond to, (2) a matcher group that
filters when it fires, (3) one or more hook handlers that run when matched.
The docs fix terminology: "hook event for the lifecycle point, matcher group
for the filter, and hook handler for the shell command, HTTP endpoint, MCP
tool, prompt, or agent that runs" (Section "Configuration").

Resolution pipeline. When an event fires, Claude Code sends JSON context to
each matching handler; for command hooks input arrives on stdin, for HTTP
hooks as the POST body; the handler "can then inspect the input, take action,
and optionally return a decision" (Section "Hook lifecycle"). The walkthrough
decomposes resolution into five steps: event fires, matcher checks, `if`
condition checks, hook handler runs, Claude Code acts on the result (Section
"How a hook resolves"). A handler only spawns when both the group matcher and
its optional `if` condition match; on a non-matching call the handler "would
never run, avoiding the process spawn overhead" (Section "How a hook
resolves").

Lifecycle cadence. The docs sort events into three cadences (Section "Hook
lifecycle"):

- once per session: `SessionStart` and `SessionEnd`
- once per turn: `UserPromptSubmit`, `Stop`, and `StopFailure`
- on every tool call inside the agentic loop: `PreToolUse` and `PostToolUse`,
  "except `EndConversation` calls, which skip both" (Section "Hook lifecycle")

The event table lists 31 events in total (Section "Hook lifecycle"): in
addition to the cadence events, `Setup`, `UserPromptExpansion`,
`PermissionRequest`, `PermissionDenied`, `PostToolUseFailure`,
`PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`,
`SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`,
`InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`,
`FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`,
`PostCompact`, `Elicitation`, and `ElicitationResult`. The lifecycle diagram
(alt text) additionally places `PermissionRequest`, `PostToolUseFailure`,
`PostToolBatch`, `SubagentStart/Stop`, and `TaskCreated/TaskCompleted` inside
the nested agentic loop, and `Elicitation`/`ElicitationResult` inside MCP
tool execution (Section "Hook lifecycle").

Five handler types (Section "Hook handler fields"):

1. `command`: run a shell command; the script receives the event's JSON input
   on stdin and "communicates results back through exit codes and stdout".
2. `http`: POST the event's JSON input to a URL; the endpoint returns results
   "using the same JSON output format as command hooks".
3. `mcp_tool`: call a tool on an already-connected MCP server; "The tool's
   text output is treated like command-hook stdout".
4. `prompt`: "send a prompt to a Claude model for single-turn evaluation.
   The model returns its decision as JSON."
5. `agent`: "spawn a subagent that can use tools like Read, Grep, and Glob to
   verify conditions before returning a decision. Agent hooks are
   experimental and may change."

Type support is event-dependent (Section "Prompt-based hooks"): 13 events
support all five types (`PermissionDenied`, `PermissionRequest`,
`PostToolBatch`, `PostToolUse`, `PostToolUseFailure`, `PreToolUse`, `Stop`,
`SubagentStop`, `TaskCompleted`, `TaskCreated`, `TeammateIdle`,
`UserPromptExpansion`, `UserPromptSubmit`); 16 events support only
`command`, `http`, and `mcp_tool`; `SessionStart` and `Setup` support only
`command` and `mcp_tool`.

Command hooks have two spawn modes (Section "Exec form and shell form"): exec
form (`args` set) resolves `command` as an executable and spawns it directly
with no shell, passing placeholders as plain strings; shell form (`args`
omitted) passes the string to `sh -c` on macOS/Linux, Git Bash on Windows,
or PowerShell when Git Bash is not installed.

Configuration locations and scoping. Seven locations with different scopes
(Section "Hook locations"): `~/.claude/settings.json` (all projects, not
shareable), `.claude/settings.json` (project, committable),
`.claude/settings.local.json` (project, gitignored), managed policy settings
(organization-wide), plugin `hooks/hooks.json` (when plugin enabled), skill
frontmatter (rest of session once invoked), subagent frontmatter (while that
subagent runs). "Hook entries merge across settings levels rather than
replacing each other" and the `/hooks` menu labels each hook with one of six
sources including `Session Hooks` (registered in memory) and `Built-in
Hooks` ("registered internally by Claude Code") (Section "The /hooks menu").

## Key claims with anchors

What the source establishes:

- Claim 1 (Section "Hook lifecycle"): events fire on three cadences as listed
  above, and `PreToolUse`/`PostToolUse` skip `EndConversation` calls.
- Claim 2 (Section "Hook lifecycle"): the page catalogs 31 hook events with a
  per-event firing description, including compaction (`PreCompact`,
  `PostCompact`), subagents (`SubagentStart`, `SubagentStop`), tasks
  (`TaskCreated`, `TaskCompleted`), worktrees, file watching, config change,
  and MCP elicitation events.
- Claim 3 (Section "Hook locations"): hooks defined in settings files,
  managed policy settings, and plugins also run inside subagents; tool events
  in a subagent fire the same configured hooks and the input carries
  `agent_id` and `agent_type`.
- Claim 4 (Section "Hook locations"): enterprise administrators can use
  `allowManagedHooksOnly`, which blocks user, project, local, and plugin
  hooks (plugins force-enabled in managed `enabledPlugins` are exempt),
  narrows `statusLine`, `fileSuggestion`, and `subagentStatusLine` to
  managed settings, and disables plugins with a `command` source unless
  `disableCommandPluginSources` is explicitly `false`.
- Claim 5 (Section "Hook locations"): the HTTP hook allowlists apply to hooks
  from every source, including managed policy settings: `allowedHttpHookUrls`
  means "Claude Code runs an HTTP hook handler only if its URL matches the
  merged allowlist", and `httpHookAllowedEnvVars` means "Claude Code
  interpolates only the environment variables on that list into hook
  headers".
- Claim 6 (Section "Disable or remove hooks"): `disableAllHooks` set in user,
  project, or local settings cannot disable managed hooks; only
  `disableAllHooks` at the managed level can. Hooks merge across levels, so
  lower levels add hooks without removing managed ones (Section "Hook
  locations").
- Claim 7 (Section "Matcher patterns"): matcher evaluation is three-way:
  `"*"`, empty, or omitted matches everything; values containing only
  letters, digits, `_`, `-`, spaces, `,`, and `|` are exact strings or lists;
  "Contains any other character" evaluates as "JavaScript regular
  expression, unanchored", tested with `RegExp.prototype.test`. Comma
  separators require v2.1.191 or later; hyphens in the exact-match set
  require v2.1.195 or later. `FileChanged` and `StopFailure` use a narrower
  exact-match set (letters, digits, `_`, `|` only).
- Claim 8 (Section "Matcher patterns"): each event type matches a different
  field: tool events (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
  `PermissionRequest`, `PermissionDenied`) match the tool name;
  `SessionStart` matches how the session started (`startup`, `resume`,
  `clear`, `compact`, `fork`); `StopFailure` matches the error type;
  `PreCompact`/`PostCompact` match `manual` or `auto`; several events
  (including `UserPromptSubmit`, `Stop`, `PostToolBatch`, `MessageDisplay`)
  have no matcher support and a `matcher` field on them "is silently
  ignored".
- Claim 9 (Section "Match MCP tools"): MCP tools appear in tool events under
  the naming pattern `mcp__<server>__<tool>`; plugin-bundled MCP servers use
  a scoped segment `mcp__plugin_<plugin-name>_<server-name>__<tool>`, and "A
  matcher written against the bare server key never fires for these tools".
- Claim 10 (Section "Common fields"): the `if` field uses permission rule
  syntax, is evaluated only on the five tool events, and fails open: "The
  filter also fails open, running your hook regardless of pattern, when the
  Bash command can't be parsed." A leading `VAR=value` assignment is stripped
  before matching, `$()` and backtick subcommands are checked, and there is no
  `&&`/`||` combination syntax: `if` holds exactly one rule (Section "Common
  fields").
- Claim 11 (Section "Common fields" and "Hook handler fields"): all matching
  hooks run in parallel; "If you define the same handler in more than one
  settings file, it runs once. A plugin's or skill's copy of the same handler
  stays separate."
- Claim 12 (Section "Common input fields"): hook input JSON carries
  `session_id`, `prompt_id` (v2.1.196+, "Absent until the first user input",
  correlates with the OpenTelemetry `prompt.id` attribute),
  `transcript_path`, `cwd`, `permission_mode`, and `hook_event_name`;
  `permission_mode` values are `"default"`, `"plan"`, `"acceptEdits"`,
  `"auto"`, `"dontAsk"`, or `"bypassPermissions"` (the docs note "Not all
  events receive this field"). Inside subagents, `agent_id` and `agent_type`
  are added. `transcript_path` "is written asynchronously and may lag the
  in-memory conversation".
- Claim 13 (Section "Exit code 0" and "Exit code output"): exit 0 means
  success; stdout is parsed as JSON only when its first non-whitespace
  character is `{`, otherwise it is plain text. On `UserPromptSubmit`,
  `UserPromptExpansion`, and `SessionStart`, plain-text stdout is added as
  context Claude can see; on most other events stdout goes to the debug log
  only. A parsed object that fails schema validation is a non-blocking error
  on any exit code other than 2.
- Claim 14 (Section "Exit code 2"): exit 2 is the blocking exit code: "even a
  JSON `permissionDecision` of `\"allow\"` can't override it", i.e. "Exit 2's
  block is the one outcome JSON can't override" (Section "Exit code output").
  The per-event table (Section "Exit code 2 behavior per event") marks which
  events can block: yes for `PreToolUse`, `UserPromptSubmit`,
  `UserPromptExpansion`, `Stop`, `SubagentStop`, `TeammateIdle`,
  `TaskCreated`, `TaskCompleted`, `ConfigChange` (except `policy_settings`),
  `PostToolBatch`, `PreCompact`, `Elicitation`, `ElicitationResult`,
  `WorktreeCreate`; no for the rest, with `PostToolUse`/`PostToolUseFailure`
  showing stderr to Claude and several events showing stderr to the user
  only.
- Claim 15 (Section "Other exit codes"): exit 1 does not block: "Without
  valid JSON on stdout, Claude Code treats exit code 1 as a non-blocking
  error and proceeds with the action, even though 1 is the conventional Unix
  failure code." Conversely, valid JSON on stdout is honored on any exit code
  other than 2 for standard-decision events, and a hook that cannot start
  (bad path) lands in the non-blocking bucket, so "a mistyped path in
  `settings.json` leaves the gate silently disabled". Exception:
  `WorktreeCreate` fails on any nonzero exit.
- Claim 16 (Section "Timeouts" and "Exit code output"): a `command`, `http`,
  or `mcp_tool` hook that reaches its timeout is canceled and "renders no
  decision"; on `PreToolUse` the timed-out hook "doesn't block the tool
  call. The call continues through the normal permission flow". Agent SDK
  callback hooks are the opposite: exceeding timeout blocks the tool call
  (Section "Timeouts").
- Claim 17 (Section "HTTP response handling"): HTTP hooks map outcomes by
  status and body: 2xx with empty body equals exit 0 with no output; 2xx with
  a JSON object body is parsed against the same output schema; 2xx with any
  other body, non-2xx, connection failure, and timeout are all non-blocking
  errors. "HTTP hooks can't signal a blocking error through status codes
  alone."
- Claim 18 (Section "JSON output"): universal output fields include
  `continue` (default `true`; if `false`, "Claude stops processing entirely
  after the hook runs" and this "Takes precedence over any event-specific
  decision fields"), `stopReason`, `suppressOutput` (accepted but does
  nothing), `systemMessage`, and `terminalSequence` (restricted to OSC
  `0`/`1`/`2`/`9`/`99`/`777` and BEL).
  "Hook output strings, including `additionalContext`, `systemMessage`, and
  plain stdout, are capped at 10,000 characters", with overflow saved to a
  file plus preview and path.
- Claim 19 (Section "Add context for Claude"): `additionalContext` is wrapped
  "in a system reminder and inserts it into the conversation at the point
  where the hook fired"; injected text is saved in the transcript and replayed
  (not re-run) on `--continue`/`--resume`, so dynamic values go stale. The
  docs warn that imperative phrasing "can trigger Claude's prompt-injection
  defenses, which causes Claude to surface the text to you instead of
  treating it as context" (Section "Add context for Claude").
- Claim 20 (Section "PreToolUse decision control"): `PreToolUse` decisions
  use `hookSpecificOutput.permissionDecision` with four outcomes, `allow`,
  deny, `ask`, `defer`; "When multiple PreToolUse hooks return different
  decisions, precedence is `deny` > `defer` > `ask` > `allow`." `updatedInput`
  replaces the entire tool input object. "Deny and ask rules are still
  evaluated regardless of what the hook returns", and a hook `"ask"` forces a
  permission prompt even in auto mode (Section "PreToolUse decision
  control"). Blocking by exit 2 routes the same as `deny` with stderr as the
  reason (Section "Exit code 2").
- Claim 21 (Section "Defer a tool call for later"): `"defer"` is honored only
  in `-p` mode; the process exits with `stop_reason: "tool_deferred"` and a
  `deferred_tool_use` payload carrying `id`, `name`, `input`; resume re-fires
  `PreToolUse` for the same call; there is "no timeout or retry limit" and
  sessions persist subject to `cleanupPeriodDays`, which "delete[s] session
  files after 30 days by default". `defer` is ignored with a warning when the
  turn contains more than one tool call.
- Claim 22 (Section "PermissionRequest" and "PermissionRequest decision
  control"): `PermissionRequest` fires only when Claude Code is about to ask
  for permission; in sessions that cannot prompt (e.g. background subagents
  in headless mode), "if no hook returns a decision, it denies the tool
  call". The `decision` object supports `behavior` (`allow`/`deny`),
  `updatedInput`, `updatedPermissions`, `message`, and `interrupt`; deny and
  ask rules are still evaluated after a hook `allow`.
- Claim 23 (Section "Permission update entries"): hooks can modify permission
  state through entry types `addRules`, `replaceRules`, `removeRules`,
  `setMode`, `addDirectories`, `removeDirectories`, with destinations
  `session`, `localSettings`, `projectSettings`, `userSettings`. `setMode` to
  `bypassPermissions` only takes effect if the session was launched with
  bypass already available; otherwise it is a no-op.
- Claim 24 (Section "PostToolUse decision control"): `updatedToolOutput`
  replaces only what Claude sees; "The tool has already run by the time the
  hook fires" and "Telemetry such as OpenTelemetry tool spans and analytics
  events also captures the original output before the hook runs."
- Claim 25 (Section "Stop input"): Stop hooks receive `stop_hook_active` and
  "Claude Code overrides the hook and ends the turn after 8 consecutive
  blocks"; they also receive `last_assistant_message`, `background_tasks`,
  and `session_crons` (v2.1.145+). The `/goal` command is "a built-in
  shortcut for a session-scoped prompt-based Stop hook" (Section "Stop").
- Claim 26 (Section "UserPromptSubmit"): this event's default timeout is 30
  seconds for `command`, `http`, and `mcp_tool` types "Because this hook
  runs before every prompt and blocks model processing until it completes";
  on timeout the output is discarded and "The prompt still reaches Claude
  without that context", while an Agent SDK callback timeout blocks the
  prompt.
- Claim 27 (Section "PreToolUse"): `PreToolUse` fires only when Claude calls
  a tool; files referenced with `@` in a prompt are inserted "without any
  tool call", so no `PreToolUse` hook fires for them. The docs list the
  matchable built-in tools: `Bash`, `PowerShell`, `Edit`, `Write`, `Read`,
  `Glob`, `Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`,
  `ExitPlanMode`, plus MCP tool names (Section "PreToolUse").
- Claim 28 (Section "Common fields", timeout row): default timeouts per
  handler type are "600 for `command`, `http`, and `mcp_tool`; 30 for
  `prompt`; 60 for `agent`", and "`UserPromptSubmit` lowers the `command`,
  `http`, and `mcp_tool` default to 30, and `MessageDisplay` lowers it to
  10"; `SessionEnd` hooks share a 1.5-second budget, raised to match the
  highest per-hook timeout in settings files, "up to 60 seconds",
  overridable via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` (Section
  "SessionEnd").
- Claim 29 (Section "Run hooks in the background" and "How async hooks
  execute"): `"async": true` is command-hook only; async hooks "can't block
  or control Claude's behavior"; results (`additionalContext` and
  `systemMessage`) are delivered on the next conversation turn; in `-p` mode
  Claude Code "kills any async hook still running at teardown and finalizes
  it with outcome `cancelled`"; there is no deduplication across firings
  (Section "Limitations" under async hooks). `asyncRewake` wakes Claude on
  exit code 2 with stderr shown as a system reminder (Section "Command hook
  fields").
- Claim 30 (Section "Prompt-based hooks" and "How prompt-based hooks work"):
  prompt hooks "Send the hook input and your prompt to a Claude model, Haiku
  by default"; the required response schema is
  `{ "ok": true | false, "reason": ..., "impossible": true | false }` with
  per-event `ok: false` semantics (Section "Response schema"), and an
  optional `continueOnBlock` field.
- Claim 31 (Section "How agent hooks work"): agent hooks spawn a subagent
  that "can use tools like Read, Grep, and Glob" and return a structured
  `{ "ok": true/false }` decision "After up to 50 turns"; they are marked
  experimental with the guidance "For production workflows, prefer command
  hooks" (Section "Agent-based hooks").
- Claim 32 (Section "Hooks in skills and agents"): subagent frontmatter hooks
  run only while that subagent runs and a `Stop` hook there is converted to
  `SubagentStop`; skill frontmatter hooks register when the skill is invoked
  and keep running "for the rest of the session", with `once: true` for
  single runs (honored only in skill frontmatter, Section "Common fields").
- Claim 33 (Section "Workspace trust"): interactive sessions hold back hooks
  "from every settings file, including your own `~/.claude/settings.json`"
  until the workspace trust dialog is accepted, but "`-p` or SDK session:
  Claude Code never shows the dialog and treats the folder as trusted, so
  hooks committed in a repository's `.claude/settings.json` run in a folder
  you've never trusted". Project subagent frontmatter hooks follow a stricter
  rule and require an interactive trust acceptance (Section "Hooks in skills
  and agents").
- Claim 34 (Section "Security considerations"): "Command hooks execute shell
  commands with your full user permissions. They can modify, delete, or
  access any files your user account can access."
- Claim 35 (Section "SessionEnd"): the `reason` input values are `clear`,
  `resume`, `logout`, `prompt_input_exit`, `other` (`bypass_permissions_disabled`
  was removed in v2.1.234). `SessionEnd` hooks cannot block termination.
- Claim 36 (Section "PreCompact" and "PostCompact"): `PreCompact` can block
  compaction via exit 2 or `decision: "block"`; blocking proactive
  auto-compaction means "the conversation continues uncompacted", while
  blocking compaction triggered to recover from a context-limit error means
  "the underlying error surfaces and the current request fails".
  `PostCompact` input includes `compact_summary`, the generated summary
  (Section "PostCompact input").
- Claim 37 (Section "DirectoryAdded"): the hook runs after Claude Code
  refreshes sandbox and permission state "so sandboxed tools already see the
  new directory when your hook runs", and "Hook commands themselves run
  unsandboxed." Claude Code does not wait for this hook (600-second default
  timeout, background).

Interpretations offered by the docs themselves, carried forward as source
claims about intent: the repeated advice that hooks are not the enforcement
mechanism (Sections "Common fields", "Timeouts", "Other exit codes"), the
warning that hooks are a supply-chain surface in scripted sessions ("Before
you script `claude -p` over a repository you didn't write, review its
`.claude/` settings files", Section "Workspace trust"), and the positioning
of prompt/agent hooks as convenience verifiers with command hooks as the
production path (Section "Agent-based hooks").

## Evaluation and evidence

Docs source: no datasets, baselines, or experiment results. Character-exact
values the page states:

- Handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent` (Section
  "Hook handler fields").
- Timeouts: "600 for `command`, `http`, and `mcp_tool`; 30 for `prompt`; 60
  for `agent`"; "`UserPromptSubmit` lowers the `command`, `http`, and
  `mcp_tool` default to 30, and `MessageDisplay` lowers it to 10" (Section
  "Common fields"); SessionEnd "1.5-second budget" raised "up to 60 seconds"
  (Sections "Common fields", "SessionEnd"); async hooks "use the same
  10-minute default as sync hooks" (Section "Run hooks in the background").
- Output cap: "capped at 10,000 characters" (Section "JSON output"); the
  same limit middle-truncates `PostToolUseFailure` error strings with a
  `... [N characters truncated] ...` marker (Section "PostToolUseFailure
  input").
- Loop protection: "8 consecutive blocks" (Section "Stop input"); agent hooks
  run "up to 50 turns" (Section "How agent hooks work").
- Session retention for deferred tool calls: "30 days by default" via
  `cleanupPeriodDays` (Section "Defer a tool call for later").
- Notification timing: `permission_prompt` after the prompt "has waited about
  six seconds"; `idle_prompt` about "60 seconds ago" since Claude finished
  (Section "Notification").
- Permission mode vocabulary: `"default"`, `"plan"`, `"acceptEdits"`,
  `"auto"`, `"dontAsk"`, `"bypassPermissions"` (Section "Common input
  fields"), plus `manual` as a `setMode` alias requiring v2.1.200+ (Section
  "Permission update entries").
- Exit types and enumeration values: SessionEnd reasons `clear`, `resume`,
  `logout`, `prompt_input_exit`, `other` (Section "SessionEnd"); StopFailure
  error types `rate_limit`, `overloaded`, `authentication_failed`,
  `oauth_org_not_allowed`, `billing_error`, `invalid_request`,
  `model_not_found`, `server_error`, `max_output_tokens`, `unknown` (Section
  "StopFailure input"); PreCompact/PostCompact trigger values `manual`,
  `auto` (Section "PreCompact"); InstructionsLoaded load reasons
  `session_start`, `nested_traversal`, `path_glob_match`, `include`,
  `compact` (Section "InstructionsLoaded input"); effort levels `"low"`,
  `"medium"`, `"high"`, `"xhigh"`, `"max"` with Ultracode reporting as
  `"xhigh"` (Section "Common input fields").
- Version-gated semantics cited on the page (selection): comma matchers
  v2.1.191; hyphen exact-match v2.1.195; `prompt_id` v2.1.196; subagents
  background by default v2.1.198; `manual` mode alias v2.1.200; exit-2 with
  invalid JSON becomes blocking v2.1.214; worktree symlink screening
  v2.1.216; subagent frontmatter hooks require trust v2.1.218;
  `bypass_permissions_disabled` reason removed v2.1.234 (Sections "Matcher
  patterns", "Common input fields", "Exit code 2", "WorktreeCreate output",
  "Hooks in skills and agents", "SessionEnd").

Not located, with where I looked:

- The CLI version this page documents: `[CITATION NEEDED]`. Looked: snapshot
  header (`sources/docs/claudeCodeDocsHooks.md:1`) and all body text; the
  page carries no version banner, and the docs index pointer at the top only
  links `llms.txt`.
- Any statement of hook execution order or priority between parallel hooks:
  `[CITATION NEEDED]`. The page says only "All matching hooks run in
  parallel" plus one-line deduplication for identical handlers (Section "Hook
  handler fields"); no scheduling detail beyond that appears anywhere on it.
- The set or behavior of "Built-in Hooks": `[CITATION NEEDED]`; the `/hooks`
  menu lists the source label "registered internally by Claude Code" (Section
  "The /hooks menu") but no built-in hook is enumerated anywhere on the page.

## Limitations

- Closed-core, vendor-normative evidence. Every behavior on this page is
  implemented in Claude Code's closed-source core; there is no code at the
  pinned checkout to cross-check any of it (claude-code is registered as
  plugin surface only, "[CLOSED core boundary]",
  `sources/registry.yaml:259-270`; coverage limit at
  `sources/registry.yaml:55`). All claims here are contract-level evidence
  from the vendor, not implementation evidence, and must be hedged as such in
  the report.
- Floating docs. The docs site is not pinned and "can drift from the pinned
  commits" (`sources/registry.yaml:57`). The snapshot fixes this text as of
  2026-08-20, but the live page may already describe different behavior, and
  nothing in this note can be tied to the pinned claude-code commit c3d2e35
  (the repo contains hook examples, e.g.
  `examples/hooks/bash_command_validator_example.py`, which the page itself
  links in Section "Decision control", but no hook runtime).
- Version churn inside one page. The page documents behavior changes across
  roughly two dozen point releases (v2.1.145 through v2.1.234 referenced) and
  states no target version of its own. A claim like "exit 2 with invalid
  JSON blocks" is true only from v2.1.214 onward (Section "Exit code 2"), so
  each behavior is conditional on client version, and the page's aggregate
  picture matches no single release exactly.
- Fail-open defaults are a design weakness the docs themselves document: exit
  1 does not block (Section "Other exit codes"); a timed-out
  command/http/mcp_tool hook leaves the tool call to the normal permission
  flow (Section "Timeouts"); a non-starting hook fails open and "leaves the
  gate silently disabled" (Section "Other exit codes"); the `if` filter fails
  open on parse failure (Section "Common fields"). A hook-based policy is
  therefore best-effort by construction unless paired with the separate
  permission system, whose internals are documented elsewhere.
- Control surface is narrow on many events: of 31 events, only 14 support any
  blocking at all via exit 2 (Section "Exit code 2 behavior per event"), and
  the decision-control table's "None" row assigns no decision control to 9
  events (`WorktreeRemove`, `Notification`, `SessionEnd`, `PostCompact`,
  `InstructionsLoaded`, `StopFailure`, `CwdChanged`, `DirectoryAdded`,
  `FileChanged`, Section "Decision control"). Async hooks and `MessageDisplay`
  are explicitly side-effect or display only (Sections "Run hooks in the
  background", "MessageDisplay output").
- Security asymmetry documented but unresolved: in `-p` and SDK sessions,
  repository hooks run without a trust dialog (Section "Workspace trust"),
  and command hooks carry full user permissions (Section "Security
  considerations"). Managed-settings controls (`allowManagedHooksOnly`,
  HTTP allowlists) mitigate organizational exposure but are admin-gated
  (Section "Hook locations").
- LLM-judged hooks add nondeterminism: prompt and agent hook decisions
  depend on a model's JSON response, agent hooks are explicitly experimental,
  and `ok: false` semantics vary per event (Sections "Response schema",
  "Agent-based hooks").
- Gate flag (`study.yaml` depth: full): this note fully covers the registered
  hooks page from a primary snapshot, so it does not itself block a
  literature-gate verdict. The residual source-level gap is structural: the
  Claude Code core that executes these hooks (turn loop, permission
  enforcement, compaction engine) remains closed and is only observable
  through other registered notes (plugin surface, other Claude Code docs
  pages, hedged teardowns), not through this one.

## Relevance to the brief

My inference, separated from the anchored claims above.

- RQ4 (what the closed core reveals): this is one of the richest official
  windows into Claude Code's internal architecture, because the hook catalog
  effectively enumerates the lifecycle the harness exposes for interception.
  The event set reveals components the docs elsewhere only imply: an agentic
  loop with parallel tool batches (`PostToolBatch`), a permission subsystem
  with a classifier-based auto mode (`PermissionRequest`, `PermissionDenied`
  with "Blocked by classifier", Sections "PermissionRequest",
  "PermissionDenied"), a context-compaction mechanism with manual/auto
  triggers and an accessible `compact_summary` (Sections "PreCompact",
  "PostCompact"), subagent transcripts stored in nested `subagents/` folders
  (Section "SubagentStop input"), session forking (`fork` sources, Section
  "SessionStart"), background tasks and session crons (Section "Stop input"),
  and an async transcript write path that can lag memory (Section "Common
  input fields"). For the report, hooks are best framed as an observability
  instrument for the otherwise closed loop.
- RQ2 (what components make a harness): fills the Claude Code cell of the
  extensibility dimension. Claude Code's extension model is lifecycle-event
  driven (31 events, five handler types) and is woven into skills, subagents,
  plugins, and managed policy, which is a different structural choice than a
  pure plugin-API model. The comparison matrix can draw on: event catalog,
  matcher semantics, handler type matrix, JSON I/O contract, exit-code
  contract, and the fail-open guarantee model.
- RQ3 (capability vs safety): directly relevant. Hooks run with full user
  permissions (Section "Security considerations"), can rewrite tool inputs
  and outputs (Sections "PreToolUse decision control", "PostToolUse decision
  control"), can grant permissions programmatically (Section "Permission
  update entries"), and can be locked down by enterprise policy
  (`allowManagedHooksOnly`, HTTP allowlists, Section "Hook locations"). The
  docs' own positioning of hooks as non-enforcing complements to the
  permission system is the key hedged takeaway: capability is high, safety
  guarantees are delegated.
- RQ1 (genuine differences): usable against the Codex and OpenCode notes once
  their extensibility entries are summarized; candidate contrast axes are
  event granularity (per-tool-call plus batch boundaries here), the
  LLM-as-judge hook types (`prompt`, `agent`), the exit-code-plus-JSON dual
  contract, and managed-settings control for organizations.
- Left open for other sources: the permission system's own rules and modes
  live on the registered permissions page (claudeCodeDocsPermissions);
  settings precedence detail lives on the settings page (linked, not
  captured here); the actual hook runtime implementation is closed.

## Quotables for the report

Short excerpts verified against the snapshot, with suggested framing.

- "Hooks are user-defined shell commands, HTTP endpoints, or LLM prompts that
  execute automatically at specific points in Claude Code's lifecycle."
  (Section "Hooks reference"). Framing: Claude Code formalizes its lifecycle
  as an interception surface shared across terminal, IDE, desktop, and web
  clients.
- "Events fall into three cadences" (Section "Hook lifecycle"): once per
  session, once per turn, and per tool call inside the agentic loop.
  Framing: the cadence taxonomy is a compact description of the turn-loop
  seams a harness exposes.
- "Exit 2's block is the one outcome JSON can't override." (Section "Exit
  code output"). Framing: the I/O contract is a dual channel, exit codes for
  hard stops, JSON for structured decisions.
- "The hook can deny the call, but staying silent doesn't approve it."
  (Section "How a hook resolves"). Framing: hooks fail closed for denial and
  open for approval.
- "Without valid JSON on stdout, Claude Code treats exit code 1 as a
  non-blocking error and proceeds with the action, even though 1 is the
  conventional Unix failure code." (Section "Other exit codes"). Framing:
  hook-based policy is best-effort by construction.
- "A timed-out `command`, `http`, or `mcp_tool` hook doesn't block the tool
  call. The call continues through the normal permission flow, so don't count
  on a stalled hook to act as a gate." (Section "Timeouts"). Framing: same
  fail-open guarantee; enforcement is delegated to the permission system.
- "When multiple PreToolUse hooks return different decisions, precedence is
  `deny` > `defer` > `ask` > `allow`." (Section "PreToolUse decision
  control"). Framing: conflict resolution is explicitly deny-preferring, the
  one safety-favoring ordering in the decision contract.
- "Command hooks execute shell commands with your full user permissions."
  (Section "Security considerations") and, for scripted sessions, "hooks
  committed in a repository's `.claude/settings.json` run in a folder you've
  never trusted" (Section "Workspace trust"). Framing: the extension surface
  doubles as a supply-chain surface, mitigated for organizations by
  `allowManagedHooksOnly` and HTTP hook allowlists (Section "Hook locations").
- "After up to 50 turns, the subagent returns a structured
  `{ \"ok\": true/false }` decision" (Section "How agent hooks work").
  Framing: Claude Code uniquely offers LLM-executing-as-verifier hooks,
  marked experimental, alongside deterministic command hooks.
