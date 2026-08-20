---
source_key: "claudeCodeDocsSandboxing"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
---

# Notes: Configure the sandboxed Bash tool (Claude Code official docs)

Anchors below cite the local snapshot by section heading and line number of
`studies/2026-08_coding-agent-harnesses/sources/docs/claudeCodeDocsSandboxing.md`,
whose header identifies it as a fetch of
`https://code.claude.com/docs/en/sandboxing.md` on 2026-08-20 (line 1). All
quotes are copied character-exact from the snapshot.

## Source identification

- Key: `claudeCodeDocsSandboxing`
- Authors, year, venue: Anthropic, 2026, Claude Code official docs
  (`code.claude.com/docs/en/sandboxing`); registry entry
  `sources/registry.yaml:370-380`.
- Tier: docs
- URL / DOI: https://code.claude.com/docs/en/sandboxing (no DOI). Snapshot:
  `sources/docs/claudeCodeDocsSandboxing.md`, accessed 2026-08-20 (line 1).
  The page carries no version stamp of its own; only historical "before
  vX" notes appear (see Evaluation and evidence).

## Problem and motivation

The page presents Claude Code's sandbox as the mechanism that converts
per-command approval prompts into an OS-enforced boundary, trading prompts
for containment. The tagline: "Learn how Claude Code's sandboxed Bash tool
provides filesystem and network isolation for safer, more autonomous agent
execution." (line 8). The framing sentence: "The Bash sandbox lets Claude run
most shell commands without stopping to ask permission. Instead of approving
each command, you define which files and network domains commands can touch,
and the operating system enforces that boundary for every Bash command and
its child processes." (line 10).

The page explicitly demarcates itself from adjacent isolation mechanisms:
dev containers, custom containers, and virtual machines live on a separate
page (Sandbox environments), and reducing prompts for tools other than Bash
is delegated to permission modes (note, lines 12-14). Capability-versus-
safety relevance is therefore stated at the outset: this is the autonomy
feature whose safety case is an OS boundary rather than human approval.

## Method or core idea

The page specifies six interacting mechanisms, not an algorithm.

1. Two independent isolation layers inside one sandbox: "filesystem
   isolation controls which paths sandboxed commands can read and write, and
   network isolation controls which domains they can reach"
   (Section~"Disable filesystem isolation", line 226). Each layer can be
   reasoned about separately; the filesystem layer can be disabled while
   network isolation stays on (line 226).

2. OS-level enforcement primitives per platform (Section~"OS-level
   enforcement", lines 502-512): Seatbelt on macOS, bubblewrap on Linux and
   WSL2; WSL1 unsupported because "bubblewrap requires kernel features only
   available in WSL2" (line 510). The same primitives ship as the standalone
   `@anthropic-ai/sandbox-runtime` package (line 512).

3. Two approval modes layered over one boundary (Section~"Sandbox modes",
   lines 117-140): "In both, the sandbox enforces the same filesystem and
   network restrictions; the difference is only in whether sandboxed
   commands are auto-approved or require explicit permission." (line 119).
   Auto-allow runs sandboxable commands without prompting; regular
   permissions keeps prompts (lines 121-140). An unsandboxed-retry escape
   hatch exists (Section~"The unsandboxed retry escape hatch", lines
   142-148).

4. Pre-run policy versus running-process enforcement. Permission rules are
   evaluated before any tool runs and apply to every tool; sandboxing
   "applies only to Bash commands and their child processes"
   (Section~"Permission rules", lines 522-523). "The operating system
   enforces the sandbox boundary on the running process, so it holds
   regardless of what the model chose to run and even if an allowed command
   does more than its name suggests." (line 525).

5. A configuration surface spanning four settings scopes (user, project,
   local, managed, plus `--settings` CLI flag), a `/sandbox` interactive
   panel, and scope-restricted keys that administrators can pin
   (Section~"Get started", lines 22-54; Section~"Configure sandboxing",
   lines 154-445; Section~"Configure the sandbox for your organization",
   lines 557-616).

6. Credential protection as a sub-layer: `sandbox.credentials` entries with
   `deny` (block/unset) and `mask` (sentinel substitution with proxy-side
   injection) modes (Sections "Protect credentials" and "Mask credentials",
   lines 268-445), including AWS SigV4 re-signing at the proxy (Section~"Re-sign
   AWS requests", lines 356-393).

## Key claims with anchors

What the source establishes, grouped by topic.

### Scope: the sandbox is Bash-only

- Claim 1 (Section~"Permission rules", lines 520-525): permission rules
  "control which tools Claude Code can use and are evaluated before any tool
  runs. They apply to every tool: Bash, Read, Edit, WebFetch, MCP, and
  others" (line 522), while sandboxing "provides OS-level enforcement that
  restricts what Bash commands can access at the filesystem and network
  level. It applies only to Bash commands and their child processes." (line
  523).
- Claim 2 (Section~"Scope", lines 654-661): "The sandbox isolates Bash
  subprocesses. Other tools operate under different boundaries:" (line 656):
  Read, Edit, and Write "use the permission system directly rather than
  running through the sandbox" (line 658); computer use "runs on your actual
  desktop rather than in an isolated environment" with per-app permission
  prompts (line 659); sandboxed Bash commands "inherit the parent process
  environment by default, including any credentials set there" (line 660);
  and subagents "run in the same process as the parent session and use the
  same sandbox configuration. Bash commands inside a subagent are sandboxed
  when sandboxing is enabled in the parent session." (line 661).
- Cross-reference (my inference, flagged): the plugin-surface note records
  the pinned repo's `examples/settings/README.md:27` statement that "The
  `sandbox` property only applies to the `Bash` tool; it does not apply to
  other tools (like Read, Write, WebSearch, WebFetch, MCPs), hooks, or
  internal commands" (`notes/claudeCodePluginSurface.md` lines 87, 191).
  This docs page corroborates the Bash-only scope at lines 523 and 656, and
  extends it with two nuances the repo sentence does not state: subagent
  Bash IS covered (line 661) and computer use is NOT (line 659).

### Sandbox modes

- Claim 3 (Section~"Sandbox modes", line 119): two modes, auto-allow and
  regular permissions, with identical filesystem/network restrictions; the
  difference is approval only.
- Claim 4 (Section~"Auto-allow mode", lines 123-130): sandboxable commands
  run sandboxed and are auto-approved; commands that cannot be sandboxed
  "fall back to the regular permission flow" (line 123). Even in auto-allow:
  explicit deny rules are always respected (line 127); `rm`/`rmdir`
  targeting a critical path still goes through the regular flow (line 128);
  content-scoped ask rules like `Bash(git push *)` still force a prompt
  (line 129); a bare `Bash` or `Bash(*)` ask rule is skipped for sandboxed
  commands but not in plan mode, and "Before v2.1.212, the skip applied in
  plan mode as well" (line 130).
- Claim 5 (Section~"Auto-allow mode", Info block, lines 132-136): auto-allow
  works independently of the permission mode except plan mode; "Bash
  commands that modify files within the sandbox boundaries execute without
  prompting, even in Manual mode, where the file edit tools would prompt."
  (line 133).
- Claim 6 (Section~"Regular permissions mode", line 140): all Bash commands
  go through the regular permission flow even when sandboxed.
- Claim 7 (Section~"The unsandboxed retry escape hatch", lines 144-148):
  when a command fails from a sandbox denial, Claude Code "appends the
  violation details to the failed command's output" and Claude "may retry
  the command with the `dangerouslyDisableSandbox` parameter" (line 144).
  The retried command runs outside the sandbox and goes through the regular
  permission flow: Manual prompts, auto mode sends it to the classifier
  (line 146). Setting `"allowUnsandboxedCommands": false` disables the
  escape hatch; the `/sandbox` Overrides tab then shows **Strict sandbox
  mode**, and `dangerouslyDisableSandbox` "is completely ignored" (line
  148).
- Claim 8 (Section~"Temporary directories", line 152): `$TMPDIR` is set to
  the session temp directory for sandboxed commands; unsandboxed commands
  inherit the shell's `$TMPDIR`, so the two resolve to different directories
  while filesystem isolation is on.

### Default boundary and protected paths

- Claim 9 (Section~"Filesystem isolation", lines 451-457): default write
  access is the current working directory and its subdirectories plus the
  session temp directory (line 453); default read access is "the entire
  computer, except certain denied directories", and "this default still
  allows reading credential files such as `~/.aws/credentials` and
  `~/.ssh/`" (line 454); writes outside cwd and temp are blocked, including
  `~/.bashrc` and system binaries in `/bin/` (line 455); when the working
  directory is a linked git worktree, writes to the main repository's shared
  `.git` directory are allowed while `hooks/` and `config` inside it remain
  denied (line 456).
- Claim 10 (Section~"Network isolation", line 480): "no domains are
  pre-allowed by default"; the first connection to a new domain prompts, or
  in auto mode goes to the classifier; answering Yes allows the host "for
  the rest of the current session".
- Claim 11 (Section~"Protected paths", lines 461-474): inside writable
  directories the sandbox still denies writes to files Claude Code loads
  configuration and code from, because such writes could "grant itself
  permissions, or add a hook or MCP server that Claude Code runs outside the
  sandbox" (line 463). Four groups: `.claude` settings/skills/agents/
  commands/hooks, `.mcp.json`, `.claude/workflows`,
  `.claude/scheduled_tasks.json` in the working-directory chain (line 465);
  shell startup files, `.gitconfig`, `.vscode`, `.idea`, `.git/hooks`,
  `.git/config` in the working directory only (line 466); bare-git-repo
  files `HEAD`, `objects`, `refs` at top level, deleted on Linux/WSL2 if
  they appear while a sandboxed command runs (line 467); and most of
  `~/.claude` (or `CLAUDE_CONFIG_DIR`), plus `~/.claude.json` and
  `.credentials.json` (line 468). A symlink appearing at a protected
  settings path denies writes to its target from the next command (line
  470). "There is no way to exempt one of these paths"; the only off switch
  is `filesystem.disabled` (line 472). `/sandbox` Config tab lists them
  under **Denied within allowed** (line 472).

### Platform enforcement and setup

- Claim 12 (Section~"Get started", line 18): "The sandbox is built into
  Claude Code and runs on macOS, Linux, and WSL2. Native Windows is not
  supported." On macOS nothing is installed; it uses the built-in Seatbelt
  framework (line 20). Repeated in Section~"Limitations: Platform and tool
  compatibility": "WSL1 and native Windows are not supported." (line 650).
- Claim 13 (Section~"Set up Linux and WSL2", lines 58-83): Linux/WSL2
  require `bubblewrap` ("the unprivileged sandboxing tool that enforces
  filesystem isolation") and `socat` ("the relay used to route network
  traffic through the sandbox proxy") (lines 60-61). The Dependencies tab
  checks `ripgrep`, `bubblewrap`, `socat`, and the seccomp filter (line 79);
  ripgrep is bundled with the native binary; the seccomp filter is optional
  and "adds Unix domain socket blocking", installed via `npm install -g
  @anthropic-ai/sandbox-runtime` (line 81).
- Claim 14 (Section~"OS-level enforcement", lines 504-512): Seatbelt on
  macOS, bubblewrap on Linux, bubblewrap on WSL2 (lines 506-508); WSL1
  unsupported for kernel-feature reasons (line 510); the same primitives are
  available as the standalone `@anthropic-ai/sandbox-runtime` package,
  linked to `https://github.com/anthropic-experimental/sandbox-runtime`
  (line 512).
- Claim 15 (accordion "Ubuntu 24.04 and later", lines 86-108): Ubuntu 24.04+
  default AppArmor policy prevents bubblewrap from creating user namespaces;
  check via `sysctl kernel.apparmor_restrict_unprivileged_userns` (0 or
  missing key: skip; 1: add an AppArmor profile granting `bwrap` the
  `userns` capability) (line 89).
- Claim 16 (accordion "WSL2 notes", line 113): on WSL2, launching Windows
  binaries (`cmd.exe`, `powershell.exe`, anything under `/mnt/c/`) is handed
  to the Windows host over a Unix socket, so it follows the sandbox's
  Unix-socket settings; blocking requires the optional seccomp filter.

### Network controls

- Claim 17 (Section~"Network isolation", line 478): "Network access is
  controlled through a proxy server running outside the sandbox", with
  "restrictions apply to all scripts, programs, and subprocesses spawned by
  commands" (line 485).
- Claim 18 (line 480): pre-allow via `allowedDomains`; "`WebFetch` allow
  rules also pre-allow domains".
- Claim 19 (line 481): `strictAllowlist` set `true` in user, managed, or CLI
  `--settings` denies any host outside the allowlist instead of prompting;
  project settings have no effect; requires Claude Code v2.1.219 or later.
- Claim 20 (line 482): managed-settings `allowManagedDomainsOnly` blocks
  non-allowed domains automatically without prompting and honors only
  managed `allowedDomains` and `WebFetch(domain:...)` rules.
- Claim 21 (line 483): corporate proxy support via `HTTPS_PROXY`,
  `HTTP_PROXY`, `NO_PROXY`; Claude Code enforces the domain allowlist and
  then tunnels allowed connections through the upstream proxy.
- Claim 22 (note, lines 487-489): the built-in proxy decides on the
  requested hostname and "by default, does not terminate or inspect TLS
  traffic"; experimental `network.tlsTerminate` (v2.1.199+) makes the proxy
  terminate TLS itself, which `mask` credential entries require.
- Claim 23 (Section~"IPv6 addresses in domain lists", lines 491-500): domain
  lists are `allowedDomains`, `deniedDomains`, and `WebFetch(domain:...)`
  rules (line 493); bracketed IPv6 form (`"[::1]"`) requires v2.1.229 or
  later; ambiguous spellings are enforced conservatively (deny lists: every
  parseable reading denied; allow lists: never widened) (lines 495-498);
  `/doctor` reports them with the warning "Sandbox network domain entries
  have unreliable spellings" (line 500). The table at lines 529-539 adds
  that `deniedDomains` "Blocks specific domains even when a broader
  `allowedDomains` wildcard would otherwise permit them" (line 539).
- Claim 24 (Section~"Limitations: Security limitations", lines 637-641 and
  warning 663-665): no content filtering by default; allowing broad domains
  such as `github.com` "can create paths for data exfiltration", and because
  the allow decision is made from the client-supplied hostname without TLS
  inspection, code in the sandbox "can potentially use domain fronting or
  similar techniques to reach hosts outside the allowlist" (lines 639-641).
  "Effective sandboxing requires both filesystem and network isolation"
  (line 664).

### Configuration surface

- Claim 25 (Section~"Get started", lines 22-50): `/sandbox` opens a panel
  with tabs **Mode**, **Overrides** (the `allowUnsandboxedCommands`
  setting), and **Config**, plus a **Dependencies** tab on Linux when the
  optional seccomp filter is missing (lines 30-34). Selecting a mode saves
  it to `.claude/settings.local.json`; Claude Code adds that file to the
  global gitignore (line 50). Org-wide enablement is `sandbox.enabled: true`
  in `~/.claude/settings.json` or managed settings (line 50).
- Claim 26 (Warning, lines 52-54): by default, if the sandbox cannot start
  (missing dependencies or unsupported platform), Claude Code "shows a
  warning and runs commands without sandboxing"; `sandbox.failIfUnavailable:
  true` makes this a hard failure, "intended for managed deployments that
  require sandboxing as a security gate."
- Claim 27 (Section~"Configure sandboxing", lines 154-206):
  `sandbox.filesystem.allowWrite` grants paths outside the default boundary;
  "These paths are enforced at the OS level, so all commands running inside
  the sandbox, including their child processes, respect them." (line 171).
  Arrays from multiple settings scopes are merged, not replaced (line 173).
  Path prefixes: `/` absolute, `~/` home-relative, `./` or no prefix
  relative to the project root for project settings or to `~/.claude` for
  user settings (lines 175-181); this syntax differs from Read/Edit
  permission rules, which use `//path` for absolute (line 183).
  `denyWrite`, `denyRead`, and `allowRead` compose with "the more specific
  path wins" (line 185); "An exact deny holds inside a wider allow" (line
  190).
- Claim 28 (Section~"Disable filesystem isolation", lines 208-266):
  `sandbox.filesystem.disabled: true` turns off filesystem isolation while
  keeping network isolation; off by default; requires Claude Code v2.1.216
  or later (lines 210, 228). Honored only from user settings, managed
  settings, and `--settings` CLI flag; project settings cannot set it "so a
  checked-out project can't switch filesystem isolation off" (line 238).
  When managed settings configure `sandbox.filesystem` at all, or list any
  `credentials.files` entry with `"mode": "deny"`, only managed settings can
  set the key (line 239). When `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` is set,
  `filesystem.disabled` is ignored from every source (line 240). With the
  layer off plus auto-allow, a sandboxed command "can write files that later
  commands run or read, such as shell startup files, executables on `$PATH`,
  or `~/.claude/settings.json`, and use them to widen its own access on the
  next run" (line 231). `autoAllowBashIfSandboxed` still defaults to `true`
  (line 266).
- Claim 29 (Section~"Protect credentials", lines 268-298):
  `sandbox.credentials` declares credential files and environment variables
  with `deny` or `mask` modes; requires Claude Code v2.1.187 or later (line
  270). `deny` files are read-blocked inside the sandbox (part of the
  filesystem layer); `deny` env vars are "unset before each sandboxed
  command runs" (line 272). "A `deny` entry only ever narrows access, so any
  scope can add one, but no scope can remove one that another scope added."
  (line 296). "There is no built-in credential deny list" and "The setting
  affects sandboxed Bash commands only." (line 298).
- Claim 30 (Section~"Mask credentials", lines 300-354): `mask` shows the
  sandboxed command a per-session sentinel; the sandbox proxy swaps in the
  real value on egress to allowed hosts (lines 302, 308). Env-var masking
  requires v2.1.199 or later (line 306) and requires
  `network.tlsTerminate`, else "masking fails without exposing anything"
  and Claude Code reports the misconfiguration at startup (line 310).
  Masking is honored only from user settings, managed settings, and
  `--settings`; `mask` entries, `network.tlsTerminate`, and
  `credentials.allowPlaintextInject` "are all ignored in a repository's
  `.claude/settings.json` or `.claude/settings.local.json`" (line 341).
  Same-variable `deny` takes precedence over `mask` (line 343). Optional
  fields `extract` (regex group 1), `onExtractNoMatch` (`warn` default,
  `deny`, `error`), and `decode: "jwt"` with `maskClaims` require
  v2.1.224 or later (lines 345-352).
- Claim 31 (Section~"Re-sign AWS requests", lines 356-393): the proxy
  detects SigV4 requests by the access key's sentinel and re-signs them;
  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` are
  linked automatically when masked whole; custom grouping via
  `credentials.awsPairs` requires v2.1.224 or later (line 360). Three
  request forms cannot be re-signed: aws-chunked streaming uploads
  (`streaming` key), presigned URLs (`presigned`), and SigV4A asymmetric
  signatures (`sigv4a`) (lines 389-393); `credentials.sigv4` (v2.1.224+)
  can relax each to `passthrough` (line 387).
- Claim 32 (Section~"Mask credential files", lines 395-445): file masking
  requires v2.1.221 or later (line 397). Linux/WSL2: sandboxed commands read
  a sentinel copy; macOS: the file is blocked entirely, "the same effect as
  `deny`", but unlike `deny` the read block holds even when filesystem
  isolation is disabled (lines 398-400). Claude Code "falls back to `deny`
  for a `mask` entry it can't mask safely: a directory path, a glob
  pattern, a file larger than 8 MiB, or a file that isn't UTF-8 text."
  (line 445). `maskDuplicates` replaces verbatim copies elsewhere; "Default:
  false." (line 443).
- Claim 33 (Section~"Configure the sandbox for your organization", lines
  561-594): the managed enforcement payload is `{ "sandbox": { "enabled":
  true, "failIfUnavailable": true, "allowUnsandboxedCommands": false } }`
  (lines 567-575). `failIfUnavailable` blocks startup when a dependency
  such as bubblewrap is missing (line 579). For boolean keys the managed
  value wins; for array keys such as `excludedCommands` and `allowRead`,
  "Claude Code merges entries from every scope, so a developer can append
  entries that widen the policy" (line 588). `allowManagedReadPathsOnly`
  locks `allowRead` to managed entries (line 590). "`excludedCommands` has
  no equivalent managed-only lockdown, so a developer can always append
  entries that run additional commands outside the sandbox." (line 594).
- Claim 34 (Section~"Custom proxy configuration", lines 596-616): custom
  proxies can decrypt/inspect HTTPS, filter, log, and integrate; configured
  via `sandbox.network.httpProxyPort` (example `8080`) and
  `socksProxyPort` (example `8081`) (lines 607-615).

### How docs frame capability versus safety

- Claim 35 (Section~"How sandboxing relates to permissions and permission
  modes", lines 514-555): sandboxing, permission rules, and permission modes
  are "complementary layers" (line 516). "`/sandbox` is not a permission
  mode" (line 547). Auto-allow and auto mode are distinct: "auto-allow
  approves Bash commands because the sandbox boundary contains them, while
  auto mode uses a classifier to review actions. The two work independently
  and can be combined." (line 555). The comparison table contrasts what each
  controls and "What replaces the prompt": for `/sandbox`, "The sandbox
  boundary itself, in auto-allow mode"; for auto mode, "A classifier that
  reviews actions"; for `--dangerously-skip-permissions`, "Nothing" (lines
  549-553).
- Claim 36 (Section~"Limitations", line 633): "Sandboxing reduces risk but
  is not a complete isolation boundary. Review the limitations below before
  relying on it as a hard security control." Additional disclosed limits:
  `allowUnixSockets` can grant access to powerful services such as
  `/var/run/docker.sock` (line 643); broad write permissions can enable
  privilege escalation (line 644); `enableWeakerNestedSandbox` "considerably
  weakens security" (line 645); `allowAppleEvents` "removes code-execution
  isolation" and is honored only from user, managed, or CLI settings (line
  646); performance overhead is "minimal, but some filesystem operations
  may be slightly slower." (line 651).

Interpretation by the source itself (distinguished from mechanism): the page
interprets its own design as capability and safety compounding rather than
trading off, i.e., auto-approval is justified by containment (line 10, line
525, line 555). That justification is the page's argument, not an
independently established fact; see Limitations.

## Evaluation and evidence

Docs source: no datasets, metrics, baselines, or quantitative evaluation.
Character-exact values the page carries:

- Version gates, in order of appearance: "Before v2.1.212" (plan-mode
  ask-rule skip, line 130), "v2.1.216" (`filesystem.disabled`, line 228),
  "v2.1.187" (`sandbox.credentials`, line 270), "v2.1.199" (env-var masking,
  line 306; `network.tlsTerminate`, line 488), "v2.1.219" (`strictAllowlist`,
  line 481), "v2.1.221" (file masking, line 397), "v2.1.224" (mask optional
  fields, line 345; `awsPairs`, line 360; `sigv4`, line 387; file `decode`,
  line 432), "v2.1.229" (bracketed IPv6, line 493).
- Size constant: mask fallback for "a file larger than 8 MiB" (line 445).
- Setting keys quoted character-exact in Key claims above; the page's own
  table of filesystem/network settings lives at lines 529-539.
- Dependencies: `bubblewrap`, `socat`, `ripgrep` (bundled), optional seccomp
  filter via `npm install -g @anthropic-ai/sandbox-runtime` (lines 60-61,
  79-81); standalone package `@anthropic-ai/sandbox-runtime` at
  `https://github.com/anthropic-experimental/sandbox-runtime` (line 512).
- Diagnostic strings: warning `Sandbox credential injectHosts entries can
  never match their destination` (line 339); warning `Sandbox network domain
  entries have unreliable spellings` (line 500); git failures with `unable
  to unlink old` ending in `Read-only file system` on Linux and WSL2 (line
  627); macOS Apple Events error `-600` (line 625).
- Troubleshooting facts: `watchman` incompatible with the sandbox, use
  `jest --no-watchman` (line 623); Go-based CLIs (`gh`, `gcloud`,
  `terraform`) may fail TLS verification under Seatbelt (line 624); `docker`
  is incompatible (line 626); `--dangerously-skip-permissions` is blocked
  when running as root or via sudo on Linux and macOS, with the check
  "skipped automatically inside a recognized sandbox" (line 629).

Not located, with where I looked:

- Any performance numbers, benchmark, or evaluation: `[CITATION NEEDED]`.
  Looked: entire snapshot; only the qualitative line 651 exists.
- The exact list of "certain denied directories" in the default read policy:
  `[CITATION NEEDED]`. Looked: Section~"Filesystem isolation" (lines
  449-459) and protected-paths list (lines 461-474); the default-deny read
  set is never enumerated.
- Which Claude Code release this page as a whole corresponds to:
  `[CITATION NEEDED]`. Looked: snapshot header (line 1, access date only)
  and full page text; only per-feature "requires vX or later" and "Before
  vX" notes appear, no page-level version pin.

## Limitations

- Closed core, docs-only evidence. The page's central enforcement claims
  ("the operating system enforces that boundary for every Bash command and
  its child processes", line 10; "These paths are enforced at the OS level",
  line 171; "The operating system enforces the sandbox boundary on the
  running process", line 525) cannot be checked against implementation code:
  the Claude Code core is closed source, and the pinned claude-code checkout
  (commit c3d2e35e5540, `sources/repos.yaml:5-11`) contains only the
  plugins/examples/scripts surface, not the sandbox implementation
  (`sources/registry.yaml:55`, `claudeCodePluginSurface` entry). The page
  points to the standalone `@anthropic-ai/sandbox-runtime` package as the
  same primitives (line 512), but that repository is not pinned in
  `sources/repos.yaml` (checked; only claude-code, codex, opencode are
  pinned) and is not registered as a source, so the "same primitives" claim
  is unverifiable in this study.
- Floating docs. The docs site is not version-pinned
  (`sources/registry.yaml:57`); the page's own version gates (v2.1.187
  through v2.1.229) show a rapidly moving surface, and nothing in the
  snapshot ties the whole page to a specific released CLI. Docs-versus-code
  comparisons for Claude Code must therefore cite this page for docs claims
  and can cite the pinned repo only for the plugin/settings surface.
- Disclosed safety-relevant defaults that weaken the headline framing:
  fail-open when the sandbox cannot start (lines 52-54); default read access
  to "the entire computer" including `~/.aws/credentials` and `~/.ssh/`
  (line 454); array-key merging plus the `excludedCommands` escape that
  developers can always widen (lines 588, 594); hostname-only allowlist
  decisions with no default TLS inspection and an acknowledged domain-
  fronting exfiltration path (lines 488, 637-641).
- The page's own stated limit: "not a complete isolation boundary" (line
  633), with a warning that neither layer alone suffices (lines 663-665).
- Snapshot completeness. The fetch appears complete (it ends with the
  "See also" section, lines 667-673, and preserves MDX-style blocks such as
  `<Warning>` and `<Steps>`), but I cannot rule out that the live page
  renders interactive content the Markdown fetch dropped; no such gap was
  observed.
- Gate flag (`depth: full`): this note fully captures the registered docs
  surface for Claude Code permissions/sandboxing, so it does not block a
  notes-gate verdict for this dimension at tier docs. It does confirm the
  permanent ceiling for RQ4 on this dimension: no code-level corroboration
  of sandbox semantics is obtainable from the closed core; the closest
  inspectable artifact (sandbox-runtime) is out of registry scope.

## Relevance to the brief

My inference, separated from the anchored material above.

- RQ3 (capability versus safety in shell and file access): this page is
  Claude Code's normative answer, and its structure is the finding. Approval
  and confinement are decoupled: a two-mode approval switch (auto-allow vs
  regular permissions) sits on top of a separately configured filesystem and
  network boundary, and capability is explicitly sold as the reward for the
  boundary (line 10, line 133: sandboxed Bash writes run without prompting
  even in Manual mode). The safety valves cut the other direction by design:
  the `dangerouslyDisableSandbox` escape hatch (lines 142-148) and
  `excludedCommands` (lines 582, 594) let specific capability out of the
  cage. That is a different shape from Codex's documented three access-level
  sandbox modes (`read-only`, `workspace-write`, `danger-full-access`,
  recorded in `notes/codexDocsSandboxing.md`) and from OpenCode's approval-
  rulesets-without-OS-sandbox posture (`notes/opencodePermissions.md`,
  `notes/opencodeDocs.md`). In the comparison matrix, Claude Code's row
  should read: OS boundary on Bash subprocesses, configurable per-path and
  per-domain, with approval modes orthogonal to the boundary.
- RQ4 (what the closed core reveals through docs and the plugin surface):
  three concrete corroborations. First, the docs confirm the plant-side
  finding that the `sandbox` settings property is Bash-only
  (`examples/settings/README.md:27` at commit c3d2e35, via
  `notes/claudeCodePluginSurface.md` line 87) with independent wording: "It
  applies only to Bash commands and their child processes." (line 523).
  Second, the docs add scope facts the repo does not state: subagent Bash is
  sandboxed (line 661), computer use is not (line 659), Read/Edit/Write are
  governed by the permission system instead (line 658). Third, the version
  gates expose the sandbox as an actively developed surface (eight version
  milestones between v2.1.187 and v2.1.229 named on this page alone), which
  fits the changelog stream of sandbox policy switches recorded in the
  plugin-surface note (`notes/claudeCodePluginSurface.md` lines 110-146).
- RQ1/RQ2 (component inventory): fills the Claude Code
  permissions/sandboxing cell at tier docs. The component vocabulary for the
  inventory: `/sandbox` panel (Mode/Overrides/Config/Dependencies tabs),
  sandbox modes, filesystem/network layers, protected paths, credentials
  deny/mask with proxy substitution and SigV4 re-signing, managed-settings
  pins, escape hatch, excludedCommands.
- Left open: the enforcement implementations themselves (Seatbelt profile
  contents, bubblewrap argv, proxy hostname matching, classifier used in
  auto mode) are all unobservable; the settings reference page
  (`/docs/en/settings`) is cited throughout but is not separately registered
  in this study (its content is partially covered by
  `notes/claudeCodeDocsPermissions.md` and the examples in the pinned repo).

## Quotables for the report

All quotes verified character-exact against the snapshot; line numbers cite
`sources/docs/claudeCodeDocsSandboxing.md`.

- "The Bash sandbox lets Claude run most shell commands without stopping to
  ask permission. Instead of approving each command, you define which files
  and network domains commands can touch, and the operating system enforces
  that boundary for every Bash command and its child processes." (line 10).
  Suggested framing: open the Claude Code safety paragraph with the
  capability-for-containment trade stated in the vendor's own words.
- "It applies only to Bash commands and their child processes." (line 523),
  paired with the repo's "The `sandbox` property only applies to the `Bash`
  tool; it does not apply to other tools (like Read, Write, WebSearch,
  WebFetch, MCPs), hooks, or internal commands" (`examples/settings/README.md:27`
  @ c3d2e35, via `notes/claudeCodePluginSurface.md` line 87). Suggested
  framing: the two official surfaces agree that the OS boundary is Bash-
  scoped by design, so the file tools remain on the pre-run permission layer.
- "The operating system enforces the sandbox boundary on the running
  process, so it holds regardless of what the model chose to run and even if
  an allowed command does more than its name suggests." (line 525). Suggested
  framing: contrast pre-run policy evaluation (permission rules, classifier)
  with in-run OS enforcement as Claude Code's stated two-layer safety model.
- "this default still allows reading credential files such as
  `~/.aws/credentials` and `~/.ssh/`" (line 454). Suggested framing: the
  default read surface is broad; the safety guarantee is concentrated in
  write containment and network egress unless the operator adds
  `sandbox.credentials` or `denyRead`.
- "By default, if the sandbox cannot start because dependencies are missing
  or the platform is unsupported, Claude Code shows a warning and runs
  commands without sandboxing." (lines 52-53). Suggested framing: the
  default posture is fail-open; `failIfUnavailable` is the documented switch
  to fail-closed for managed deployments.
- "Sandboxing reduces risk but is not a complete isolation boundary." (line
  633). Suggested framing: the vendor's own limitation statement, usable as
  the closing caveat for any claim about Claude Code confinement strength.
- "`excludedCommands` has no equivalent managed-only lockdown, so a
  developer can always append entries that run additional commands outside
  the sandbox." (line 594). Suggested framing: even the managed-settings
  floor has a documented widening path.
