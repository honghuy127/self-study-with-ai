---
# Note for the tengu-decoded README snapshot (third-party teardown of the
# Claude Code binary). Full snapshot read: sources/docs/tenguDecoded.md
# (README at main 8b2060df3da4dd676c9d1340e55cc228dcc87ddf, fetched
# 2026-08-20). Anchors cite README section headings plus snapshot line
# numbers. Everything in this note is the repo author's assertions, reported
# at catalog level without asserting accuracy; per registry provenance rules
# this source may only support hedged contextual claims about the closed core.
source_key: "tenguDecoded"
read_date: "2026-08-20"
confidence: "high"    # the snapshot itself is short and was read in full; trust in the underlying claims is low (see Limitations)
relevance: "2"        # useful context for RQ4; cannot bear strong claims (registry: context only)
---

# Notes: Tengu Decoded: reverse-engineering Claude Code's internals (feature flags, gated features, telemetry, device fingerprinting), version by version

## Source identification

- Key: tenguDecoded
- Authors, year, venue: wtfwhs, 2026, GitHub personal research archive
  (third-party teardown of the publicly distributed Claude Code binary; per
  the repository description, analyzed v2.1.32, v2.1.169, v2.1.197)
- Tier: blog
- URL / DOI: https://github.com/wtfwhs/tengu-decoded (snapshot:
  `sources/docs/tenguDecoded.md`, README fetched from
  `https://raw.githubusercontent.com/wtfwhs/tengu-decoded/main/README.md`
  2026-08-20 at `main` commit
  `8b2060df3da4dd676c9d1340e55cc228dcc87ddf`, snapshot header lines 1-2)
- The snapshot contains only the README (196 lines). All linked artifacts it
  references (per-version reports, datasets, extracted bundle, comparisons)
  are not in the snapshot and could not be consulted; see Limitations.

## Problem and motivation

The repository states its purpose as "Reverse-engineering Claude Code's
internals" covering "feature flags, gated features, telemetry, device
fingerprinting, and the infrastructure behind Anthropic's AI coding tool"
(Section "Tengu Decoded", subtitle, snapshot line 5). It asserts that
"Tengu" is Anthropic's internal codename for Claude Code and says the
repository "documents what the publicly distributed Claude Code binary
actually does, version by version" (Section "Tengu Decoded", snapshot lines
7-8). The author frames it as "a personal research archive", specifically "a
deep, private teardown for understanding the tool, not a published product"
(Section "Tengu Decoded", snapshot lines 17-18). Its claimed significance is
methodological: because recent builds embed the application JavaScript as
cleartext, the author says "findings come from real function bodies, not
isolated strings" (Section "Tengu Decoded", snapshot lines 10-15).

## Method or core idea

The README describes two complementary methods keyed to packaging (Section
"Methodology", snapshot lines 178-190):

1. String extraction with `strings`/`grep`, which "works on any build" and
   was used for v2.1.32 (snapshot line 182).
2. Cleartext bundle extraction plus beautification, used from v2.1.169: the
   author asserts Bun-compiled builds embed the application JavaScript as
   plaintext, that the byte range is carved out with `dd` and beautified "so
   whole function bodies can be read", and that the carved bundle and raw
   extracts are committed under each version's `bundle/` and `data/raw/`
   (snapshot lines 183-186). The author explicitly disclaims decompilation:
   "No machine code or JSC bytecode is decompiled/disassembled" (snapshot
   lines 187-188).

The author's own stated interpretive limit: "Variable names are
minified/mangled, so inferences about purpose come from call sites and
surrounding context" (Section "Methodology", snapshot lines 186-188). The
README points to `docs/methodology.md` for "the full extraction guide and
known limitations"; that document is not in the snapshot (snapshot line 190).

Reported version coverage (Section "Analyzed Versions", snapshot lines
20-31): three analyzed versions, all Linux x86-64: v2.1.197 (build date
2026-06-29, status "Complete (deep)"), v2.1.169 (build date 2026-06-08,
"Complete (deep)"), v2.1.32 (build date 2026-02-05, "Complete"). Cross-
version diffs are claimed to live in `comparisons/` as
`2.1.32-to-2.1.169.md` and `2.1.169-to-2.1.197.md` (snapshot lines 28-31 and
Section "Version Comparisons", snapshot lines 192-196).

## Key claims with anchors

All claims below are the repository author's assertions about the analyzed
binaries. This note reports them at catalog level and does not assert their
accuracy. Where the README states facts it is "establishing" (counts, file
lists, endpoint strings); where it assigns purpose to minified symbols or
frames a release narrative, it is interpreting, and I mark those cases.

Runtime and packaging:

- Claim 1 (Section "Key Findings (v2.1.169)", Runtime row, snapshot line 52):
  v2.1.169 is asserted to be a "Bun v1.3.14 compiled standalone binary"
  replacing the Node.js SEA packaging of v2.1.32, with the JS source
  recoverable as plaintext.
- Claim 2 (Section "Key Findings (v2.1.169)" note, snapshot lines 43-46):
  the author asserts the full 16.5 MB plaintext JS bundle was carved out and
  beautified to ~662k readable lines for v2.1.169.
- Claim 3 (blockquote "Latest (v2.1.197)", snapshot line 33): v2.1.197 is
  asserted to be Bun v1.4.0 with ~733k beautified lines.

Harness scale (catalog counts):

- Claim 4 (Section "Key Findings (v2.1.169)", Scale row, snapshot line 53):
  v2.1.169 is asserted to contain "218 feature flags, 1086 telemetry events,
  ~46 built-in tools, 490 env vars", versus "48 / 239 / 17 / 54 in 2.1.32".
- Claim 5 (blockquote "Latest (v2.1.197)", snapshot lines 36-38): v2.1.197
  headline counts asserted as "243 feature flags (+25), 1086 → 1163
  telemetry events, 49 built-in tools, 526 env vars, 164 API path
  templates".

Harness mechanisms most relevant to the brief (all author-asserted):

- Claim 6 (Section "Key Findings (v2.1.169)", Security row, snapshot line
  59): the author asserts "The 14-category regex injection pipeline is gone",
  replaced by "an LLM prefix-classifier + destructive-command regex + a
  two-stage auto-mode classifier; plus bubblewrap/seatbelt/WFP sandboxing".
- Claim 7 (Section "Key Findings (v2.1.169)", System Prompt row, snapshot
  line 60): the system prompt is asserted to be "Composed by `iT()` with
  per-section caching (`rT`)", with "modern models" receiving "a compact
  '# Harness' intro instead of the legacy 6-section layout". (`iT`, `rT` are
  minified identifiers; the purposes are the author's interpretation.)
- Claim 8 (Section "Key Findings (v2.1.169)", Providers row, snapshot line
  61): asserted provider planes are "Anthropic, Bedrock, Vertex, Foundry,
  Mantle, Gateway", selected by `Mq()`.
- Claim 9 (Section "Key Findings (v2.1.169)", Models row, snapshot line 62):
  the asserted default model is "claude-opus-4-8"; "fast mode" is described
  as a `speed:"fast"` request flag; 1M context is asserted to be enabled via
  a `[1m]` suffix; "Pro can now meter Opus against usage credits".
- Claim 10 (Section "Key Findings (v2.1.169)", Autonomy row, snapshot line
  57): the author asserts a background-agent daemon with `/background`,
  `/tasks`, `/fork`; "kairos" loops and scheduling with `/loop`, `/schedule`,
  cron; and "a VM-sandboxed Workflows engine".
- Claim 11 (Section "Key Findings (v2.1.169)", Cloud backend row, snapshot
  line 56): asserted new managed-agents API endpoints `/v1/sessions`,
  `/v1/agents`, `/v1/environments`, `/v1/files`, plus a "Remote-Control
  bridge over `wss://bridge.claudeusercontent.com`".
- Claim 12 (Section "Key Findings (v2.1.169)", Agent Teams row, snapshot
  line 58): the server-side Agent Teams gate is asserted to default open via
  flag "`tengu_amber_flint` `false`→`true`", still requiring
  "`--agent-teams`/env opt-in", adding "coordinator mode + shared team
  memory".
- Claim 13 (Section "Key Findings (v2.1.169)", Commands row, snapshot line
  63): "~64 active" slash commands asserted, plus hidden/easter-egg commands
  (`/radio`, `/heapdump`, `/bridge-kick`).
- Claim 14 (Section "Documentation", v2.1.169 report table, snapshot line
  130; v2.1.32 table, snapshot line 153): per-topic write-ups are claimed to
  exist covering harness internals, including an Architecture report on
  "Compaction, MCP, providers, teams, daemon, bridge, loops, workflows"
  (2.1.169) and "Context compaction, MCP, provider routing, agent teams"
  (2.1.32), plus Tool Definitions ("49 tools, schemas, permission modes" for
  2.1.197, snapshot line 105) and Security Model reports.

Telemetry and fingerprinting (author-asserted):

- Claim 15 (Section "Key Findings (v2.1.169)", Telemetry row, snapshot line
  55): "Segment removed." is asserted; first-party event logging at
  `/api/event_logging/v2/batch` is called "the spine"; "Datadog US5 is an
  allow-listed mirror (off by default)"; stack listed as "GrowthBook +
  optional OpenTelemetry + Perfetto".
- Claim 16 (Section "Key Findings (v2.1.169)", Device ID row, snapshot line
  54): the transmitted `device_id` is asserted to be "a random 256-bit
  per-install token (`crypto.randomBytes(32)` → `~/.claude.json`), not
  hardware-derived; the OS machine UUID is read but stripped to
  `host.arch`".
- Claim 17 (blockquote "Latest (v2.1.197)", snapshot lines 40-41): the
  author asserts "the Datadog telemetry token was not rotated this cycle",
  and asserts new v2.1.197 cloud surfaces: a declarative model catalog with
  the "`fable` family (`claude-fable-5`, Mythos-class) and `claude-sonnet-5`"
  plus "credential Vaults, memory stores, skill versioning, Claude Design
  MCP, and web-artifact frame deploy" (snapshot lines 38-40).

Codenames and flag naming (author's mappings, i.e. interpretation):

- Claim 18 (Section "Internal Codenames", snapshot lines 159-176): asserted
  mappings include tengu = "Claude Code (the product)", marble = "Model
  access and capabilities", copper = "Subscription and upsell system", coral
  = "Session and prompt features", grove = "Policy and privacy system",
  kairos = "Loops, scheduling, brief mode, push notifications", harbor =
  "Channels / cowork / teams", bridge/ccr = "Remote control & cloud-bundle
  execution", amber = "Agent Teams & autonomy", sage_compass = "Advisor
  tool"; kairos, harbor, bridge/ccr, amber, sage_compass are marked "new in
  2.1.169".
- Claim 19 (Section "Internal Codenames", note, snapshot lines 174-176):
  since 2.1.169, most flag names are asserted to be "auto-generated
  `adjective_noun` pairs from an embedded word pool" where "the noun carries
  the meaning, the adjective is random".

Claimed repository artifacts (catalog of what the repo says it contains;
not verified in this workspace):

- Claim 20 (Section "What's in each version directory", snapshot lines
  67-81): each version directory is claimed to ship `metadata.yaml`,
  per-topic `*.md` reports, `data/*.yaml` structured findings, `data/raw/`
  raw extraction output ("strings dumps, grep extracts") described as
  provenance, and `bundle/` containing `cli.beauty.js` ("beautified bundle
  (~662k lines)", called "the primary analysis source"), `cli.min.js`
  ("carved minified bundle (byte-for-byte from the binary)"), `carve.py`,
  and `ANALYSIS_CONTEXT.md`.
- Claim 21 (Section "Documentation", snapshot lines 136-139): v2.1.169
  structured datasets are claimed to include `feature-flags.yaml`,
  `telemetry-events.yaml`, `api-endpoints.yaml`, `environment-vars.yaml`,
  `commands.yaml`, `models.yaml`, `security-checks.yaml`, `tools.yaml`,
  `fingerprinting.yaml`.
- Claim 22 (Section "Documentation", General table, snapshot lines 85-92):
  general docs claimed to exist: `docs/methodology.md`, `docs/glossary.md`
  ("Internal codenames (tengu, marble, copper, coral, grove, kairos, harbor,
  …)"), `docs/architecture-overview.md`, `docs/how-to-analyze.md`.

## Evaluation and evidence

This is a blog-tier teardown index, not an evaluation; there are no
datasets, baselines, or metrics in the academic sense. What the README
offers as its evidence apparatus, all as the author's claims:

- Reproducibility claim: "Each version directory ships the extracted bundle
  and the raw extraction output alongside the write-ups, so every claim is
  reproducible" (Section "Tengu Decoded", snapshot lines 14-15). The
  committed artifacts named are `bundle/cli.beauty.js`, `bundle/cli.min.js`,
  `bundle/carve.py` ("extraction script (byte offsets used)"), and
  `data/raw/` (Section "What's in each version directory", snapshot lines
  69-81). None of these files are present in the snapshot, so the
  reproducibility claim could not be checked; I looked only at
  `sources/docs/tenguDecoded.md` and its header (snapshot lines 1-2 and 67-115).
- Quantities, copied character-exact from the README: v2.1.169 bundle "16.5
  MB plaintext JS bundle" beautified to "~662k readable lines" (snapshot
  lines 44-45); v2.1.197 "~733k beautified lines" (snapshot line 33); counts
  "243 feature flags (+25), 1086 → 1163 telemetry events, 49 built-in tools,
  526 env vars, 164 API path templates" (snapshot lines 36-38); for v2.1.169
  "218 feature flags, 1086 telemetry events, ~46 built-in tools, 490 env
  vars (vs 48 / 239 / 17 / 54 in 2.1.32)" (snapshot line 53).
- No independent replication, citation, or review of these findings appears
  in the snapshot. The author identifies the work as "a deep, private
  teardown for understanding the tool, not a published product" (snapshot
  lines 17-18).

## Limitations

This is an unverifiable third-party teardown. Its claims may only support
hedged, contextual statements in the report, never load-bearing claims about
Claude Code's harness. Concrete weaknesses:

- Single-source, author-asserted content. Every factual statement about the
  binary (counts, endpoint strings, flag names, classifier architecture,
  codename meanings) originates from wtfwhs and is not corroborated anywhere
  in the snapshot. The Claude Code core is closed source, so no pinned
  codebase cross-check exists for these claims.
- The snapshot is the README only. All linked evidence (per-version
  `*.md` reports, `data/*.yaml` datasets, `data/raw/` extracts,
  `bundle/cli.beauty.js`, `docs/methodology.md`, `comparisons/*`) is outside
  the snapshot and was not read; the summary therefore catalogs the index,
  not the evidence.
- Author's own interpretive caveat: "Variable names are minified/mangled, so
  inferences about purpose come from call sites and surrounding context"
  (Section "Methodology", snapshot lines 186-188). Purposes assigned to
  symbols like `iT()`, `rT`, `Mq()` are interpretations, not established
  facts.
- The README defers known limitations to `docs/methodology.md` (snapshot
  line 190), which is not in the snapshot; the author's own error modes are
  therefore unknown at note time. `[CITATION NEEDED]` (looked: snapshot
  lines 178-190, the only methodology text present).
- Coverage skew: all three analyzed builds are "Linux x86-64" (Section
  "Analyzed Versions", snapshot lines 22-26), yet the Security row asserts
  platform-specific mechanisms for Linux, macOS, and Windows
  ("bubblewrap/seatbelt/WFP", snapshot line 59); per-platform behavior is not
  directly observed (my inference from the table, not a README statement).
- Freshness: counts and gate states are per analyzed version (build dates
  2026-02-05, 2026-06-08, 2026-06-29, snapshot lines 22-26) and the README
  itself records them changing between versions (e.g., "243 feature flags
  (+25)", snapshot line 36); none of these values can be assumed to hold at
  any other version, including whatever build the pinned claude-code repo
  checkout corresponds to.
- No visible review process; personal archive framing ("not a published
  product", snapshot lines 17-18) means no editorial or peer check is
  implied.

## Relevance to the brief

My own inference, separated from source claims:

- RQ4 (what the closed core reveals): this is the most comprehensive
  third-party index of Claude Code internals in the registry. If its catalog
  is taken at face value, it suggests the closed harness includes roughly 49
  built-in tools with per-tool permission modes, a composed/cached system
  prompt, an LLM-based injection classifier plus OS sandboxes
  (bubblewrap/seatbelt/WFP claimed), growth-book feature-flag gating at a
  scale (218-243 flags asserted) with no analogue in the open systems. All
  such statements must stay hedged and attributed.
- RQ1/RQ3 (harness differences, capability vs safety): the teardown supplies
  testable hypotheses rather than findings, e.g. that Claude Code pairs an
  LLM prefix-classifier with regex and a two-stage auto-mode classifier,
  versus Codex's execpolicy/sandbox crates and OpenCode's rulesets visible in
  the pinned checkouts. Confirming or refuting any of this from primary
  sources is impossible for Claude Code's core; the comparison can only note
  the teardown's picture as alleged.
- Corroboration opportunities: claims that overlap with official docs or the
  pinned claude-code plugin surface (hooks settings examples, sandbox
  settings JSON) can be checked against those primary notes; teardown-only
  claims (telemetry endpoints, model catalog ids, cloud managed-agents API)
  stay context-only.
- Leaves open: turn-loop structure, compaction algorithm, and session-state
  format for Claude Code; the README's Architecture reports claim coverage of
  "Compaction" and "daemon" internals (snapshot lines 130, 153) but the
  report text is not in the snapshot, so even the teardown's detailed
  answers are unavailable to this note.

## Quotables for the report

Suggested framing for all of these: attribute explicitly and hedge, e.g.
"According to a third-party teardown of the distributed binary~\citep{...},
..." Never present these as established facts about Claude Code.

- Scale, v2.1.197 (blockquote "Latest (v2.1.197)", snapshot lines 36-38):
  "243 feature flags (+25), 1086 → 1163 telemetry events, 49 built-in tools,
  526 env vars, 164 API path templates". Use as the headline illustration of
  the closed harness's alleged configuration surface.
- Security model shift (Section "Key Findings (v2.1.169)", Security row,
  snapshot line 59): "The 14-category regex injection pipeline is gone",
  replaced by "an LLM prefix-classifier + destructive-command regex + a
  two-stage auto-mode classifier; plus bubblewrap/seatbelt/WFP sandboxing".
  Use as an alleged example of LLM-based input policing, contrasted with
  Codex's execpolicy approach.
- System prompt composition (Section "Key Findings (v2.1.169)", System
  Prompt row, snapshot line 60): prompt "Composed by `iT()` with per-section
  caching (`rT`)", with a compact "# Harness" intro on modern models. Use to
  hedge that prompt assembly in the closed core is modular and cached.
- Methodological self-description (Section "Tengu Decoded", snapshot lines
  13-15): "findings come from real function bodies, not isolated strings".
  Use only when explaining what kind of evidence a teardown can offer.
- Device identity (Section "Key Findings (v2.1.169)", Device ID row,
  snapshot line 54): the transmitted `device_id` is asserted to be "a random
  256-bit per-install token (`crypto.randomBytes(32)` → `~/.claude.json`),
  not hardware-derived". Use as the clearest teardown claim relevant to
  harness state files, if retained at all.
