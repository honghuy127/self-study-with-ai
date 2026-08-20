---
source_key: "opencodePermissions"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "opencode"
commit: "d545d8fba57283528db69281f59c803c646eb7e9"
---

# Notes: OpenCode: permission rulesets and confinement (no OS sandbox found) (opencode)

## Source identification

- Key: opencodePermissions
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`)
- Component scope: `packages/opencode/src/permission/` (`index.ts`, `evaluate.ts`, `arity.ts`); the gating sites that consume it (`packages/opencode/src/session/tools.ts`, `packages/opencode/src/session/processor.ts`, `packages/opencode/src/agent/agent.ts`, `packages/opencode/src/agent/subagent-permissions.ts`, `packages/opencode/src/tool/task.ts`, `packages/opencode/src/tool/shell.ts`, `packages/opencode/src/tool/{edit,write,external-directory}.ts`); git-worktree sandbox workspaces (`packages/opencode/src/worktree/index.ts`, `packages/schema/src/project.ts` `Project.sandboxes`, `packages/opencode/src/project/{project,instance-context}.ts`); confined interpreter (`packages/codemode/`, host adapter `packages/opencode/src/tool/code-mode.ts`). Cross-component anchors (marked below) touch `packages/schema/src/v1/permission.ts`, `packages/core/src/v1/config/permission.ts`, `packages/core/src/util/wildcard.ts`, `packages/core/src/global.ts`, and `packages/opencode/src/effect/runtime-flags.ts`, which live in sibling registry entries; they are included only to wire the data model together.
- Tier: codebase

## Purpose and role in the harness

OpenCode's safety boundary is a **pattern-matched permission ruleset evaluated in-process before each tool call**, not an OS sandbox. Every tool execution funnels through a `Permission.ask` effect that matches the permission name plus one or more glob-like patterns against a flat array of rules and resolves to one of three actions, `allow | deny | ask`, literal-defined in `packages/schema/src/v1/permission.ts:16`. When the action is `ask`, the runtime suspends the tool call on a `Deferred`, publishes a `permission.asked` event, and only resumes after a user reply (`packages/opencode/src/permission/index.ts:98-106`). There is no seatbelt/bubblewrap/landlock/seccomp layer anywhere in scope (verified below). Isolation that does exist is one of three softer mechanisms: (1) the ruleset, (2) `git worktree` sandbox workspaces, and (3) the confined `codemode` JavaScript interpreter that only reaches host-provided tools.

The three-action model and rule shape are fixed by the schema: a `Rule` is `{ permission: string, pattern: string, action: Action }` and a `Ruleset` is `Schema.Array(Rule)` (`packages/schema/src/v1/permission.ts:19-25`). Rules are matched with a wildcard matcher where `*` becomes `.*` and `?` becomes `.` in an anchored regex (`packages/core/src/util/wildcard.ts:3-13`); a trailing ` *` is made optional so `ls *` matches both `ls` and `ls -la` (`packages/core/src/util/wildcard.ts:11`).

## Mechanism

### Evaluation: flat ruleset, last match wins, default `ask`

`evaluate` flattens the supplied rulesets in order and takes the last rule whose `permission` field matches the permission name and whose `pattern` field matches the pattern argument (`packages/opencode/src/permission/index.ts:28-38`). When no rule matches it falls back to `{ action: "ask", permission, pattern: "*" }` (`packages/opencode/src/permission/index.ts:32-36`). `evaluate.ts` is a one-line re-export of this function (`packages/opencode/src/permission/evaluate.ts:1`). Because `Permission.merge` is simply array concatenation (`return rulesets.flat()`, `packages/opencode/src/permission/index.ts:200-202`), precedence is purely positional: whichever ruleset is merged later wins under `findLast`. This is how user config overrides built-in defaults (see below).

### The ask/reply gate

`ask` iterates the request's `patterns`, evaluating each against `evaluate(request.permission, pattern, ruleset, approved)` (`packages/opencode/src/permission/index.ts:72-73`). The action aggregation across patterns is:

- any `deny` → immediately fail the call with `PermissionV1.DeniedError`, carrying the subset of rules that matched the permission name so the model sees why (`packages/opencode/src/permission/index.ts:75-79`);
- all `allow` → return without prompting (`packages/opencode/src/permission/index.ts:80-84`);
- otherwise → prompt. It allocates an id, stores `{ info, deferred }` in a `pending` map, publishes `Permission.Event.Asked`, and awaits the deferred (`packages/opencode/src/permission/index.ts:86-106`).

`reply` resolves a pending request by `requestID` (`packages/opencode/src/permission/index.ts:109-167`). Replies are the `Reply` literals `once | always | reject` (`packages/schema/src/v1/permission.ts:38`):

- `reject` fails this deferred (`RejectedError`, or `CorrectedError` carrying feedback when a message is present, `packages/core/src/v1/permission.ts:7-19`) and also rejects every other pending request in the same session (`packages/opencode/src/permission/index.ts:121-139`);
- `once` succeeds only this deferred (`packages/opencode/src/permission/index.ts:142-143`);
- `always` succeeds this deferred, then pushes one `{ permission, pattern, action: "allow" }` rule per `info.always` entry into the in-memory `approved` array and re-evaluates every other pending request in the session, auto-resolving those now fully allowed (`packages/opencode/src/permission/index.ts:145-166`).

The `approved` approvals live in `State { pending, approved }` held by `InstanceState.make` (`packages/opencode/src/permission/index.ts:23-26`, `46-65`), i.e. per-instance runtime state. A finalizer rejects all still-pending requests when the instance's scope closes (`packages/opencode/src/permission/index.ts:54-61`). I did not find, within this component, code that persists `approved` across restarts (see Limitations).

### Where tool calls are gated

The tool-execution context hands every tool a `ctx.ask` closure. Its `ruleset` is the merge of the active agent's ruleset with the session's optional ruleset: `ruleset: Permission.merge(input.agent.permission, input.session.permission ?? [])` (`packages/opencode/src/session/tools.ts:81-90`). Each built-in tool calls `ctx.ask(...)` with a permission name and patterns before doing its work:

- **bash / shell** (`packages/opencode/src/tool/shell.ts:263-291`): two asks. First, any directory referenced by a file-manipulating command that resolves outside the project boundary becomes an `external_directory` ask with `<dir>/*` globs (`shell.ts:264-280`). Second, a single `bash` ask (`ShellID.ToolID`, which is the string `"bash"`, `packages/opencode/src/tool/shell/id.ts:16`) whose `patterns` are the full source text of each parsed command and whose `always` are arity-normalized prefixes (`shell.ts:283-290`, `407-410`). Commands are parsed with tree-sitter (`shell.ts:311-336`); only commands not in the `CWD` set (`cd`, `chdir`, `popd`, `pushd`, `push-location`, `set-location`, `shell.ts:28`) contribute patterns (`shell.ts:407`). Path-bearing commands in the `FILES` set (`rm`, `cp`, `mv`, `mkdir`, `touch`, `chmod`, `chown`, `cat`, plus PowerShell `*-item` cmdlets, `shell.ts:29-50`) additionally resolve their path arguments to detect external directories (`shell.ts:397-405`).
- **edit / write** (`packages/opencode/src/tool/edit.ts:102-110`, `145-153`; `packages/opencode/src/tool/write.ts:54-62`): permission `edit`, pattern is the file path made relative to the instance worktree (`path.relative(instance.worktree, filePath)`), `always: ["*"]`. Both first run `assertExternalDirectoryEffect` (`write.ts:44`), which asks `external_directory` with a `<dir>/*` glob when the target is outside the project boundary (`packages/opencode/src/tool/external-directory.ts:15-45`).
- **task (subagent spawn)** (`packages/opencode/src/tool/task.ts:119-129`): permission `task`, pattern `[subagent_type]`, `always: ["*"]`, skipped when `ctx.extra.bypassAgentCheck` is set.
- **doom loop** (`packages/opencode/src/session/processor.ts:356-380`): after the assistant emits a tool call whose name+input match the last 3 tool parts (`DOOM_LOOP_THRESHOLD = 3`, `processor.ts:29`), the processor issues `permission.ask({ permission: "doom_loop", patterns: [value.name], always: [value.name], ruleset: agent.permission })` (`processor.ts:372-379`). This is a rate/confirmation gate against identical repeated calls, and `doom_loop` defaults to `ask` (see below).
- **MCP tools** (`packages/opencode/src/session/tools.ts:390-489`): each raw MCP tool is wrapped so that execution first does `ctx.ask({ permission: key, metadata: {}, patterns: ["*"], always: ["*"] })` (`tools.ts:408`). MCP resource tools ask `read` with `mcp:<server>:*` or `mcp:<server>:<uri>` patterns (`tools.ts:172-185`, `343-348`).

So gating is cooperative and convention-based: the tool body must call `ctx.ask` itself. There is no central interceptor that wraps `item.execute` with a permission check; the `execute` wrapper in `tools.ts:102-133` only fires plugin `tool.execute.before/after` hooks and then runs the tool, trusting the tool to have asked.

### Pattern granularity for bash: the arity table

Shell pattern granularity is normalized by a command-prefix arity dictionary, `packages/opencode/src/permission/arity.ts`. `BashArity.prefix(tokens)` scans the token list for the longest matching key in `ARITY` and returns the first `arity` tokens; unknown commands fall back to the first token (`arity.ts:1-9`). The shell tool appends `" *"` to this prefix to form the `always` pattern (`shell.ts:409`): so `git checkout main` produces the durable allow pattern `git checkout *` (because `git` has arity 2, `arity.ts:83`), while `npm run dev` yields `npm run dev *` (because `npm run` has arity 3, `arity.ts:114`). The `ARITY` table is a generated dictionary (comment at `arity.ts:11-23`) mapping common commands to token counts, e.g. `cat: 1` (`arity.ts:25`), `docker: 2` (`arity.ts:70`), `docker compose: 3` (`arity.ts:72`). The per-call `patterns` array still carries the exact command text, so a `once`/exact approval is command-specific while an `always` approval is the whole arity family.

### Built-in agent defaults (the base ruleset)

`Agent.layer` constructs the base `defaults` ruleset via `Permission.fromConfig` (`packages/opencode/src/agent/agent.ts:119-136`):

- `"*": "allow"` — the base is allow-all; every permission that has no more specific rule resolves to allow.
- `doom_loop: "ask"`.
- `external_directory: { "*": "ask", ...whitelistedDirs: "allow" }` — paths outside the project prompt unless whitelisted. The whitelist is `Truncate.GLOB`, `<Global.Path.tmp>/*`, skill dirs `*`, and reference dirs `*` (`agent.ts:108-117`). `Truncate.GLOB` is `path.join(TRUNCATION_DIR, "*")` (`packages/opencode/src/tool/truncate.ts:17`) and `TRUNCATION_DIR` is `path.join(Global.Path.data, "tool-output")` (`packages/opencode/src/tool/truncation-dir.ts:4`).
- `question: "deny"`, `plan_enter: "deny"`, `plan_exit: "deny"`.
- `read: { "*": "allow", "*.env": "ask", "*.env.*": "ask", "*.env.example": "allow" }` — env-file reads prompt (`agent.ts:130-135`, with the gitignore-mirroring comment at `agent.ts:129`).

Each built-in agent layers more rules over `defaults` and then appends the user's config rules last (`Permission.merge(defaults, ...builtin..., user)`):

- `build` (the default primary agent) adds `question: "allow"`, `plan_enter: "allow"` (`agent.ts:141-155`).
- `plan` denies all edits except plan files (`edit: { "*": "deny", ".opencode/plans/*.md": "allow", <plans dir>/*.md: "allow" }`), denies `task.general`, allows `plan_exit` and writes under the data plans dir (`agent.ts:156-181`).
- `general` (subagent) denies `todowrite` (`agent.ts:182-195`).
- `explore` (subagent) is allowlist-based: `"*": "deny"`, then `allow` for `grep`, `glob`, `list`, `bash`, `webfetch`, `websearch`, `read`, plus a read-only `external_directory` map (`agent.ts:196-218`).
- `compaction`, `title`, `summary` are `"*": "deny"` (hidden primary agents, `agent.ts:219-264`).

User config agents are merged in a loop; `item.permission = Permission.merge(item.permission, Permission.fromConfig(value.permission ?? {}))` (`agent.ts:267-294`, permission merge at `agent.ts:293`). Finally, unless a user rule explicitly denies `Truncate.GLOB`, every agent gets `external_directory: { [Truncate.GLOB]: "allow" }` appended so truncated-output files are always readable (`agent.ts:296-310`).

The config permission vocabulary is typed in `packages/core/src/v1/config/permission.ts`: known keys are `read`, `edit`, `glob`, `grep`, `list`, `bash`, `task`, `external_directory`, `todowrite`, `question`, `webfetch`, `websearch`, `lsp`, `doom_loop`, `skill`, plus arbitrary string keys (so per-tool and per-MCP-tool names are valid), each mapping to an action or an object of pattern→action (`config/permission.ts:17-36`). `fromConfig` normalizes a string action to pattern `"*"` and expands `~`/`$HOME` prefixes via `expand` (`packages/opencode/src/permission/index.ts:178-198`).

### Tool-level denial: removing tools outright

`Permission.disabled` computes which tools are hidden: a tool is disabled when the last matching rule for its permission has `pattern === "*"` and `action === "deny"` (`packages/opencode/src/permission/index.ts:204-214`). It folds `edit`, `write`, `apply_patch` into permission `edit` and the MCP resource tools into `read` (`index.ts:205-209`). `visibleTools` filters them out of the registry (`index.ts:216-219`). So a config like `bash: "deny"` does not merely reject each call; it removes `bash` from the model-visible tool list.

### Session and subagent inheritance

A session can carry its own ruleset: `CreateInput` and `SetPermissionInput` both accept `permission: PermissionV1.Ruleset` (`packages/opencode/src/session/session.ts:267`, `289-292`). At ask time, the session ruleset is merged after the agent's (`tools.ts:87`), so session rules override agent defaults by positional last-match-wins.

When the `task` tool spawns a subagent session it derives the child's session ruleset with `deriveSubagentSessionPermission` (`packages/opencode/src/agent/subagent-permissions.ts:14-27`): it copies the parent session's `external_directory` rules and every `deny` rule, then appends default denies for `todowrite` and `task` unless the target agent's own ruleset already mentions them. The doc comment states the intent that the parent agent's restrictions govern only the parent; the subagent's own permissions determine its capabilities, with only deny and external-directory constraints inherited (`subagent-permissions.ts:4-13`). The `task` tool additionally adds `todowrite`/`task` denies and any `cfg.experimental.primary_tools` denies, and creates the child session with the merged permission (`packages/opencode/src/tool/task.ts:139-172`). Recursion is capped by `cfg.subagent_depth ?? 1` (`task.ts:111-117`).

## Key facts with anchors

- Three actions are `allow | deny | ask` (`packages/schema/src/v1/permission.ts:16`); a `Rule` is `{ permission, pattern, action }` and `Ruleset = Schema.Array(Rule)` (`permission.ts:19-25`).
- Evaluation is positional last-match-wins over a flat concatenated array; no-match defaults to `ask` (`packages/opencode/src/permission/index.ts:28-38`, `200-202`).
- The base ruleset is allow-all (`"*": "allow"`) with targeted overrides: `doom_loop:"ask"`, `external_directory:"ask"` (wildcard), `question`/`plan_enter`/`plan_exit:"deny"`, and `.env` reads `ask` except `.env.example` (`packages/opencode/src/agent/agent.ts:119-136`).
- Wildcard matching compiles `*`→`.*`, `?`→`.` into an anchored regex, case-insensitive on win32; trailing ` *` is optional (`packages/core/src/util/wildcard.ts:3-13`).
- `ctx.ask` merges `agent.permission` with `session.permission` per tool call (`packages/opencode/src/session/tools.ts:81-90`).
- Deny short-circuits and surfaces the matching rules to the model (`packages/opencode/src/permission/index.ts:75-79`); reject cascades to all pending asks in the same session (`index.ts:121-139`); `always` pushes allow rules into in-memory `approved` (`index.ts:145-151`).
- bash patterns: exact full command per call, arity-prefix + ` *` for `always` (`packages/opencode/src/tool/shell.ts:407-410`, `283-290`; `packages/opencode/src/permission/arity.ts:1-9`, `24-161`). bash tool id/permission key is the string `"bash"` (`shell/id.ts:16`).
- edit/write use permission `edit` with the path relative to the worktree as the pattern (`edit.ts:102-110`; `write.ts:54-62`); out-of-project paths trigger `external_directory` (`external-directory.ts:15-45`).
- Doom loop threshold is 3 identical consecutive tool calls (`processor.ts:29`, `356-380`).
- Subagent session ruleset inherits parent `deny` + `external_directory` rules, then adds default `todowrite`/`task` denies (`subagent-permissions.ts:14-27`; child session created with merged denies, `task.ts:139-172`).
- Tools with a `*: deny` rule are removed from the tool list entirely, not just rejected per call (`packages/opencode/src/permission/index.ts:204-219`).
- No OS-level sandbox: searches across `packages/opencode` for `seatbelt|bubblewrap|bwrap|landlock|seccomp|apparmor|sandbox-exec|chroot|unshare|setuid|rlimit` return no relevant mechanism (only unrelated `unshare` for session sharing), and no `.sb`/`.profile` files exist in the tree. The only in-tree uses of "sandbox" refer to git-worktree directories (`packages/opencode/src/project/project.ts:244-247`, `402-425`).

## Configuration and defaults

Config keys and environment variables, character-exact at the pinned commit:

- Config `permission` object: keys `read`, `edit`, `glob`, `grep`, `list`, `bash`, `task`, `external_directory`, `todowrite`, `question`, `webfetch`, `websearch`, `lsp`, `doom_loop`, `skill`, plus arbitrary tool names; each value an action string or `{ pattern: action }` object (`packages/core/src/v1/config/permission.ts:17-36`). Config parsing preserves user key order for precedence (`config/permission.ts:14-16`).
- Env `OPENCODE_PERMISSION`: JSON merged into `result.permission`; invalid JSON is logged and skipped (`packages/opencode/src/config/config.ts:545-551`; flag read at `packages/core/src/flag/flag.ts:69-70`).
- Config `tools` map is translated to permission actions, with `write`/`edit`/`patch` folding into `perms.edit` (`config.ts:553-564`).
- Built-in default ruleset values (from `agent.ts:119-136`): `"*": "allow"`, `doom_loop: "ask"`, `external_directory: { "*": "ask", ... }`, `question: "deny"`, `plan_enter: "deny"`, `plan_exit: "deny"`, `read: { "*": "allow", "*.env": "ask", "*.env.*": "ask", "*.env.example": "allow" }`.
- Whitelisted external dirs auto-allowed: `Truncate.GLOB` (`tool-output` under `Global.Path.data`), `Global.Path.tmp/*`, skill dirs, reference dirs (`agent.ts:108-117`; `truncate.ts:17`; `truncation-dir.ts:4`; `Global.Path` built from XDG dirs, `packages/core/src/global.ts:11-29`).
- `subagent_depth` config, default `1`, bounds nested subagents (`task.ts:111-117`). If a default value is set rather than in code I would write `[EVIDENCE NEEDED]`, but here the `?? 1` is in code.
- Feature flags gating related surfaces (`packages/opencode/src/effect/runtime-flags.ts:41-53`): `OPENCODE_ENABLE_QUESTION_TOOL`, `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS`, `OPENCODE_EXPERIMENTAL_LSP_TOOL`, `OPENCODE_EXPERIMENTAL_PLAN_MODE`, `OPENCODE_EXPERIMENTAL_CODE_MODE`, `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS`. `experimental` features default to off unless `OPENCODE_EXPERIMENTAL` is true (`runtime-flags.ts:10-14`). bash default timeout is `flags.bashDefaultTimeoutMs ?? 2 * 60 * 1000` (`shell.ts:347`).
- codemode execution limits (`timeoutMs`, `maxToolCalls`, `maxOutputBytes`) all default to **none** by design ("execution budgets are host policy, not library policy", `packages/codemode/README.md` Execution Limits); the host `execute` tool creates the runtime without passing limits (`packages/opencode/src/tool/code-mode.ts:239-260`).

### Worktree "sandbox" workspaces (git-level isolation, not OS confinement)

The worktree service creates isolated working directories with `git worktree add --no-checkout` (`packages/opencode/src/worktree/index.ts:216-221`), branches named `opencode/<name>` (`worktree/index.ts:183`), under `Global.Path.data/worktree/<project.id>` (`worktree/index.ts:208`). Each created worktree directory is registered as a project sandbox via `project.addSandbox` (`worktree/index.ts:228`), which appends the directory to `Project.sandboxes`, a `Schema.Array(Schema.String)` field (`packages/schema/src/project.ts:39`; add/remove logic `packages/opencode/src/project/project.ts:229-247`, `402-441`). `reset` hard-resets a non-primary worktree to the default branch and cleans it (`worktree/index.ts:525-611`). This is a workspace/branch isolation convenience; it provides no filesystem or syscall restriction on what the agent may do inside the worktree (agent's file/bash permissions apply unchanged). The project-boundary check `containsPath` treats paths inside `ctx.directory` or `ctx.worktree` as in-bounds so they do not trigger `external_directory` (`packages/opencode/src/project/instance-context.ts:18-24`).

### codemode confined interpreter

`codemode` is an interpreter for a restricted JavaScript subset; a model-written program can only call the tools the host supplies and receives no ambient filesystem, process, network, module, or application authority (`packages/codemode/README.md:3-5`). Confinement mechanics at the pinned commit:

- The global scope is an explicit allowlist. The interpreter seeds only `tools`, `Promise`, `undefined`, `Object`, `Math`, `JSON`, `Number`, `String`, `Boolean`, `Array`, `console`, `parseInt`, `parseFloat`, `Date`, `RegExp`, `Map`, `Set`, `URL`, `URLSearchParams`, `encodeURI`/`encodeURIComponent`/`decodeURI`/`decodeURIComponent`, error constructors, `NaN`, `Infinity` (`packages/codemode/src/interpreter/runtime.ts:622-661`). There is no `eval`, `Function`, `globalThis`, `process`, `require`, timer, or module global.
- Unavailable syntax (modules/imports, classes, generators, timers, `eval`, prototype access, promise chaining) is rejected; the model-facing language section names this (`packages/codemode/src/tool-runtime.ts:604-611`; README "Supported Programs" and non-goals, `packages/codemode/README.md:236-256`, `349-356`).
- Values cross the host boundary only as plain data via `copyIn`/`copyOut`; blocked prototype members `__proto__`, `constructor`, `prototype` are rejected (`packages/codemode/src/tool-runtime.ts:152-154`); max nesting depth is the fixed constant `MAX_VALUE_DEPTH = 32` (`tool-runtime.ts:122`). Tool resolution refuses unknown paths and blocked members (`tool-runtime.ts:676-698`).
- Tool calls are counted against an optional `maxToolCalls`; concurrency is capped by `TOOL_CALL_CONCURRENCY` (`tool-runtime.ts:746-753`; README states at most 8 concurrent, `packages/codemode/README.md:249`, `288`).
- The reserved namespace `$codemode` is injected for discovery (`tool-runtime.ts:85`, `716-719`); hosts cannot define it (`tool-runtime.ts:478-482`).
- The host's `execute` tool filters the callable MCP catalog to what the merged agent+session ruleset allows via `Permission.visibleTools` (`packages/opencode/src/tool/code-mode.ts:209-212`), and each child MCP tool invocation still performs a permission ask `ctx.ask({ permission: entry.key, ..., patterns: ["*"], always: ["*"] })` (`code-mode.ts:146-148`). The `execute` tool is only registered when `experimentalCodeMode` is enabled (`packages/opencode/src/tool/registry.ts:118-119`, `226`, `246`); when enabled, the session skips exposing raw MCP tools directly (`packages/opencode/src/session/tools.ts:388`).
- Explicit non-goal: "A filesystem or process sandbox for arbitrary JavaScript" and "Generic permission prompts or approval workflows" (`packages/codemode/README.md:349-356`). codemode confines which tools a script can reach; it delegates authorization to the host's tools (`README.md:317-337`).

## Limitations and unknowns

- **Gating is trust-based per tool.** There is no central enforcer wrapping `item.execute`; each tool body must call `ctx.ask` (`packages/opencode/src/session/tools.ts:102-133`). A built-in tool that omitted `ctx.ask` would run unguarded. The codebase relies on convention here; I did not audit every tool for a missing ask beyond the ones anchored above.
- **Approval persistence is unresolved.** The `always` approvals live in in-memory `State.approved` scoped to the instance (`packages/opencode/src/permission/index.ts:23-26`, `145-151`). Schema types `PermissionApproval` (`packages/schema/src/v1/permission.ts:46-49`) and `PermissionSaved.Info` (`packages/schema/src/permission-saved.ts:14-19`) exist, and a `PermissionSaved` node is registered in the HTTP API server (`packages/opencode/src/server/routes/instance/httpapi/server.ts:60`, `233`), but I did not find the read/write path within this component. Whether `always` approvals survive a restart, and where, is `[EVIDENCE NEEDED]` (looked in `packages/opencode/src/permission/`, `session/`, `config/`; not found).
- **`*` rules are broad.** Because the wildcard compiles to a full-match `^...$` regex with `*` → `.*`, a pattern like `bash: "git * : allow"` semantics are literal regex; there is no path-canonicalization before matching edit patterns (patterns are the relative path string as computed). Symlink/`..` normalization behavior for permission patterns is not established by this code path.
- **No OS confinement is confirmed within searched scope.** I searched `packages/` for seatbelt/bubblewrap/landlock/seccomp/apparmor/sandbox-exec/chroot/unshare/setuid/rlimit and found none, and no `.sb`/`.profile` files. This is a claim about the pinned TypeScript tree; I did not inspect any shipped native binaries or out-of-tree helpers (there is no evidence of them in this checkout, but absence beyond the searched globs is not proven).
- **`OPENCODE_PERMISSION` is merged but not validated against the schema here**; malformed JSON is only logged and skipped (`config.ts:548-550`).
- The registry coverage note ("no OS-level sandbox ... within searched scope") is corroborated by my search, but the phrase "searched scope" is itself a boundary: I have not enumerated every package outside `packages/opencode` and `packages/codemode` for a hypothetical native sandbox.

## Relevance to the brief

This is central to RQ3 ("How does each system trade capability against safety in shell and file access?") and RQ1/RQ2 (permission/sandboxing as a harness component). The key comparative inference, separated from code facts:

- OpenCode's default posture is **allow-with-targeted-asks**: the base ruleset is `"*": "allow"` (`agent.ts:120`), so in-project edits and shell commands run without prompting, while out-of-project directory access, `.env` reads, and doom-loop repeats prompt. This differs sharply from Codex's model in the sibling note, where an OS sandbox + approval policy gates every command (`codexSandboxPermissions.md`). Where Codex confines by OS mechanism and Claude Code prompts by default via hooks/settings, OpenCode confines primarily by a permission ruleset plus two workspace-level conveniences (git worktree, codemode interpreter) and explicitly ships no OS sandbox.
- The pattern granularity story (arity-normalized bash patterns, worktree-relative edit patterns) is directly comparable to Codex's execpolicy prefix rules and is a concrete axis for the comparison matrix.
- It leaves open how these defaults behave in practice against a real repo (brief forbids live runs) and whether `always` approvals persist, both flagged above.

## Quotables for the report

- Three-action literal: `Schema.Literals(["allow", "deny", "ask"])` — `packages/schema/src/v1/permission.ts:16`. Framing: "OpenCode reduces every tool decision to allow/deny/ask."
- Default allow-all base: `"*": "allow"` — `packages/opencode/src/agent/agent.ts:120`. Framing: "OpenCode's base ruleset is allow-by-default with targeted asks."
- Last-match-wins: `rulesets.flat().findLast(...)` with `ask` fallback — `packages/opencode/src/permission/index.ts:31-36`. Framing: "Precedence is positional; user config wins because it is merged last."
- bash arity patterns: `scan.always.add(BashArity.prefix(tokens).join(" ") + " *")` — `packages/opencode/src/tool/shell.ts:409`. Framing: "`always` approvals generalize a command to its human-understandable prefix (e.g. `git checkout *`)."
- No-OS-sandbox non-goal: "A filesystem or process sandbox for arbitrary JavaScript" — `packages/codemode/README.md:355`. Framing: "OpenCode's confinement is interpreter- and ruleset-level, not OS-level."
- Confined-global allowlist: `globalScope.set("tools", ...)` with no `eval`/`process`/timers — `packages/codemode/src/interpreter/runtime.ts:629-661`. Framing: "The codemode interpreter seeds an explicit allowlist of globals and exposes only host-supplied tools."