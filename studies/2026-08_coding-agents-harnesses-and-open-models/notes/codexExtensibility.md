---
source_key: "codexExtensibility"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "codex"
commit: "af700180808cce2ce28a31aad0fbad4dc58b857a"
---

# Notes: Codex extensibility, MCP server/client, hooks, skills, plugins (codex)

## Source identification

- Key: codexExtensibility
- Repository: `codex` at `af700180808cce2ce28a31aad0fbad4dc58b857a` (see `sources/repos.yaml`)
- Component scope: `codex-rs/mcp-server/`; `codex-rs/rmcp-client/`; `codex-rs/hooks/` (schema + runtime); `codex-rs/skills/`; `codex-rs/plugin/`; `codex-rs/core-plugins/`; `codex-rs/connectors/`; `codex-rs/core/src/plugins/`; `codex-rs/core/src/skills.rs`; `codex-rs/core/src/hook_runtime.rs`; `codex-rs/core/src/hook_mcp_executor.rs`; `codex-rs/core/src/mcp.rs`; `codex-rs/core/src/mcp_skill_dependencies.rs`. Supporting files read for anchors: `codex-rs/config/src/hook_config.rs`, `codex-rs/config/src/skills_config.rs`, `codex-rs/config/src/mcp_types.rs`, `codex-rs/config/src/types.rs`, `codex-rs/config/src/hooks_tests.rs`, `codex-rs/config/src/config_toml.rs`, `codex-rs/config/src/loader/mod.rs`, `codex-rs/features/src/lib.rs`, `codex-rs/hooks/src/events/` (pre_tool_use, common, session_end), `codex-rs/hooks/src/output_spill.rs`, `codex-rs/hooks/src/mcp.rs`, `codex-rs/connectors/src/lib.rs`, `codex-rs/exec-server-protocol/src/protocol.rs`, `codex-rs/cli/src/main.rs`.
- Tier: codebase

## Purpose and role in the harness

This component is Codex's third-party extension surface: it decides everything the model can use beyond built-in tools, and when external code runs around the agent loop.

- MCP servers are the primary integration axis. Users register servers under `[mcp_servers.<name>]` (`codex-rs/config/src/config_toml.rs:261-263`); plugins and extensions contribute servers that are layered onto the user config at runtime (`codex-rs/core/src/mcp.rs:152-271`); and Codex itself runs as an MCP server via `codex mcp-server`, exposing the whole agent as two tools (`codex-rs/mcp-server/src/message_processor.rs:254`, `356-369`).
- Hooks give external code control points on the session lifecycle with Claude Code compatible event names, regex matchers, and hash-based trust gating (`codex-rs/hooks/src/lib.rs:22-35`, `codex-rs/hooks/src/engine/discovery.rs:771-782`).
- Skills are Markdown packages (`SKILL.md` + frontmatter) injected into model context within a token budget (`codex-rs/skills/src/parser.rs:22-41`, `codex-rs/config/src/skills_config.rs:40-43`).
- Plugins bundle skills, hooks, MCP servers, and apps, distributed through git or local marketplaces including OpenAI's curated `openai/plugins` repo (`codex-rs/core-plugins/src/loader.rs:64-68`, `codex-rs/core-plugins/src/startup_sync.rs:23-30`).
- Connectors model hosted app integrations (e.g. first-party "codex_apps") fronted by an in-process MCP server and cached with a 1h TTL (`codex-rs/connectors/src/lib.rs:56-58`, `codex-rs/core/src/mcp.rs:245-259`).

All of this is feature-flagged and stable-by-default: `hooks`, `plugins`, `skill_mcp_dependency_install`, and `skill_search` are `Stage::Stable` with `default_enabled: true` (`codex-rs/features/src/lib.rs:1027-1032`, `1199-1204`, `1319-1324`, `1325-1330`).

## Mechanism

### MCP client: configuration surface

- A server entry deserializes through `RawMcpServerConfig` with two transport shapes: stdio (`command`, `args`, `env`, `env_vars`, `cwd`) and streamable HTTP (`url`, `bearer_token`, `bearer_token_env_var`, `http_headers`, `env_http_headers`, `http_headers_helper`), plus shared `environment_id`, `auth`, timeouts, `enabled`, `required`, and tool allow/deny lists (`codex-rs/config/src/mcp_types.rs:302-339`).
- Transport validation rejects HTTP-only fields on stdio servers (`codex-rs/config/src/mcp_types.rs:422-425`) and restricts `http_headers_helper` to local servers with a non-empty value (`codex-rs/config/src/mcp_types.rs:445-458`).
- The effective `McpServerConfig` adds behavioral policy: `auth` defaults to `oauth` with an alternative `chatgpt` flow that reuses the ChatGPT session for trusted first-party origins (`codex-rs/config/src/mcp_types.rs:154-172`); `enabled` defaults true (`190-194`); `required` makes `codex exec` exit with an error if initialization fails (`196-198`); `supports_parallel_tool_calls` advertises all tools as parallel-safe (`200-202`); `omit_tools_from` hides tools per model-facing surface (`204-207`); approval is layered as `default_tools_approval_mode`, `enabled_tools`, `disabled_tools`, and a per-tool `tools` map (`225-252`).
- `environment_id` defaults to `local`; non-local environments isolate OAuth credentials with an `executor:<env>:<server>` key prefix while local ones reuse stored credentials (`codex-rs/config/src/mcp_types.rs:254-272`).

### MCP client: runtime assembly

- `McpManager` projects an `McpConfig` per step by merging, in order: user/profile-managed servers, selected-plugin servers, and runtime extension overlays (`Set`, `HostedApps`, `SelectedPlugin`, `SelectedPluginPackage`, `Remove`), each tagged with a contributor id and a global `contribution_order` (`codex-rs/core/src/mcp.rs:152-234`).
- When `apps_enabled`, the built-in `codex_apps` server is registered through a compatibility path; otherwise it is removed (`codex-rs/core/src/mcp.rs:245-259`).
- Environment authority gates which servers a thread may use: the default environment is `Unrestricted`; non-default environments resolve to `SelectedPluginsOnly` unless the thread selected them, and their `mcp_policy` can further `Restrict` or mark them `Unavailable` while pending/failed (`codex-rs/core/src/mcp.rs:272-304`). Conflicting contributor actions are warned and resolved by catalog outcome (`305-312`).
- Selected plugin packages also contribute connector sources that are merged into the connector snapshot (`codex-rs/core/src/mcp.rs:214-222`, `314-319`).

### MCP client: protocol compatibility and credentials (rmcp-client)

- Sessions pick one `McpProtocolMode`: `Legacy` (default) pins MCP protocol version `2025-06-18`, while `V20260728` allows the 2026-07-28 lifecycle with legacy fallback (`codex-rs/rmcp-client/src/protocol_mode.rs:7-34`).
- Stdio servers stay on Legacy unless both the session mode and the server opt in via `CODEX_MCP_PROTOCOL_VERSION=2026-07-28`; unknown values on a modern session are an error (`codex-rs/rmcp-client/src/protocol_mode.rs:36-51`).
- MCP OAuth credentials are stored in the OS keyring via the `keyring` crate, falling back to `CODEX_HOME/.credentials.json` when the keyring is unavailable ("consistent with other coding CLI agents", per the module comment) (`codex-rs/rmcp-client/src/oauth.rs:1-17`).

### MCP server mode (codex as a tool provider)

- `codex mcp-server` is a CLI subcommand (`codex-rs/cli/src/main.rs:157`, `1181-1187`). The server identifies as `Implementation::new("codex-mcp-server", ...)` with title `Codex` (`codex-rs/mcp-server/src/message_processor.rs:254`).
- It exposes exactly two tools, `codex` and `codex-reply`, handled by `handle_tool_call_codex` and `handle_tool_call_codex_session_reply`; unknown tools return an error result (`codex-rs/mcp-server/src/message_processor.rs:356-369`, `codex-rs/mcp-server/src/codex_tool_config.rs:237`). (My inference: this is the interface other MCP clients use to drive Codex turns and continue sessions.)

### Hooks: schema and discovery

- Eleven events, character-exact: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` (`codex-rs/hooks/src/lib.rs:23-35`). Nine of them honor `matcher` fields (`PreToolUse`...`SubagentStop`, except `UserPromptSubmit` and `Stop`) (`codex-rs/hooks/src/lib.rs:37-52`). Matchers are regexes, validated with `regex::Regex::new` (`codex-rs/hooks/src/events/common.rs:128-132`).
- Handler types (`codex-rs/config/src/hook_config.rs:147-187`):
  - `command`: shell `command` (plus `commandWindows`), `timeout`, `async`, `statusMessage`, and `additionalContextLimit` (spill threshold in tokens, default 2,500, `0` disables spilling) (`151-171`).
  - `mcp_tool`: `server` + `tool` + static `input` (must round-trip to TOML for trust hashing) + `timeout` + `statusMessage` (`172-182`).
  - `prompt` and `agent`: declared but carry no fields in this schema (`183-186`) (see Limitations).
- Sources, ordered low-to-high by the config layer stack: (1) enterprise "managed hooks" requirements, which can hard-require handlers (`codex-rs/hooks/src/engine/discovery.rs:205-239`) and can restrict discovery to managed hooks only via `allow_managed_hooks_only` (`104-113`); (2) each config layer's optional `hooks.json` file in that layer's folder (`143-148`, `336-340`) or inline `[hooks]` TOML (`codex-rs/config/src/config_toml.rs:442-443`; both present produces a warning, `discovery.rs:151-161`); (3) plugin hooks (`241-292`). For trusted project checkouts, the project root's `[hooks]` table replaces lower layers' hooks (`codex-rs/config/src/loader/mod.rs:1560-1576`).
- Plugin hooks load from `hooks/hooks.json` in the plugin root (`codex-rs/core-plugins/src/loader.rs:65`, `1166-1209`) or from inline `hooks` entries in the plugin manifest, sourced as `plugin.json#hooks[i]` (`codex-rs/core-plugins/src/loader.rs:1190-1204`). Plugin hook commands receive `PLUGIN_ROOT`, `CLAUDE_PLUGIN_ROOT`, `PLUGIN_DATA`, and `CLAUDE_PLUGIN_DATA` env vars, the latter two "For OOTB compat with existing plugins" (`codex-rs/hooks/src/engine/discovery.rs:259-267`), an explicit Claude Code plugin compatibility seam.

### Hooks: trust model and gating

- Every discovered hook gets a stable key `<key_source>:<event>:<group_index>:<handler_index>`, e.g. `demo@test:hooks/hooks.json:pre_tool_use:0:0` (`codex-rs/hooks/src/engine/discovery.rs:656`, `codex-rs/hooks/src/declarations.rs:88-96`).
- Per-hook state lives under `hooks.state.<key>` with `enabled` and `trusted_hash` (`codex-rs/config/src/hook_config.rs:27-33`).
- Trust status is computed from the hook content hash against `trusted_hash`: `Managed` (admin requirements), `Trusted` (hash equal), `Modified`, `Untrusted` (`codex-rs/hooks/src/engine/discovery.rs:771-782`). A handler only becomes runnable when enabled and (trust bypassed, or status is `Managed`/`Trusted`) (`693-713`). Hook state keys observed in tests use `sha256:`-prefixed hashes (`codex-rs/config/src/hooks_tests.rs:196-198`, `227-232`).

### Hooks: dispatch, outcomes, and runtime glue

- Core drives hooks through per-event entrypoints: `run_pending_session_start_hooks`, `run_pre_tool_use_hooks`, `run_permission_request_hooks`, `run_post_tool_use_hooks`, `run_turn_stop_hooks`, `run_session_end_hooks`, `run_pre_compact_hooks`, `run_post_compact_hooks`, `run_legacy_after_agent_hook`, plus `inspect_pending_input`/`record_pending_input`/`drain_async_hook_results` for queued prompts (`codex-rs/core/src/hook_runtime.rs:111-615`).
- `PreToolUseOutcome` can block with a reason, add model-visible additional contexts, or rewrite tool input (`codex-rs/hooks/src/events/pre_tool_use.rs:39-44`). A command hook exiting code 2 blocks, with stderr as the reason and a fallback message when stderr is empty (`264-274`); the last-completing hook's `updated_input` wins (`129-134`, `153-166`).
- MCP-tool hooks execute through `HookMcpExecutor` (`codex-rs/hooks/src/mcp.rs:7-22`), implemented in core by `CoreHookMcpExecutor`, which calls `McpRuntime::latest_call_tool` with `{"threadId": ...}` metadata, the configured timeout, and `wait_for_server = false`, then flattens text content and fails on `isError` (`codex-rs/core/src/hook_mcp_executor.rs:12-50`).
- Timeouts: command hooks default to 600s with a 1s floor (`codex-rs/hooks/src/engine/discovery.rs:727-728`); `SessionEnd` overrides that with a 1s default clamped to a maximum of 3s with a warning (`codex-rs/hooks/src/events/session_end.rs:20`, `codex-rs/hooks/src/engine/discovery.rs:719-740`).
- Large `additionalContext` is spilled to disk once over the hook's token limit (default 2,500 tokens), with a preview plus recovery metadata (`codex-rs/hooks/src/output_spill.rs:11-12`, `codex-rs/config/src/hook_config.rs:161-170`).

### Skills: format, discovery, and context budget

- A skill is a `SKILL.md` with YAML frontmatter: `name` (max 64 chars, falls back to a default from the directory), required `description`, and optional `metadata.short-description`; values are sanitized to single lines (`codex-rs/skills/src/parser.rs:4-14`, `22-92`). Invalid YAML gets a conservative line-based repair pass aimed at prose-like scalar values such as `description: Build for AWS: ECS` (`52-62`, `98-120`).
- Skills come from host roots and plugin `skills/` directories; the plugin loader defaults skill discovery to a `skills` dir in the plugin root (`codex-rs/core-plugins/src/loader.rs:64`, `1064-1083`). The `SkillScope` taxonomy is `User`/`Repo`/`System`/`Admin` (`codex-rs/core/src/skills.rs:103-108`).
- Core builds the host load input from cwd, effective skill roots, and the config layer stack (`codex-rs/core/src/skills.rs:25-34`). Explicit mentions vs injected skills are reconciled for telemetry, and implicit invocations (e.g. the model running a skill's command) are detected once per session per skill via a seen-set keyed `scope:path:name` (`codex-rs/core/src/skills.rs:36-160`).
- The catalog is context-budgeted: `max_context_tokens` defaults to 2% of the model context window and is capped at 10,000 tokens when set (`codex-rs/config/src/skills_config.rs:40-43`); `include_instructions` toggles the automatic skills instructions block (`36-38`); `[[skills.config]]` entries enable/disable skills by `path` or `name` (`20-28`, `45-46`); bundled skills are on by default (`49-60`).

### Skill-declared MCP dependencies

- Skills can declare MCP server dependencies that the harness offers to install before use. Feature `skill_mcp_dependency_install` is Stable, default on (`codex-rs/features/src/lib.rs:1319-1324`).
- When a declared dependency is missing, the user sees a `skill_mcp_dependency_install` prompt with options `Install` and `Continue anyway` (`codex-rs/core/src/mcp_skill_dependencies.rs:36-38`). Dependencies already prompted this session are skipped, and servers that managed or attachment policy would reject are not prompted (`codex-rs/core/src/mcp_skill_dependencies.rs:66-80`, `327-346`).
- Supported transports are `streamable_http` (default, requires `url`) and `stdio` (requires `command`), case-insensitive (`codex-rs/core/src/mcp_skill_dependencies.rs:378-391`, `396-441`).

### Plugins and marketplaces

- A plugin is identified `<plugin>@<marketplace>`; parsing error: "invalid plugin key `{plugin_key}`; expected `<plugin>@<marketplace>`" (`codex-rs/plugin/src/plugin_id.rs:26-43`). Segments must be ASCII alphanumeric plus `-`/`_` (plugin names may also use `.`, with traversal blocked) (`50-79`).
- `PluginManifest` is a `plugin.json` with `name`, optional `version`, and paths for `skills`, `mcp_servers`, `apps`, `hooks`, plus an `interface` block (`codex-rs/plugin/src/manifest.rs:8-42`). In-repo discoverable manifest locations include `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.cursor-plugin/plugin.json` (`codex-rs/exec-server-protocol/src/protocol.rs:46-49`), so Codex plugins can live in Claude or Cursor plugin layouts.
- Plugins ship: skills (default `skills/` dir), hooks (`hooks/hooks.json` or manifest-inline), MCP servers (`.mcp.json`), and apps (`.app.json`), with a plugin-local `config.toml` (`codex-rs/core-plugins/src/loader.rs:64-68`, `1081-1083`, `1101`, `1155`).
- Storage: cached plugin checkouts under `plugins/cache`, plugin data under `plugins/data`, agent plugins under `agent-plugins`, default version `local` (`codex-rs/core-plugins/src/store.rs:25-28`); marketplace clones under `CODEX_HOME/.tmp/marketplaces` (`codex-rs/core-plugins/src/installed_marketplaces.rs:12-15`).
- A curated OpenAI plugin catalog syncs from `https://github.com/openai/plugins.git` against `https://api.github.com` at startup (`codex-rs/core-plugins/src/startup_sync.rs:23-30`).
- User config keys plugins by `plugin@marketplace`: `enabled` plus per-MCP-server policy overlays (`codex-rs/config/src/types.rs:843-852`, `codex-rs/config/src/config_toml.rs:445-447`). The policy split is explicit in code: "plugin manifests own how the MCP server is launched, while user config owns enablement and tool policy" (`codex-rs/config/src/types.rs:854-857`). Marketplaces record `source_type` (`git`/`local`), `source`, `ref`, and sparse checkout paths (`codex-rs/config/src/types.rs:894-922`).

### Connectors and apps

- Connectors are remote app integrations with a directory cache and metadata cache TTL of 3,600 seconds (`CONNECTORS_CACHE_TTL`, `CONNECTOR_METADATA_CACHE_TTL`) (`codex-rs/connectors/src/lib.rs:56-58`).
- The first-party surface is the in-process `codex_apps` MCP server, registered as a compatibility built-in when apps are enabled (`codex-rs/core/src/mcp.rs:245-259`); plugins can contribute connector ids through `SelectedPluginPackage` contributions (`203-222`, `314-319`).
- Apps are toggled in config via `[apps]` with a `_default` section plus per-app entries keyed by app id (`codex-rs/config/src/config_toml.rs:492`, `codex-rs/config/src/types.rs:493-501`).

## Key facts with anchors

- Eleven hook events, nine matcher-capable (`codex-rs/hooks/src/lib.rs:23-35`, `42-52`); matchers are regexes (`codex-rs/hooks/src/events/common.rs:128-132`).
- Hook handlers are commands or MCP tool calls; command hooks default to 600s, `SessionEnd` to 1s max 3s (`codex-rs/config/src/hook_config.rs:147-187`, `codex-rs/hooks/src/engine/discovery.rs:719-740`).
- Hooks are content-hashed and only run if `Managed` or `Trusted` (`codex-rs/hooks/src/engine/discovery.rs:655-713`, `771-782`).
- Plugin hook env exports Claude compat vars `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` (`codex-rs/hooks/src/engine/discovery.rs:259-267`).
- `PreToolUse` hooks can block, inject context, or rewrite tool input; exit code 2 means block (`codex-rs/hooks/src/events/pre_tool_use.rs:39-44`, `264-274`).
- MCP servers are config-defined and plugin/extension-overlaid per step, with environment-based authority (`codex-rs/core/src/mcp.rs:152-327`).
- MCP protocol is pinned to 2025-06-18 by default; 2026-07-28 is per-session opt-in (`codex-rs/rmcp-client/src/protocol_mode.rs:7-34`).
- MCP OAuth uses OS keyring with a `CODEX_HOME/.credentials.json` fallback (`codex-rs/rmcp-client/src/oauth.rs:1-17`).
- `codex mcp-server` exposes exactly `codex` and `codex-reply` (`codex-rs/mcp-server/src/message_processor.rs:254`, `356-369`).
- Skills are `SKILL.md` documents with name (<=64 chars) and required description, budgeted at 2%/10k tokens of catalog context (`codex-rs/skills/src/parser.rs:4`, `82`, `codex-rs/config/src/skills_config.rs:40-43`).
- Skills can trigger MCP dependency install prompts (`Install` / `Continue anyway`) for `streamable_http` (default) or `stdio` servers (`codex-rs/core/src/mcp_skill_dependencies.rs:36-38`, `378-391`).
- Plugins are `<plugin>@<marketplace>` packages bundling skills, hooks, `.mcp.json`, and `.app.json`, discovered under `.codex-plugin`, `.claude-plugin`, and `.cursor-plugin` (`codex-rs/plugin/src/plugin_id.rs:26-43`, `codex-rs/core-plugins/src/loader.rs:64-68`, `codex-rs/exec-server-protocol/src/protocol.rs:46-49`).
- A curated plugin marketplace syncs from `https://github.com/openai/plugins.git` (`codex-rs/core-plugins/src/startup_sync.rs:23-30`).
- `hooks`, `plugins`, `skill_mcp_dependency_install`, `skill_search` are Stable/default-on; `plugin_hooks` is `Stage::Removed` (`codex-rs/features/src/lib.rs:1027-1032`, `1199-1204`, `1211-1216`, `1319-1330`).

## Configuration and defaults

Config TOML keys (`codex-rs/config/src/config_toml.rs:439-457`):

- `[skills]`: `include_instructions` (auto skills instruction block), `max_context_tokens` (default 2% of context window, capped at 10,000 when set), `[[skills.config]]` (`path`/`name` selector + `enabled`), and `bundled.enabled` (default true) (`codex-rs/config/src/skills_config.rs:20-60`).
- `[hooks]`: inline event tables using PascalCase keys `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop`, plus `hooks.state.<key>` = `{ enabled, trusted_hash }` (`codex-rs/config/src/hook_config.rs:27-58`, `codex-rs/config/src/config_toml.rs:442-443`). Per-layer `hooks.json` files sit in each layer's hooks folder (`codex-rs/hooks/src/engine/discovery.rs:143-148`, `336-340`); trusted project roots override with their own `[hooks]` (`codex-rs/config/src/loader/mod.rs:1560-1576`).
- `[mcp_servers.<name>]`: transport fields (`command`/`args`/`env`/`env_vars`/`cwd` or `url`/`bearer_token`/`bearer_token_env_var`/`http_headers`/`env_http_headers`/`http_headers_helper`), `auth` (default `oauth`, alternative `chatgpt`), `enabled` (default true), `required` (default false), `supports_parallel_tool_calls` (default false), `omit_tools_from`, `startup_timeout_sec`/`startup_timeout_ms`, `tool_timeout_sec`, `default_tools_approval_mode`, `enabled_tools`, `disabled_tools`, `scopes`, `oauth`, `oauth_resource`, and per-tool `[mcp_servers.<name>.tools.<tool>]` (`codex-rs/config/src/mcp_types.rs:154-252`, `302-339`). `environment_id` defaults to `local` (`codex-rs/config/src/mcp_types.rs:254-257`).
- `[plugins.<plugin>@<marketplace>]`: `enabled` (default true) and `[plugins.<plugin>@<marketplace>.mcp_servers.<server>]` with `enabled`, `default_tools_approval_mode`, `enabled_tools`, `disabled_tools`, `tools` (`codex-rs/config/src/types.rs:843-892`).
- `[marketplaces.<name>]`: `last_updated`, `last_revision`, `source_type` (`git`/`local`), `source`, `ref`, `sparse_paths` (`codex-rs/config/src/types.rs:894-922`).
- `[apps]`: `_default` plus per-app tables keyed by app id, e.g. `[apps.google_drive]` (`codex-rs/config/src/types.rs:493-501`).
- `[features]`: `hooks`, `plugins`, `skill_mcp_dependency_install`, `skill_search` default-enabled Stable; `plugin_hooks` Removed (`codex-rs/features/src/lib.rs:1027-1032`, `1199-1204`, `1211-1216`, `1319-1330`).
- `[tool_suggest]`: additional discoverable tools suggestable for installation (`codex-rs/config/src/config_toml.rs:427-428`).
- Environment: `CODEX_MCP_PROTOCOL_VERSION=2026-07-28` opts a stdio MCP server into the modern lifecycle (`codex-rs/rmcp-client/src/protocol_mode.rs:36-51`); plugin hook commands get `PLUGIN_ROOT`, `CLAUDE_PLUGIN_ROOT`, `PLUGIN_DATA`, `CLAUDE_PLUGIN_DATA` (`codex-rs/hooks/src/engine/discovery.rs:259-267`).
- Paths: plugin cache `plugins/cache`, plugin data `plugins/data`, agent plugins `agent-plugins` (`codex-rs/core-plugins/src/store.rs:25-28`); marketplace clones `.tmp/marketplaces` (`codex-rs/core-plugins/src/installed_marketplaces.rs:12-15`); hooks outputs spill under a `hook_outputs` dir with a 2,500-token default limit (`codex-rs/hooks/src/output_spill.rs:11-12`).

## Limitations and unknowns

- MCP transport lifecycle, retry, elicitation, and tool-call execution live in `codex-rs/codex-mcp/`, which belongs to the `codexInterfaces` component, not this note's scope. The default values for `startup_timeout_sec`/`tool_timeout_sec` are not set in the config crate and resolve downstream there (`codex-rs/config/src/mcp_types.rs:214-223` defines the fields as `Option` only).
- Hook handler types `prompt` and `agent` exist in the schema but carry no fields (`codex-rs/config/src/hook_config.rs:183-186`); their runtime semantics (who consumes them) were not traced and are presumably model-facing handlers wired elsewhere.
- Skill catalog selection, prompt assembly, and implicit-invocation detection beyond the core glue live in `codex-rs/ext/skills/` (`codex_skills_extension`), outside this component's registered paths; the 2%/10k budget mechanics and root discovery are asserted by config docs but not traced here (`codex-rs/config/src/skills_config.rs:40-43`).
- Connectors are server-driven: the catalog, auth flows, and app capabilities come from a remote directory (cached 1h, `codex-rs/connectors/src/lib.rs:56-58`), so their actual behavior depends on OpenAI-hosted state not visible in the repo.
- Marketplace JSON schema (`.agents/plugins/marketplace.json`, `api_marketplace.json`) is referenced (`codex-rs/core-plugins/src/loader.rs:463-470`) but not fully read here.
- The `hooks.state` trusted-hash format is observed in tests as `sha256:`-prefixed strings (`codex-rs/config/src/hooks_tests.rs:196-198`, `227-232`); the hashing algorithm and normalization are in `discovery.rs` but not extracted in detail.

## Relevance to the brief

This is my inference, separated from code facts:

- Codex's extensibility is a deliberate Claude Code compatibility strategy, not a from-scratch design. Same hook event names, same regex matchers, same `hooks.json`-per-folder layout, same exit-code-2 block convention, Claude plugin env vars (`CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA`), and discovery of `.claude-plugin/plugin.json` manifests (`codex-rs/hooks/src/lib.rs:23-52`, `codex-rs/hooks/src/events/pre_tool_use.rs:264-274`, `codex-rs/hooks/src/engine/discovery.rs:259-267`, `codex-rs/exec-server-protocol/src/protocol.rs:46-49`). This materially lowers the cost of porting Claude Code extensions and suggests the market is converging on one extension vocabulary.
- Where Codex departs from Claude Code, it leans on stronger safety machinery: hash-based hook trust with enterprise "managed hooks", content-hash gating, and per-environment MCP authority (`codex-rs/hooks/src/engine/discovery.rs:655-713`, `codex-rs/core/src/mcp.rs:272-304`). For the brief's question on security posture of extension systems, hooks are the sharpest example: untrusted hooks are inert by default.
- The MCP-first architecture means plugins, apps, and skill dependencies all reduce to MCP servers with policy overlays, giving one uniform trust surface for very different provenance (user config, plugins, curated marketplace, hosted apps) (`codex-rs/core/src/mcp.rs:152-327`). This is the strongest cross-harness comparison point against Claude Code's MCP + plugins + connector model.
- Open questions for comparison: how hooks trust is initialized/refreshed in practice (user UX around `trusted_hash`), how `prompt`/`agent` hook types behave, and how skill catalog selection interacts with `disable-model-invocation`-style frontmatter (present in other harnesses; not confirmed here).

## Quotables for the report

- Plugin key format and error: "expected `<plugin>@<marketplace>`" (`codex-rs/plugin/src/plugin_id.rs:29`).
- Explicit Claude compat: env vars `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` with comment "For OOTB compat with existing plugins" (`codex-rs/hooks/src/engine/discovery.rs:263-267`).
- Trust gate: handlers run only when `enabled && (bypass_hook_trust || matches!(trust_status, HookTrustStatus::Managed | HookTrustStatus::Trusted))` (`codex-rs/hooks/src/engine/discovery.rs:693-698`).
- Policy split: "plugin manifests own how the MCP server is launched, while user config owns enablement and tool policy" (`codex-rs/config/src/types.rs:856-857`).
- Skill catalog budget: "Defaults to 2% of the model context window and is capped at 10,000 tokens when set" (`codex-rs/config/src/skills_config.rs:40-41`).
- Server identity: `Implementation::new("codex-mcp-server", env!("CARGO_PKG_VERSION")).with_title("Codex")` (`codex-rs/mcp-server/src/message_processor.rs:254`).
- Discoverable manifests: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` (`codex-rs/exec-server-protocol/src/protocol.rs:46-49`).
