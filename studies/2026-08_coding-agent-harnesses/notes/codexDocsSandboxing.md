---
# Note for the official Codex docs-site sandboxing page. The summarizer agent
# has webfetch denied (.opencode/agents/summarizer.md) and no snapshot of the
# page was retained in .research/ (searched .research/runs/, empty dir, and
# artifact_path is null in EVD-022). Content below is anchored to the
# gathering-stage verification record EVD-022, which logged a full-text check
# of the page on 2026-08-20. All unverifiable details carry [CITATION NEEDED].
source_key: "codexDocsSandboxing"
read_date: "2026-08-20"           # page accessed 2026-08-20 (EVD-022); note written same day
confidence: "low"                 # section-level record only; page not read directly here
relevance: "3"                    # central to RQ3 and the Codex permissions/sandboxing dimension
---

# Notes: Sandbox: How sandboxing works across ChatGPT and Codex clients

## Source identification

- Key: codexDocsSandboxing
- Authors, year, venue: OpenAI, 2026, developers.openai.com Codex docs (official)
- Tier: docs
- URL / DOI: https://developers.openai.com/codex/sandboxing (no DOI)
- Access record: page fetched with full text on 2026-08-20 during the
  gathering stage, verification status `full-text-checked` (EVD-022,
  `.research/evidence.jsonl:22`). The page title recorded there, "Sandbox:
  How sandboxing works across ChatGPT and Codex clients", matches the
  registry entry (`sources/registry.yaml:283-292`).

## Problem and motivation

The page is the official statement of how Codex sandboxes agent actions and
asks for approvals, and it explicitly spans more than the CLI: the recorded
title covers "ChatGPT and Codex clients" (EVD-022,
`.research/evidence.jsonl:22`). The repository itself treats this docs-site
area as canonical: at the pinned commit, `docs/sandbox.md` contains no
sandbox prose, only a heading and a pointer out of the repo
(`docs/sandbox.md:1-3` @ af700180808c):

> ## Sandbox & approvals
> For information about Codex sandboxing and approvals, see [this
> documentation](https://developers.openai.com/codex/security).

`SECURITY.md` likewise defers to the docs site "for details on Codex
security boundaries, including sandboxing, approvals, and network controls"
(`SECURITY.md:17` @ af700180808c). So the docs page, not the repo, carries
the normative capability-versus-safety framing that users and operators are
pointed to.

## Method or core idea

Only the section structure of the page is established by the available
record (EVD-022 locator, `.research/evidence.jsonl:22`; page fetched
2026-08-20). The page documents:

1. What the sandbox does (section "what the sandbox does", EVD-022 locator).
2. Platform-native enforcement, naming three backends: Seatbelt (macOS),
   bwrap (Linux), and a Windows sandbox (section "platform-native
   enforcement", EVD-022 locator).
3. Sandbox modes, named `read-only`, `workspace-write`, and
   `danger-full-access` (section "sandbox modes", EVD-022 locator).
4. Approval policies (section "approval policies", EVD-022 locator).
5. The `approvals_reviewer` setting, including the `auto_review` reviewer
   (section "approvals_reviewer incl. auto_review", EVD-022 locator).

The semantics of each section (what each mode permits, when approvals fire,
what the reviewer decides, any networking rules) are not recoverable from
the evidence record alone. `[CITATION NEEDED]` Where I looked: the page
itself (unreachable here, webfetch denied for this agent), `.research/runs/`
(empty, no retained snapshot), and `artifact_path: null` in EVD-022.

## Key claims with anchors

Established by the record (not by a direct read of the page in this note):

- Claim 1 (EVD-022, `.research/evidence.jsonl:22`): the page exists at
  `https://developers.openai.com/codex/sandboxing`, was fetched 2026-08-20,
  and passed a full-text check with the section structure listed above.
- Claim 2 (EVD-022 locator): the three documented sandbox mode names are
  `read-only`, `workspace-write`, `danger-full-access`, character-exact in
  the record.
- Claim 3 (EVD-022 locator): the documented enforcement is platform-native,
  with Seatbelt, bwrap, and a Windows sandbox as the three named backends.
- Claim 4 (EVD-022 locator): the page documents `approvals_reviewer` and
  includes `auto_review` as a reviewer option.
- Claim 5 (`docs/sandbox.md:1-3`, `SECURITY.md:17` @ af700180808c): the
  pinned repository treats the docs site as the authoritative location for
  sandboxing, approvals, and network-control prose, and for security
  boundaries generally.
- Claim 6 (EVD-022 notes field): the docs site is floating relative to the
  pinned code: it "may describe features newer than pinned checkout
  af70018", and the ledger directive is "cite page, not commit"
  (`.research/evidence.jsonl:22`; repeated in `sources/registry.yaml:57`).

Interpretation by the ledger, carried forward: EVD-022 assigns this page to
the permissions/sandboxing and config dimensions of the study
(`.research/evidence.jsonl:22`).

My inference (flagged, not a source claim): these mode and reviewer names
align character-exact with the pinned code's serialization, e.g.
`SandboxPolicy` variants and the sandbox tag strings
(`codex-rs/protocol/src/protocol.rs:1003-1051`,
`codex-rs/core/src/sandbox_tags.rs:45-57`, as recorded in
`notes/codexSandboxPermissions.md`), which suggests the page documents the
same policy model the pinned CLI implements, but the page text itself is not
available here to confirm the mapping.

## Evaluation and evidence

Docs source; there are no datasets, baselines, or metrics. Character-exact
values the record preserves:

- Sandbox mode names: `read-only`, `workspace-write`, `danger-full-access`
  (EVD-022 locator).
- Enforcement backend names: `Seatbelt`, `bwrap`, `Windows sandbox`
  (EVD-022 locator).
- Reviewer setting and option: `approvals_reviewer`, `auto_review`
  (EVD-022 locator).

Not located, with where I looked:

- Networking rules on this page: `[CITATION NEEDED]`. EVD-022's section list
  does not name a networking section. Looked: EVD-022 locator text; the repo
  defers network controls to the docs site in general (`SECURITY.md:17`
  mentions "network controls" but links a different slug, see Limitations).
- Config-key tables, default values, example TOML, any numerical limits on
  the page: `[CITATION NEEDED]`. Looked: same as above; no snapshot exists.
- How the page frames the capability-versus-safety tradeoff in its own
  words: `[CITATION NEEDED]`. Only the presence of mode and approval
  sections is recorded.

## Limitations

- Principal weakness: this note was written without a direct read of the
  page. The summarizer agent denies webfetch and bash
  (`.opencode/agents/summarizer.md:5-11`), and no snapshot of the fetched
  page was retained (`artifact_path: null` in EVD-022; `.research/runs/` is
  empty). Every content claim is therefore second-hand, anchored to a
  section-level locator logged by the gathering stage, and the note does not
  meet the claim-checkable bar against the page itself until the page is
  re-fetched or a snapshot is committed.
- URL relationship unverified. The registry URL is `/codex/sandboxing`, but
  the pinned repo's redirect target is `/codex/security`
  (`docs/sandbox.md:3` @ af700180808c) and `SECURITY.md:17` links
  `/codex/agent-approvals-security`. Whether these are three pages, or
  redirects of one page under rename, cannot be established from permitted
  inputs. `[CITATION NEEDED]`
- Floating-docs drift risk: the page may describe features newer than the
  pinned commit af700180808c (`sources/registry.yaml:57`, EVD-022 notes
  field). Any docs-versus-code comparison in this study must cite the page
  for docs claims and the pinned tree for code claims, and must not assume
  equality.
- The page's stated scope includes ChatGPT clients, which have no inspectable
  counterpart in the pinned checkout; those claims, whatever they are, are
  unverifiable against local code by construction.
- Gate flag for the literature gate (`study.yaml: depth: full`): this is a
  source-level gap on a registered docs entry. It does not block the code
  notes (the pinned-tree mechanics are covered by `codexSandboxPermissions`),
  but it does block a verdict that the Codex permissions/sandboxing
  dimension is fully covered at tier docs until the page is captured.

## Relevance to the brief

My inference, separated from the anchored material above.

- RQ3 (capability vs safety in shell and file access): this page is the
  normative user-facing half of Codex's answer, complementing the
  implementation half captured in `notes/codexSandboxPermissions.md`. Even
  the section-level record confirms the design surface the code shows:
  three named sandbox modes, platform-native enforcement per OS, approval
  policies, and a reviewer abstraction that includes model auto-review
  (EVD-022 locator). That the docs name the same three modes the code
  serializes (inference above) is worth a line in the report once verified.
- RQ1/RQ2 (component inventory): fills the Codex cell of the
  permissions/sandboxing dimension at tier docs, with an explicit caveat
  that docs-site content floats against pinned code
  (`sources/registry.yaml:57`). The ledger also flags nav siblings for later
  reading (`/codex/hooks`, `/codex/skills-and-plugins`,
  `/codex/agent-configuration/subagents`, EVD-022 notes field), which the
  orchestrator may want registered if extensibility docs coverage is needed.
- Left open until the page is captured: exact per-mode permission wording,
  networking rules, the documented interaction between sandbox modes and
  approval policies, and the page's own safety framing. The comparison
  matrix can carry the mode names and backend names now, marked as
  second-hand via EVD-022.

## Quotables for the report

Only strings verified in the permitted inputs; everything else is
`[CITATION NEEDED]`.

- Repo deferral to the docs site: "For information about Codex sandboxing
  and approvals, see [this documentation](https://developers.openai.com/codex/security)."
  (`docs/sandbox.md:3` @ af700180808c). Suggested framing: OpenAI keeps the
  sandbox contract off the repo and on the docs site, so the contract floats
  relative to any pinned commit.
- Documented mode vocabulary: `read-only`, `workspace-write`,
  `danger-full-access` (EVD-022 locator, page fetched 2026-08-20). Suggested
  framing: the user-facing knob is a three-state sandbox mode with
  platform-native enforcement (Seatbelt, bwrap, Windows sandbox) behind it.
- Documented reviewer vocabulary: `approvals_reviewer` including
  `auto_review` (EVD-022 locator). Suggested framing: Codex documents a
  second reviewer, a model, as a first-class approval path.
