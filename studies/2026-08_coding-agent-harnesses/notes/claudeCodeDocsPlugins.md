---
# Note for the official Claude Code "Create plugins" docs page, read directly
# from the retained snapshot sources/docs/claudeCodeDocsPlugins.md (accessed
# 2026-08-20). Anchors are quoted section headings plus snapshot line numbers,
# e.g. (Section "Plugin structure overview", L164-187).
source_key: "claudeCodeDocsPlugins"
read_date: "2026-08-20"
confidence: "high"                # full snapshot read directly; all claims section-anchored
relevance: "3"                    # central to RQ4 (Claude Code plugin surface) and the extensibility dimension
---

# Notes: Create plugins

## Source identification

- Key: claudeCodeDocsPlugins
- Authors, year, venue: Anthropic, 2026, Claude Code official docs
  (code.claude.com/docs/en/plugins)
- Tier: docs
- URL / DOI: https://docs.claude.com/en/docs/claude-code/plugins (no DOI).
  Snapshot header records the fetched page as
  `https://code.claude.com/docs/en/plugins.md` accessed 2026-08-20
  (snapshot L1), which matches the registry entry's venue
  (`sources/registry.yaml:326-336`). The page carries no product-version
  stamp; only the snapshot access date is recorded.

## Problem and motivation

The page is the authoring guide for Claude Code plugins. Its stated purpose:
"Plugins let you extend Claude Code with custom functionality that can be
shared across projects and teams" (intro, L10), and "Create custom plugins to
extend Claude Code with skills, agents, hooks, and MCP servers" (page
subtitle, L8). It motivates plugins against a simpler alternative by
distinguishing plugins from standalone `.claude/` configuration (Section
"When to use plugins vs standalone configuration", L14-25): standalone is
"Best for: Personal workflows, project-specific customizations, quick
experiments" while plugins are "Best for: Sharing with teammates,
distributing to community, versioned releases, reusable across projects"
(L20-21). The recommended path is to "Start with standalone configuration in
`.claude/` for quick iteration, then convert to a plugin when you're ready to
share" (Tip, L23-25).

## Method or core idea

**Plugin anatomy.** A plugin is a self-contained directory; every component
directory lives at the plugin root, and only the manifest goes inside
`.claude-plugin/`: "Don't put `commands/`, `agents/`, `skills/`, or `hooks/`
inside the `.claude-plugin/` directory. Only `plugin.json` goes inside
`.claude-plugin/`. All other directories must be at the plugin root level."
(Warning, Section "Plugin structure overview", L169). The documented
component table (L174-185), all located at "Plugin root" unless noted:

| Directory | Purpose (verbatim, L174-185) |
| :-- | :-- |
| `.claude-plugin/` | "Contains `plugin.json` manifest (optional if components use default locations)" |
| `skills/` | "Skills as `<name>/SKILL.md` directories" |
| `commands/` | "Skills as flat Markdown files. Use `skills/` for new plugins" |
| `agents/` | "Custom agent definitions" |
| `hooks/` | "Event handlers in `hooks.json`" |
| `.mcp.json` | "MCP server configurations" |
| `.lsp.json` | "LSP server configurations for code intelligence" |
| `monitors/` | "Background monitor configurations in `monitors.json`" |
| `bin/` | "Executables added to the Bash tool's `PATH` while the plugin is enabled" |
| `settings.json` | "Default settings applied when the plugin is enabled" |

The manifest is optional: ".claude-plugin/ ... optional if components use
default locations" (L177), and "Every plugin lives in its own directory
containing your skills, agents, or hooks, optionally alongside a
`.claude-plugin/plugin.json` manifest" (Quickstart step 1, L39). When
present, the manifest "defines your plugin's identity: its name, description,
and version", and Claude Code "uses this metadata to display your plugin in
the plugin manager" (Quickstart step 2, L49). Additional fields such as
`homepage`, `repository`, and `license` exist but are documented only in the
separate "full manifest schema" page (L77). A shortcut layout exists: a
plugin with exactly one skill can place `SKILL.md` directly at the plugin
root, loaded as a single skill using the frontmatter `name` field for the
invocation name (L187).

**Namespacing.** The manifest `name` field is the "Unique identifier and
skill namespace. Skills are prefixed with this (e.g.,
`/my-first-plugin:hello`)" (L72); the skill folder name is "prefixed with
the plugin's namespace (`hello/` in a plugin named `my-first-plugin` creates
`/my-first-plugin:hello`)" (L81). The doc's stated rationale: "Plugin skills
are always namespaced (like `/my-first-plugin:hello`) to prevent conflicts
when multiple plugins have skills with the same name", and "To change the
namespace prefix, update the `name` field in `plugin.json`" (Note, L117-119).
Standalone skills invoke as `/hello` versus `/plugin-name:hello` for plugin
skills (L20-21), and after migration "Plugin skills are namespaced as
`/plugin-name:skill-name`, so the original `/skill-name` and the plugin copy
both remain available rather than one overriding the other" (Note, L454).

**Component behaviors.** Skills "are model-invoked: Claude automatically
uses them based on the task context" (Section "Add Skills to your plugin",
L195), each `SKILL.md` carrying YAML frontmatter where `description` tells
Claude when to use it (L208); the quickstart demonstrates
`disable-model-invocation: true` as an opt-out frontmatter key (L94) and a
`$ARGUMENTS` placeholder that "captures any text the user provides after the
skill name" (L124-125). LSP support comes from a `.lsp.json` mapping a
language key to `command`, `args`, and `extensionToLanguage` (example: `"go"`
with `"command": "gopls"`, `"args": ["serve"]`, `".go": "go"`, L232-242);
"Users installing your plugin must have the language server binary installed
on their machine" (L244), and a failing server shows in the `/plugin` Errors
tab, e.g. `Executable not found in $PATH`, while "An entry with an invalid
configuration is skipped instead; run `claude --debug` to see why" (L246).
Background monitors are defined in `monitors/monitors.json` as an array
entries with `name`, `command`, `description` (example command
`tail -F ./logs/error.log`, L256-264): "Background monitors let your plugin
watch logs, files, or external status in the background and notify Claude as
events arrive. Claude Code starts each monitor automatically when the plugin
is active" (L252), and "Each stdout line from `command` is delivered to
Claude as a notification during the session" (L266). A plugin `settings.json`
applies defaults when enabled, but "Currently, only the `agent` and
`subagentStatusLine` keys are supported" (Section "Ship default settings with
your plugin", L270); "Setting `agent` activates one of the plugin's custom
agents as the main thread, applying its system prompt, tool restrictions, and
model" (L272; example `{"agent": "security-reviewer"}`, L274-278), and
"Settings from `settings.json` take priority over `settings` declared in
`plugin.json`. Unknown keys are silently ignored" (L280). Hooks use a
`hooks/hooks.json` whose `hooks` object format is "the same" as the one in
`.claude/settings.json`/`settings.local.json` (migration step 3, L417); the
worked example matches `PostToolUse` on `Write|Edit` and pipes hook input
JSON on stdin through `jq` (L419-430).

**Local development and precedence.** `claude --plugin-dir ./my-plugin`
"loads your plugin directly without requiring installation" (Section "Test
your plugins locally", L288-292), also accepts a `.zip` archive (L294-298),
and can be repeated to load multiple plugins (L309-313). Precedence: "When a
`--plugin-dir` plugin has the same name as an installed marketplace plugin,
the local copy takes precedence for that session", with the exception
that "plugins that managed settings force-enable or force-disable:
`--plugin-dir` cannot override those" (L300). `--plugin-url` fetches a
`.zip` archive at a URL (e.g., a CI build artifact): "Claude Code fetches the
archive at startup and loads it for that session only. If Claude Code can't
fetch the archive, or the archive is invalid, it starts without the plugin
and records a plugin load error that you can review in the `/plugin`
manager's Errors tab" (L316); multiple URLs are passed by repeating the flag
or as one quoted space-separated list (L318-328). A third load path bypasses
flags entirely: `claude plugin init my-tool` scaffolds
`~/.claude/skills/my-tool/` with a manifest and starter `SKILL.md`, and "On
the next session it loads as `my-tool@skills-dir` with no marketplace or
install step" (Section "Develop a plugin in your skills directory", L154-160);
auto-load rules, personal vs. project scope, and the workspace-trust
requirement are deferred to the plugins-reference page (L162).

**Reload semantics.** `/reload-plugins` "pick[s] up the updates without
restarting. This reloads plugins, skills, agents, hooks, plugin MCP servers,
and plugin LSP servers" (L302). Two documented quirks: after install, if the
summary reports `Run /reload-plugins to activate.`, run it to load Skills
(L222), and "The skills count in the summary covers only `commands/`
directories, so it can report `0 skills` even though the skill you just
edited reloaded" (L138). Verification during development: run skills with
`/plugin-name:skill-name`, "Check that agents appear in `/context` under
Custom Agents, or @-mention one by its scoped name", and trigger hook events;
"Claude Code records which hooks matched, their exit codes, and their output
in the debug log" (L304-306; repeated for migration at L440). Skills also
appear in the `/help` Custom commands tab "under the plugin namespace" (L114).

**Distribution: marketplaces, trust, and versioning.** Sharing goes through
plugin marketplaces (Section "Share your plugins", L344); a marketplace in a
private repository keeps a plugin "internal to your team" (L347). Anthropic
maintains two public marketplaces (Section "Submit your plugin to the
community marketplace", L351-354): `claude-plugins-official`, "a curated set
of plugins maintained by Anthropic", which "Claude Code registers
automatically the first time you start Claude Code interactively"; if Claude
Code ran non-interactively before that first interactive launch, "or a
marketplace policy blocked an earlier attempt, register it yourself with
`claude plugin marketplace add anthropics/claude-plugins-official`" (L353);
and `claude-community`, "the public community marketplace where third-party
submissions land after review", added via
`/plugin marketplace add anthropics/claude-plugins-community` and installed
from "as `@claude-community`" (L354). Submissions use in-app forms on
claude.ai (requires a Team or Enterprise organization and directory
management access) or the Console form for individual authors (L356-361).
Pre-submission validation: "Run `claude plugin validate ./your-plugin`
locally before you submit... The review pipeline runs the same check on every
submission, along with automated safety screening", printing `✔ Validation
passed` or `✔ Validation passed with warnings`; "Warnings don't fail
validation; add `--strict` to treat them as errors" (L363). Community
versioning: "Approved plugins are pinned to a specific commit SHA in the
`anthropics/claude-plugins-community` catalog, and CI bumps the pin
automatically as you push new commits to your repository. The public catalog
syncs nightly from the review pipeline, so there can be a delay between
approval and your plugin appearing in `marketplace.json`" (L365). The
official marketplace "is curated separately. Anthropic decides which plugins
to include at its discretion. There is no application process" (L367).
Manifest versioning: `version` is "Optional. If set, users only receive
updates when you bump this field, except for a `command` source; see version
management. If omitted, the version comes from the next source in version
management" (L74); the fallback source order itself is on the
plugins-reference page and not reproduced here [CITATION NEEDED]. Trust
language for ad-hoc loading: "The same trust considerations apply as for any
plugin source: only point this flag at archives you control or trust" (on
`--plugin-url`, L316), deferring to discover-plugins#security for substance.

**Relation to standalone `.claude/`.** Migration is mechanical (Section
"Convert existing configurations to plugins", L371-442): copy
`.claude/commands`, `.claude/agents`, `.claude/skills` to the plugin root
(L396-407) and move hooks from settings into `hooks/hooks.json` (L410-431).
What changes (table, L446-451): standalone is "Only available in one
project" versus "Can be shared via marketplaces"; files move from
`.claude/commands/` to `plugin-name/commands/`; hooks move from
`settings.json` to `hooks/hooks.json`; distribution moves from "Must manually
copy to share" to "Install with `/plugin install`". Override precedence on
conflict: "Project and user `.claude/agents/` definitions override same-named
plugin agents, so the plugin version only takes effect once the originals are
removed" (Note, L454), while namespacing keeps plugin and standalone skills
coexisting rather than overriding (L454).

## Key claims with anchors

What the page establishes:

- Claim 1 (Section "Plugin structure overview", L174-185): a plugin root can
  carry exactly ten documented components: `.claude-plugin/`, `skills/`,
  `commands/`, `agents/`, `hooks/`, `.mcp.json`, `.lsp.json`, `monitors/`,
  `bin/`, `settings.json`, with the purposes quoted in the anatomy table
  above.
- Claim 2 (Warning, L169-171): component directories belong at the plugin
  root, never inside `.claude-plugin/`, and the plugin root is "never
  `~/.claude/`"; specifically "Claude Code doesn't read a `.mcp.json` placed
  at `~/.claude/.mcp.json`".
- Claim 3 (L72, L81, L117-119): plugin skills are always namespaced
  `/plugin-name:skill-name`, with the prefix taken from the manifest `name`
  field, to prevent same-name skill conflicts across plugins.
- Claim 4 (L74): the manifest `version` field gates update delivery ("users
  only receive updates when you bump this field") except for a `command`
  source, and falls back to other sources when omitted; the fallback order is
  defined only on the plugins-reference page.
- Claim 5 (Section "Test your plugins locally", L288-328): `--plugin-dir`
  loads a directory or `.zip` without install and shadows a same-named
  installed marketplace plugin for the session, except where managed settings
  force-enable or force-disable; `--plugin-url` loads a remote `.zip` for
  that session only and fails soft with a recorded load error in the
  `/plugin` Errors tab.
- Claim 6 (L302): `/reload-plugins` hot-reloads "plugins, skills, agents,
  hooks, plugin MCP servers, and plugin LSP servers" without restart.
- Claim 7 (L351-367): Anthropic maintains two public marketplaces,
  `claude-plugins-official` (auto-registered on first interactive launch,
  curated at Anthropic's discretion, no application process) and
  `claude-community` (third-party submissions after review, commit-SHA
  pinned, catalog syncs nightly, submissions screened by
  `claude plugin validate` plus "automated safety screening").
- Claim 8 (L270-280): plugin `settings.json` supports only the `agent` and
  `subagentStatusLine` keys, ignores unknown keys, overrides `settings`
  declared in `plugin.json`, and can swap the main-thread agent wholesale
  (system prompt, tool restrictions, model).
- Claim 9 (L184): plugin `bin/` executables are "added to the Bash tool's
  `PATH` while the plugin is enabled".
- Claim 10 (L252-266): monitors start automatically with the plugin and each
  stdout line is "delivered to Claude as a notification during the session".
- Claim 11 (L446-454): standalone `.claude/` configuration and plugins share
  the same underlying component formats (hooks object, commands, agents,
  skills directories); standalone and plugin skills coexist via namespacing,
  while project/user `.claude/agents/` override same-named plugin agents.

What the page interprets (guidance and rationale it supplies, not mechanics
it proves): the doc's own rationale for namespacing (L117), the
start-standalone-then-convert workflow (L23-25), the "Common mistake"
warning as the most frequent structural error (L169), the advice to prefer
pre-built marketplace LSP plugins over custom ones for TypeScript, Python,
and Rust (Tip, L227), and the trust caution on `--plugin-url` (L316).

My inference, flagged separately: see "Relevance to the brief".

## Evaluation and evidence

Docs source: there are no datasets, metrics, or baselines, and the page
contains no benchmark numbers or version stamps. Character-exact values the
page carries, for reuse:

- Marketplace names: `claude-plugins-official`, `claude-community`; repos
  `anthropics/claude-plugins-official`,
  `anthropics/claude-plugins-community`; catalog file
  `.claude-plugin/marketplace.json` (L353-365).
- Commands and flags: `claude --plugin-dir`, `claude --plugin-url`,
  `claude plugin init`, `claude plugin validate ./your-plugin` with
  `--strict`, `/plugin install`, `/plugin marketplace add`, `/reload-plugins`
  (L105, L157, L291, L321, L354, L363, L138).
- Validation messages: `✔ Validation passed`, `✔ Validation passed with
  warnings` (L363).
- Skills-directory load name: `my-tool@skills-dir` (L160).
- Supported plugin settings keys: `agent`, `subagentStatusLine` (L270).
- Example strings: `{"agent": "security-reviewer"}` (L277),
  `tail -F ./logs/error.log` (L260), `"command": "gopls"` with `["serve"]`
  (L235-236), `Executable not found in $PATH` (L246),
  `/my-first-plugin:hello` (L72), `Run /reload-plugins to activate.` (L222),
  `0 skills` (L138).

Not located in this page, with where I looked:

- The version-management fallback source order referenced by the `version`
  field description: `[CITATION NEEDED]`. Looked: L74 and its links, which
  point to `plugins-reference#version-management`; that page is not in the
  registry snapshots.
- The full manifest schema (`homepage`, `repository`, `license`, and the
  `settings` field implied by L280): `[CITATION NEEDED]`. Looked: L77 and
  L280, both deferring to `plugins-reference#plugin-manifest-schema`.
- Skills-directory auto-load rules, personal vs. project scope, and the
  workspace-trust requirement: `[CITATION NEEDED]`. Looked: L162, deferred to
  `plugins-reference#skills-directory-plugins`.
- The `.mcp.json` schema and MCP server lifecycle details: `[CITATION NEEDED]`.
  Looked: L181 (one table row) and L302 (reload mention); the MCP docs page
  is a separate registry entry (claudeCodeDocsMcp) not yet noted.
- Monitors full schema (`when` trigger, variable substitution): `[CITATION
  NEEDED]`. Looked: L266, deferred to `plugins-reference#monitors`.
- The substance of "trust considerations" for plugin installation: `[CITATION
  NEEDED]`. Looked: L316, deferred to `discover-plugins#security`, not in the
  registry.

## Limitations

- Snapshot is floating, not pinned. The page carried no Claude Code version
  or date stamp; only the access date 2026-08-20 is recorded (snapshot L1),
  and the registry notes docs sites are not pinned and "can drift from the
  pinned commits" (`sources/registry.yaml:57`). Claude Code's core is closed
  source (`sources/registry.yaml:55`), so no behavior described here can be
  checked against implementation, only against this snapshot.
- Heavy deferral to sibling pages. The page leaves at least six harness
  relevant specifications elsewhere: full manifest schema, version-management
  source order, skills-directory auto-load and workspace-trust rules, LSP
  configuration options, monitors schema, and debugging/validation CLI
  commands (L77, L74, L162, L248, L266, L336). Those pages
  (plugins-reference, discover-plugins, plugin-marketplaces) are not
  snapshotted in this study, so the extensibility docs dimension is only
  partially covered by registered sources.
- Security model is referenced, not elaborated. The page flags "trust
  considerations" (L316) and "automated safety screening" in the review
  pipeline (L363), but never describes what plugins can and cannot do at
  install time or runtime, even though it documents three high-privilege
  surfaces: `bin/` executables injected into the Bash tool `PATH` (L184),
  monitors streaming arbitrary stdout into the agent's context (L266), and a
  `settings.json` `agent` key that replaces the main-thread system prompt,
  tool restrictions, and model (L270-272). The trust story for these is out
  of the page's scope and unverifiable here.
- Vendor-asserted mechanics. Precedence rules (local copy shadows installed
  plugin, L300), managed-settings force-enable/disable semantics (L300,
  L353), auto-registration timing of the official marketplace (L353), and
  nightly catalog sync (L365) are stated by the docs author with no
  mechanism exposed; this note can only report them as documented behavior.
- Self-contradiction risk on reload bookkeeping: the reload summary's skills
  count "covers only `commands/` directories" and "can report `0 skills`
  even though the skill you just edited reloaded" (L138), so the documented
  feedback channel is known to be misleading by the doc itself.
- `plugin.json` can apparently declare a `settings` field (L280 says
  `settings.json` takes priority over "`settings` declared in `plugin.json`")
  yet this page never documents that field, leaving manifest-vs-file settings
  merging unspecified here.
- Nothing here covers where installed plugins are stored on disk, how
  enable/disable state persists across sessions, or how plugins interact with
  session resume; only `--plugin-url` loading is stated to be "for that
  session only" (L316).

## Relevance to the brief

My inference, separated from the anchored material above.

- RQ4 (Claude Code's closed core via its surfaces): this page is the
  authoritative map of Claude Code's documented extension boundary. The ten
  component locations (L174-185) imply which subsystems the closed harness
  must implement: a namespaced skill dispatcher, an agent registry with
  override precedence, an event hook system keyed on tool events, MCP server
  lifecycle, an LSP client, background process management, PATH injection for
  the Bash tool, and a settings merge order. Combined with the official
  plugins in the pinned repo (registry entry claudeCodePluginSurface), this
  bounds what RQ4 can claim about the core without leak-based material.
- RQ2 (harness component inventory): fills the Claude Code cell of the
  extensibility dimension at tier docs, alongside the hooks, subagents, and
  MCP docs entries. The standalone-vs-plugin distinction matters for the
  comparison matrix: Claude Code separates personal configuration (`.claude/`)
  from shareable packages with identical component formats (L446-454), a
  packaging distinction to compare against OpenCode's and Codex's plugin
  loaders.
- RQ3 (capability vs. safety): the page documents capability-side surfaces
  with notable safety implications (PATH injection via `bin/`, monitor stdout
  into context, main-agent replacement via `settings.json`) while delegating
  the trust model elsewhere (L316). The only in-page controls are the
  managed-settings carve-out that `--plugin-dir` cannot override (L300),
  commit-SHA pinning plus validation and safety screening for the community
  catalog (L363-365), and a workspace-trust requirement that is only named,
  not described (L162). The report should mark Claude Code's plugin trust
  story as documented-but-unverified pending the discover-plugins page.
- Left open for the gate: because plugins-reference, discover-plugins, and
  plugin-marketplaces are not registered or snapshotted, the full plugin
  trust/versioning chain (install-time prompts, version fallback order,
  managed marketplace restrictions) is a source-level gap. The orchestrator
  may need those pages captured before the extensibility docs column of the
  comparison matrix can be filled without `[CITATION NEEDED]` cells.

## Quotables for the report

All strings verified against the snapshot.

- Extension framing: "Plugins let you extend Claude Code with custom
  functionality that can be shared across projects and teams." (intro, L10).
  Suggested framing: Claude Code's official story for plugins is distribution
  and reuse, not capability per se.
- Structure invariant: "Only `plugin.json` goes inside `.claude-plugin/`.
  All other directories must be at the plugin root level." (L169). Suggested
  framing: the plugin layout is convention over configuration, with one
  manifest file and ten fixed component locations.
- Namespacing rationale: "Plugin skills are always namespaced (like
  `/my-first-plugin:hello`) to prevent conflicts when multiple plugins have
  skills with the same name." (L117). Suggested framing: Claude Code resolves
  multi-plugin collisions by construction rather than by load order.
- Privilege surface: `bin/` holds "Executables added to the Bash tool's
  `PATH` while the plugin is enabled" (L184). Suggested framing: enabling a
  plugin extends the shell surface of the harness, the clearest
  capability-versus-safety seam in the plugin model.
- Main-agent override: "Setting `agent` activates one of the plugin's custom
  agents as the main thread, applying its system prompt, tool restrictions,
  and model." (L272). Suggested framing: a plugin can reconfigure the whole
  harness persona, not just add components.
- Trust deference: "The same trust considerations apply as for any plugin
  source: only point this flag at archives you control or trust." (L316).
  Suggested framing: the docs push the trust decision onto the user for
  ad-hoc loads, while the community pipeline gates submissions with
  validation, safety screening, and commit-SHA pins (L363-365).
