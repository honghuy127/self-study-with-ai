---
source_key: "claudeCodeDocsMemory"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
---

# Notes: How Claude remembers your project (CLAUDE.md and auto memory)

## Source identification

- Key: `claudeCodeDocsMemory`
- Authors, year, venue: Anthropic, 2026, Claude Code official docs (code.claude.com/docs/en/memory)
- Tier: docs
- URL / DOI: https://docs.claude.com/en/docs/claude-code/memory (registry URL); served from https://code.claude.com/docs/en/memory.md
- Read as: the local snapshot `sources/docs/claudeCodeDocsMemory.md`, captured from https://code.claude.com/docs/en/memory.md on 2026-08-20 (snapshot header, line 1). The docs site is not version-pinned: the registry's `coverage_limits` records that code.claude.com/docs "reflects current versions (checked 2026-08-19/2026-08-20) and can drift from the pinned commits" (registry `provenance.coverage_limits`). All anchors below are section headings of the snapshot page, with snapshot line numbers given as `L<nn>` where useful.

## Problem and motivation

The page opens from a harness constraint: "Each Claude Code session begins with a fresh context window. Two mechanisms carry knowledge across sessions" (Intro, L10). The two mechanisms are "CLAUDE.md files: instructions you write to give Claude persistent context" and "Auto memory: notes Claude writes itself based on your corrections and preferences" (Intro, L12-L13). The page positions itself as usage documentation for both: where to place files, how they load, how to scope rules to paths, how to configure auto memory, and how to troubleshoot when instructions are not followed (Intro, L15-L20).

The page states an explicit design boundary between guidance and enforcement: "Both are loaded at the start of every conversation. Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead." (Section "CLAUDE.md vs auto memory", L24).

## Method or core idea

### The two systems at a glance

The comparison table (Section "CLAUDE.md vs auto memory", L26-L32) characterizes the split:

| | CLAUDE.md files | Auto memory |
| :-- | :-- | :-- |
| Who writes it | You | Claude |
| What it contains | Instructions and rules | Learnings and patterns |
| Scope | Project, user, or org | Per repository, shared across worktrees |
| Loaded into | Every session | Every session (first 200 lines or 25KB) |
| Use for | Coding standards, workflows, project architecture | Build commands, debugging insights, preferences Claude discovers |

### CLAUDE.md locations and load order

Four scopes exist, listed "in load order, from broadest scope to most specific, so a project instruction appears in context after a user instruction" (Section "Choose where to put CLAUDE.md files", L55):

1. Managed policy, per-OS paths: macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux and WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` (L59).
2. User instructions at `~/.claude/CLAUDE.md` (L60).
3. Project instructions at `./CLAUDE.md` or `./.claude/CLAUDE.md` (L61).
4. Local instructions at `./CLAUDE.local.md`, intended for `.gitignore` (L62).

### Directory-tree resolution

"Claude Code reads CLAUDE.md files by walking up the directory tree from your current working directory, checking each directory along the way for `CLAUDE.md` and `CLAUDE.local.md` files." (Section "How CLAUDE.md files load", L156). "All discovered files are concatenated into context rather than overriding each other. Across the directory tree, content is ordered from the filesystem root down to your working directory", so `foo/CLAUDE.md` appears before `foo/bar/CLAUDE.md`; within a directory `CLAUDE.local.md` is appended after `CLAUDE.md` (L158). Ancestor files above the working directory load in full at launch (Section "Choose where to put CLAUDE.md files", L64).

Lazy subdirectory loads: "Claude also discovers `CLAUDE.md` and `CLAUDE.local.md` files in subdirectories under your current working directory. Instead of loading them at launch, they are included when Claude reads files in those subdirectories." (L160). Block-level HTML comments in CLAUDE.md files "are stripped before the content is injected into Claude's context"; comments inside code blocks are preserved, and comments stay visible when the file is opened directly with the Read tool (L164).

`--add-dir` grant does not load memory files by default; setting `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` loads `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, and `CLAUDE.local.md` from the additional directory (Section "Load from additional directories", L168-L176).

### Imports

"CLAUDE.md files can import additional files using `@path/to/import` syntax. Imported files are expanded and loaded into context at launch alongside the CLAUDE.md that references them." (Section "Import additional files", L96). Both relative and absolute paths are allowed; "Relative paths resolve relative to the file containing the import, not the working directory. Imported files can recursively import other files, with a maximum depth of four hops." (L98). Import parsing skips Markdown code spans and fenced code blocks, so a backtick-wrapped `` `@README` `` stays literal (L100).

Trust gate: "An import in a project-level memory file is external when its path resolves outside your working directory... The first time Claude Code encounters external imports in a project, it shows an approval dialog listing the files. If you decline, the imports stay disabled and the dialog doesn't appear again." Imports in user-scope memory files (`~/.claude/CLAUDE.md`, `~/.claude/rules/`) load without the dialog (Warning block in "Import additional files", L120-L124).

### Path-scoped rules in `.claude/rules/`

`.claude/rules/` holds one-topic markdown files discovered recursively, including subdirectories (Section "Organize rules with `.claude/rules/`", L178-L188). "Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`." (Section "Set up rules", L200). Project rules are skipped when `project` is excluded from `--setting-sources`; "Before v2.1.211, rules that load on demand, including path-scoped rules and rules in nested `.claude/rules/` directories, loaded even when `project` was excluded." (L202).

Path scoping uses YAML frontmatter with a `paths` field of glob patterns: "Rules without a `paths` field are loaded unconditionally and apply to all files. Path-scoped rules trigger when Claude reads files matching the pattern, not on every tool use. As of v2.1.198, matching also works when Claude reaches a file through a symlinked path to the project directory" (Section "Path-specific rules", L221). Brace expansion is budgeted: "a rule's whole `paths` list shares one budget of 1,000 expanded patterns and 4 MiB, and patterns without braces don't count against it." (L243). `.claude/rules/` supports symlinks with circular links "detected and handled gracefully" (Section "Share rules across projects with symlinks", L251). User-level rules live in `~/.claude/rules/` and "are loaded before project rules, giving project rules higher priority." (Section "User-level rules", L262-L270).

### Managed policy

The managed CLAUDE.md "cannot be excluded by individual settings" (Section "Deploy organization-wide CLAUDE.md", L278), uses the three OS-specific paths above (L282-L284), and can alternatively be embedded directly in `managed-settings.json` via the `claudeMd` key, which "Loads before user and project CLAUDE.md" and is honored in "managed and policy settings only" (L292-L298). `claudeMdExcludes` skips files by absolute path or glob at any settings layer with arrays merging across layers, but "Managed policy CLAUDE.md files cannot be excluded." (Section "Exclude specific CLAUDE.md files", L324-L339). The page draws the enforcement line explicitly: "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer." (L320).

### Auto memory

On by default; toggled via `/memory`, which saves `autoMemoryEnabled` to `~/.claude/settings.json`; per-project opt-out via `"autoMemoryEnabled": false`; env var `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` disables it entirely (Section "Enable or disable auto memory", L345-L355).

Storage: "Each project gets its own memory directory at `~/.claude/projects/<project>/memory/`. The `<project>` path is derived from the git repository, so all worktrees and subdirectories within the same repo share one auto memory directory. Outside a git repo, the project root is used instead." (Section "Storage location", L359). `autoMemoryDirectory` overrides the location from any settings scope; the value "must be an absolute path or start with `~/`", and project-settings values are honored under the workspace trust rule (L361-L369). The directory holds a `MEMORY.md` entrypoint ("Concise index, loaded into every session") plus optional topic files such as `debugging.md` (L371-L381). Auto memory is machine-local and excluded from the `cleanupPeriodDays` retention sweep that deletes old session transcripts (L383-L385).

Load window and limits: "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation. Content beyond that threshold is not loaded at session start." (Section "How it works", L389). After each write to `MEMORY.md` the file is measured against the two limits; near a limit Claude Code reminds Claude to shorten it; "If the file is over a limit, the write still succeeds, but Claude Code returns an error telling Claude to rewrite the index, because everything past the limit is dropped on the next load." (L391). Measurement strips YAML frontmatter and block-level HTML comments first; "Before v2.1.211, Claude Code measured the raw file" (L393). "This limit applies only to `MEMORY.md`. CLAUDE.md files are loaded in full regardless of length, though shorter files produce better adherence." (L395). Topic files "are not loaded at startup. Claude reads them on demand using its standard file tools" (L397).

Subagent memory: "The main conversation's auto memory isn't loaded into subagents; the exception is a fork, which inherits the parent conversation and system prompt. A subagent's own auto memory, enabled with the subagent `memory` field, is a separate directory." (L399). Writes record a `modified` frontmatter field "as an ISO 8601 timestamp" on files that already have frontmatter; "The `modified` field requires Claude Code v2.1.214 or later." (L403). UI surfaces the activity with messages like "Saved 2 memories" or "Recalled 2 memories" (L401).

### AGENTS.md handling

"Claude Code reads `CLAUDE.md`, not `AGENTS.md`." (Section "AGENTS.md", L130). Recommended bridge: a `CLAUDE.md` whose first line is `@AGENTS.md`, optionally with Claude-specific additions below; a symlink `ln -s AGENTS.md CLAUDE.md` also works, except on Windows where symlink creation needs Administrator privileges or Developer Mode (L130-L148). `/init` reads Cursor rules in `.cursor/rules/` or `.cursorrules` and Copilot rules in `.github/copilot-instructions.md`; with `CLAUDE_CODE_NEW_INIT=1` it additionally reads `AGENTS.md`, `.devin/rules/`, `.windsurf/rules/` or `.windsurfrules`, and `.clinerules` (L150). `/import` copies another agent's instruction files into the matching `CLAUDE.md` and carries over MCP servers, commands, subagents, and skills; "Requires Claude Code v2.1.213 or later." (L152).

### What survives compaction

"Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session. Nested CLAUDE.md files in subdirectories and rules with `paths:` frontmatter are not re-injected automatically; they reload the next time Claude reads a file in that subdirectory or a file matching the rule's patterns." (Section "Instructions seem lost after `/compact`", L452). Instructions given only in conversation are lost; the page defers the full breakdown to `/docs/en/context-window#what-survives-compaction`, which is not part of this snapshot (L454).

### Delivery mechanism and debugging

"CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself. Claude reads it and tries to follow it, but there's no guarantee of strict compliance, especially for vague or conflicting instructions." (Section "Claude isn't following my CLAUDE.md", L423). For must-run behavior the page redirects to hooks: "Hooks execute as shell commands at fixed lifecycle events and apply regardless of what Claude decides to do." (L432). `--append-system-prompt` places instructions at system prompt level but "must be passed every invocation" (L434). The `InstructionsLoaded` hook logs which instruction files load, when, and why (L437). `/context` lists loaded files under **Memory files** (L411, L427). `/doctor` proposes trims for a checked-in CLAUDE.md, keeping "pitfalls, rationale, and conventions that differ from tool defaults"; "The trim check requires Claude Code v2.1.206 or later." (Section "My CLAUDE.md is too large", L448). `Before v2.1.216, /memory waited for you to close the file before responding.` (Section "View and edit with /memory", L413).

## Key claims with anchors

Source claims (what the page establishes as product behavior):

- Claim 1 (Section "CLAUDE.md files", L40; Section "How CLAUDE.md files load", L156): CLAUDE.md files are plain-text markdown that "Claude reads them at the start of every session", resolved by walking up the directory tree from the cwd, checking each directory for `CLAUDE.md` and `CLAUDE.local.md`.
- Claim 2 (Section "Choose where to put CLAUDE.md files", L55-L62): load order from broadest to most specific is managed policy, user (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md` or `./.claude/CLAUDE.md`), local (`./CLAUDE.local.md`); project content therefore appears after user content in context.
- Claim 3 (Section "How CLAUDE.md files load", L158-L160): discovered files are concatenated, never overriding; order runs filesystem root down to working directory; per directory `CLAUDE.local.md` appends after `CLAUDE.md`; subdirectory files are discovered at launch but loaded only when Claude reads files in those subdirectories (lazy subdirectory loads).
- Claim 4 (Section "Import additional files", L96-L100): imports use `@path/to/import`, expand at launch, resolve relative to the importing file, recurse "with a maximum depth of four hops", and skip Markdown code spans and fenced code blocks.
- Claim 5 (Warning block, Section "Import additional files", L120-L124): external imports (paths resolving outside the working directory) in project-scope memory files trigger a first-time approval dialog; user-scope file imports load without it.
- Claim 6 (Section "Deploy organization-wide CLAUDE.md", L278-L298): managed policy CLAUDE.md lives at `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `/etc/claude-code/CLAUDE.md` (Linux and WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows); it cannot be excluded; the `claudeMd` key embeds the same content in `managed-settings.json` and loads before user and project CLAUDE.md.
- Claim 7 (Section "Organize rules with `.claude/rules/`", L188, L200): all `.md` files under `.claude/rules/` are discovered recursively; unscoped rules load at launch with the same priority as `.claude/CLAUDE.md`.
- Claim 8 (Section "Path-specific rules", L206-L221): `paths:` frontmatter scopes rules with glob patterns; such rules "trigger when Claude reads files matching the pattern, not on every tool use"; symlinked-path matching works "As of v2.1.198".
- Claim 9 (Section "Path-specific rules", L243-L245): brace expansion in `paths` shares "one budget of 1,000 expanded patterns and 4 MiB" per rule; patterns without braces are exempt; an over-budget pattern is used unexpanded with literal braces matching nothing; "Before v2.1.217, a `paths` value with many brace groups stalled or crashed the CLI at startup."
- Claim 10 (Section "User-level rules", L270): `~/.claude/rules/` loads before project rules, giving project rules higher priority.
- Claim 11 (Section "Auto memory", L343, L347): auto memory is on by default; Claude "decides what's worth remembering based on whether the information would be useful in a future conversation"; disable via `autoMemoryEnabled` in user or project settings or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- Claim 12 (Section "Storage location", L359-L385): per-project memory directory `~/.claude/projects/<project>/memory/`, keyed by git repository so worktrees share it; `MEMORY.md` is the index over optional topic files; memory is machine-local and exempt from the `cleanupPeriodDays` retention sweep.
- Claim 13 (Section "How it works", L389-L395): "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation"; over-limit writes succeed but return an error directing a rewrite because "everything past the limit is dropped on the next load"; the limit "applies only to `MEMORY.md`", since "CLAUDE.md files are loaded in full regardless of length".
- Claim 14 (Section "How it works", L397-L399): topic files load on demand, not at startup; the main conversation's auto memory is not loaded into subagents, a fork is the exception, and a subagent's own memory (its `memory` field) is a separate directory.
- Claim 15 (Section "AGENTS.md", L130): "Claude Code reads `CLAUDE.md`, not `AGENTS.md`"; interoperation is via `@AGENTS.md` import or symlink.
- Claim 16 (Section "How it works", L403): memory writes update a `modified` frontmatter field with an ISO 8601 timestamp when frontmatter exists; requires v2.1.214 or later.
- Claim 17 (Section "Instructions seem lost after `/compact`", L452): project-root CLAUDE.md survives compaction by being re-read from disk and re-injected after `/compact`; nested CLAUDE.md files and path-scoped rules are not re-injected automatically and reload on the next matching file read.
- Claim 18 (Section "Claude isn't following my CLAUDE.md", L423): CLAUDE.md content is "delivered as a user message after the system prompt, not as part of the system prompt itself", with no strict-compliance guarantee.
- Claim 19 (Section "Manage CLAUDE.md for large teams", L320): "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer."
- Claim 20 (Section "How CLAUDE.md files load", L164): block-level HTML comments in CLAUDE.md are stripped before context injection; comments inside code blocks survive.

Source guidance (the page's own prescription and interpretation, not verifiable mechanism):

- Guidance 1 (Section "Write effective instructions", L82): "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." The context-consumption part is mechanism; the adherence claim is qualitative advice with no supporting data on the page.
- Guidance 2 (Section "Write effective instructions", L80, L86-L92): instructions should be specific, structured with headers and bullets, and verifiable ("Use 2-space indentation" instead of "Format code properly"); "if two rules contradict each other, Claude may pick one arbitrarily."
- Guidance 3 (Section "When to add to CLAUDE.md", L44-L51): add entries on repeated mistakes, review catches, repeated corrections, or new-teammate context; move multi-step or area-specific procedures to skills or path-scoped rules.
- Guidance 4 (Section "Deploy organization-wide CLAUDE.md", L308-L319): use managed settings for technical enforcement (`permissions.deny`, `sandbox.enabled`, `env`, `forceLoginMethod`, `forceLoginOrgUUID`) and managed CLAUDE.md for behavioral guidance (code style, compliance reminders).

## Evaluation and evidence

This is a product documentation page. It contains no datasets, benchmarks, baselines, or quantitative evaluation of either memory system; I searched the entire snapshot for compliance or adherence measurements and found none. The only numeric values on the page are design parameters, copied character-exact from the snapshot:

- Auto memory load window: "first 200 lines or 25KB" (comparison table, L31); restated as "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first" (Section "How it works", L389).
- CLAUDE.md size guidance: "target under 200 lines per CLAUDE.md file" (Section "Write effective instructions", L82).
- Import recursion: "a maximum depth of four hops" (Section "Import additional files", L98).
- Path-rule expansion budget: "one budget of 1,000 expanded patterns and 4 MiB" (Section "Path-specific rules", L243).
- Versioned behavior statements, verbatim version identifiers: "As of v2.1.198" (symlinked-path matching, L221), "Before v2.1.207" (invalid bracket-expression pattern made the Read tool fail for every file, L247), "Before v2.1.211" (two fixes: on-demand rules leaked past `--setting-sources project` exclusion, L202; `MEMORY.md` measured raw including frontmatter and comments, L393), "Requires Claude Code v2.1.213 or later" (`/import`, L152), "requires Claude Code v2.1.214 or later" (`modified` frontmatter, L403), "Before v2.1.216" (`/memory` blocked until editor closed, L413), "Before v2.1.217" (brace-group `paths` stalled or crashed the CLI at startup, L245), "requires Claude Code v2.1.206 or later" (`/doctor` trim check, L448).
- Configuration surface, exact identifiers: settings keys `autoMemoryEnabled`, `autoMemoryDirectory`, `claudeMd`, `claudeMdExcludes`, `cleanupPeriodDays`; env vars `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD`, `CLAUDE_CODE_NEW_INIT=1`; slash commands `/memory`, `/context`, `/init`, `/import`, `/compact`, `/doctor`; hook `InstructionsLoaded`; CLI flags `--add-dir`, `--setting-sources`, `--append-system-prompt`, `--settings`.
- Storage paths, exact: `~/.claude/projects/<project>/memory/`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/settings.json`, plus the three managed-policy paths under "Managed policy".

`[CITATION NEEDED]` item: the page never states which Claude Code release the page as a whole documents. It mixes "As of" and "Before" version statements without declaring a documentation version. I looked at the snapshot header (L1) and the version paragraphs throughout; none carries an explicit page version. Where it looked: snapshot L1 header, all eight version-bearing paragraphs above.

`[CITATION NEEDED]` item: no evidence on the page that the 200-line guidance changes adherence in any measured way. The only support is the qualitative sentence in Guidance 1. I looked for tables, links to studies, or telemetry descriptions on the snapshot; none exist.

## Limitations

- Unfalsifiable adherence claims. The page's central efficacy statements ("Longer files consume more context and reduce adherence", "The more specific and concise your instructions, the more consistently Claude follows them", "Claude may pick one arbitrarily" on contradictions, L24, L82, L92) are asserted without data, experiment, or metric. They are vendor guidance, not evidence.
- Docs not pinned to a version or commit. The snapshot is dated 2026-08-20 (L1) from code.claude.com/docs/en/memory.md, and the registry records that the docs site "reflects current versions... and can drift from the pinned commits" (registry `provenance.coverage_limits`). The page itself declares no product version. Behavior documented here cannot be tied to the pinned claude-code checkout (c3d2e35e5540, whose core is closed, per registry entry `claudeCodePluginSurface`), so every claim rests on the documentation's authority alone.
- Closed implementation. The page describes load order, lazy loads, import expansion, limit enforcement, and compaction re-injection as behavior of the closed Claude Code core. No source anchors exist to verify any of them; this study's pinned claude-code tree contains only the plugin/example surface.
- Deferred and out-of-snapshot detail. The full compaction-survival breakdown is explicitly delegated to `/docs/en/context-window#what-survives-compaction` (L454), subagent memory mechanics to `/docs/en/sub-agents#enable-persistent-memory` (L36, L399). Those pages are not in this snapshot, so this note cannot verify what else survives compaction or how subagent memory is stored beyond "a separate directory".
- Anthropomorphic mechanism language. Auto memory's selection criterion is stated as the model's decision ("It decides what's worth remembering", L343). Whether this is model judgment, heuristic, or both is not specified; the page gives no implementation account of when writes happen.
- Qualitative delivery claim. "there's no guarantee of strict compliance" for user-message-delivered instructions (L423) is a scope disclaimer, not a measured failure rate; the page quantifies no compliance level.
- Self-consistency risk in the comparison table. The table says CLAUDE.md is "Loaded into: Every session" (L31), while the load mechanics section shows lazy subdirectory loading for nested files (L160); the table is accurate for root/user/managed/ancestor files but elides the lazy case. Not an error, but a flattening worth noting when quoting the table.

## Relevance to the brief

My inferences, separated from source claims:

- RQ2 (harness components): this page is the primary documentation for Claude Code's memory files and for the memory half of context management. It establishes that Claude Code splits persistent instructions into a hierarchically scoped file tree (managed, user, project, local, nested, rules) plus an agent-written memory index with a hard load window (200 lines/25KB) and on-demand topic files. The compaction-survival rules (root CLAUDE.md re-injected; nested and path-scoped content reloaded lazily) directly inform the context management and compaction dimension where the `codexContextCompaction` and `opencodeContextCompaction` notes cover the open systems.
- RQ1 (genuine differences): the AGENTS.md treatment is a concrete divergence point. Claude Code "reads `CLAUDE.md`, not `AGENTS.md`" (L130) and interoperates with the cross-agent convention only through an import or symlink, while Codex centers AGENTS.md per `notes/codexDocsRepo.md`. That asymmetry belongs in the comparison matrix.
- RQ3 (capability versus safety): the explicit guidance/enforcement split (L24, L320) plus the external-import approval dialog (L120-L124) and the managed-policy non-excludability (L278, L339) show where Claude Code places its trust boundary: CLAUDE.md is advisory context, settings and hooks are enforcement. Useful for characterizing the safety model of memory specifically.
- RQ4 (closed core through docs): this is one of the study's best docs windows on the closed core. Load order (L55, L156-L160), four-hop imports (L98), lazy subdirectory loads (L160), and post-compaction re-injection (L452) are implementation facts that only the docs attest to, and the report should mark them as docs-attested, not code-verified.
- Left open for synthesis: the complete compaction-survival list lives off-page (context-window doc); subagent memory storage is delegated to the sub-agents page (covered by the `claudeCodeDocsSubagents` note); no quantitative picture of context-token cost of memory files exists anywhere on the page. For the literature gate under `depth: full`, this source can support claims about Claude Code's documented memory design only, hedged by the drift risk between the floating docs site and any specific release.

## Quotables for the report

- "Each Claude Code session begins with a fresh context window. Two mechanisms carry knowledge across sessions" (Intro, L10). Framing sentence for why the harness needs a persistence layer; quote when motivating the memory-files dimension.
- "Claude treats them as context, not enforced configuration." (Section "CLAUDE.md vs auto memory", L24). Use to draw the capability/safety line: memory files guide, hooks and settings enforce. Pair with L320.
- "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer." (Section "Deploy organization-wide CLAUDE.md", L320). Report language for RQ3.
- "Claude Code reads `CLAUDE.md`, not `AGENTS.md`." (Section "AGENTS.md", L130). The cleanest one-line statement of the cross-tool instruction-file divergence; quote in the comparison section.
- "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation." (Section "How it works", L389). The quantitative anchor for Claude Code's agent-written memory budget.
- "Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session." (Section "Instructions seem lost after `/compact`", L452). The key compaction-survival fact; cite when comparing compaction behavior across the three harnesses.
- "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself." (Section "Claude isn't following my CLAUDE.md", L423). Use for the context-assembly discussion; it locates memory files in the message stream rather than the system prompt.
