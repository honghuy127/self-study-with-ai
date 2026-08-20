---
source_key: "codexDocsRepo"
read_date: "2026-08-20"
confidence: "high"
relevance: "2"
repo: "codex"
commit: "af700180808cce2ce28a31aad0fbad4dc58b857a"
---

# Notes: Codex CLI repository documentation (docs/ directory)

## Source identification

- Key: `codexDocsRepo`
- Authors, year, venue: OpenAI, 2026, `docs/` directory of github.com/openai/codex (official repository documentation)
- Tier: docs
- URL / DOI: https://github.com/openai/codex/tree/main/docs
- Read as: the pinned local checkout at `/Users/hong.huy.nguyen/Work/Code/references/coding-agents/codex`, commit `af700180808cce2ce28a31aad0fbad4dc58b857a` (`sources/repos.yaml`; `.git/refs/heads/main` confirmed equal to the pinned commit, tree recorded clean at pin time 2026-08-19). All `docs/*` anchors below are relative to that commit. Code cross-checks cite files under `codex-rs/` in the same commit.

## Problem and motivation

`docs/` is the user-facing documentation shipped inside the Codex CLI source tree. At the pinned commit it contains 15 files spanning product documentation areas (getting started, configuration, sample configuration, sandbox and approvals, non-interactive mode, AGENTS.md, skills, slash commands, execution policy, authentication) plus install/build, license, CLA, contributing, and a funding program (directory listing of `docs/` at the pinned commit).

The docs state no motivation of their own; their role must be inferred from structure and content. The dominant structural fact at this commit is that the directory is primarily a routing layer to the external docs site developers.openai.com: 9 of the 15 files are 3-line stubs whose entire content is a heading and one "see [this documentation](...)" link (`docs/getting-started.md:1-3`, `docs/sandbox.md:1-3`, `docs/agents_md.md:1-3`, `docs/exec.md:1-3`, `docs/skills.md:1-3`, `docs/slash_commands.md:1-3`, `docs/execpolicy.md:1-3`, `docs/authentication.md:1-3`, `docs/example-config.md:1-3`). `docs/config.md` follows the same redirect pattern for its first seven lines but adds one substantive in-repo section ("Lifecycle hooks", `docs/config.md:9-15`). The remaining 5 files carry in-repo prose (`docs/install.md`, `docs/contributing.md`, `docs/license.md`, `docs/CLA.md`, `docs/open-source-fund.md`).

## Method or core idea

### Redirect map (targets copied character-exact)

Each stub delegates one topic to one developers.openai.com URL:

- `docs/getting-started.md:3` delegates to `https://developers.openai.com/codex/cli/features#running-in-interactive-mode`
- `docs/config.md:3`, `:5`, `:7` delegate basic configuration, advanced configuration, and the full configuration reference to `https://developers.openai.com/codex/config-basic`, `https://developers.openai.com/codex/config-advanced`, `https://developers.openai.com/codex/config-reference`
- `docs/sandbox.md:3` delegates to `https://developers.openai.com/codex/security`
- `docs/agents_md.md:3` delegates to `https://developers.openai.com/codex/guides/agents-md`
- `docs/exec.md:3` delegates to `https://developers.openai.com/codex/noninteractive`
- `docs/skills.md:3` delegates to `https://developers.openai.com/codex/skills`
- `docs/slash_commands.md:3` delegates to `https://developers.openai.com/codex/cli/slash-commands`
- `docs/execpolicy.md:3` delegates to `https://developers.openai.com/codex/exec-policy`
- `docs/authentication.md:3` delegates to `https://developers.openai.com/codex/auth`
- `docs/example-config.md:3` delegates to `https://developers.openai.com/codex/config-sample`

### Harness-relevant content kept in the repo

1. Lifecycle hooks policy (`docs/config.md:9-15`): the only configuration-level statement in the directory. Full text quoted in Key claims, claim 2.
2. Install, build, and logging (`docs/install.md:1-65`): a system-requirements table (`docs/install.md:5-9`); a DotSlash release artifact for version-pinning the `codex` binary in source control (`docs/install.md:11-13`); build-from-source steps that identify `codex-rs` as "the root of the Cargo workspace", use `just` and `cargo-nextest` helpers, and launch the TUI with `cargo run --bin codex -- "explain this codebase to me"` (`docs/install.md:15-50`); a "Tracing / verbose logging" section describing `RUST_LOG`, the `log_dir` config key, the `-c key=value` override, and the non-interactive log default (`docs/install.md:52-65`).

### Adjacent docs split (structural observation)

A second doc tree, `codex-rs/docs/`, exists at the same commit with files `bazel.md`, `codex_mcp_interface.md`, `protocol_v1.md` (directory listing of `codex-rs/docs/` at the pinned commit). It is outside this entry's component scope (the sibling note `notes/codexInterfaces.md` cites it for the protocol surface). Recorded here only so the documentation split is explicit: user-facing docs live in or route through `docs/`, protocol and build docs live in `codex-rs/docs/`.

## Key claims with anchors

Source claims (what the docs state):

- Claim 1 (`docs/config.md:3-7`): basic configuration, advanced configuration, and the full configuration reference are published externally; the repo file gives no configuration reference of its own.
- Claim 2 (`docs/config.md:9-15`): "Admins can set top-level `allow_managed_hooks_only = true` in `requirements.toml` to ignore user, project, and session hook configs while still allowing managed hooks from requirements and managed config layers." Furthermore: "This setting is only supported in `requirements.toml`; putting it in `config.toml` does not enable managed-hooks-only mode."
- Claim 3 (`docs/sandbox.md:1-3`): sandbox and approvals form one documentation area, titled "Sandbox & approvals", documented at developers.openai.com/codex/security.
- Claim 4 (`docs/agents_md.md:1-3`): AGENTS.md is a named documentation area, documented at developers.openai.com/codex/guides/agents-md.
- Claim 5 (`docs/exec.md:1-3`): non-interactive execution is a named mode, titled "Non-interactive mode", documented at developers.openai.com/codex/noninteractive.
- Claim 6 (`docs/skills.md:3`, `docs/slash_commands.md:3`, `docs/execpolicy.md:1-3`, `docs/authentication.md:1-3`): skills, slash commands, execution policy, and authentication are named documentation areas, each documented at the URLs in the redirect map.
- Claim 7 (`docs/install.md:5-9`): supported platforms are "macOS 12+, Ubuntu 20.04+/Debian 10+, or Windows 11 **via WSL2**"; "Git (optional, recommended) 2.23+ for built-in PR helpers"; "RAM 4-GB minimum (8-GB recommended)".
- Claim 8 (`docs/install.md:11-13`): "The GitHub Release also contains a [DotSlash](https://dotslash-cli.com/) file for the Codex CLI named `codex`", enabling a source-control commit that pins one executable version across platforms.
- Claim 9 (`docs/install.md:17-38`): the source builds from `codex-rs` ("the root of the Cargo workspace") with `cargo build`, and `cargo run --bin codex -- "explain this codebase to me"` launches the TUI.
- Claim 10 (`docs/install.md:54`): "Codex is written in Rust, so it honors the `RUST_LOG` environment variable to configure its logging behavior."
- Claim 11 (`docs/install.md:56-61`): "The TUI records diagnostics in bounded local stores by default. Set `log_dir` explicitly to enable a plaintext TUI log for a run", with the example `codex -c log_dir=./.codex-log` followed by `tail -F ./.codex-log/codex-tui.log`.
- Claim 12 (`docs/install.md:63`): "The non-interactive mode (`codex exec`) defaults to `RUST_LOG=error`, but messages are printed inline, so there is no need to monitor a separate file."
- Claim 13 (`docs/contributing.md:5`): "We do not accept external code contributions or pull requests." Community contribution is limited to issue reports, analysis, and feedback; implementation "is comparatively straightforward with the help of Codex itself" (`docs/contributing.md:9-13`).
- Claim 14 (`docs/license.md:3`): "This repository is licensed under the [Apache-2.0 License](../LICENSE)."
- Claim 15 (`docs/open-source-fund.md:3-6`): "a **$1 million initiative** supporting open source projects that use Codex CLI and other OpenAI models"; "Grants are awarded up to **$25,000** API credits."; "Applications are reviewed **on a rolling basis**."

Doc-versus-code checks at the same pinned commit (my verification, code anchors given):

- Claim 2 is corroborated by code (docs agree). `allow_managed_hooks_only` is parsed as `Option<Sourced<bool>>` from requirements config (`codex-rs/config/src/config_requirements.rs:174`); hook discovery keeps a hook only when `!self.allow_managed_hooks_only || source.is_managed` (`codex-rs/hooks/src/engine/discovery.rs:81-87`), reading the flag from the config layer stack's requirements layer (`codex-rs/hooks/src/engine/discovery.rs:105-108`). The `requirements.toml`-only restriction is tested directly: `top_level_allow_managed_hooks_only_in_user_config_does_not_enable_requirements_policy` (`codex-rs/core/src/config/config_loader_tests.rs:357-378`) and `hooks_allow_managed_hooks_only_in_user_config_does_not_enable_requirements_policy` (`codex-rs/core/src/config/config_loader_tests.rs:384-419`) assert the flag in user config layer does not enable the policy, and `allow_managed_hooks_only_in_config_toml_does_not_enable_policy` asserts the same for `config.toml` (`codex-rs/hooks/src/engine/mod_tests.rs:1189`).
- Claim 12 simplifies the code (docs understate). The exec fallback filter constant is `EXEC_DEFAULT_LOG_FILTER: &str = "error,opentelemetry_sdk=off,opentelemetry_otlp=off"` (`codex-rs/exec/src/lib.rs:168`), applied only when `RUST_LOG` is unset because `EnvFilter::try_from_default_env()` takes precedence (`codex-rs/exec/src/lib.rs:240-242`). The docs omit the OpenTelemetry suppression and do not state the precedence.
- Claim 11's `-c key=value` syntax agrees with code. It is a global clap option (short `-c`, long `--config`, "Override a configuration value that would otherwise be loaded from `~/.codex/config.toml`", dotted keys, TOML-parsed values) (`codex-rs/utils/cli/src/config_override.rs:19-37`), with an example `-c 'sandbox_permissions=["disk-full-read-access"]'` (`codex-rs/utils/cli/src/config_override.rs:27`).
- Claim 11's file behavior agrees with code where the docs make assertions: the plaintext TUI log is named `codex-tui.log` (`codex-rs/tui/src/lib.rs:236`), and the TUI file log layer is built only when `log_dir` is present in the effective config layer or requirements layer (`codex-rs/tui/src/startup_orchestration.rs:412-421`, `:450-465`). The code extends beyond the docs: the log file is opened with mode `0o600` on Unix (`codex-rs/tui/src/startup_orchestration.rs:459-463`) and the file layer defaults to `codex_core=info,codex_tui=info,codex_rmcp_client=info` unless `RUST_LOG` overrides (`codex-rs/tui/src/startup_orchestration.rs:467-469`).
- Claim 11's "bounded local stores" are unquantified in the docs. My inference, not a docs claim: the default in-memory diagnostic store is the feedback crate's bounded ring buffer ("Capture diagnostics independently of `RUST_LOG` without filling the feedback ring", `codex-rs/feedback/src/lib.rs:216`). The docs do not name this mechanism, so treat the mapping as inference pending confirmation in the pinned code's feedback wiring.

No internal contradictions were found among the 15 in-repo files.

## Evaluation and evidence

No datasets, metrics, baselines, or quantitative evaluation of any kind. I searched all 15 files at the pinned commit; the source is product documentation and contains no evaluation. `[CITATION NEEDED]` is therefore not applicable to any metric; there are no evaluation values to locate. The only numbers in the source are the vendor platform and resource values in claim 7 (copied character-exact there), the fund figures in claim 15 ("$1 million", "$25,000"), and the Git threshold "2.23+" (`docs/install.md:8`). No CLI version string appears anywhere in `docs/` at this commit (checked all 15 files).

## Limitations

- Harness-semantics documentation is absent from the pinned tree. Approval modes, sandbox semantics, AGENTS.md/memory semantics, non-interactive exec options, execution-policy rules, skills, and slash commands are all named topics whose content lives only at the unpinned URLs in the redirect map. This note cannot verify those pages (no web access), and the only separately registered docs-site page is developers.openai.com/codex/sandboxing (registry key `codexDocsSandboxing`).
- The stubs carry no version numbers or dates, so redirect targets can drift against commit `af700180808c` with no in-repo signal. The registry's own `coverage_limits` already warns that Codex docs-site content may describe features newer than the pinned checkout.
- At least one documented value understates the code: the exec log default is "`RUST_LOG=error`" in the docs (`docs/install.md:63`) versus `"error,opentelemetry_sdk=off,opentelemetry_otlp=off"` in code (`codex-rs/exec/src/lib.rs:168`).
- The in-repo config surface is one key deep. Only `allow_managed_hooks_only` and its layer restriction are documented (`docs/config.md:9-15`); the full config reference is external (`docs/config.md:7`), so the docs cannot be reconciled here against the complete set of keys the code accepts.
- Platform-support values are vendor assertions with no supporting evidence in the tree; record them as vendor statements, not verified claims.
- Governance: external code contributions are explicitly refused (`docs/contributing.md:5`), so docs-code agreement depends entirely on OpenAI internal process, with no third-party review pressure on either side.

## Relevance to the brief

The following are my inferences, separated from the source claims above.

- RQ1 and RQ2 (where Codex harness behavior is documented): the comparison matrix cells for Codex approvals, sandbox semantics, AGENTS.md, exec options, skills, slash commands, and execution policy cannot be filled from this source at the pinned commit. They must be filled from the pinned code (notes `codexSandboxPermissions`, `codexToolsPatch`, `codexExtensibility`, `codexInterfaces`, `codexConfigProviders`) and from docs-site entries (`codexDocsSandboxing`; the developers.openai.com config and noninteractive pages are not registered in this study). The negative finding itself is reportable: at this commit Codex has externalized its user-facing harness documentation, so the repository no longer self-documents harness semantics.
- RQ3 (capability versus safety): the only in-repo safety-adjacent statement is the admin-facing `allow_managed_hooks_only` control (`docs/config.md:9-15`), code-corroborated above. It shows Codex exposes an enterprise policy layer (`requirements.toml`) that can strip hooks supplied by user, project, or session layers. How this layer relates to approvals and sandboxing is deferred to `codexSandboxPermissions` and `codexDocsSandboxing`.
- RQ1 (interfaces): two small, code-verified facts for the interfaces row: non-interactive `codex exec` logs at error level by default with inline output (`docs/install.md:63`, refined by `codex-rs/exec/src/lib.rs:168`), and the TUI offers an opt-in plaintext log via `log_dir` or `-c` override (`docs/install.md:56-61`, `codex-rs/tui/src/startup_orchestration.rs:450-465`).
- Left open: everything behind the redirect map, the managed-config layer semantics beyond the hooks-only flag, and the complete configuration surface.

Gap flag for the literature gate (depth: full): this source alone cannot fill the Codex docs cell for approval modes, sandbox semantics, AGENTS.md, or the config reference. The blocking dependencies are the still-`to-read` entry `codexDocsSandboxing` and the unregistered developers.openai.com config/noninteractive pages. These should be resolved before a notes-gate verdict that claims full Codex documentation coverage.

## Quotables for the report

- "Admins can set top-level `allow_managed_hooks_only = true` in `requirements.toml` to ignore user, project, and session hook configs while still allowing managed hooks from requirements and managed config layers." (`docs/config.md:11-14`). Suggested framing: evidence that Codex ships an enterprise policy layer for extensibility; cite alongside the code anchor `codex-rs/hooks/src/engine/discovery.rs:87` for a dual docs-plus-code citation.
- "The non-interactive mode (`codex exec`) defaults to `RUST_LOG=error`, but messages are printed inline, so there is no need to monitor a separate file." (`docs/install.md:63`). Suggested framing: non-interactive logging posture in the interfaces comparison; include the code-level refinement if the sentence needs precision.
- "macOS 12+, Ubuntu 20.04+/Debian 10+, or Windows 11 **via WSL2**" (`docs/install.md:7`). Suggested framing: platform-support row of the harness comparison table.
- "We do not accept external code contributions or pull requests." (`docs/contributing.md:5`). Suggested framing: governance contrast when discussing docs-code agreement risk across the three systems.
- "Set `log_dir` explicitly to enable a plaintext TUI log for a run" with `codex -c log_dir=./.codex-log` (`docs/install.md:56-60`). Suggested framing: concrete example of the `-c` config-override surface in the configuration comparison.
