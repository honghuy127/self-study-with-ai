---
# Note for the official Claude Code sub-agents docs page. The summarizer read
# the retained snapshot directly: sources/docs/claudeCodeDocsSubagents.md
# (snapshot header records https://code.claude.com/docs/en/sub-agents.md
# accessed 2026-08-20). Every claim anchors to a section heading of that
# snapshot page; quoted values are character-exact from it. Where a value is
# absent from the page, the note says [CITATION NEEDED] and where it looked.
source_key: "claudeCodeDocsSubagents"
read_date: "2026-08-20"           # snapshot access date per its header; note written same day
confidence: "high"                # full snapshot read directly, line by line
relevance: "3"                    # central to RQ4 and to the Claude Code extensibility dimension
---

# Notes: Create custom subagents

## Source identification

- Key: claudeCodeDocsSubagents
- Authors, year, venue: Anthropic, 2026, Claude Code official docs
  (code.claude.com/docs/en/sub-agents)
- Tier: docs
- URL / DOI: https://docs.claude.com/en/docs/claude-code/sub-agents (registry
  URL; no DOI). Canonical fetch endpoint recorded in the snapshot header:
  `https://code.claude.com/docs/en/sub-agents.md` accessed 2026-08-20
  (`sources/docs/claudeCodeDocsSubagents.md:1`).
- Snapshot: `sources/docs/claudeCodeDocsSubagents.md` (1284 lines, full page
  including frontmatter tables, code examples, and version-gated behavior
  notes). Section anchors below quote the page's own headings.

## Problem and motivation

The page documents Claude Code's subagent machinery: specialized AI
assistants that run in isolated context windows and are delegated to by the
main conversation. The stated motivations (Section "Create custom subagents",
intro): use a subagent "when a side task would flood your main conversation
with search results, logs, or file contents you won't reference again: the
subagent does that work in its own context and returns only the summary", and
define a custom one "when you keep spawning the same kind of worker with the
same instructions."

The page lists five benefits (Section "Create custom subagents", bullets
"Subagents help you"):

- "Preserve context" by keeping exploration and implementation out of the
  main conversation
- "Enforce constraints" by limiting which tools a subagent can use
- "Reuse configurations" across projects with user-level subagents
- "Specialize behavior" with focused system prompts for specific domains
- "Control costs" by routing tasks to faster, cheaper models like Haiku

Delegation is description-driven: "Claude uses each subagent's description to
decide when to delegate tasks" (Section "Create custom subagents"). A
boundary note states subagents work within a single session; parallel
independent sessions, cross-session messaging, and agent teams are separate
features (Section "Create custom subagents", Note).

## Method or core idea

The mechanism, as documented. Anchors throughout are snapshot section
headings.

**Built-in subagents** (Section "Built-in subagents"). Claude Code ships
built-ins that Claude uses automatically; "Each inherits the parent
conversation's permissions; most run with a restricted tool set." Explore and
Plan are exceptional: they "skip your CLAUDE.md files and the parent
session's git status to keep research fast and inexpensive. Every other
built-in and custom subagent loads both."

- Explore: "A fast, read-only agent optimized for searching and analyzing
  codebases." Write and Edit are denied. As of v2.1.198 it inherits the main
  conversation's model "instead of always running on Haiku"; on the Claude
  API "the inherited model is capped at Opus", while on any other provider
  (Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, Claude Platform
  on AWS) it "inherits the main conversation's model directly". A user or
  project subagent named `Explore` overrides the built-in and keeps its own
  `model` field. Claude specifies a thoroughness level when invoking it:
  "quick", "medium", or "very thorough" (Section "Built-in subagents",
  Explore tab).
- Plan: a research agent used during plan mode; inherits the main model;
  read-only, Write and Edit denied. In plan mode it keeps exploration output
  "in a separate context window while the main conversation remains
  read-only" (Section "Built-in subagents", Plan tab).
- General-purpose: "A capable agent for complex, multi-step tasks that
  require both exploration and action"; inherits the main model; gets "every
  tool available to subagents"; used "when the task requires both exploration
  and modification, complex reasoning to interpret results, or multiple
  dependent steps" (Section "Built-in subagents", General-purpose tab).
- Other helpers table: `claude` (Model: Inherits; catch-all with every tool
  available to subagents; default agent for a dispatched background session),
  `statusline-setup` (Model: Sonnet; runs on `/statusline`),
  `claude-code-guide` (Model: Haiku; answers questions about Claude Code
  features) (Section "Built-in subagents", Other tab).
- Restriction paths: `permissions.deny` with `Agent(subagent-name)`; denying
  the `Agent` tool itself blocks all delegation;
  `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` removes only built-in Explore
  and Plan (requires v2.1.198 or later);
  `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` removes all built-ins in
  non-interactive mode and the Agent SDK (Section "Built-in subagents",
  bullet list). An Agent tool call that omits `subagent_type` fails with
  `subagent_type is required` "when the session has no `general-purpose`
  subagent to fall back on" (Section "Built-in subagents").

**Definition format, scope, and precedence.** Subagents are Markdown files
with YAML frontmatter plus a system-prompt body (Sections "Quickstart",
"Write subagent files"). Five definition locations with a fixed priority
order (Section "Choose the subagent scope", table):

1. Managed settings, organization-wide, priority "1 (highest)"
2. `--agents` CLI flag, current session, priority 2
3. `.claude/agents/`, current project, priority 3
4. `~/.claude/agents/`, all your projects, priority 4
5. Plugin's `agents/` directory, "where plugin is enabled", priority
   "5 (lowest)"

"When multiple subagents share the same name, Claude Code uses the one from
the higher-priority location." Project subagents are discovered by walking up
from the current working directory; since v2.1.178 the definition closest to
the working directory wins among nested directories. Both standard scopes are
scanned recursively and identity comes only from the `name` frontmatter
field; two files under the same `.claude/agents/` directory with the same
name lead Claude Code to load "only one of them, chosen by filesystem read
order rather than a documented precedence". Plugin `agents/` subfolders
become part of a scoped identifier: `agents/review/security.md` in plugin
`my-plugin` registers as `my-plugin:review:security`. `--agents` accepts JSON
(definitions "exist only for that session and aren't saved to disk") with a
`prompt` field plus the frontmatter fields `description`, `tools`,
`disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`,
`maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, and
`isolation`. For security, "plugin subagents don't support the `hooks`,
`mcpServers`, or `permissionMode` frontmatter fields. These fields are
ignored when loading agents from a plugin" (Section "Choose the subagent
scope").

**Frontmatter fields** (Section "Supported frontmatter fields" table; "Only
`name` and `description` are required"):

- `name` (required): unique identifier, lowercase letters and hyphens; hooks
  receive it as `agent_type`; the filename doesn't have to match; `:` is
  reserved for plugin-scoped identifiers and since v2.1.218 names containing
  it are not loaded.
- `description` (required): when Claude should delegate here.
- `tools`: allowlist; "Inherits every tool available to subagents if
  omitted"; if no entry resolves to a tool the subagent usually fails to
  launch with an error naming the entries.
- `disallowedTools`: denylist, "removed from inherited or specified list".
- `model`: `sonnet`, `opus`, `haiku`, `fable`, a full model ID (example
  given: `claude-opus-5`), or `inherit`; "Defaults to `inherit`".
- `permissionMode`: `default`, `acceptEdits`, `auto`, `dontAsk`,
  `bypassPermissions`, `plan`, or `manual` "as an alias for `default`"
  (requires v2.1.200 or later); ignored for plugin subagents.
- `maxTurns`: "Maximum number of agentic turns before the subagent stops".
- `skills`: skills preloaded "into the subagent's context at startup. The
  full skill content is injected, not only the description"; unlisted skills
  remain invokable through the Skill tool.
- `mcpServers`: server names referencing already-configured servers, or
  inline definitions; ignored for plugin subagents.
- `hooks`: lifecycle hooks scoped to this subagent; ignored for plugin
  subagents.
- `memory`: persistent memory scope `user`, `project`, or `local`; "Enables
  cross-session learning".
- `background`: `true` keeps the subagent in the background even when Claude
  asks for the foreground.
- `effort`: `low`, `medium`, `high`, `xhigh`, `max`; overrides session
  effort; "available levels depend on the model".
- `isolation`: `worktree` runs the subagent in a temporary git worktree
  "branched by default from your default branch rather than the parent
  session's `HEAD`"; cleaned up automatically if no changes are made.
- `color`: display color; accepts `red`, `blue`, `green`, `yellow`,
  `purple`, `orange`, `pink`, or `cyan`.
- `initialPrompt`: auto-submitted as the first user turn when the agent runs
  as the main session agent via `--agent` or the `agent` setting.

A subagent's body "becomes the system prompt"; subagents "receive only this
system prompt plus basic environment details like the working directory, not
the full Claude Code system prompt" (Section "Write subagent files"). A
subagent starts in the main conversation's current working directory; `cd`
does not persist between Bash or PowerShell calls and does not affect the
main conversation (Section "Write subagent files"). `isolation: worktree`
commands are confined by a working-directory check covering the whole
repository (since v2.1.210, plus the main checkout a linked worktree came
from) plus, for Bash, command-content checks that block git redirects to the
main checkout and refuse unverifiable command shapes; PowerShell gets only
the working-directory check (Section "Write subagent files").

**Model resolution** (Section "Choose a model"): resolution order is
(1) `CLAUDE_CODE_SUBAGENT_MODEL` env var, (2) the per-invocation `model`
parameter, (3) the subagent definition's `model` frontmatter, (4) the main
conversation's model. Since v2.1.196, setting the env var to `inherit` is the
same as leaving it unset. Values are checked against the organization's
`availableModels` allowlist; a blocked family alias substitutes "the newest
version of that family the allowlist permits"; any other blocked value falls
back to the inherited model. Since v2.1.198 subagents also inherit the main
conversation's extended thinking configuration; "There is no per-subagent
thinking setting."

**Tool filtering** (Section "Available tools"). Subagents inherit built-in
and MCP tools from the main conversation, narrowed by two filters:

- Filter one removes these tools from every subagent, "even when listed in
  the `tools` field": `Agent` (only when the subagent is at the depth limit;
  in a fork it stays listed but errors instead of spawning),
  `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode`
  ("unless the subagent's `permissionMode` is `plan`"), `ScheduleWakeup`,
  `TaskOutput`, `WaitForMcpServers`, `Workflow`.
- Filter two applies to background subagents: they "keep every MCP tool but
  only these built-in tools: `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`,
  `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`,
  `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`,
  `TaskStop`, `SendMessage`, and `Artifact`", and Claude Code "removes every
  other built-in tool" whether inherited or listed in `tools`, "so the same
  definition can resolve to different tools in the foreground and the
  background".
- Forks "skip both filters and receive the main conversation's exact tool
  pool" (Section "Available tools").
- `disallowedTools` "is applied first, then `tools` is resolved against the
  remaining pool"; a tool in both is removed. Zero resolving tools means
  Claude Code "usually refuses to launch the subagent" (before v2.1.208 it
  launched with no tools). Both fields accept MCP server-level patterns:
  `mcp__<server>` or `mcp__<server>__*`, and `mcp__*` in `disallowedTools`
  removes every MCP tool (Section "Available tools").
- `Agent(agent_type)` allowlist syntax in `tools` applies only to an agent
  running as the main thread via `claude --agent`; "In a subagent definition,
  listing `Agent` in `tools` lets that subagent spawn subagents of its own
  while the depth limit allows it, but any type list inside the parentheses
  is ignored." The Task tool was renamed to Agent "In version 2.1.63";
  `Task(...)` references still work as aliases (Sections "Available tools",
  "Restrict which subagents can be spawned").

**MCP scoping** (Section "Scope MCP servers to a subagent"): `mcpServers`
entries are string references (sharing the parent session's connection) or
inline definitions (connected at subagent start, disconnected at finish),
using the `.mcp.json` schema with `stdio`, `http`, `sse`, and `ws` types.
Since v2.1.153 the main session's MCP restrictions also cover frontmatter
servers: `--strict-mcp-config`, `--bare`, enterprise managed MCP
configuration, and `allowedMcpServers`/`deniedMcpServers` policies; blocked
servers are skipped with a warning, except `--strict-mcp-config` does not
filter inline servers passed via `--agents` or the SDK `agents` option
("since those are explicit caller input").

**Permission modes** (Section "Permission modes"). Modes: `default` ("Manual
mode: prompts for permission"), `acceptEdits` (auto-accept edits in the
working directory or `additionalDirectories`), `auto` ("a background
classifier reviews commands and protected-directory writes"), `dontAsk`
(auto-deny prompts; explicitly allowed tools still work), `bypassPermissions`
("Skip permission prompts"), `plan` ("read-only exploration"). If unset, the
subagent inherits the main conversation's mode, "which starts as auto mode on
Pro, Max, and Team plans unless your settings or your organization change
it." Precedence: "If the parent uses `bypassPermissions` or `acceptEdits`,
this takes precedence and can't be overridden. If the parent uses auto mode,
the subagent inherits auto mode and any `permissionMode` in its frontmatter
is ignored." When bypass is disabled by
`permissions.disableBypassPermissionsMode`, frontmatter
`permissionMode: bypassPermissions` is ignored (since v2.1.223). The
`bypassPermissions` warning lists writes the mode still permits without
approval: "including writes to `.git`, `.config/git`, `.claude`, `.vscode`,
`.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, and `.mvn`".

**Persistent memory** (Section "Enable persistent memory"): `memory` scopes
and locations (table): `user` at `~/.claude/agent-memory/<name-of-agent>/`;
`project` at `.claude/agent-memory/<name-of-agent>/`; `local` at
`.claude/agent-memory-local/<name-of-agent>/`. It is part of auto memory:
turning auto memory off (`autoMemoryEnabled` setting or
`CLAUDE_CODE_DISABLE_AUTO_MEMORY`) makes the `memory` field "have no effect".
When enabled: the system prompt includes memory instructions and "the first
200 lines or 25KB of `MEMORY.md` in the memory directory, whichever comes
first"; Read, Write, and Edit "are automatically enabled".

**Hooks** (Section "Define hooks for subagents"): two configuration paths,
frontmatter hooks that run only while that subagent is active, and
`settings.json` hooks that "fire for the subagent's tool calls the same way
they do in the main conversation", plus `SubagentStart` and `SubagentStop`
events (matcher input: agent type name). Frontmatter `Stop` hooks are
"automatically converted to `SubagentStop` events" when invoked as a
subagent. Project-level subagents' frontmatter hooks require accepting the
workspace trust dialog; until trusted, "the subagent still runs, but Claude
Code skips its frontmatter hooks" (stricter since v2.1.218).

**Invocation** (Sections "Understand automatic delegation", "Invoke
subagents explicitly"): automatic delegation keys off the request, the
`description` field, and current context; include phrases like "use
proactively" in the description to encourage it. Three explicit patterns:
natural language, @-mention ("guarantees the subagent runs for one task"),
and session-wide via `--agent <name>` or the `agent` setting (the subagent's
system prompt then "replaces the default Claude Code system prompt entirely",
while `CLAUDE.md` files still load; the choice persists across resume).
`permissions.deny` entries like `"Agent(Explore)"` or the CLI flag
`--disallowedTools "Agent(Explore)"` disable specific subagents (Section
"Disable specific subagents").

## Key claims with anchors

Source claims; anchors are snapshot section headings.

- Claim 1 (Section "Built-in subagents"): built-ins inherit the parent
  conversation's permissions; Explore and Plan additionally skip CLAUDE.md
  files and the parent session's git status, and "Explore and Plan are the
  only subagents that omit CLAUDE.md and git status. There is no frontmatter
  field or per-agent setting to change which agents skip them." (Section
  "What loads at startup").
- Claim 2 (Section "Built-in subagents", Other tab): additional built-ins
  beyond Explore, Plan, and general-purpose are `claude` (Inherits),
  `statusline-setup` (Sonnet), and `claude-code-guide` (Haiku).
- Claim 3 (Section "Choose the subagent scope"): five definition scopes,
  priorities 1 (managed settings) through 5 (plugin `agents/`); same-name
  conflicts resolve to the higher-priority location; same-directory
  duplicates resolve by filesystem read order without documented precedence.
- Claim 4 (Section "Supported frontmatter fields"): only `name` and
  `description` are required; the full field set is as in Method above,
  including `maxTurns` (turn cap), `background` (force background), `effort`
  (`low`, `medium`, `high`, `xhigh`, `max`), and `isolation: worktree`.
- Claim 5 (Section "Choose a model"): resolution order is
  `CLAUDE_CODE_SUBAGENT_MODEL`, then per-invocation `model` parameter, then
  frontmatter `model`, then the main conversation's model; subagents inherit
  the session's extended thinking configuration since v2.1.198.
- Claim 6 (Section "Available tools"): two sequential filters; filter one
  removes the nine named tools from every subagent; filter two reduces
  background subagents (the default) to the 19 named built-in tools while
  keeping every MCP tool; forks bypass both filters; `disallowedTools` is
  applied before `tools`; `mcp__<server>`, `mcp__<server>__*`, and `mcp__*`
  patterns operate server-wide.
- Claim 7 (Section "Permission modes"): parent `bypassPermissions` or
  `acceptEdits` take precedence and can't be overridden; a parent in auto
  mode forces the subagent into auto mode with its frontmatter
  `permissionMode` ignored.
- Claim 8 (Section "Run subagents in foreground or background"): foreground
  subagents block the main conversation; background subagents run
  concurrently and surface permission prompts in the main session (before
  v2.1.186 they auto-denied prompting tool calls). Choice follows a fixed
  precedence: teammate-spawned runs foreground; `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`
  forces foreground; fork mode on runs everything Claude spawns in the
  background; fork mode off defaults to background with foreground when
  Claude needs the result.
- Claim 9 (Section "Let subagents spawn their own subagents"): default depth
  limit is "up to three layers below the main conversation"; at the limit
  the `Agent` tool is withheld, except forks keep it listed and it errors;
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the limit, `1` turns
  nesting off. Earlier defaults: five unchangeable layers (v2.1.172 through
  v2.1.216), one (v2.1.217 through v2.1.218), three from v2.1.219.
- Claim 10 (Section "Concurrent subagent limit"): "when 20 subagents are
  running in a session, spawning another with the Agent tool fails with
  `Concurrent subagent limit reached`"; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`
  changes the limit; "Sessions with ultracode active are exempt"; requires
  v2.1.217 or later; resuming a finished subagent takes a fresh slot without
  checking the limit, so resumes can push past it.
- Claim 11 (Section "What loads at startup"): a non-fork subagent's initial
  context contains exactly: its own system prompt plus appended environment
  details (not the full Claude Code system prompt), Claude's delegation task
  message, every CLAUDE.md level the main conversation loads (Explore and
  Plan skip), a git status snapshot "taken at the start of the parent
  session" (absent when not a Git repo or when `includeGitInstructions` is
  `false`; Explore and Plan skip it regardless), full content of skills named
  in the `skills` field (built-ins preload none), and since v2.1.206 a
  sibling roster listing `main` and every other named agent (only when the
  subagent has `SendMessage` and at least one other agent has a name;
  snapshot at subagent start). Output style, the parent's auto memory, and
  the parent's context window size never reach a non-fork subagent ("a
  subagent's context window is sized by its own model, not the parent's").
- Claim 12 (Section "Resume subagents"): each invocation creates a new
  instance; resumed subagents "retain their full conversation history,
  including all previous tool calls, results, and reasoning"; Explore and
  Plan "are one-shot and return no agent ID, so they can't be resumed";
  resumption uses the `SendMessage` tool with the agent's ID or name; a
  completed subagent auto-resumes in the background on `SendMessage`, while a
  user-stopped subagent does not auto-resume (since v2.1.191). Transcripts
  live at `~/.claude/projects/{project}/{sessionId}/subagents/` as
  `agent-{agentId}.jsonl`, survive main-conversation compaction, persist
  within the session across restarts, and are deleted after
  `cleanupPeriodDays`, "30 days by default".
- Claim 13 (Section "Auto-compaction"): subagents support automatic
  compaction "using the same logic as the main conversation";
  `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` applies to subagents; compaction events
  are logged in transcript files as `"type": "system"`,
  `"subtype": "compact_boundary"` with `compactMetadata` containing
  `"trigger": "auto"` and a `preTokens` count.
- Claim 14 (Sections "Fork the current conversation", "How forks differ from
  other subagents", "Turn fork mode on or off"): a fork "inherits the entire
  conversation so far instead of starting fresh" ("drops the input
  isolation"), while its tool calls stay out of the main conversation and
  "only its final result comes back". Started via `/subtask` (requires
  v2.1.212; on v2.1.161 through v2.1.211 the command is `/fork`) or by Claude
  requesting the `fork` subagent type when fork mode is on. Fork mode is on
  by default in interactive sessions (requires v2.1.232), off by default in
  non-interactive `-p` mode and the Agent SDK; `CLAUDE_CODE_FORK_SUBAGENT`
  overrides (`1` on everywhere, `0` off everywhere). A fork shares the
  parent's prompt cache, and "A fork can't spawn further forks."
- Claim 15 (Section "Subagent output scanning", requires v2.1.210): every
  subagent's final report is scanned before Claude reads it; the scan "never
  removes or rewords anything" but inserts backslashes into text imitating
  Claude Code output (`<system-reminder>` tags, lines starting `Human:` or
  `Assistant:`) and prepends a marker line starting with
  `[harness: subagent output matched instruction-shaped pattern(s):` when the
  report imitates such tags or mentions permission settings. It "isn't a
  substitute for restricting what a subagent can reach".
- Claim 16 (Section "API errors in subagents", since v2.1.199):
  API-error-terminated subagents report failure rather than returning error
  text as findings; foreground subagents return partial text output with a
  cut-off note, or fail with `Agent terminated early due to an API error`;
  background subagents are marked failed with the API error and last output
  preserved.

Interpretation by the page itself (source framing, not mechanism): the page
positions subagents primarily as a context-management device ("Preserve
context", "Control costs") and a constraint-enforcement device ("Enforce
constraints"), and recommends the main conversation for iterative work and
subagents for verbose-output, self-contained, or restriction-bearing tasks
(Section "Choose between subagents and main conversation"). It states the
fork tradeoff explicitly: giving up input isolation to reuse context and
prompt cache.

My inference (flagged, not source claims): see Relevance to the brief. The
page does not reproduce the built-in system prompts, only that "Built-in
agents have predefined prompts" (Section "What loads at startup"), so
built-in prompt content remains closed.

## Evaluation and evidence

Docs source: no datasets, baselines, or benchmark metrics. Character-exact
constants the page states (verified against the snapshot):

- Built-in names: `Explore`, `Plan`, `general-purpose` (tabs); `claude`,
  `statusline-setup`, `claude-code-guide` (Other tab table).
- Explore thoroughness levels: `quick`, `medium`, `very thorough` (Explore
  tab).
- Scope priorities: `1 (highest)` managed settings; 2 `--agents` CLI flag; 3
  `.claude/agents/`; 4 `~/.claude/agents/`; `5 (lowest)` plugin `agents/`
  directory (Section "Choose the subagent scope").
- Filter-one list: `Agent`, `AskUserQuestion`, `EndConversation`,
  `EnterPlanMode`, `ExitPlanMode`, `ScheduleWakeup`, `TaskOutput`,
  `WaitForMcpServers`, `Workflow` (Section "Available tools").
- Filter-two background built-in list, 19 tools as listed: `Read`, `Grep`,
  `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`,
  `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`,
  `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`, `Artifact` (Section
  "Available tools").
- `permissionMode` vocabulary: `default`, `acceptEdits`, `auto`, `dontAsk`,
  `bypassPermissions`, `plan`, plus `manual` alias (Section "Permission
  modes"; frontmatter table).
- Model values: `sonnet`, `opus`, `haiku`, `fable`, a full model ID such as
  `claude-opus-5`; default `inherit` (Section "Choose a model").
- Depth: "up to three layers below the main conversation"; override
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (example value `"2"`; `1` turns
  nesting off). History: five layers v2.1.172 through v2.1.216
  (unchangeable), one v2.1.217 through v2.1.218, three from v2.1.219
  (Section "Let subagents spawn their own subagents").
- Concurrency: default 20 running subagents; error string `Concurrent
  subagent limit reached`; override `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`;
  ultracode exempt; requires v2.1.217 or later (Section "Concurrent
  subagent limit").
- Memory window: "the first 200 lines or 25KB of `MEMORY.md` in the memory
  directory, whichever comes first" (Section "Enable persistent memory").
- Retention: transcripts deleted after `cleanupPeriodDays`, "30 days by
  default" (Section "Resume subagents").
- Compaction example: `"preTokens": 167189` (Section "Auto-compaction"; an
  illustrative transcript event, not a measured threshold).
- Version gates cited by the page itself, collected across all sections:
  v2.1.63 (Task renamed to Agent), v2.1.153, v2.1.161, v2.1.172, v2.1.178,
  v2.1.186, v2.1.191, v2.1.195, v2.1.196, v2.1.197, v2.1.198, v2.1.199,
  v2.1.200, v2.1.203, v2.1.205, v2.1.206, v2.1.208, v2.1.210, v2.1.211,
  v2.1.212, v2.1.216, v2.1.217, v2.1.218, v2.1.219, v2.1.222, v2.1.223,
  v2.1.232.

Not located, with where I looked (all `[CITATION NEEDED]`):

- Any numeric trigger threshold for subagent auto-compaction: the page says
  compaction "triggers under the same conditions" as the main conversation
  and defers the override's timing to the env-vars page (Section
  "Auto-compaction"). Looked: full snapshot; only the example `preTokens`
  value exists.
- Any quantitative measurement of context savings from delegation: the page
  defers "the context savings in practice" to a separate context-window
  visualization page (intro). Looked: full snapshot; no numbers.
- The system prompts of built-in subagents: stated to exist but not
  reproduced (Section "What loads at startup").
- The `maxTurns` default when omitted: the frontmatter table describes the
  cap but gives no default. Looked: Section "Supported frontmatter fields".

## Limitations

- Floating docs, not pinned: the page is a live docs site captured on
  2026-08-20 and its content is heavily version-gated ("As of v2.1.X" and
  "Before v2.1.X" notes in nearly every section), so it describes a moving
  release train rather than any pinned commit. The registry's coverage
  limits record that docs sites "can drift from the pinned commits"
  (`sources/registry.yaml:57`). Concretely, the pinned claude-code checkout
  (commit c3d2e35e5540, `sources/repos.yaml:5-11`) carries `CHANGELOG.md` up
  through `## 2.1.235` (`CHANGELOG.md:3` @ c3d2e35e5540), whose entries
  include a subagent-related fix ("Fixed the Agent tool advertising a
  general-purpose default in sessions where that agent is unavailable",
  `CHANGELOG.md:10` @ c3d2e35e5540) that postdates the snapshot page's newest
  version-gated note (v2.1.232, Section "Turn fork mode on or off"). The
  snapshot therefore lags the pinned checkout's documented behavior by at
  least that entry.
- No code cross-check possible: the pinned claude-code checkout contains no
  product code (root listing at commit c3d2e35e5540 shows only the
  plugin/example/script/docs surface, no CLI bundle or package manifest),
  matching the claudeCodePluginSurface registry entry's record that the
  agent core is closed source. Every mechanism claim here is an official
  statement verified against this page, not against an implementation.
- Cross-page dependencies: load-bearing details are deferred to other doc
  pages outside this snapshot: worktree redirect vectors and shape rules
  (/docs/en/worktrees, Section "Write subagent files"), the auto-mode
  classifier's rules (Section "Permission modes"), hook input schema and
  exit-code semantics (Section "Conditional rules with hooks"),
  `availableModels` substitution rules (Section "Choose a model"), and
  `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` timing (Section "Auto-compaction").
  Claims touching those areas are at the level of "this page says it defers
  there".
- Quantitative evidence is thin: no benchmark, metric, or threshold is given
  for context savings or compaction triggers; the only telemetry-looking
  number (`"preTokens": 167189`) is a fabricated transcript example. The
  concurrency default (20) and depth default (3) are stated without
  rationale.
- Conditional portability: several behaviors hold only under stated
  conditions a summary can lose: the Explore model cap applies "On the
  Claude API" only (Explore tab); the auto-mode default applies to "Pro,
  Max, and Team plans" (Section "Permission modes"); foreground/background
  defaults flip between interactive, `-p` non-interactive, and SDK sessions
  (Sections "Run subagents in foreground or background", "Turn fork mode on
  or off"). Generalized versions of those claims are false.
- Security framing is vendor-stated: the output-scanning section concedes
  the scan "doesn't judge whether content is malicious" and that permission
  checks remain the actual control (Section "Subagent output scanning");
  report the page's safety claims as design intent, not measured guarantees.
- Gate flag for the literature gate (`study.yaml: depth: full`): this note
  resolves the sub-agents docs area with a direct snapshot read, so no
  source-level gap from this entry blocks a gate verdict. Residual gaps it
  surfaces for the comparison matrix, each on a page not registered in this
  study: built-in prompt content (closed), subagent compaction trigger
  thresholds (env-vars page), and worktree enforcement vectors (worktrees
  page). None is central to this entry's RQ coverage, but the report would
  need registered sources to cite them.

## Relevance to the brief

My inference, separated from the anchored material above.

- RQ4 (what the closed core reveals through docs and plugin surface): this
  page is the richest single official source on Claude Code's delegation
  architecture, exposing design decisions the closed core otherwise hides:
  a two-filter tool pipeline that gives background subagents (the default
  interactive posture) a fixed 19-tool built-in pool; default nesting of
  three layers with a 20-concurrent cap; permission precedence where a
  permissive parent (bypassPermissions, acceptEdits, or auto) overrides
  per-agent frontmatter; and a fork mode that trades input isolation for
  prompt-cache reuse. These are harness-design facts directly comparable to
  the pinned code of the two open systems.
- RQ2 (component inventory, extensibility and context dimensions): fills the
  Claude Code cell for subagents, MCP scoping, hooks, and skills on the
  extensibility axis, and shows Claude Code also uses subagents as
  context-management machinery: isolated windows, delegation-message-only
  input, one-shot read-only research agents, and per-agent persistent memory
  with a 200-line/25KB `MEMORY.md` window. Suggested comparison-matrix rows:
  tool-filter structure, depth and concurrency defaults, resume semantics,
  fork-versus-fresh spawning.
- Cross-system leads (inference, to verify against the pinned trees): the
  Codex registry components include built-in agent definitions
  (`codex-rs/core/src/agent/builtins/explorer.toml`) that can be contrasted
  with Claude Code's closed built-ins (Explore, Plan, general-purpose are
  documented but not inspectable); the OpenCode registry components include
  `packages/opencode/src/agent/subagent-permissions.ts`, the natural
  comparator for the permissionMode inheritance rules documented here.
- Left open: built-in system-prompt content and any token thresholds for
  subagent compaction remain unobserved; because the page is version-gated,
  any "Claude Code does X" statement in the report should carry its version
  condition (the snapshot's newest gate is v2.1.232).

## Quotables for the report

Strings verified character-exact against the snapshot; anchors are snapshot
section headings.

- Delegate-by-description architecture: "Each subagent runs in its own
  context window with a custom system prompt, specific tool access, and
  independent permissions." (Section "Create custom subagents"). Framing:
  the subagent contract is a Markdown file whose `description` field is the
  router.
- Built-in asymmetry: "Explore and Plan skip your CLAUDE.md files and the
  parent session's git status to keep research fast and inexpensive."
  (Section "Built-in subagents"). Framing: the read-only research agents
  trade the memory files for startup cost, an explicit documented tradeoff.
- Filter structure: a background subagent keeps "only these built-in tools:
  `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`,
  `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`,
  `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`,
  `SendMessage`, and `Artifact`" plus "every MCP tool" (Section "Available
  tools"). Framing: background execution is a reduced-capability tier, and
  one definition resolves to different tool pools by run mode.
- Limit constants: "By default, a subagent can spawn subagents of its own,
  up to three layers below the main conversation." (Section "Let subagents
  spawn their own subagents") and "when 20 subagents are running in a
  session, spawning another with the Agent tool fails with `Concurrent
  subagent limit reached`" (Section "Concurrent subagent limit"). Framing:
  delegation is bounded in depth and breadth, each with an env-var override.
- Fork economics: "Because a fork's system prompt and tool definitions are
  identical to the parent, its first request reuses the parent's prompt
  cache. This makes forking cheaper than spawning a fresh subagent for tasks
  that need the same context." (Section "How forks differ from other
  subagents"). Framing: prompt-cache reuse is a first-class harness feature.
- Resume semantics: "Resumed subagents retain their full conversation
  history, including all previous tool calls, results, and reasoning."
  (Section "Resume subagents"). Framing: subagent transcripts persist
  per-agent as `agent-{agentId}.jsonl` and survive main-session compaction,
  an explicit state-management design point.
- Precedence rule: "If the parent uses `bypassPermissions` or `acceptEdits`,
  this takes precedence and can't be overridden." (Section "Permission
  modes"). Framing: per-agent permission frontmatter is advisory below a
  permissive parent; the session's safety posture wins.
