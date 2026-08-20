# Synthesis: coding-agent harnesses (Claude Code, Codex, OpenCode)

Study: `2026-08_coding-agent-harnesses`. Basis: 33 notes in `notes/`, 12
ANALYZED claims (`CLM-E{1..4}-{1..3}a` in `.research/claims.jsonl`), and the
four static-trace experiments in `experiments/` (gate verdict PASS,
`experiments/gate-report.md`; 59/131/75/35 anchor checks re-verified). Pins:
codex `af700180808cce2ce28a31aad0fbad4dc58b857a`, opencode
`d545d8fba57283528db69281f59c803c646eb7e9`, claude-code
`c3d2e35e554060b5a20ee6b28140fbdbd4eb0048` (`sources/repos.yaml`,
pinned 2026-08-19). Claude Code docs snapshots fetched 2026-08-20. The
claude-code checkout carries no core code; its cells are docs-based,
surface-attested, or `[CLOSED]`. Blog-tier teardowns
(`minusXClaudeCodeTeardown`, `agiflowClaudeCodeInternals`, `tenguDecoded`)
support hedged context only, never a matrix cell on their own.

# Comparison matrix

| Dimension | Codex (af70018) | OpenCode (d545d8f) | Claude Code (c3d2e35 + docs) |
|---|---|---|---|
| Turn loop | Abortable background-task state machine: `Op` 27 variants, `TaskKind` 3, `TurnAbortReason` 4; spawn preempts with `Replaced`; continuation bit `needs_follow_up = model_needs_follow_up \|\| has_pending_input` (codexTurnLoop, protocol.rs:543-700; state/turn.rs:67-72; tasks/mod.rs:279-288; session/turn.rs:405; CLM-E1-1a) | Persistence-driven `while (true)` loop over stored messages; exit needs non-`tool-calls` finish + no pending tool parts + assistant parented to last user message; step verdict `compact\|stop\|continue`; `DOOM_LOOP_THRESHOLD = 3`, `RETRY_MAX_RETRIES = 5` (opencodeSessionLoop, prompt.ts:1088,:1106-1130; processor.ts:29-30,:679-681; retry.ts:31; CLM-E1-2a) | `[CLOSED]` core. Nearest seams: hook cadences (per session `SessionStart`/`SessionEnd`; per turn `UserPromptSubmit`/`Stop`/`StopFailure`; per tool call `PreToolUse`/`PostToolUse` "inside the agentic loop"); only numeric loop constant: stop-hook override after 8 consecutive blocks (claudeCodeDocsHooks, snapshot :20-24,:2397; CLM-E1-3a). Continuation condition, step cap, retry backoff `[EVIDENCE NEEDED]` |
| Tools and patch application | 32 handler-to-tool mappings (30 model-visible tool names) registered conditionally per turn; `shell_command` vs `exec_command`+`write_stdin` by shell tool type; `apply_patch` freeform string via 19-line Lark grammar gated on `model_info.apply_patch_tool_type`; no dedicated read/glob/grep tools; shell defaults 10 s / 1 MiB / 10,000 deltas (codexToolsPatch, spec_plan.rs:893-1229; apply_patch.lark; exec.rs; CLM-E2-1b) | Fixed ordered array of 17 tool IDs; `apply_patch` replaces `edit`/`write` for model IDs containing `gpt-` except `gpt-4`/`oss`; apply_patch is a port of the codex format ("Core types matching the Rust implementation"); `edit` = 9-stage replacer cascade, Levenshtein similarity 0.65 (opencodeTools, registry.ts:231-300; patch/index.ts:12; edit.ts; CLM-E2-2a) | Docs name 12 built-ins plus MCP tools (Bash, PowerShell, Edit, Write, Read, Glob, Grep, Agent, WebFetch, WebSearch, AskUserQuestion, ExitPlanMode; snapshot :1513); pinned surface attests 8 more (LS, NotebookRead, TodoWrite, KillShell, BashOutput, Task, MultiEdit, NotebookEdit); `ToolSearch` on by default and doubles as MCP wait point (claudeCodeDocsHooks, claudeCodeDocsMcp :279,:310; claudeCodePluginSurface; CLM-E2-3a). Full registry `[EVIDENCE NEEDED]`; core `[CLOSED]` |
| Context management and compaction | Fractional trigger: `auto_compact_token_limit = (window * 9) / 10` on a 95% effective window; local summarization caps user messages at 20,000 tokens; remote-v2 retains 64,000 tokens, agent messages capped 10,000, 2 retries (codexContextCompaction, openai_models.rs:376-378,:488-499; turn_context.rs:310-315; compact.rs:57; compact_remote_v2.rs:65-69; CLM-E4-1a) | Reserved-buffer trigger: overflow when count >= input limit - reserved, where reserved defaults to min(`COMPACTION_BUFFER`=20,000, `maxOutputTokens`); `PRUNE_MINIMUM` 20,000, `PRUNE_PROTECT` 40,000, `TOOL_OUTPUT_MAX_CHARS` 2,000, `PRUNE_PROTECTED_TOOLS = ['skill']`; retention clamps 25% of usable window to 2,000..15,000 tokens; unknown counts estimated as chars/4 (opencodeContextCompaction, overflow.ts:8-34; compaction.ts:28-33,:115-118; token.ts:3-5; CLM-E4-2a) | Seam only: `PreCompact`/`PostCompact` hooks (`manual`/`auto` trigger values; blocking recovery from context-limit surfaces the error), `compact_summary` in PostCompact input, `/compact` re-injects project-root CLAUDE.md but not nested files (claudeCodeDocsHooks :64-65; claudeCodeDocsMemory :450-454; CLM-E4-3a). All numeric thresholds `[EVIDENCE NEEDED]`; core `[CLOSED]` |
| Permissions and sandboxing | OS sandbox plus Starlark execpolicy engine: `Decision = {Allow, Prompt, Forbidden}`, strictest-wins `max()`; 4 `SandboxPolicy` variants; Seatbelt base policy (122 lines) compiled in, bubblewrap argv + seccomp/landlock network policy; `WritableRoot` protects `.git`/`.agents`/`.codex` metadata names (protocol/src/permissions.rs:24-33); 90-line banned amendable-prefix list; no `.rules` ships, example labeled "not recommended for actual use" (codexSandboxPermissions, decision.rs:9-16; policy.rs:402-403; protocol.rs:1003-1069; exec_policy.rs:58-147; seatbelt.rs:21-24; landlock.rs:179-253; bwrap.rs:267-360; CLM-E3-1a) | In-process permission ruleset only, no OS sandbox in the pinned tree: defaults `"*": allow`, `doom_loop: ask`, `question`/`plan_enter`/`plan_exit: deny`, read asks on `*.env`; bash commands normalized via longest-prefix-wins ARITY dictionary (~130 entries) before matching (opencodePermissions, agent.ts:119-136; arity.ts:1-161; shell.ts:409; CLM-E3-2a). Merge precedence `[EVIDENCE NEEDED]` | Two documented layers: permission rules evaluated before every tool (order deny, then ask, then allow; hook decisions `deny > defer > ask > allow`) plus OS sandbox that "applies only to Bash commands and their child processes"; Read/Edit/Write use the permission system directly; six modes default/acceptEdits/plan/auto/dontAsk/bypassPermissions; kill switches `disableBypassPermissionsMode`/`disableAutoMode`; macOS Seatbelt built in, Linux/WSL2 need bubblewrap + socat; no pre-allowed domains; protected paths (`.claude`, `.git/hooks`, ...) deny writes inside writable roots with no per-path exemption (claudeCodeDocsPermissions :34-69; claudeCodeDocsHooks :261; claudeCodeDocsSandboxing :117-148,:451-480,:504-525,:654-661; claudeCodePluginSurface examples/settings/README.md:27; CLM-E3-3a). Enforcement internals `[EVIDENCE NEEDED]`; core `[CLOSED]` |
| Extensibility | 11 hook events (9 matcher-capable, regex matchers); hooks content-hashed, run only when `Managed` or `Trusted`; `PreToolUse` can block/inject/rewrite (exit 2); plugins are `<plugin>@<marketplace>` bundling skills/hooks/`.mcp.json`/`.app.json`, discovered under `.codex-plugin`, `.claude-plugin`, `.cursor-plugin`; Claude-compat env `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA`; skills `SKILL.md` budgeted 2%/10k tokens; MCP config-defined with per-step overlay, protocol pinned 2025-06-18; `codex mcp-server` exposes exactly `codex` and `codex-reply` (codexExtensibility, hooks/lib.rs:23-52; discovery.rs:655-782; plugin_id.rs:26-43; skills_config.rs:40-43; mcp.rs:152-327; protocol_mode.rs:7-34; message_processor.rs:254) | Plugins are in-process TypeScript `(input, options?) => Promise<Hooks>`; dispatch sequential by registration order; 7 built-in agents (build, plan, general, explore, compaction, title, summary), explore read-only by ruleset except an explicit `bash: "allow"` (agent.ts:205); MCP client advertises only `roots` (sampling/elicitation disabled); skills discovered from `.claude`/`.agents` layouts and remote feeds; every skill doubles as a slash command; kill switches `OPENCODE_PURE` etc. (opencodeExtensibility, plugin/index.ts:220-295; agent/agent.ts:140-265; mcp/index.ts:39-50; skill/index.ts:186-227; command/index.ts:134-152; runtime-flags.ts:18-30). Plugins receive the SDK client; `permission.ask` hook declared but no trigger call site found | Docs: 31 hook events, 5 handler types (command/http/mcp_tool/prompt/agent); hooks run in parallel; agent hooks up to 50 turns; hooks also run inside subagents; workspace trust gates hooks except in `-p`/SDK sessions; plugins carry up to 10 component kinds (skills, commands, agents, hooks, `.mcp.json`, `.lsp.json`, monitors, bin, settings.json, `.claude-plugin/`); two marketplaces (claude-plugins-official, claude-community); subagents: Explore/Plan skip CLAUDE.md and git status, depth default 3 layers, 20-concurrent limit, fork shares prompt cache, per-subagent JSONL transcripts (claudeCodeDocsHooks; claudeCodeDocsPlugins L174-185,L351-367; claudeCodeDocsSubagents). Surface: exit-code contract 0/1/2, Stop-hook creates unbounded loops outside the core (ralph-wiggum) (claudeCodePluginSurface, examples/hooks/bash_command_validator_example.py:58-79; plugins/ralph-wiggum/hooks/stop-hook.sh:130-177). Core `[CLOSED]` |
| Configuration and providers | 10 layer provenances with numeric precedence -10..50; recursive table merge, overlay-wins for non-tables, arrays never union; project-local `.codex/config.toml` trust-gated and denied by a 12-key denylist from setting provider endpoints, model providers, notify, profile, realtime, and otel keys; built-in provider ids exactly `openai`, `amazon-bedrock`, `amazon-bedrock-runtime`, `ollama`, `lmstudio`; wire API is Responses-only (`chat` is a hard error); provider retries 4/5, stream idle timeout 300,000 ms; unknown model slugs fall back to a 272,000-token descriptor (codexConfigProviders, config_layer_source.rs:33-51; merge.rs:94-121; loader/mod.rs:71-84,:1056-1074; model-provider-info/src/lib.rs:56-90,:494-526) | Nine-layer precedence chain ending in managed config and macOS MDM plist ("override everything"); `.opencode` dir precedence is inverse of plain-file precedence; 24 bundled AI-SDK provider packages plus runtime `npm install` of arbitrary provider SDKs; hosted model catalog (models.opencode.ai) cached 5 min; `OUTPUT_TOKEN_MAX = 32,000`; `auth.json` plaintext `0o600`; unknown config keys silently dropped (opencodeConfigProviders, config.ts:398-534,:524-534; provider.ts:107-134,:1812-1830; models-dev.ts:160-164; transform.ts:18; auth/index.ts:73-89) | `[CLOSED]` loader code. Docs: settings hierarchy with managed policy non-excludable ("enforced by the client regardless of what Claude decides"); managed-policy CLAUDE.md paths per OS; CLAUDE.md itself is advisory context ("not a hard enforcement layer"); MCP scopes Local > Project > User > plugins > connectors, fields not merged across scopes; `.mcp.json` approvals gated on workspace trust (claudeCodeDocsMemory :278-298,:320; claudeCodeDocsMcp :434-520,:243-255). Provider env vars (Bedrock/Vertex/Foundry/Mantle) attested only via plugin hooks (claudeCodePluginSurface). Provider plumbing `[EVIDENCE NEEDED]` |
| State, rollout, sharing | Append-only JSONL rollouts under `sessions/YYYY/MM/DD/` (flush per record, retry once), first line `session_meta`; 6-DB SQLite mirror (WAL, 5 s busy) with read-repair fallback; reconstruction by reverse scan to a compaction base plus forward replay honoring rollbacks; cold rollouts zstd-compressed after 7 days; offline memory generation from rollouts (codexStateRollout, recorder.rs:1607-1629,:1968-1974; rollback_reconstruction via rollout_reconstruction.rs:114-437; sqlite.rs:29-34,:278-291; compression.rs:254-261) | SQLite session/message/part tables written exclusively by event projectors over a durable per-aggregate event log with contiguous sequence numbers; filesystem history as git tree objects in a shadow repo (never commits), 2 MiB skip, hourly gc `--prune=7.days`; revert = `git checkout <hash> -- <file>` in batches of 100; snapshots captured pre-stream and at every step-start/step-finish; sharing syncs to opncd.ai with 1000 ms debounce (opencodeStateSnapshots, session/sql.ts:22-98; event/sql.ts:4-25; snapshot/index.ts:23-24,:341-344,:425-458; processor.ts:424-470; share-next.ts:141-145) | `[EVIDENCE NEEDED]` for session storage. Docs attest per-subagent transcripts at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`, retained through restarts within a session and deleted after `cleanupPeriodDays` (default 30 days); hook input carries `transcript_path`, "written asynchronously and may lag" (claudeCodeDocsSubagents Claim 12; claudeCodeDocsHooks Claim 12). Core `[CLOSED]` |
| Interfaces | One binary dispatching TUI/exec/mcp-server/app-server/exec-server; every frontend is an app-server protocol client (JSON-RPC 2.0 without the `jsonrpc` field; `thread/start`, `turn/start`); approvals are server-to-client requests; exec defaults `AskForApproval::Never` and refuses non-git directories; backpressure error -32001; threads unload 30 min after last subscriber (codexInterfaces, cli/main.rs:132-230; app-server README; exec/lib.rs:409-411,:799-805; error_code.rs:7) | TUI is a client of an in-process HTTP server (fake base URL `http://opencode.internal`); HTTP routes include prompt_async/command/shell/summarize/fork/abort/share/revert/unrevert; port 0 prefers 4096; server auth off unless `OPENCODE_SERVER_PASSWORD`; ACP agent with protocolVersion 1, one auth method `opencode-login`, list limit 100; 38 built-in LSP servers; edit/write/apply_patch feed LSP diagnostics into tool output ("LSP errors detected in this file, please fix:"), severity-1 only, 20 per file (opencodeInterfaces, cli/cmd/tui.ts:238-249; routes instance httpapi; acp/service.ts:94-146,:246-290; core/v1/config/lsp.ts:22-61; tool/edit.ts:197-201) | `[CLOSED]` interface internals. Docs attest CLI, VS Code and JetBrains extensions, and desktop-app surfaces (claudeCodeDocsPermissions :58); MCP servers added via `claude mcp add` (http/sse/stdio/ws transports); plugins may ship `.lsp.json` (claudeCodeDocsMcp :68-155; claudeCodeDocsPlugins L174-185); reference confinement is an out-of-process devcontainer with an egress firewall (claudeCodePluginSurface, .devcontainer/init-firewall.sh:107-119). Protocol/transport details `[EVIDENCE NEEDED]` |

## Prose synthesis

### Q1. Where do the three genuinely differ? (primary question)

The three harnesses agree on the abstract contract, prompt in, sample,
execute tool calls, decide continue or stop, and diverge on every concrete
realization of it.

1. **Control flow.** Codex models a turn as an abortable Tokio task inside a
   state machine: a `Submission` envelope (`Op` with exactly 27 variants) is
   dispatched until `Op::Shutdown`, `spawn_task` preempts any running task
   with `TurnAbortReason::Replaced`, and the sampling loop continues while
   `needs_follow_up = model_needs_follow_up || has_pending_input`
   (codexTurnLoop; CLM-E1-1a). OpenCode is persistence-driven: a `while
   (true)` loop recomputes its exit condition from stored message parts each
   iteration, and each provider step returns the verdict `compact | stop |
   continue` (opencodeSessionLoop; CLM-E1-2a). Claude Code exposes no loop
   code; the docs attest a per-turn `UserPromptSubmit ... Stop/StopFailure`
   boundary nesting per-tool-call `PreToolUse`/`PostToolUse` events "inside
   the agentic loop", with the 8-consecutive-block stop-hook override as the
   only numeric loop constant (claudeCodeDocsHooks; CLM-E1-3a). The shared
   anti-loop instinct is implemented differently: Codex rejects steering
   inputs with an 8-variant `NotSubmittedReason` taxonomy; OpenCode raises a
   `doom_loop` permission ask after 3 byte-identical calls of the same tool;
   Claude Code caps blocking stop hooks at 8.

2. **Patch application is a converging format, not a converging policy.**
   Codex parses a freeform `apply_patch` string against a 19-line Lark
   grammar (codexToolsPatch). OpenCode ports the same format ("Core types
   matching the Rust implementation", opencode patch/index.ts:12) and switches
   between `apply_patch` and `edit`/`write` by model ID, `gpt-*` except
   `gpt-4`/`oss` (CLM-E2-2a). Claude Code's choice between `Edit`,
   `MultiEdit`, and `Write` is not documented (docs/surface attest the tools'
   existence only). Codex has no dedicated read/glob/grep tools; OpenCode and
   Claude Code both expose them. Codex registers tools conditionally per turn
    (32 mappings behind feature/model gates, covering 30 model-visible tool names); OpenCode ships a fixed 17-ID
   array; Claude Code's docs name 12 built-ins plus MCP tools and the pinned
   surface adds 8 more, with the full registry unverifiable.

3. **Safety architectures are structurally distinct.** Codex layers an OS
   sandbox (Seatbelt on macOS, bubblewrap argv plus seccomp/landlock network
   filtering on Linux) under a Starlark rule engine with strictest-wins
   aggregation, and ships no usable policy (only a 78-line example marked
   "not recommended for actual use") (CLM-E3-1a). OpenCode stays in-process:
   a default-allow ruleset with narrow friction (`.env` ask, doom-loop ask),
   command-arity normalization before matching, and no OS sandbox anywhere in
   the pinned tree (CLM-E3-2a). Claude Code documents a two-layer model where
   permission rules cover every tool but OS sandboxing "applies only to Bash
   commands and their child processes", with Read/Edit/Write on the
   permission layer, six permission modes, enterprise kill switches, and
   protected paths that cannot be individually exempted (CLM-E3-3a). Its
   reference confinement for untrusted repos is out-of-process: a devcontainer
   with an egress firewall (claudeCodePluginSurface).

4. **Compaction triggers: fraction vs reserved buffer.** Codex compacts at
   9/10 of a 95%-effective window and budgets retention explicitly (20,000
   user-message tokens locally; 64,000 retained with 10,000-per-agent-message
   caps remotely) (CLM-E4-1a). OpenCode compacts when the running count
   reaches input limit minus a 20,000-token reserved buffer, then preserves
   the last 40,000 tokens of tool output and clamps recent-message retention
   to 25% of usable window within 2,000..15,000 tokens (CLM-E4-2a). Claude
   Code discloses no threshold in any pinned snapshot; only the seam surface
   (hooks, `/compact` survival of root CLAUDE.md) is attestable (CLM-E4-3a).

5. **State stores: JSONL-first vs SQL-event-first vs undisclosed.** Codex
   keeps an append-only, human-inspectable JSONL rollout as source of truth
   with a repairable SQLite mirror and exact rebuild via reverse-scan +
   forward-replay (codexStateRollout). OpenCode keeps SQLite tables rebuilt
   by event projectors from a durable event log, and treats file undo as
   first-class state through shadow-git tree objects captured at every step
   (opencodeStateSnapshots). Claude Code session storage is not inspectable;
   docs attest only subagent transcript files and a 30-day cleanup default
   (claudeCodeDocsSubagents).

6. **Interfaces: protocol-first vs server-first.** Codex routes every
   frontend (TUI, exec, app-server, exec-server) through one JSON-RPC
   protocol with approvals as server-to-client requests and a dedicated
   backpressure error (codexInterfaces). OpenCode runs a local HTTP/OpenAPI
   server that its own TUI consumes, plus an ACP implementation and 38
   built-in LSP servers whose diagnostics are fed back into edit results
   (opencodeInterfaces). Claude Code's docs confirm multiple surfaces but the
   transports are closed.

### Q2. What components make up a coding-agent harness?

Cross-system, a harness decomposes into eight machinery dimensions, each
independently implemented by all three systems: turn loop; tool surface and
file-edit protocol; context assembly and compaction; memory files; permission
and sandbox policy; extensibility (hooks, plugins, skills, subagents, MCP);
configuration and provider plumbing; and session state with durable storage
plus user interfaces. The framing literature supplies the same decomposition
at the abstraction level: ReAct's interleave of reasoning traces and
environment actions (yao2023react), Toolformer's interrupt-execute-resume
tool protocol and its observation that tool leverage emerges only at scale
(schick2023toolformer), and SWE-agent's agent-computer interface result,
where interface design (a guarded edit command, lint gating, windowed file
viewing) moved SWE-bench Lite resolution from 11.0% (shell-only) to 18.0%
with GPT-4 Turbo (yang2024sweagent). The three studied harnesses are
industrial implementations of exactly that interface layer: every system
invests in a structured edit path, a tool-filtering policy, and explicit
context-budget machinery, confirming the interface as a first-order harness
component rather than a UI detail.

### Q3. How does each system trade capability against safety?

- Codex spends capability on gating rather than withholding: wide shell
  access with per-command execpolicy evaluation, OS-level confinement,
  trust-gated project configuration (with an explicit denylist keeping repo
  content away from credential routing), and hook trust by content hash. Its
  conservative move is shipping no default policy content.
- OpenCode spends on capability: default-allow for all tools, in-process
  rules as the only safety layer, but invests in recoverability instead of
  prevention (per-step snapshots, revert/unrevert), with friction points at
  `.env` reads, doom loops, and external directories. Its plugin surface is
  the widest trusted-compute exposure of the three (plugins get the SDK
  client in-process) and the `permission.ask` hook appears dead at this
  commit.
- Claude Code splits the two concerns across layers: an advisory instruction
  layer (CLAUDE.md, "shape Claude's behavior but are not a hard enforcement
  layer") and an enforcement layer (permission rules, Bash-only OS sandbox,
  managed settings). The sandbox's explicit Bash-only scope means capability
  (Read/Edit/Web tools run unsandboxed) is traded against a narrow,
  well-enforced shell boundary; the documentation itself warns that argument
  patterns are evadable and pushes deny rules or hooks instead.

### Q4. What does Claude Code's closed core reveal?

Three evidence classes remain: (1) official docs, which are rich on
behavioral contracts (31 hook events, six permission modes, sandbox scope,
memory loading order, subagent quotas) but carry no numeric compaction
thresholds and no loop implementation; (2) the pinned plugin/example surface,
which shows the extension protocol in executable form (exit-code contract,
Stop-hook agent loops, devcontainer confinement) and drift between bundled
skill docs and the changelog; (3) third-party teardowns, usable only as
hedged context. The teardowns assert, among other things, a ~2,800-token
system prompt with ~9,400 tokens of tools and >50% of "important" calls
routed to a small model (minusxClaudeCodeTeardown, unverified), and catalog
counts such as 243 feature flags, 1,163 telemetry events, and 49 built-in
tools at v2.1.197 (tenguDecoded, unverified). Agiflow's trace excerpts
suggest CLAUDE.md arrives as `system-reminder`-wrapped user content after the
system prompt, a shape corroborated by the official memory docs
(agiflowClaudeCodeInternals, cross-verified against claudeCodeDocsMemory).

### Conflicts and resolutions

- OpenCode MCP default timeout: config schema annotation says 5 s, the code
  constant is `DEFAULT_TIMEOUT = 30,000` ms. Conflict preserved as
  `[EVIDENCE NEEDED]` in opencodeExtensibility; report cites both and does
  not adjudicate (opencodeExtensibility, mcp/index.ts:38 vs
  core/src/v1/config/mcp.ts:21).
- OpenCode `.opencode` directory precedence is inverse to plain-file
  precedence (farther-from-cwd wins). Recorded as a code fact, not a
  conflict; whether intentional is open (opencodeConfigProviders,
  paths.ts:23-41).
- Claude Code bundled skill docs say command hooks default to 60 s while the
  changelog records a 60 s to 10-minute change; docs-surface drift, marked
  `[CLOSED]` (claudeCodePluginSurface, plugins/plugin-dev/skills/
  hook-development/SKILL.md:491 vs CHANGELOG.md:4287).
- Codex `load_config_layers_state` doc comment disagrees with README + code
  on where legacy managed layers sit; the note trusts README + code
  (codexConfigProviders, loader/mod.rs:105-117 vs README.md:26-36).
- Registry's opencode `examples/` mention vs codex holding only a codegen
  helper there (codexConfigProviders Limitations); negative finding kept.

### Gap register (carried into report Limitations)

- Claude Code numeric compaction thresholds: `[EVIDENCE NEEDED]` (CLM-E4-3a);
  the referenced survival page /docs/en/context-window is not in the snapshot
  set.
- Claude Code turn-loop implementation (continuation condition, step cap,
  retry backoff): `[EVIDENCE NEEDED]` (CLM-E1-3a).
- Claude Code complete tool registry and provider plumbing: `[EVIDENCE
  NEEDED]` (CLM-E2-3a; claudeCodePluginSurface limitations).
- Claude Code sandbox enforcement mechanisms beyond documented scope:
  `[EVIDENCE NEEDED]` (CLM-E3-3a).
- OpenCode permission merge precedence and runtime enforcement of
  schema-description defaults: `[EVIDENCE NEEDED]` (opencodePermissions,
  opencodeConfigProviders).
- Codex remote model catalog contents and enterprise cloud bundle contents:
  server-side state, `[EVIDENCE NEEDED]` (codexConfigProviders).
- Blog-tier teardowns carry unverified assertions (token counts, flag
  catalogs, model routing); never used to fill a matrix cell
  (minusXClaudeCodeTeardown, tenguDecoded, agiflowClaudeCodeInternals).
- All findings are bounded to the three pinned commits and the 2026-08-20
  docs snapshots; nothing generalizes to newer versions (gate-report).
