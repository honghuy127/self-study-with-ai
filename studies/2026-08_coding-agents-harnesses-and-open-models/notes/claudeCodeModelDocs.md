---
source_key: claudeCodeModelDocs
read_date: 2026-08-20
confidence: high
relevance: 3
---

# Notes: Claude Code docs: model configuration

Anchor convention: every `(Lnnn)` anchor is a line number in the evidence
snapshot `sources/docs/claudeCodeModelConfig.md` (825 lines), a fetch of
`https://code.claude.com/docs/en/model-config` saved at gathering time on
2026-08-20. Quotes are character-exact from that snapshot.

## Source identification

- Key: `claudeCodeModelDocs`
- Authors, year, venue: Anthropic, 2026, `code.claude.com/docs`
- Tier: docs
- URL / DOI: https://code.claude.com/docs/en/model-config (evidence: local
  snapshot `sources/docs/claudeCodeModelConfig.md`)

Source establishes: this is the official "Model configuration" page of the
Claude Code documentation. Its stated scope is to "Configure which model
Claude Code uses, effort levels, extended context, and the auto-compact
window" (L7). The page opens with a documentation-index banner pointing to
`https://code.claude.com/docs/llms.txt` (L1-L3).

## Problem and motivation

Source establishes: the page documents the user-facing mechanisms for model
selection in Claude Code. It states that the `model` setting accepts either
"A **model alias**" or "A **model name**", where a model name is, per
provider: "Anthropic API: a full **model name**", "Amazon Bedrock: an
inference profile ARN", "Microsoft Foundry: a deployment name", "Google
Cloud's Agent Platform: a version name" (L11-L18). The motivation it gives
for aliases is to "select model settings without remembering exact version
numbers" (L28).

The page is heavily version-gated: it contains many "Before v2.1.x" and
"Requires Claude Code v2.1.x or later" notes, the newest being
"Requires Claude Code v2.1.236 or later" for `ANTHROPIC_DEFAULT_MODEL`
(L160) and "Requires Claude Code v2.1.234 or later" for Remote Control
effort controls (L545), so the snapshot describes behavior at or after
v2.1.236. The snapshot itself carries no version stamp or fetch date beyond
what the registry records (interpretation).

## Method or core idea

Source establishes: the page defines a complete configuration surface made of
four kinds of knobs: an in-session command, a launch flag, environment
variables, and settings-file keys, with an explicit priority order.

Model selection, listed "in order of priority" (L95):

1. "**During session**: use `/model <alias|name>` to switch immediately, or
   run `/model` with no argument to open the picker" (L97)
2. "**At startup**: launch with `claude --model <alias|name>`" (L98)
3. "**Environment variable**: set `ANTHROPIC_MODEL=<alias|name>`" (L99)
4. "**Settings**: configure permanently in your settings file using the
   `model` field" (L100)
5. "**Default for new sessions**: set `ANTHROPIC_DEFAULT_MODEL=<alias|name>`"
   (L101)

Scope of the transient knobs: "The `--model` flag and `ANTHROPIC_MODEL`
environment variable apply only to the session you launch with them" (L112).
`ANTHROPIC_DEFAULT_MODEL` "Requires Claude Code v2.1.236 or later" and is
used "only when none of these selects a model: * The `--model` flag *
`ANTHROPIC_MODEL` * A `model` value in any settings file ... * An
organization default model" (L160-L168). It is ignored when "set to
`default`, `inherit`, `opusplan`, or `haiku`" (L175).

Model aliases (L30-L40), quoted: `default` ("clears any model override and
reverts to the runtime default for your account", "Not itself a model
alias"), `best` ("Uses Fable 5 where your organization has access to it,
otherwise the latest Opus model"), `fable`, `sonnet`, `opus`, `haiku`,
`sonnet[1m]`, `opus[1m]`, `opusplan` ("uses `opus` during plan mode, then
switches to `sonnet` for execution"). Alias-to-version resolution differs by
provider (L44-L49): Anthropic API `Opus 5` / `Sonnet 5`; Claude Platform on
AWS `Opus 5` / `Sonnet 4.6`; Amazon Bedrock and Google Cloud's Agent
Platform `Opus 5` / `Sonnet 4.5`; Microsoft Foundry `Opus 4.6` /
`Sonnet 4.5`.

The `default` alias resolves by account type (L364-L369): "Max, Team
Premium, Enterprise pay-as-you-go, and Anthropic API: defaults to Opus 5";
"Claude Platform on AWS, Amazon Bedrock, and Google Cloud's Agent Platform:
defaults to Opus 5"; "Pro, Team Standard, and Enterprise subscription seats:
defaults to Sonnet 5"; "Microsoft Foundry: defaults to Sonnet 4.5". "Fable 5
is not the default model on any account type" (L379).

Alias-pinning environment variables (table at L694-L700):
`ANTHROPIC_DEFAULT_FABLE_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`,
`ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, and
`CLAUDE_CODE_SUBAGENT_MODEL` (model "for all subagents, agent teams, and
agents in a workflow"; "Set to `inherit` to use normal model resolution
instead"). Plus: "Note: `ANTHROPIC_SMALL_FAST_MODEL` is deprecated in favor
of `ANTHROPIC_DEFAULT_HAIKU_MODEL`" (L702-L703).

Settings keys documented on the page: `model` (L100, example `"model":
"opus"` at L154), `fallbackModel` array (L410-L415), `availableModels`
(L184, example `["sonnet", "haiku"]` at L222-L225),
`enforceAvailableModels` (L252-L258), `modelOverrides` map (L789-L799),
`autoCompactWindow` (L631), `effortLevel` (L544), `alwaysThinkingEnabled`
(L569), `switchModelsOnFlag` (L452), `advisorModel` (L195),
`showThinkingSummaries` (L574), `ultracode` (L509).

Base URL and custom options: "`ANTHROPIC_BASE_URL` changes where requests
are sent, not which model answers them" (L23). `ANTHROPIC_CUSTOM_MODEL_OPTION`
adds "a single custom entry to the `/model` picker without replacing the
built-in aliases. This is useful for testing model IDs that Claude Code does
not list by default" (L670-L672), with optional
`ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` and
`ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION` (L677-L682); "Claude Code skips
validation for the model ID set in `ANTHROPIC_CUSTOM_MODEL_OPTION`, so you
can use any string your API endpoint accepts" (L684). For gateway
deployments, "Claude Code can populate the picker from the gateway's
`/v1/models` endpoint when `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`
is set" (L672).

Model-ID validation: on the Anthropic API, Claude Code "recognizes" "a model
alias", "an entry from the `/model` picker", "any name that starts with
`claude-`", and "a value you configured yourself as a custom model option or
in `modelOverrides`" (L122-L127); it "rejects an unrecognized string with
`Model \"<name>\" is not a recognized model id.`" (L129). "The check runs
only on the Anthropic API. On Amazon Bedrock, Google Cloud's Agent Platform,
Microsoft Foundry, Claude Platform on AWS, and behind an LLM gateway or a
custom `ANTHROPIC_BASE_URL`, your provider or gateway defines the model
names, so Claude Code passes any string through without checking it" (L131).

## Key claims with anchors

All items below are source claims unless labeled interpretation.

Negative-scope finding (verified absence, my verification method stated in
Limitations): the snapshot contains no mention of non-Anthropic models,
open-weight models, Ollama, LM Studio, vLLM, LiteLLM, or OpenAI-compatible
endpoints. Every provider named on the page is an Anthropic-model host or a
relay for one: Anthropic API, Amazon Bedrock, Google Cloud's Agent Platform
(the Vertex pathway, linked as `/docs/en/google-vertex-ai` at L464 and L707),
Microsoft Foundry, Claude Platform on AWS, the Amazon Bedrock Mantle endpoint
(L301, L807), the Claude apps gateway (L114), and generic "LLM gateway"
references (e.g., L23, L620, L655). Checked sections: title and subtitle
(L5-L7), Available models (L9-L24), Model aliases (L26-L59), Work with Fable
5 (L61-L91), Setting your model (L93-L180), Restrict model selection
(L182-L322), Organization default model (L324-L352), Organization effort
limits (L354-L358), Special model behavior (L360-L560), Extended thinking
(L562-L574), Extended context (L576-L621), Context window and
auto-compaction (L623-L661), Checking your current model (L663-L668), Add a
custom model option (L670-L688), Environment variables including Pin models
for third-party deployments, Customize pinned model display and
capabilities, Override model IDs per version, and Prompt caching
configuration (L690-L825).

Third-party-host pathways referenced (source claims):

- Pinning variables with provider examples (L719-L723): Amazon Bedrock
  `export ANTHROPIC_DEFAULT_OPUS_MODEL='us.anthropic.claude-opus-4-8'`;
  Google Cloud's Agent Platform
  `export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-8'`; Microsoft Foundry
  `export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-opus-4-8'`. Bedrock also
  takes full ARNs, e.g.
  `arn:aws:bedrock:us-east-1:123456789012:custom-model/abc` (L773) and
  inference-profile ARNs in `modelOverrides` (L794-L796). Models reachable
  through these pins are Claude models only: the page's examples and
  resolution tables name Fable 5, Opus 5/4.8/4.7/4.6, Sonnet 5/4.6/4.5, and
  Haiku (L44-L49, L53, L364-L369, L485-L487).
- Unpinned behavior: "Without pinning, Claude Code uses model aliases such
  as `fable`, `opus`, `sonnet`, and `haiku` that resolve to a built-in
  default model ID for each provider", with Bedrock and Agent Platform
  falling back to earlier versions and Foundry showing errors (L709).
- Companion display/capability variables per pinned family
  (L749-L755): `ANTHROPIC_DEFAULT_OPUS_MODEL_NAME`,
  `ANTHROPIC_DEFAULT_OPUS_MODEL_DESCRIPTION`,
  `ANTHROPIC_DEFAULT_OPUS_MODEL_SUPPORTED_CAPABILITIES`, with the same
  `_NAME`, `_DESCRIPTION`, `_SUPPORTED_CAPABILITIES` suffixes for the Sonnet,
  Haiku, Fable, and custom-option variables. These "take effect on
  third-party providers such as Amazon Bedrock, Google Cloud's Agent
  Platform, and Microsoft Foundry"; `_NAME` and `_DESCRIPTION` also apply
  behind `ANTHROPIC_BASE_URL` gateways; "They have no effect when connecting
  directly to `api.anthropic.com`" (L747).
- `modelOverrides` "maps individual Anthropic model IDs to the
  provider-specific strings that Claude Code sends to your provider's API"
  (L785), keys "must be Anthropic model IDs" (L801).

Context windows, reasoning effort, capability settings (source claims):

- Effort levels: per-model support table (L483-L488): Fable 5 and "Opus 5,
  Sonnet 5, Opus 4.8, and Opus 4.7" take "`low`, `medium`, `high`, `xhigh`,
  `max`"; "Opus 4.6 and Sonnet 4.6" take "`low`, `medium`, `high`, `max`".
  "The default effort is `high` on every model that supports effort, except
  Opus 4.7, which defaults to `xhigh`" (L491). Setting an unsupported level
  falls back: "`xhigh` runs as `high` on Opus 4.6" (L489). Controls:
  `/effort`, the effort slider inside `/model`, `--effort` flag,
  `CLAUDE_CODE_EFFORT_LEVEL` ("The environment variable takes precedence over
  all other methods", L548), settings key `effortLevel` ("`max` and
  `ultracode` are session-only and are not accepted here", L544), and
  skill/subagent frontmatter `effort` (L538-L546). `ultracode` "is a Claude
  Code setting rather than a model effort level: it sends `xhigh` to the
  model and additionally has Claude orchestrate dynamic workflows" (L503).
  "Include `ultrathink` anywhere in your prompt to request deeper reasoning
  on that turn without changing your session effort setting" (L534).
  Organization admins can cap effort per model per role (L354-L356).
- Extended thinking: session toggle `Option+T` / `Alt+T`, global default
  saved "as `alwaysThinkingEnabled` in `~/.claude/settings.json`", and
  "`MAX_THINKING_TOKENS=0`, which turns thinking off on the Anthropic API
  except on Fable 5. On third-party providers this omits the `thinking`
  parameter instead, and adaptive-reasoning models may still think"
  (L566-L570). "Thinking cannot be turned off on Fable 5" (L572). Fixed
  budget mode: "On Opus 4.6 and Sonnet 4.6, you can set
  `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` to revert to the previous fixed
  thinking budget controlled by `MAX_THINKING_TOKENS`" (L560).
- Extended context: "Fable 5, Sonnet 5, Opus 4.6 and later, and Sonnet 4.6
  support a 1 million token context window" (L578); "On the Anthropic API,
  Fable 5, Sonnet 5, and Opus 4.7 and later always run with the 1M window"
  (L580). Kill switch: "To turn off 1M context, set
  `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`", which also "treats the model as
  having a 200K context window" for native-1M models (L592). Third-party
  providers: "Sonnet 4.6 and Opus 4.6 without extended context compact at
  the 200K boundary, and so do Opus 4.8 and Opus 5 when they run with a 200K
  context window, such as on Amazon Bedrock, Google Cloud's Agent Platform,
  and Microsoft Foundry" (L648); on those providers "Sonnet 5 always runs
  with the 1M window ... and never needs the suffix" (L737).
- Auto-compact window: three set points, `/autocompact` (saved as
  `autoCompactWindow`), `--autocompact`, and
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW` which "takes precedence over the command,
  the flag, and the setting" (L629-L633). "The command and the flag accept a
  window size from 100K to 1M tokens" in plain-count, `k`/`M`, or
  bare-100-to-1000 forms; "The environment variable accepts only the plain
  token count. Claude Code caps the window at the model's context window"
  (L635-L641). Default compaction is "when the conversation reaches the
  model's context limit" with listed exceptions (L645-L651), including:
  "Sonnet 5 ... Sessions auto-compact before the window fills, at about 967K
  tokens by default" on the Anthropic API (L616).
- Context-window correction for non-standard IDs: "On an LLM gateway or
  other custom deployment, Claude Code can assume a context window for the
  model ID that differs from the model's real window" (L655).
  `CLAUDE_CODE_MAX_CONTEXT_TOKENS` declares the assumed window; "If the ID
  doesn't start with `claude-` or contain `[1m]`, in any casing, and Claude
  Code can't resolve it to a Claude model, the variable applies directly and
  proactive compaction continues at the declared window" (L657). IDs
  starting with `claude-` need `DISABLE_COMPACT` set for the variable to
  take effect (L659). Separately,
  "`CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1`" makes Claude
  Code "compact only after the API rejects the conversation with a too-long
  error Claude Code recognizes"; this recovery fails "when a gateway rewrites
  the error to wording Claude Code doesn't recognize" (L661).
- Capability gating: "Claude Code enables features like effort levels and
  extended thinking by matching the model ID against known patterns.
  Provider-specific IDs such as Amazon Bedrock ARNs or custom deployment
  names often don't match these patterns, leaving supported features
  disabled" (L757). `_SUPPORTED_CAPABILITIES` declares them, with values
  `effort`, `xhigh_effort`, `max_effort`, `thinking`, `adaptive_thinking`,
  `interleaved_thinking` (L759-L766); "When the variable is unset, Claude
  Code falls back to built-in detection based on the model ID" (L768).
- Fallbacks: `--fallback-model` flag and `fallbackModel` setting
  (L404-L418); "Claude Code caps chains at three models after duplicate
  removal and ignores extra entries" (L402); compaction-relevant rule: it
  "won't fall back to a model with a smaller context window than the
  primary's" (L425). Content-based automatic fallback exists only "from
  Fable 5 and Opus 5" safety classifiers (L429-L434), with third-party
  deployment resolution rules (L462-L469).
- Prompt caching toggles: `DISABLE_PROMPT_CACHING` (all models) plus
  `DISABLE_PROMPT_CACHING_HAIKU`, `_SONNET`, `_OPUS`, `_FABLE`
  (L817-L823).

Interpretation of source framing (the doc's own, not independently
verifiable here): the page repeatedly frames `ANTHROPIC_BASE_URL`, LLM
gateways, and custom model options as ways to route to Claude deployments
that Claude Code does not list by default (L23, L590, L620, L655, L672),
never as ways to run non-Claude models.

## Evaluation and evidence

Not applicable in the experimental sense: this is a documentation page with
no datasets, metrics, or baselines. The numeric values it carries, copied
character-exact: default auto-compact for Sonnet 5 on the Anthropic API "at
about 967K tokens by default" (L616); `/autocompact` and `--autocompact`
accept "a window size from 100K to 1M tokens" (L635); fallback chains are
capped "at three models after duplicate removal" (L402); organization model
restriction changes "take effect on new requests within about a minute"
(L320). Version gates cited verbatim above (v2.1.153, v2.1.154, v2.1.170,
v2.1.175, v2.1.187, v2.1.195, v2.1.196, v2.1.197, v2.1.200, v2.1.205,
v2.1.219, v2.1.229, v2.1.234, v2.1.236; L53-L58, L75, L103, L160, L252,
L305, L326, L356, L440, L493, L545, L597).

Locatable-value checks: every quoted value was located in the snapshot. One
gap: the wire protocol Claude Code speaks behind `ANTHROPIC_BASE_URL` or an
LLM gateway (whether it is the Anthropic Messages shape or anything else) is
not stated on this page. I searched the full 825-line snapshot for
"chat completions", "responses", "wire", "API shape", and "Messages";
zero hits. `[CITATION NEEDED]`, looked in the entire snapshot.

## Limitations

- The snapshot is a single fetched page. It carries no fetch timestamp or
  Claude Code version header of its own, so claims rest on the registry's
  recorded fetch date (2026-08-20) and on the page's internal version notes,
  which document changes through v2.1.236 (L160). Drift between this snapshot
  and the live page is not assessed.
- Documentation is a claim about behavior, not behavior. The brief already
  records that Claude Code's loader is closed; nothing on this page can be
  checked against code for this source.
- Silence is not impossibility. The absence of Ollama, LM Studio, or
  OpenAI-compatible wording is an absence on this page. The page links out
  to `/docs/en/llm-gateway`, `/docs/en/amazon-bedrock`, `/docs/en/env-vars`,
  `/docs/en/settings`, and `/docs/en/third-party-integrations` (L23, L114,
  L462-L464, L747), which are not part of this snapshot and could differ.
  The Amazon Bedrock page is snapshotted separately in this study
  (`claudeCodeBedrockDocs`); the others are not.
- Several behaviors depend on account state or server responses that a
  static reader cannot verify, e.g. Fable 5 picker availability "only after
  the server reports it available for your organization" (L78) and plan-based
  1M access checks (L590).
- The doc's model family names and version lineup (Fable 5, Opus 5, Sonnet 5,
  Opus 4.8, etc.) are taken at face value; this note does not corroborate
  them against any model-card or API source.

## Relevance to the brief

My inferences, separated from source claims.

- RQ1, Claude Code column: this page is the documentation-attested evidence
  that Claude Code's official configuration surface has no Ollama, LM Studio,
  or generic OpenAI-compatible pathway. The only named third-party hosts are
  Anthropic-model clouds (Bedrock, Agent Platform, Foundry, Claude Platform
  on AWS) plus LLM gateways and `ANTHROPIC_BASE_URL` redirections that the
  page defines as routing, not model-swapping (L23). I infer the Claude Code
  cells for Ollama/LM Studio/generic-endpoint in the compatibility matrix
  should read "not documented" (documentation-negative), with any positive
  story coming only from out-of-scope community routers, exactly as the
  brief's scope anticipates.
- RQ2, minimum contract: the page documents the contract Claude Code applies
  to unrecognized model IDs rather than to unknown wire formats.
  `CLAUDE_CODE_MAX_CONTEXT_TOKENS` (applied "directly" for IDs that neither
  start with `claude-` nor contain `[1m]` nor resolve to a Claude model,
  L657) and `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1`
  (error-triggered compaction, fragile if a gateway "rewrites the error",
  L661) tell us what a gateway or server must preserve for context accounting
  and compaction recovery. I infer context-window reporting and too-long
  error wording belong in the minimum contract for Claude Code, while wire
  API shape is unattested from this source.
- RQ3, degradation points: capability gating is explicitly ID-pattern-based
  (L757), with a manual override (`_SUPPORTED_CAPABILITIES`, L759-L766) that
  only attaches to the pinned `ANTHROPIC_DEFAULT_*_MODEL` families and the
  custom-option variable (L755), not to arbitrary session models. Effort
  fallback (L489), 200K compaction boundaries on third-party providers
  (L648), assumed windows for unrecognized IDs (L651, L655), and the
  pass-through-without-validation on non-Anthropic-API paths (L131) are the
  concrete degradation surfaces I expect open models to hit. I infer
  "features disabled until capabilities are declared" is Claude Code's
  open-model degradation signature, the analogue of OpenCode's ID gating but
  documented at the configuration level only.
- Left open by this source: whether `ANTHROPIC_BASE_URL` plus
  `ANTHROPIC_CUSTOM_MODEL_OPTION` can in practice carry a non-Claude model
  end-to-end; what request shape is sent to a gateway; and whether the
  `/v1/models` discovery endpoint (L672) implies `/v1/models` is otherwise
  called. These need the LLM-gateway docs page, which this study did not
  snapshot, or the pinned `claude-code` checkout surface traces.

## Quotables for the report

- "`ANTHROPIC_BASE_URL` changes where requests are sent, not which model
  answers them." (L23). Framing: the official escape hatch is documented as
  transport redirection for Claude models, not as a model-provider switch.
- "your provider or gateway defines the model names, so Claude Code passes
  any string through without checking it" (L131). Framing: outside the
  Anthropic API, Claude Code performs no model-ID validation, so failure
  modes move to request time.
- "Claude Code skips validation for the model ID set in
  `ANTHROPIC_CUSTOM_MODEL_OPTION`, so you can use any string your API
  endpoint accepts." (L684). Framing: the closest documented surface to an
  arbitrary model ID, positioned by the docs as testing unlisted Claude IDs.
- "Claude Code enables features like effort levels and extended thinking by
  matching the model ID against known patterns." (L757). Framing:
  model-ID-gated capability detection is documented behavior, with
  `_SUPPORTED_CAPABILITIES` (values `effort`, `xhigh_effort`, `max_effort`,
  `thinking`, `adaptive_thinking`, `interleaved_thinking`, L759-L766) as the
  documented override.
- "If the ID doesn't start with `claude-` or contain `[1m]`, in any casing,
  and Claude Code can't resolve it to a Claude model, the variable applies
  directly and proactive compaction continues at the declared window."
  (L657). Framing: unrecognized IDs get user-declared context windows via
  `CLAUDE_CODE_MAX_CONTEXT_TOKENS`.
- "Claude Code doesn't run that recovery when a gateway rewrites the error
  to wording Claude Code doesn't recognize." (L661). Framing: compaction
  recovery for unknown models depends on server error wording, a minimum-
  contract item.
- "Sessions auto-compact before the window fills, at about 967K tokens by
  default" (L616, Sonnet 5 on the Anthropic API). Framing: a concrete
  context-accounting default if the report contrasts agents.
