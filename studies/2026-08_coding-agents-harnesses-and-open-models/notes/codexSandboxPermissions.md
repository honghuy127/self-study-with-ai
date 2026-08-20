---
source_key: "codexSandboxPermissions"
read_date: "2026-08-20"
confidence: "high"
relevance: "3"
repo: "codex"
commit: "af700180808cce2ce28a31aad0fbad4dc58b857a"
---

# Notes: Codex: sandboxing, exec policy, process hardening, approvals (codex)

## Source identification

- Key: codexSandboxPermissions
- Repository: `codex` at `af700180808cce2ce28a31aad0fbad4dc58b857a` (see `sources/repos.yaml`)
- Component scope: `codex-rs/sandboxing/` (macOS seatbelt, bubblewrap discovery, landlock argv builder, denial/violation taxonomy, policy transforms), `codex-rs/linux-sandbox/` (bubblewrap + seccomp + legacy Landlock helper binary), `codex-rs/execpolicy/` (prefix-rule policy engine), `codex-rs/process-hardening/`, `codex-rs/shell-escalation/` (execve interception and escalation protocol), `codex-rs/bwrap/` (bundled bubblewrap shim), `codex-rs/windows-sandbox-rs/` (crate-level survey only), `codex-rs/core/src/exec_policy.rs`, `codex-rs/core/src/sandboxing/mod.rs`, `codex-rs/core/src/guardian/`, `codex-rs/core/src/windows_sandbox.rs`, `codex-rs/core/src/network_policy_decision.rs`. Cross-component anchors (marked below) touch `codex-rs/protocol/src/`, `codex-rs/config/src/`, `codex-rs/core/src/exec.rs`, and `codex-rs/core/src/tools/{sandboxing,orchestrator}.rs`, which live in sibling registry entries; they are included only to wire the flow together.
- Tier: codebase

## Purpose and role in the harness

This component is the safety boundary for every shell command the model proposes. It
turns a declarative `PermissionProfile` (managed filesystem rules plus a network
policy, `codex-rs/protocol/src/models.rs:411`) into a concrete OS sandbox at spawn
time and decides, before execution, whether a command needs user approval
(`codex-rs/core/src/exec_policy.rs:315`). The pieces:

- `codex-rs/sandboxing/` owns platform policy selection and argv construction:
  `SandboxManager::transform` wraps a command in `/usr/bin/sandbox-exec` (macOS)
  or the `codex-linux-sandbox` helper (Linux), or returns it unwrapped
  (`codex-rs/sandboxing/src/manager.rs:323`).
- `codex-rs/linux-sandbox/` is the helper binary that builds the bubblewrap
  filesystem view, then applies `no_new_privs` + seccomp inside the sandboxed
  process (`codex-rs/linux-sandbox/src/linux_run_main.rs:149-155`).
- `codex-rs/execpolicy/` evaluates commands against user-written Starlark
  `prefix_rule` files with decisions `allow | prompt | forbidden`
  (`codex-rs/execpolicy/src/decision.rs:9`).
- `codex-rs/shell-escalation/` intercepts `execve(2)` from an approved
  interactive shell and forwards each command to the harness for a
  `Run | Escalate | Deny` decision (`codex-rs/shell-escalation/README.md:6-16`).
- `codex-rs/process-hardening/` strips `LD_*`/`DYLD_*` variables and blocks
  ptrace/core dumps pre-main (`codex-rs/process-hardening/src/lib.rs:12`).
- `codex-rs/core/src/guardian/` is an optional model-based auto-reviewer that
  answers approval prompts instead of the user, and fails closed
  (`codex-rs/core/src/guardian/mod.rs:1-12`).

## Mechanism

### Approval policy modes (cross-component: codex-rs/protocol)

`AskForApproval` has four modes, serialized kebab-case: `untrusted`
(`UnlessTrusted`, only `is_safe_command()` read-only commands auto-approved),
`on-request` (`OnRequest`, the `#[default]`, alias `on-failure`), `granular`
(`Granular(GranularApprovalConfig)`), and `never` (`Never`, failures go straight
back to the model) (`codex-rs/protocol/src/protocol.rs:916-940`). The granular
config gates five prompt families independently: `sandbox_approval`, `rules`,
`skill_approval`, `request_permissions`, `mcp_elicitations`
(`codex-rs/protocol/src/protocol.rs:943-957`). The sandbox policy enum is
`SandboxPolicy` with variants `danger-full-access`, `read-only`,
`external-sandbox`, `workspace-write` (the last carries `writable_roots`,
`network_access`, `exclude_tmpdir_env_var`, `exclude_slash_tmp`)
(`codex-rs/protocol/src/protocol.rs:1003-1051`). The runtime-normalized form is
`PermissionProfile::{Managed, Disabled, External}` whose `Default` is
`Managed` with restricted empty filesystem entries and
`NetworkSandboxPolicy::Restricted` (`codex-rs/protocol/src/models.rs:411-470`).

### Policy evaluation pipeline (execpolicy)

Rules are Starlark files with `prefix_rule(pattern=[...], decision, justification,
match, not_match)` plus `host_executable(name, paths)` and `network_rule(host,
protocol, decision)` (`codex-rs/execpolicy/README.md:14-44`,
`codex-rs/execpolicy/src/parser.rs:347-428`). Matching keys rules by first token
(`Policy.rules_by_program`, `codex-rs/execpolicy/src/policy.rs:29`); exact
first-token match is tried first, then optional basename fallback for absolute
paths gated by `host_executable` path lists
(`codex-rs/execpolicy/src/policy.rs:334-371`). When no rule matches, a caller-
supplied heuristics fallback returns a `HeuristicsRuleMatch`
(`codex-rs/execpolicy/src/policy.rs:322-331`). The aggregate decision is the
strictest severity across matches, `forbidden` > `prompt` > `allow`, via `max()`
on `PartialOrd` (`codex-rs/execpolicy/src/policy.rs:402-411`,
`codex-rs/execpolicy/README.md:95`).

`codex-rs/core/src/exec_policy.rs` loads `*.rules` files from every config
layer's `rules/` directory in low-to-high precedence order
(`codex-rs/core/src/exec_policy.rs:650-704`, dir/ext/file constants at
`:55-57`: `RULES_DIR_NAME = "rules"`, `RULE_EXTENSION = "rules"`,
`DEFAULT_POLICY_FILE = "default.rules"`). User-approved amendments are appended
to `$CODEX_HOME/rules/default.rules` as
`prefix_rule(pattern=..., decision="allow")`
(`codex-rs/core/src/exec_policy.rs:452-500`,
`codex-rs/execpolicy/src/amend.rs:65-79`).

The heuristics fallback `render_decision_for_unmatched_command` implements the
approval-policy/sandbox coupling
(`codex-rs/core/src/exec_policy.rs:740-841`):

- `is_known_safe_command` + `UnlessTrusted` → `Allow`
  (`codex-rs/core/src/exec_policy.rs:771-777`).
- Dangerous-word match (`DangerousCommandMatch`, e.g. forced `rm`) → `Prompt`,
  or `Forbidden` under `Never` (`codex-rs/core/src/exec_policy.rs:785-793`,
  rejection text `rm -f style commands are not permitted. Use a safer approach`
  at `:1101-1110`).
- `Never` → `Allow`, explicitly "relying on the sandbox for protection"
  (`codex-rs/core/src/exec_policy.rs:796-800`).
- `OnRequest` with a restricted filesystem kind → `Allow` unless the tool call
  requested a sandbox override (`codex-rs/core/src/exec_policy.rs:806-825`),
  i.e. the sandbox, not a prompt, polices ordinary commands.

`Decision::Prompt` surfaces to the user unless the approval policy rejects it:
`Never` yields `approval required by policy, but AskForApproval is set to Never`
(`codex-rs/core/src/exec_policy.rs:49-50`, `:218-240`). A prompt decision on a
restricted `OnRequest`/`Granular` flow can be intercepted by the guardian
auto-reviewer instead of the user
(`codex-rs/core/src/guardian/review.rs:193-201`: routing requires
`approvals_reviewer == ApprovalsReviewer::AutoReview`).

### Sandbox selection and transformation (macOS seatbelt, Linux helper)

`SandboxType` is `None | MacosSeatbelt | LinuxSeccomp | WindowsRestrictedToken`
with metric tags `none | seatbelt | seccomp | windows_sandbox`
(`codex-rs/sandboxing/src/manager.rs:36-53`). Platform choice is static per OS
except Windows, where the backend must be enabled
(`codex-rs/sandboxing/src/manager.rs:62-76`).
`SandboxManager::should_sandbox` returns true for preference `Require`, false
for `Forbid`, and for `Auto` delegates to `should_require_platform_sandbox`
(`codex-rs/sandboxing/src/manager.rs:302-321`), which requires a sandbox when
managed network requirements are active, when network is restricted, or when the
filesystem kind is `Restricted` without full-disk write; `ExternalSandbox`
suppresses nesting (`codex-rs/sandboxing/src/policy_transforms.rs:541-561`).

macOS: the wrapper is hard-coded to `/usr/bin/sandbox-exec` ("to defend against
an attacker trying to inject a malicious version on the PATH",
`codex-rs/sandboxing/src/seatbelt.rs:35-39`). The generated SBPL always starts
from `seatbelt_base_policy.sbpl`, whose first rule is `(deny default)`
(`codex-rs/sandboxing/src/seatbelt_base_policy.sbpl:8`) and which allows
`(allow process-exec)` and `(allow process-fork)` so children inherit the policy
(`:10-13`), then appends read roots, write roots, deny-read glob regexes, and a
dynamic network section; roots are passed as `-DKEY=value` parameters, never
interpolated into rule text (`codex-rs/sandboxing/src/seatbelt.rs:757-789`).
Network policy fails closed when proxy configuration exists but no loopback
endpoint can be inferred (`codex-rs/sandboxing/src/seatbelt.rs:321-331`).
Workspace metadata names `.git`, `.agents`, `.codex` are protected inside
writable roots with `(require-not (literal ...))` plus `(require-not
(subpath ...))` specifically to close the `mkdir .codex` gap
(`codex-rs/sandboxing/src/seatbelt.rs:389-404`,
`codex-rs/protocol/src/permissions.rs:24-33`).

Linux: `SandboxManager::transform` serializes the whole `PermissionProfile` to
JSON and re-execs the trusted helper with args `--sandbox-policy-cwd`,
`--command-cwd`, `--permission-profile <json>`, optional
`--use-legacy-landlock` / `--allow-network-for-proxy`, then `--` and the command
(`codex-rs/sandboxing/src/landlock.rs:23-60`). The helper binary is
`codex-linux-sandbox`; when the exe basename differs, argv[0] is overridden to
`CODEX_LINUX_SANDBOX_ARG0 = "codex-linux-sandbox"`
(`codex-rs/sandboxing/src/landlock.rs:6`,
`codex-rs/sandboxing/src/manager.rs:708-714`).

The helper's `run_main` sequence is: build bubblewrap filesystem view, apply
in-process restrictions (`no_new_privs` + seccomp), `execvp` the command
(`codex-rs/linux-sandbox/src/linux_run_main.rs:149-155`). Concretely:

- Inner stage (`--apply-seccomp-then-exec`) verifies descriptor-backed mounts,
  then panics if any effective or permitted Linux capability remains: "Linux
  sandbox retained effective or permitted capabilities" via raw `SYS_capget`
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:196-218`).
- With full-disk write and no proxy requirement the helper skips bubblewrap and
  applies only the in-process restrictions
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:274-285`).
- Default path builds bwrap argv, re-execs itself inside as the seccomp stage,
  and "never falls back to legacy Landlock on failure"
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:287-319`).
- Legacy Landlock path applies read-only-filesystem Landlock rules only when the
  policy round-trips, uses `ABI::V5`, and errors
  `SandboxErr::LandlockRestrict` on `RulesetStatus::NotEnforced`
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:321-331`,
  `codex-rs/linux-sandbox/src/landlock.rs:137-163`); it rejects restricted
  read-only access as unsupported
  (`codex-rs/linux-sandbox/src/landlock.rs:71-77`).

Bubblewrap argv construction (`codex-rs/linux-sandbox/src/bwrap.rs`):
restricted policies start from `--ro-bind / /` (full-read) or `--tmpfs /` plus
scoped `--ro-bind` mounts; writable roots are layered with `--bind <root>
<root>`; protected subpaths are re-protected with `--ro-bind <subpath>
<subpath>`; unreadable paths are masked; documented mount order at
`codex-rs/linux-sandbox/src/bwrap.rs:362-377`, root bind at `:451-463`. Every
invocation carries `--new-session`, `--die-with-parent`, `--unshare-user`,
`--unshare-pid`, `--cap-drop ALL`, and `--unshare-net` unless network is fully
allowed (`codex-rs/linux-sandbox/src/bwrap.rs:267-303`, `:326-353`). Fresh
`/proc` is mounted unless a preflight detects `Can't mount proc` in restricted
containers, in which case the run retries without `--proc`
(`codex-rs/linux-sandbox/src/linux_run_main.rs:394-414`, `:1450-1456`). Full-
disk-write policies skip wrapping entirely unless network isolation or
unreadable globs are needed (`codex-rs/linux-sandbox/src/bwrap.rs:245-256`).

Seccomp network filter (applied to the current thread, only the child inherits
it): always denies `ptrace`, `process_vm_readv`, `process_vm_writev`, and all
three `io_uring_*` syscalls
(`codex-rs/linux-sandbox/src/landlock.rs:179-184`). `Restricted` mode denies
connect/accept/bind/listen/send class calls and allows `socket`/`socketpair`
only for `AF_UNIX` (`recvfrom` is deliberately left open "so cargo clippy runs"
, `:198-216`). `ProxyRouted` mode allows only `AF_INET`/`AF_INET6` sockets
inside the isolated namespace plus `AF_UNIX` socketpair
(`codex-rs/linux-sandbox/src/landlock.rs:218-247`). Filter action is
default-allow with `Errno(EPERM)` on rule match, x86_64/aarch64 only
(`codex-rs/linux-sandbox/src/landlock.rs:250-261`). Managed-network sessions
stay fail-closed even under full-network policies
(`codex-rs/linux-sandbox/src/landlock.rs:96-103`).

bwrap sourcing: system `bwrap` from `PATH` is preferred, excluding any instance
inside the current working directory
(`codex-rs/sandboxing/src/bwrap.rs:168-191`); capability probing runs
`bwrap --help` and requires `--as-pid-1` and `--perms`
(`codex-rs/linux-sandbox/src/launcher.rs:185-205`), with a no-`--argv0` compat
path for old distro builds (`codex-rs/linux-sandbox/README.md:11-14`). Missing
system bwrap falls back to the bundled `codex-resources/bwrap`
(`codex-rs/linux-sandbox/README.md:14-16`); the bundled binary's sha256 is
verified against build-time env `CODEX_BWRAP_SHA256` and mismatch exits with
`BUNDLED_BWRAP_DIGEST_VERIFICATION_FAILURE_EXIT_CODE = 8`
(`codex-rs/linux-sandbox/src/bundled_bwrap.rs:28-46`,
`codex-rs/linux-sandbox/src/lib.rs:27-29`). The bundled `bwrap` crate compiles
vendored bubblewrap C sources (`codex-rs/bwrap/src/main.rs:1-29`, sources
expected at `codex-rs/vendor/bubblewrap` per the fallback panic message at
`codex-rs/bwrap/src/main.rs:33-39`). WSL1 is rejected with a dedicated warning
because it cannot create user namespaces
(`codex-rs/sandboxing/src/bwrap.rs:25-29`,
`codex-rs/sandboxing/src/manager.rs:680-694`).

### Denial detection and the escalation path when a command is denied

There is no deterministic channel from the kernel back to the harness; the
detection is a heuristic. `is_likely_sandbox_denied` returns false for exit 0 or
quick-reject codes `[2, 126, 127]`, true for exit `128 + SIGSYS` under
`LinuxSeccomp`, and true when any of seven keywords ("operation not permitted",
"permission denied", "read-only file system", "seccomp", "sandbox", "landlock",
"failed to write file") appear in stdout/stderr
(`codex-rs/sandboxing/src/denial.rs:13-42`, `:50-58`; same keyword table at
`codex-rs/sandboxing/src/violation.rs:11-31` for the violation taxonomy with
backends `linux_sandbox | managed_network_proxy | seatbelt | windows_sandbox`
at `:47-63`).

On detection, `finalize_exec_result` records a filesystem violation and converts
the output into `CodexErr::Sandbox(SandboxErr::Denied { .. })`
(`codex-rs/core/src/exec.rs:793-799`, cross-component). The tool orchestrator's
documented sequence is "approval → select sandbox → attempt → retry with an
escalated sandbox strategy on denial (no re‑approval thanks to caching)"
(`codex-rs/core/src/tools/orchestrator.rs:1-8`). On `SandboxErr::Denied` it:
bails if the tool opts out (`escalate_on_failure()`)
(`codex-rs/core/src/tools/orchestrator.rs:334`); under `Never` or `OnRequest`
does not retry unsandboxed, except an `OnRequest` network-denial prompt
(`:346-370`); refuses unsandboxed retry entirely when the policy has denied-read
restrictions, since those are enforced only inside the sandbox
(`codex-rs/core/src/tools/sandboxing.rs:269-295`,
`codex-rs/core/src/tools/orchestrator.rs:371-380`); otherwise requests approval
(fresh guardian review under strict auto-review, because a prior auto-approval
covered only the sandboxed attempt, `:391-395`) and retries with
`SandboxType::None` (`:423-439`). A per-command override exists: the tool-arg
`sandbox_permissions` enum `use_default | require_escalated |
with_additional_permissions` (`codex-rs/protocol/src/models.rs:46-79`,
cross-component; tool-schema wording at
`codex-rs/core/src/tools/handlers/shell_spec.rs:305-329`, cross-component),
and `require_escalated` bypasses the sandbox on the first attempt after approval
(`codex-rs/core/src/tools/sandboxing.rs:238-267`).

Interactive escalation is a separate mechanism for approved long-lived shells:
a patched zsh (`EXEC_WRAPPER` support, patch pinned to upstream commit
`77045ef899e53b9598bebc5a41db93a548a40ca6`,
`codex-rs/shell-escalation/README.md:18-29`) routes every `execve(2)` through
`codex-execve-wrapper`, which asks the server over the fd in
`CODEX_ESCALATE_SOCKET` (`codex-rs/shell-escalation/src/unix/escalate_protocol.rs:11`,
`:14`). The server answers `Run` (exec inside the sandboxed shell), `Escalate`
(fds forwarded, command runs outside the sandbox, exit code forwarded back), or
`Deny` (wrapper prints an error and exits `1`)
(`codex-rs/shell-escalation/README.md:6-16`,
`codex-rs/shell-escalation/src/unix/escalate_protocol.rs:37-40`; policy trait at
`codex-rs/shell-escalation/src/unix/escalation_policy.rs:9-16`, concrete
`EscalationPolicy for CoreShellActionProvider` at
`codex-rs/core/src/tools/runtimes/shell/unix_escalation.rs:658`, cross-component).

Network denials flow through the managed proxy: blocked reasons map to stable
strings such as `denied` → "domain is explicitly denied by policy and cannot be
approved from this prompt" and `not_allowed` → "domain is not on the allowlist
for the current sandbox mode"
(`codex-rs/core/src/network_policy_decision.rs:60-67`), and user-approved
network amendments become `network_rule(...)` entries with justification
`Allow https_connect access to <host>`
(`codex-rs/core/src/network_policy_decision.rs:74-102`).

### Guardian auto-review

Guardian routing requires `AskForApproval::{OnRequest, Granular}` and
`approvals_reviewer == ApprovalsReviewer::AutoReview`
(`codex-rs/core/src/guardian/review.rs:193-201`; reviewer enum with default
`user` at `codex-rs/protocol/src/config_types.rs:160-172`, cross-component). The
reviewer gets a truncated transcript (caps include
`GUARDIAN_MAX_MESSAGE_TRANSCRIPT_TOKENS = 10_000`), must return strict JSON
matching `GuardianAssessment { risk_level, user_authorization, outcome,
rationale }`, and the system fails closed "on timeout, execution failure, or
malformed output" with `GUARDIAN_REVIEW_TIMEOUT = 90s` and at most
`GUARDIAN_REVIEW_MAX_ATTEMPTS = 3` attempts
(`codex-rs/core/src/guardian/mod.rs:53-68`,
`codex-rs/core/src/guardian/review.rs:72`, `:104-106`, `:305-306`). The bundled
policy is a risk taxonomy (`codex-rs/core/src/guardian/policy.md`) whose default
rule allows `low`/`medium` risk "regardless of user authorization" except for
explicit policy denies or clear prompt-injection signs
(`codex-rs/core/src/guardian/policy_template.md:73`). A circuit breaker
interrupts a turn after `MAX_CONSECUTIVE_GUARDIAN_DENIALS_PER_TURN = 3`
consecutive denials or `MAX_RECENT_AUTO_REVIEW_DENIALS_PER_TURN = 10` in the
last 50 reviews (1/1 for cyber models)
(`codex-rs/core/src/guardian/mod.rs:55-59`, `:152-202`,
`codex-rs/core/src/guardian/review.rs:243-293`). Denial responses instruct the
agent that it "must not attempt to achieve the same outcome via workaround,
indirect execution, or policy circumvention"
(`codex-rs/core/src/guardian/review.rs:58-64`). User override of a guardian
denial exists as op input `ApproveGuardianDeniedAction`
(`codex-rs/protocol/src/protocol.rs:891`, cross-component).

### Process hardening

`pre_main_hardening()` runs via `#[ctor::ctor]` and, per platform: Linux sets
`prctl(PR_SET_DUMPABLE, 0)` (exit code 5 on failure), zeroes `RLIMIT_CORE`
(exit 7), and removes all `LD_*` env vars (noted as redundant for MUSL release
builds); macOS calls `ptrace(PT_DENY_ATTACH)` (exit 6), zeroes `RLIMIT_CORE`,
and removes all `DYLD_*` vars; Windows is a no-op TODO
(`codex-rs/process-hardening/src/lib.rs:12-131`). At the pinned commit the only
in-tree call sites are the responses-api-proxy binary
(`codex-rs/responses-api-proxy/src/main.rs:4-6`) and
`disable_process_dumping()` used by the Linux sandbox proxy lifecycle
(`codex-rs/linux-sandbox/src/proxy_lifecycle.rs:124`).

## Key facts with anchors

- Three OS backends are selected statically by host OS: seatbelt on macOS, the
  `codex-linux-sandbox` helper (bubblewrap + seccomp) on Linux, and optional
  restricted-token sandboxing on Windows
  (`codex-rs/sandboxing/src/manager.rs:62-76`).
- The macOS wrapper path is hard-coded to `/usr/bin/sandbox-exec` as an
  anti-PATH-injection measure (`codex-rs/sandboxing/src/seatbelt.rs:35-39`), and
  every generated seatbelt policy starts with `(deny default)`
  (`codex-rs/sandboxing/src/seatbelt_base_policy.sbpl:8`).
- On Linux, bubblewrap is the default filesystem sandbox and Landlock is only a
  legacy fallback; the bubblewrap path explicitly never falls back to Landlock
  on failure (`codex-rs/linux-sandbox/README.md:26-48`,
  `codex-rs/linux-sandbox/src/linux_run_main.rs:287-290`).
- Every bubblewrap invocation unshares user and PID namespaces and drops all
  capabilities (`--unshare-user`, `--unshare-pid`, `--cap-drop ALL`), and adds
  `--unshare-net` whenever network is not fully allowed
  (`codex-rs/linux-sandbox/src/bwrap.rs:267-303`, `:326-353`, `:100-104`).
- Even inside the sandbox, seccomp denies `ptrace`, `process_vm_readv`,
  `process_vm_writev`, and `io_uring_*` unconditionally
  (`codex-rs/linux-sandbox/src/landlock.rs:179-184`).
- execpolicy decisions are `allow | prompt | forbidden`, aggregated to the
  strictest match; unmatched commands fall through to approval-policy-aware
  heuristics (`codex-rs/execpolicy/src/decision.rs:9-26`,
  `codex-rs/execpolicy/src/policy.rs:402-411`,
  `codex-rs/core/src/exec_policy.rs:740-841`).
- Under `approval_policy = "never"`, unmatched non-dangerous commands are
  allowed "relying on the sandbox for protection"
  (`codex-rs/core/src/exec_policy.rs:796-800`): the trust model swaps approval
  for mandatory sandboxing.
- Approved commands can be persisted as `prefix_rule(..., decision="allow")`
  appended to `$CODEX_HOME/rules/default.rules`
  (`codex-rs/execpolicy/src/amend.rs:65-79`,
  `codex-rs/core/src/exec_policy.rs:853-855`); a hard-coded
  `BANNED_PREFIX_SUGGESTIONS` list (shells, interpreters, `rm`, `sudo`, `git`,
  `env`) is never offered as a reusable prefix amendment
  (`codex-rs/core/src/exec_policy.rs:58-147`).
- Sandbox denial is detected heuristically from exit codes and seven output
  keywords (`codex-rs/sandboxing/src/denial.rs:13-58`), then drives a
  single retry outside the sandbox after (re-)approval
  (`codex-rs/core/src/tools/orchestrator.rs:299-439`).
- Escalation to unsandboxed execution is blocked when the policy has any
  denied-read rules, because deny-reads are enforced only inside the sandbox
  (`codex-rs/core/src/tools/sandboxing.rs:269-295`).
- `.git`, `.agents`, `.codex` are the protected workspacemetadata names kept
  read-only inside writable roots on every backend
  (`codex-rs/protocol/src/permissions.rs:24-33`; seatbelt enforcement at
  `codex-rs/sandboxing/src/seatbelt.rs:389-404`, bwrap enforcement at
  `codex-rs/linux-sandbox/src/bwrap.rs:666-694`).
- The bundled bubblewrap binary is digest-verified against a build-time sha256;
  mismatch exits with code 8
  (`codex-rs/linux-sandbox/src/bundled_bwrap.rs:28-46`,
  `codex-rs/linux-sandbox/src/lib.rs:27-29`).
- Guardian auto-review fails closed on timeout/failure/malformed output with a
  90s timeout and 3 attempts, and a denial circuit breaker interrupts abusive
  turns (`codex-rs/core/src/guardian/mod.rs:53-68`,
  `codex-rs/core/src/guardian/review.rs:72`, `:305-306`, `:243-293`).

## Configuration and defaults

- `approval_policy` config key (`codex-rs/config/src/config_toml.rs:173`) maps
  to `AskForApproval`; code default is `OnRequest`
  (`codex-rs/protocol/src/protocol.rs:926-927`). `approvals_reviewer` defaults
  to `user` (`codex-rs/protocol/src/config_types.rs:165-168`).
- `sandbox_mode` (`codex-rs/config/src/config_toml.rs:198`) takes `read-only |
  workspace-write | danger-full-access` with enum default `ReadOnly`
  (`codex-rs/protocol/src/config_types.rs:86-96`). When unset, a directory with
  a trust decision defaults to `workspace-write`, except unsandboxed Windows
  which defaults to `read-only`; without a trust decision the enum default
  `read-only` applies (`codex-rs/config/src/config_toml.rs:736-763`).
  `danger-full-access` maps to `PermissionProfile::Disabled`
  (`codex-rs/config/src/config_toml.rs:788`).
- `[sandbox_workspace_write]` subkeys: `writable_roots`, `network_access`,
  `exclude_tmpdir_env_var`, `exclude_slash_tmp`
  (`codex-rs/protocol/src/protocol.rs:1029-1050`,
  `codex-rs/config/src/config_toml.rs:767-787`).
- `features.use_legacy_landlock = true` (or CLI `-c use_legacy_landlock=true`)
  forces the legacy Landlock path; it is used only when the split policy is
  sandbox-equivalent to the legacy model after cwd resolution
  (`codex-rs/linux-sandbox/README.md:42-48`).
- Windows: `WindowsSandboxLevel::{Disabled (default), RestrictedToken,
  Elevated}` (`codex-rs/protocol/src/config_types.rs:279-284`); resolved from
  config `windows.sandbox` (`elevated | unelevated`) or feature flags
  `WindowsSandboxElevated`/`WindowsSandbox`
  (`codex-rs/core/src/windows_sandbox.rs:24-43`);
  `sandbox_private_desktop` defaults to `true`
  (`codex-rs/core/src/windows_sandbox.rs:52-57`). Managed networking requires
  the elevated backend (`codex-rs/sandboxing/src/manager.rs:424-430`).
- Execpolicy files: `rules/*.rules` directory per config layer
  (`codex-rs/core/src/exec_policy.rs:650-671`); amendments persist to
  `$CODEX_HOME/rules/default.rules`
  (`codex-rs/core/src/exec_policy.rs:853-855`). Per-profile glob scan cap:
  `[permissions.workspace.filesystem] glob_scan_max_depth`
  (`codex-rs/linux-sandbox/README.md:71-79`); internal match cap
  `MAX_UNREADABLE_GLOB_MATCHES = 8192`
  (`codex-rs/linux-sandbox/src/bwrap.rs:56`).
- Environment variables the harness itself uses: `CODEX_SANDBOX=seatbelt` is
  injected for seatbelt-sandboxed processes and
  `CODEX_SANDBOX_NETWORK_DISABLED=1` when the network policy is restricted
  (`codex-rs/core/src/spawn.rs:21-26`,
  `codex-rs/core/src/sandboxing/mod.rs:169-179`); `CODEX_ESCALATE_SOCKET`
  carries the escalation socket fd and `EXEC_WRAPPER` names the wrapper in
  escalated shells (`codex-rs/shell-escalation/src/unix/escalate_protocol.rs:11-14`).
- Managed requirements (enterprise layers) can constrain
  `allowed_sandbox_modes` and `allowed_approval_policies`
  (`codex-rs/config/src/config_requirements.rs:935`, `:1646-1661`,
  cross-component); a disallowed default sandbox mode warns and "fall[s] back
  to required default" read-only
  (`codex-rs/config/src/config_toml.rs:790-798`).
- `codex-rs/config/defaults.toml` (packaged client defaults) contains no
  sandbox or approval keys (`codex-rs/config/defaults.toml:1-17`), so those
  defaults come from the code defaults above.

## Limitations and unknowns

- Denial detection is admittedly heuristic: the code comment says "We don't have
  a fully deterministic way to tell if our command failed because of the
  sandbox" (`codex-rs/sandboxing/src/denial.rs:5-9`). Keyword matching on
  command output can both false-positive (a command printing "permission
  denied") and false-miss (silent EPERM handling), which directly affects
  whether the escalation retry fires.
- Process hardening wiring at the pinned commit: `pre_main_hardening` is called
  only from `codex-rs/responses-api-proxy/src/main.rs` in-tree
  (`codex-rs/responses-api-proxy/src/main.rs:4-6`); I found no `#[ctor::ctor]`
  call in the CLI binaries. Whether release packaging applies it to the main
  `codex` binary is not verifiable from this checkout. [EVIDENCE NEEDED]
  Searched: grep for `pre_main_hardening` and `ctor::ctor` across `codex-rs/`.
- Windows backend internals (`codex-rs/windows-sandbox-rs/src/`) were surveyed
  at crate level only (setup orchestration in
  `codex-rs/core/src/windows_sandbox.rs`); restricted-token mechanics,
  private-desktop implementation, and the elevated helper are not described
  here beyond their call surface.
- `docs/linux_sandbox.md` is referenced by
  `codex-rs/sandboxing/src/landlock.rs:21` but does not exist in the pinned
  tree (searched `docs/` and `codex-rs/docs/`). `docs/sandbox.md` at the pinned
  commit is a one-line redirect to `developers.openai.com/codex/security`
  (`docs/sandbox.md:1-3`), so the authoritative prose docs live outside this
  checkout (registry entry codexDocsSandboxing).
- Which model serves guardian auto-review is config/provider state outside this
  component; routing conditions are visible but the reviewer selection pipeline
  (`review_session.rs`) was not characterized here.
- Static reading only: no sandbox was exercised, so runtime behavior (e.g.
  actual seatbelt rule effectiveness on current macOS, bwrap behavior inside
  nested containers beyond the `/proc` preflight) is claimed only as
  code-stated intent.
- Gate flag for the literature gate (study.yaml `depth: full`): no blocking
  source-level gaps found for this component. The open items above are
  within-component unknowns, not blockers; the Windows deep-dive and the
  docs-site page are separate registered sources.

## Relevance to the brief

Inference, separated from the code facts above.

- RQ3 (capability vs safety trade in shell/file access): Codex answers with a
  layered, mutually reinforcing stack rather than one mechanism: declarative
  permission profiles, OS-kernel enforcement (seatbelt/landlock/seccomp/bwrap),
  a rule engine with a trusted-command safelist, approval prompts, optional
  model auto-review, and post-hoc denial-driven escalation. The striking design
  point is the `Never` approval mode's contract: it does not mean "anything
  goes", it means the sandbox bears the full protection burden
  (`codex-rs/core/src/exec_policy.rs:796-800`). Equally notable is the fail-
  closed bias: proxy-network inference failures deny network
  (`codex-rs/sandboxing/src/seatbelt.rs:321-331`), guardian failures deny the
  action (`codex-rs/core/src/guardian/mod.rs:11`), and deny-read policies
  structurally forbid unsandboxed retries
  (`codex-rs/core/src/tools/sandboxing.rs:269-295`).
- RQ1/RQ2 (harness component inventory): this note covers the "permissions"
  dimension for Codex and parts of "tools" (exec approval requirements) and
  "extensibility boundary" (user-authored `.rules` files as the policy
  extension point, persisted amendments as learned policy). The two escalation
  mechanisms (denial retry, zsh execve interception) are the closest analog to
  Claude Code's hooks/permission prompts and OpenCode's permission rulesets and
  belong in the `_synthesis.md` comparison matrix.
- Left open: the Claude Code and OpenCode side of the comparison (other
  registered components), the docs-site claims about sandboxing (codexDocsSandboxing),
  and how `unified_exec` session processes inherit these protections
  (`codex-rs/core/src/unified_exec/`, sibling component) beyond the shared
  `is_likely_sandbox_denied` call sites observed here.

## Quotables for the report

- Default-deny seatbelt base: `(deny default)` followed by `(allow
  process-exec)` / `(allow process-fork)` so children inherit the policy
  (`codex-rs/sandboxing/src/seatbelt_base_policy.sbpl:8-13`). Framing: Codex's
  macOS sandbox is a generated per-command SBPL policy over a closed default.
- Hardened wrapper path: `pub const MACOS_PATH_TO_SEATBELT_EXECUTABLE: &str =
  "/usr/bin/sandbox-exec";` with the comment about PATH injection
  (`codex-rs/sandboxing/src/seatbelt.rs:35-39`).
- The sandbox-for-approval swap under `never`: "We allow the command to run,
  relying on the sandbox for protection."
  (`codex-rs/core/src/exec_policy.rs:796-800`). Framing: capability is granted
  precisely when kernel enforcement is active.
- Strictest-decision aggregation: "The effective `decision` is the strictest
  severity across all matches (`forbidden` > `prompt` > `allow`)."
  (`codex-rs/execpolicy/README.md:95`).
- Two-stage Linux pipeline: "1. When needed, wrap the command with bubblewrap to
  construct the filesystem view. 2. Apply in-process restrictions
  (no_new_privs + seccomp). 3. `execvp` into the final command."
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:149-155`).
- Capability paranoia inside the sandbox: `panic!("Linux sandbox retained
  effective or permitted capabilities")` after a `SYS_capget` check
  (`codex-rs/linux-sandbox/src/linux_run_main.rs:196-218`).
- Escalation protocol vocabulary: `EscalationDecision::{Run, Escalate, Deny}`
  over `CODEX_ESCALATE_SOCKET`
  (`codex-rs/shell-escalation/src/unix/escalate_protocol.rs:11`, `:37-40`;
  `codex-rs/shell-escalation/README.md:6-16`). Framing: interception happens at
  the `execve` boundary inside an approved interactive shell, not per tool call.
- Guardian fail-closed stance: "Fail closed on timeout, execution failure, or
  malformed output." (`codex-rs/core/src/guardian/mod.rs:11`) with
  `GUARDIAN_REVIEW_TIMEOUT: Duration = Duration::from_secs(90)` (`:53`).
- Denial heuristic keyword table (`codex-rs/sandboxing/src/denial.rs:50-58`).
  Framing: absence of a deterministic denial channel from the kernel forces a
  keyword heuristic, which is the seam where Codex's safety story meets
  pragmatic UX.
