---
source_key: "claudeCodeDocsPermissions"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
---

# Notes: Configure permissions (Claude Code official docs)

Anchors below cite this snapshot by section heading and line number of
`studies/2026-08_coding-agent-harnesses/sources/docs/claudeCodeDocsPermissions.md`,
which the snapshot header identifies as a fetch of
`https://code.claude.com/docs/en/permissions.md` on 2026-08-20 (line 1).

## Source identification

- Key: `claudeCodeDocsPermissions`
- Authors, year, venue: Anthropic, 2026, Claude Code official docs (`code.claude.com/docs/en/permissions`).
- Tier: docs
- URL / DOI: https://code.claude.com/docs/en/permissions (snapshot: `sources/docs/claudeCodeDocsPermissions.md`, accessed 2026-08-20, line 1)

## Problem and motivation

The page presents Claude Code's permission layer as the mechanism that
"control[s] what Claude Code can access and do with fine-grained permission
rules, modes, and managed policies" (tagline, line 8). It motivates
fine-grained permissions as letting users "specify exactly what the agent is
allowed to do and what it can't," with rules checkable into version control
for an organization while each developer can customize their own (line 10).
The page frames the design goal as a "tiered permission system to balance
power and safety" (Section~"Permission system", line 14).

## Method or core idea

The page specifies four interacting mechanisms rather than an algorithm.

1. Permission tiers and prompt table (Section~"Permission system", lines
   12-32). In Manual mode, read-only actions (file reads, Grep) do not
   require approval within the working directory and additional directories;
   Bash commands require approval except a built-in read-only set; file
   modification requires approval; WebFetch requires approval except
   preapproved documentation domains; WebSearch requires approval (table,
   lines 16-22). Permanent approvals save to `.claude/settings.local.json` at
   the git repository root, resolved through worktrees to the main checkout;
   file-modification approvals last only until session end (line 24). Before
   v2.1.211 rules saved in the starting directory instead (line 26).
2. Rule language (Section~"Permission rule syntax", lines 71-161, and
   Section~"Tool-specific permission rules", lines 163-414). Rules are
   `Tool` or `Tool(specifier)` (line 73), stored under `permissions.allow`,
   `permissions.ask`, `permissions.deny` in settings files.
3. Modes (Section~"Permission modes", lines 52-69). `default`, `acceptEdits`,
   `plan`, `auto`, `dontAsk`, `bypassPermissions`, selected via `defaultMode`
   in settings (line 54).
4. Policy layering (Sections "Settings precedence", "Managed settings",
   "Project allow rules and workspace trust", lines 490-571). Managed
   settings sit highest; project-granting rules are gated behind a workspace
   trust dialog.

A cross-cutting statement: "Permission rules are enforced by Claude Code,
not by the model. Instructions in your prompt or `CLAUDE.md` shape what
Claude tries to do, but they don't change what Claude Code allows"
(Section~"Manage permissions", note, line 49).

## Key claims with anchors

Permission modes (Section~"Permission modes", table lines 56-63):

- `default`: "Prompts for permission on first use of each tool. Labeled
  Manual in the CLI, the VS Code and JetBrains extensions, and the desktop
  app, and Claude Code accepts `manual` as an alias. The label and alias
  require Claude Code v2.1.200 or later." (line 58)
- `acceptEdits`: "Automatically accepts file edits and common filesystem
  commands such as `mkdir`, `touch`, `mv`, and `cp` for paths in the working
  directory or `additionalDirectories`" (line 59).
- `plan`: "Claude reads files and runs read-only shell commands to explore
  but doesn't edit your source files; with auto mode available,
  classifier-approved commands also run." (line 60)
- `auto`: "Auto-approves tool calls with background safety checks that
  verify actions align with your request" (line 61).
- `dontAsk`: "Auto-denies tools unless pre-approved via `/permissions` or
  `permissions.allow` rules. `AskUserQuestion`, connector tools your
  organization set to `ask`, and MCP tools marked `requiresUserInteraction`
  are denied even if you've allowed them" (line 62).
- `bypassPermissions`: "Skips permission prompts, except for the actions no
  mode auto-approves" (line 63) (the list itself lives on another page, see
  Limitations).
- Warning: "`bypassPermissions` mode skips permission prompts, including for
  writes to protected paths such as `.git` and `.claude`... Only use this
  mode in isolated environments like containers or VMs" (line 66).
- `permissions.disableBypassPermissionsMode` or `permissions.disableAutoMode`
  set to `"disable"` in any settings file blocks those modes; "most useful
  in managed settings where they can't be overridden" (line 69).

Rule evaluation (Section~"Manage permissions", lines 34-50):

- `/permissions` lists every rule and the `settings.json` file it comes
  from; edits apply "starting with Claude's next tool call in the same
  turn"; before v2.1.234 changes queued until the turn finished (line 36).
- "Rules are evaluated in order: deny, then ask, then allow. The first match
  in that order determines the outcome, and rule specificity doesn't change
  the order." (line 42)
- A broad deny such as `Bash(aws *)` blocks even calls matching a narrower
  allow like `Bash(aws s3 ls)`, "so a deny rule can't carry allowlist
  exceptions" (line 44).
- A bare tool name deny "removes the tool from Claude's context entirely"
  except `EndConversation`, which no deny can remove and no ask can prompt
  for "while any other tool remains"; scoped rules such as `Bash(rm *)` keep
  the tool available and block matching calls (line 46).

Rule syntax (Section~"Permission rule syntax", lines 71-161):

- Format `Tool` or `Tool(specifier)` (line 73); `Bash(*)` equals bare `Bash`,
  and as a deny rule both remove the tool from context (line 85).
- Specifier examples: `Bash(npm run build)` exact command, `Read(./.env)`,
  `WebFetch(domain:example.com)` (lines 93-95).
- Parameter matching `Tool(param:value)` works for deny and ask rules only,
  because "An allow rule for one parameter value wouldn't establish that the
  call is safe overall" (line 99). Examples: `Agent(model:opus)`,
  `Agent(isolation:worktree)`, `Bash(run_in_background:true)` (lines
  103-105). Values compare "against the literal input Claude sends, before
  any normalization" (line 113); a parameter the model omits never matches
  (line 112).
- Primary content fields cannot be matched this way: `command` for Bash and
  PowerShell, `file_path` for Read/Edit/Write, `path` for Grep and Glob,
  `notebook_path` for NotebookEdit, `url` for WebFetch; `Bash(command:rm *)`
  "is ignored and emits a startup warning" because a compound command could
  bypass it (line 116).
- Tool-name wildcards: `"*"` matches every tool, `"mcp__*"` every MCP tool;
  allow rules accept tool-name globs only after a literal, glob-free
  `mcp__<server>__` prefix; unanchored allow globs (`"*"`, `"B*"`,
  `"mcp__*"`) are "skipped with a warning and don't auto-approve anything"
  (lines 145-157). Unknown-tool deny/ask rules produce a startup warning,
  with names containing `_` or `*` exempt (line 159). Rules match canonical
  tool names, not transcript labels, e.g. label `Stop Task` is canonical
  name `TaskStop` (line 161).

Bash rules (Section~"Tool-specific permission rules", lines 163-242):

- Wildcards `*` match any sequence including spaces at any position
  (lines 167-175); a trailing `*` preceded by a space enforces a word
  boundary, so `Bash(ls *)` matches `ls -la` but not `lsof`, while
  `Bash(ls*)` matches both (line 177).
- Recognized command separators are `&&`, `||`, `;`, `|`, `|&`, `&`, and
  newlines; "A rule must match each subcommand independently" (line 182).
  Approving a compound command saves one rule per subcommand, "Up to 5 rules
  may be saved for a single compound command" (line 185).
- Claude Code strips a fixed, non-configurable wrapper set before matching:
  `timeout`, `time`, `nice`, `nohup`, `stdbuf`, builtins `command` and
  `builtin`, and zsh `noglob` (line 191); leading assignments of known-safe
  environment variables are stripped for allow rules, while deny/ask rules
  match past any leading assignment (line 193); bare flag-less `xargs` is
  stripped (line 195). Runners such as `direnv exec`, `devbox run`,
  `mise exec`, `npx`, `docker exec` are deliberately not stripped (line
  197). `watch`, `setsid`, `ionice`, `flock`, and `find` with `-exec`/
  `-delete` always prompt in Manual mode under prefix rules (line 199).
- Built-in read-only set runs without a prompt in every mode: `ls`, `cat`,
  `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`,
  `stat`, `du`, `cd`, and read-only forms of `git` (line 203). Not
  configurable; to re-prompt one you add an ask or deny rule (line 203).
  Manual mode still prompts for unquoted globs on write-capable commands
  (`find`, `sort`, `sed`, `git`), `docker` pointed at another daemon, `file`
  with path-opening flags, Windows UNC paths, and commands the analysis
  can't parse; "Commands longer than 10,000 characters always prompt"
  (lines 209-215). `cd` with `git`, and `cd` with an output redirect, prompt
  even when each part is read-only (lines 217-220).
- Argument-constraining patterns are declared fragile: the docs walk through
  five evasions of `Bash(curl http://github.com/ *)` and recommend deny
  rules plus WebFetch, PreToolUse hooks, or CLAUDE.md guidance, noting
  "using WebFetch alone doesn't prevent network access. If Bash is allowed,
  Claude can still use `curl`, `wget`, or other tools to reach any URL."
  (warning, lines 222-237)
- Output redirection targets (`>`, `>>`, `2>`) are checked as file writes
  against Edit allow/deny rules, protected paths, and working directories;
  `/dev/null` is exempt; targets starting with `~` or containing a glob
  character need approval (line 242).

PowerShell rules mirror Bash: same wildcard shape, aliases canonicalized so
`PowerShell(Get-ChildItem *)` matches `gci`, `ls`, `dir`; matching is
case-insensitive; Claude Code parses the PowerShell AST and splits compound
commands on `|`, `;`, and (PowerShell 7+) `&&`/`||`, requiring a rule to
match every subcommand (Section~"PowerShell", lines 244-264).

Read and Edit rules (lines 266-360):

- `Edit` rules apply to all built-in editing tools; `Read` rules apply
  best-effort to Grep, Glob, `@file` mentions, and IDE-shared context (line
  270). A `Read` deny also blocks Edit and Write on the same path including
  new-file creation, but NotebookEdit isn't covered; enforcement requires
  v2.1.208 or later on edits and v2.1.228 or later on writes (line 272).
- File permissions consult `Edit(path)` and `Read(path)` rules only; path
  rules written for `Write`, `NotebookEdit`, `Glob`, or legacy `MultiEdit`
  are accepted but never consulted and warn at startup (except a `Glob` rule
  in `--allowedTools`); v2.1.210 or later (line 274).
- Read/Edit deny rules "Don't apply to arbitrary subprocesses that read or
  write files indirectly"; OS-level enforcement requires the sandbox
  (warning, line 277).
- Path patterns use gitignore syntax with four anchors: `//path` filesystem
  absolute, `~/path` home, `/path` relative to the settings source, `path`
  or `./path` relative to cwd (table, lines 282-287; `/Users/alice/file` is
  not absolute, line 290). `/path` resolves differently by settings source
  (table, lines 295-301); user-settings `Read(/secrets/**)` blocks
  `~/.claude/secrets/**`, not the project (line 305). Windows paths
  normalize to POSIX (`C:\Users\alice` becomes `/c/Users/alice`) (line 307).
- Single-segment directory patterns match at different depths by rule type:
  allow rules match only `<cwd>/src`, deny and ask rules match `secrets` at
  any depth (lines 323-326); `*` stays within a path segment, `**` crosses
  directories (line 350). Generated rules escape gitignore characters;
  before v2.1.202 they were saved unescaped (line 353).
- Symlink handling is asymmetric: allow rules require both the symlink path
  and its target to match, deny rules apply when either matches (lines
  355-358).

WebFetch rules match the URL hostname with a `domain:` prefix,
case-insensitively, stripping a trailing dot; `domain:*.example.com` matches
subdomains at any depth but not the apex domain; a wildcard outside a
leading `*.` or bare `*` matches only one dot-separated label, which "keeps
a trailing wildcard from matching domains an attacker could register"
(Section~"WebFetch", lines 362-370).

MCP rules use `mcp__<server>` or `mcp__<server>__<tool>`; claude.ai
connector tools an organization set to `ask` prompt on every call even in
`auto` and `bypassPermissions`, are denied in `dontAsk`, and appear as
`mcp__claude_ai_<server>__<tool>` (Section~"MCP", lines 372-380).

`Agent(AgentName)` rules gate subagents (`Agent(Explore)`, `Agent(Plan)`,
custom names), disabled via deny rules or `--disallowedTools`
(Section~"Agent (subagents)", lines 382-398). `Cd` rules gate only the
user-run `/cd` command, which the model cannot invoke; any `Cd` allow rule
switches `/cd` to allowlist mode; `*` matches exactly one path segment, `**`
across segments (Section~"Cd", lines 400-414).

Hooks (Section~"Extend permissions with hooks", lines 416-424):

- PreToolUse hooks run before the permission prompt for every tool except
  `EndConversation`, and "can deny the tool call, force a prompt, or skip
  the prompt" (line 418).
- Hook decisions do not bypass rules: matching deny rules still block and
  matching ask rules still prompt even when a hook returned `"allow"` (line
  420). A hook exiting code 2 blocks before permission rules evaluate, so a
  blocking hook also trumps allow rules (line 424).

Working directories and additional directories (Section~"Working
directories", lines 426-462):

- Access extends via `--add-dir` at startup, `/add-dir` during a session, or
  `additionalDirectories` in settings; added files follow the same
  permission rules (lines 430-434). `/cd` relocates the session, reloads the
  new directory's `CLAUDE.md`, and requires v2.1.169 or later (line 438).
- "Adding a directory extends where Claude can read and edit files. It
  doesn't make that directory a full configuration root" (line 442). Only
  `--add-dir`/`/add-dir` directories load any configuration: `.claude/skills/`
  with live reload; `.claude/commands/` and `.claude/agents/` without live
  reload; settings limited to `enabledPlugins` and `extraKnownMarketplaces`;
  CLAUDE.md files only when `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
  (table, lines 448-454). Directories from `permissions.additionalDirectories`
  "grant file access only and don't load any of the configuration" (line 444).

Sandbox interplay (Section~"How permissions interact with sandboxing",
lines 464-488):

- Permissions govern tool and path/domain access; sandboxing "provides
  OS-level enforcement that restricts the Bash tool's filesystem and network
  access," applying only to Bash and its children; the docs prescribe both
  for defense-in-depth (lines 466-476).
- With `autoAllowBashIfSandboxed` at its default of `true`, sandboxed Bash
  commands run without prompting even under a bare `Bash` ask rule (line 478).
  Plan mode skips this substitution; before v2.1.212 it applied there too
  (line 480). Content-scoped ask rules, explicit denies, and `rm`/`rmdir`
  targeting a critical path still go through the regular flow (lines
  482-486).

Managed settings and precedence (Sections "Managed settings" and "Settings
precedence", lines 490-531):

- Managed settings "can't be overridden by user or project settings, apart
  from a few security-sensitive keys," and arrive via MDM/OS-level policies,
  managed settings files, server-managed settings, or a self-hosted Claude
  apps gateway (line 492).
- Managed-only keys include `allowManagedPermissionRulesOnly` ("prevents
  user and project settings from defining `allow`, `ask`, or `deny`
  permission rules"), `disableSideloadFlags` (rejects `--plugin-dir`,
  `--plugin-url`, `--agents`, `--mcp-config` at startup; v2.1.193 or later),
  `forceRemoteSettingsRefresh` (fail-closed startup),
  `strictPluginOnlyCustomization`, `sandbox.network.allowManagedDomainsOnly`,
  and ten more (table, lines 498-515). `disableBypassPermissionsMode` works
  from any scope, including a user locking themselves out (line 517).
- "Permission rules follow the same settings precedence as all other Claude
  Code settings, with managed settings highest: no other level, including
  command line arguments, can override a managed permission rule." (line
  525). A tool denied at any level cannot be allowed at any other;
  `--disallowedTools` can only add restrictions (line 527). Deny rules from
  any scope evaluate before allow rules (line 529). Embedding hosts add
  managed policy via the SDK `managedSettings` option (line 531).

Workspace trust (Section~"Project allow rules and workspace trust", lines
533-571):

- `permissions.allow` and `additionalDirectories` in a project's
  `.claude/settings.json` "grant capability, so Claude Code applies them
  only after you accept the workspace trust dialog for that folder"; deny
  and ask rules are not gated (line 535).
- Trust is keyed on the git repository root in repos (main checkout root in
  worktrees), on the starting directory outside repos excluding nested git
  repos, and held for the current session only, not written to disk, when
  starting in the home directory (lines 539-541).
- The dialog appears only in interactive sessions; "A `claude -p` run or an
  SDK session never shows it" (line 543).
- `.claude/settings.local.json` is treated as repository-supplied (and held
  until trust) when tracked in git or when `.claude` is a symlink (line
  547); versions 2.1.196 through 2.1.199 and before v2.1.207 behaved
  differently (line 551).
- Pre-trust behavior table: settings-file hooks, the `env` block and
  `apiKeyHelper` run even for a merely parent-trusted folder and in `claude
  -p`/SDK runs; project allow rules do not, and `-p` prints `this workspace
  has not been trusted`; subagent frontmatter hooks, `@skills-dir` plugins,
  and `extraKnownMarketplaces` never run without the exact folder trusted
  and offer no dialog; `.mcp.json` servers prompt when only a parent is
  trusted but are "Connected without asking, approved or not" in
  never-trusted `-p`/SDK sessions (table, lines 557-562). Manual trust sets
  `projects["<path>"].hasTrustDialogAccepted` to `true` in `~/.claude.json`
  (line 564).
- Recommended `-p` hardening: `--setting-sources user`, `--bare` (still
  applies the project `env` block and helpers), `--settings
  '{"disableAllHooks": true}'`, or `disabledMcpjsonServers` entries (lines
  568-571).

## Evaluation and evidence

This is normative reference documentation, so there are no datasets,
baselines, or benchmark metrics; `[CITATION NEEDED]` applies to any
performance claim, and I looked for an evaluation section and found none
(the page ends with "See also" links, lines 577-583). The checkable content
is specification and version history. Character-exact values copied from the
snapshot:

- Modes: `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`,
  `bypassPermissions` (lines 56-63).
- Version gates: `manual` label/alias require v2.1.200 (line 58); Read-deny
  blocks edits at v2.1.208 and writes at v2.1.228 (line 272);
  Write/NotebookEdit/Glob/MultiEdit path-rule warning requires v2.1.210
  (line 274); repo-root rule storage from v2.1.211 (line 26);
  `/permissions` mid-turn application from v2.1.234 (line 36); `/cd` from
  v2.1.169 (line 438); rule escaping from v2.1.202 (line 353); plan-mode
  sandbox substitution change at v2.1.212 (line 480); `disableSideloadFlags`
  from v2.1.193 (line 508); `disableCommandPluginSources` from v2.1.229
  (line 507); local-settings trust changes across 2.1.196-2.1.199 and
  v2.1.207 (line 551).
- Limits: "Up to 5 rules may be saved for a single compound command" (line
  185); "Commands longer than 10,000 characters always prompt" (line 215).
- Wrapper strip list: `timeout`, `time`, `nice`, `nohup`, `stdbuf`,
  `command`, `builtin`, `noglob` (line 191). Recognized separators: `&&`,
  `||`, `;`, `|`, `|&`, `&`, and newlines (line 182). Read-only set: `ls`,
  `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`,
  `diff`, `stat`, `du`, `cd`, and read-only forms of `git` (line 203).
- Starter configurations live at
  `github.com/anthropics/claude-code/tree/main/examples/settings` (line 575).

## Limitations

- The requested list of "actions no mode auto-approves" is not in this
  snapshot. It is deferred to another page (`/docs/en/permission-modes`
  #actions-no-mode-auto-approves, line 63). The same holds for the full
  "protected paths" list (only exemplified as "such as `.git` and `.claude`",
  line 66), the "critical path" list (line 486), the auto-mode classifier
  behavior (line 14), and per-plan default startup mode ("Which mode a
  session starts in", line 54). This note cannot verify those lists
  character-exact.
- The docs page is not pinned to a product version. The snapshot is a
  `.md` fetch from 2026-08-20 (line 1); it describes current behavior with
  many version gates and can drift from the pinned checkout (`claude-code` @
  c3d2e35, per registry), whose core is closed source. All claims here are
  claims about documented behavior, not verified enforcement code.
- The source itself flags design weaknesses: Bash argument-constraining
  patterns are "fragile" with five concrete evasions (lines 222-237);
  `Write`/`NotebookEdit`/`Glob`/`MultiEdit` path rules are accepted but
  never enforced (line 274); Read/Edit deny rules do not cover indirect
  subprocess file access (line 277); env runners like `docker exec` and
  `npx` are not wrapper-stripped, so prefix rules over them over-match
  (`devbox run rm -rf .` example, line 197).
- Pre-trust execution surface is broad: settings-file hooks, the `env`
  block, and `apiKeyHelper` run even without folder trust (line 559), and
  `.mcp.json` servers connect without asking in never-trusted `-p`/SDK runs
  (line 562). These are stated behaviors, but their interaction with
  prompt injection is not analyzed on this page.

## Relevance to the brief

This is my inference, separated from source claims. The page is the primary
documentary evidence for Claude Code's permissions dimension, which the
brief in scope ("permissions and sandboxing") and both RQ3 and RQ4 require,
and it earns relevance 3. For RQ3 (capability vs. safety in shell and file
access), it shows Claude Code's specific trade: capability grows through
glob rules, wrapper stripping, a built-in read-only set, and sandbox-backed
auto-approval of Bash, while safety rests on deny-first precedence enforced
in the harness rather than the model, workspace trust gating of
project-supplied grants, managed-policy overrides that even CLI flags cannot
pierce, and an asymmetry principle repeated across the design (deny matches
broader than allow: symlink targets, single-segment patterns at any depth,
deny past env assignments). For RQ1 cross-system comparison, these surfaces
give concrete contrast points against OpenCode's ruleset-only permission
model with no OS sandbox (registry coverage_limits) and Codex's
execpolicy/sandboxing crates. What it leaves open, and blocks in
`_synthesis.md` until filled from other notes: the exact "actions no mode
auto-approves," "protected paths," and "critical paths" lists (on the
permission-modes page, not snapshotted under this key), and any
implementation-level confirmation, since the enforcement code is closed.
Because `depth: full`, I flag the missing permission-modes snapshot as a
source-level gap for the permissions/sandboxing comparison cell, mitigated
only if `claudeCodeDocsSandboxing` (already snapshotted) covers the
overlapping sandbox-side statements.

## Quotables for the report

- "Rules are evaluated in order: deny, then ask, then allow. The first
  match in that order determines the outcome, and rule specificity doesn't
  change the order." (line 42). Use as the headline statement of Claude
  Code's policy semantics, contrasted with Codex and OpenCode.
- "Permission rules are enforced by Claude Code, not by the model." (line
  49). Use to mark the harness/model separation for RQ4.
- "`bypassPermissions` mode skips permission prompts, including for writes
  to protected paths such as `.git` and `.claude`... Only use this mode in
  isolated environments" (line 66). Use in the safety-trade discussion.
- "Bash permission patterns that try to constrain command arguments are
  fragile." (line 223). Use as Anthropic's own admission of the limits of
  string-pattern policy.
- "`permissions.allow` rules and `permissions.additionalDirectories` entries
  in a project's `.claude/settings.json` grant capability, so Claude Code
  applies them only after you accept the workspace trust dialog" (line 535).
  Use when comparing trust models across the three harnesses.
