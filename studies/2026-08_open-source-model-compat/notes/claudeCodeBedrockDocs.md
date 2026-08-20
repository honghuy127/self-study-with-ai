---
source_key: "claudeCodeBedrockDocs"
read_date: "2026-08-20"
confidence: "high"
relevance: "2"
---

# Notes: Claude Code docs: Amazon Bedrock integration

## Source identification

- Key: claudeCodeBedrockDocs
- Authors, year, venue: Anthropic, 2026, code.claude.com/docs
- Tier: docs
- URL / DOI: https://code.claude.com/docs/en/amazon-bedrock
- Snapshot: `sources/docs/claudeCodeBedrock.md` (595 lines, fetched 2026-08-20 per
  registry provenance). All anchors below are line numbers into this snapshot,
  written `(L###)`.

## Problem and motivation

The page documents how to run Claude Code against Amazon Bedrock instead of
Anthropic's first-party API: setup, IAM configuration, model pinning, and
troubleshooting. Its stated scope is "configuring Claude Code through Amazon
Bedrock, including setup, IAM configuration, and troubleshooting" (L7). The
audience is enterprise or AWS-committing users: prerequisites include "An AWS
account with Amazon Bedrock access enabled" and "Access to desired Claude
models (for example, Claude Sonnet 4.6) in Amazon Bedrock" (L85-L86). A login
wizard and a manual environment-variable path are both offered (L90, L114).

## Method or core idea

Two connection paths exist, both AWS-credentialed and both Claude-only:

**Path 1: Bedrock Invoke API.** Set `CLAUDE_CODE_USE_BEDROCK=1` (L230),
optionally `export AWS_REGION=us-east-1  # optional if your AWS profile already sets a region`
(L231). Credentials come from "the default AWS SDK credential chain" (L129),
with five documented options: `aws configure` (L134), access key
environment variables `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` /
`AWS_SESSION_TOKEN` (L140-L142), an SSO profile via `AWS_PROFILE` (L150-L152),
`aws login` (L160), or a Bedrock API key via
`export AWS_BEARER_TOKEN_BEDROCK=your-bedrock-api-key` (L168). Region resolves
in this order: `AWS_REGION`, `AWS_DEFAULT_REGION`, the active AWS profile's
`region` (shared credentials file first, then shared config), then `us-east-1`
(L246-L249); a value "containing a slash, dot, or space" is treated as unset
(L251). Optional knobs: `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION` for the
small/fast model's region (L236) and `ANTHROPIC_BEDROCK_BASE_URL` "to override
the Bedrock endpoint URL for custom endpoints or gateways" (L238-L239).

**Path 2: Mantle endpoint.** "Mantle is an Amazon Bedrock endpoint that serves
Claude models through the native Anthropic API shape rather than the Amazon
Bedrock Invoke API" (L477). Enable with `CLAUDE_CODE_USE_MANTLE=1` plus
`AWS_REGION` (L484-L485); override the URL with
`ANTHROPIC_BEDROCK_MANTLE_BASE_URL` (L488, L540); `CLAUDE_CODE_SKIP_MANTLE_AUTH=1`
disables client-side auth for gateways that inject AWS credentials server-side
(L525-L530, L541). Both paths can run in one session: "Model IDs that match the
Mantle format are routed to Mantle, and all other model IDs go to the Amazon
Bedrock Invoke API" (L504-L508).

**Model ID formats.** Three documented shapes:
1. Cross-region inference profile IDs, a region prefix plus an Anthropic model
   ID, e.g. `us.anthropic.claude-opus-4-8`, `us.anthropic.claude-sonnet-4-6`,
   `us.anthropic.claude-haiku-4-5-20251001-v1:0` (L271-L273). "These IDs use
   the `us.` cross-region inference profile prefix" and GovCloud uses the
   `us-gov.` prefix (L276). Prefixes derived from region: `us-gov.*` → `us-gov.`,
   `us-*` → `us.`, `eu-*` → `eu.`, `ap-*` → `apac.`, all others → `global.`
   (L361-L367); `ANTHROPIC_BEDROCK_REGION_PREFIX` (valid values `us`, `eu`,
   `apac`, `jp`, `au`, `global`) overrides the preferred prefix, requires
   v2.1.224 or later (L369, L374).
2. Application inference profile ARNs, e.g.
   `arn:aws:bedrock:us-east-2:your-account-id:application-inference-profile/your-model-id`
   (L313).
3. Mantle IDs, "prefixed with `anthropic.` and without a version suffix, for
   example `anthropic.claude-sonnet-5` or `anthropic.claude-haiku-4-5`" (L494).

**Model selection and defaults.** Pinning variables
`ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`,
`ANTHROPIC_DEFAULT_HAIKU_MODEL` map the `opus`/`sonnet`/`haiku` aliases to
specific Bedrock IDs (L266-L274); without pins the defaults are Primary model
"Opus 5, for example `us.anthropic.claude-opus-5` in a `us-*` region" and
Small/fast model "Sonnet 4.5, for example
`us.anthropic.claude-sonnet-4-5-20250929-v1:0` in a `us-*` region"
(L291-L292). Background tasks run on the default Sonnet model rather than
Haiku "because Haiku may not be enabled in every account or region" (L294).
`ANTHROPIC_MODEL` sets the primary model directly (L309, L313). `modelOverrides`
maps individual Claude version IDs to application inference profile ARNs, all
examples `claude-opus-*` (L332-L341). Startup checks verify account access and
fall back to earlier versions or a lower tier when the default is unavailable
(L347-L351).

**IAM shape.** Required actions: `bedrock:InvokeModel`,
`bedrock:InvokeModelWithResponseStream`, `bedrock:ListInferenceProfiles`,
`bedrock:GetInferenceProfile`, over foundation-model and inference-profile
resources, plus a marketplace subscribe statement conditioned on
`aws:CalledViaLast: bedrock.amazonaws.com` (L396-L431). Missing
`GetInferenceProfile` costs "an extra round-trip" per new model (L435-L437).
First use additionally requires submitting a use-case form per AWS account:
"open the Model catalog, select an Anthropic model, and submit the use case
form. Access is granted immediately after submission" (L98, L116-L123).

## Key claims with anchors

Claims the source states:

- Enabling the integration is a single environment variable:
  `export CLAUDE_CODE_USE_BEDROCK=1` (L230).
- Credential handling is AWS-native: "Claude Code uses the default AWS SDK
  credential chain" (L129), with a documented Bedrock API key option
  `AWS_BEARER_TOKEN_BEDROCK` (L168). Resolved credentials are cached in memory,
  reused "until five minutes before they expire, or for one hour when they
  carry no expiration"; chain resolution times out after 60 seconds
  (L175, L179).
- The wizard "verifies which Claude models your account can invoke, and lets
  you pin them" and writes results into the settings file (L106, L110).
- Alias resolution without pins: "the `opus` alias on Amazon Bedrock resolves
  to Opus 5, and without `ANTHROPIC_DEFAULT_SONNET_MODEL`, the `sonnet` alias
  resolves to Sonnet 4.5" (L268). Defaults: Opus 5 primary, Sonnet 4.5
  small/fast (L291-L292).
- Feature losses on Bedrock: "the `/logout` command is unavailable since
  authentication is handled through AWS credentials" (L256); "The WebSearch
  tool is not available on Amazon Bedrock" (L257).
- API shape: "Claude Code uses the Amazon Bedrock Invoke API and does not
  support the Converse API" (L564). Streaming uses "a binary event-stream
  format with the content-type `application/vnd.amazon.eventstream`", and
  Claude Code rejects successful streaming responses with a different
  content-type (L568).
- Prompt caching: "Prompt caching may not be available in all Amazon Bedrock
  regions" (L324); a 1-hour cache TTL is opt-in via `ENABLE_PROMPT_CACHING_1H=1`
  and "billed at a higher rate than the 5-minute default" (L318-L322);
  `DISABLE_PROMPT_CACHING=1` exists (L316).
- Service tiers: `ANTHROPIC_BEDROCK_SERVICE_TIER` accepts `default`, `flex`, or
  `priority` and "let you trade off cost against latency"; sent as the
  `X-Amzn-Bedrock-Service-Tier` header (L453-L459).
- 1M token context window is model-gated: "Claude Sonnet 5, Opus 4.6 and
  later, and Sonnet 4.6 support the 1M token context window on Amazon Bedrock",
  enabled by appending `[1m]` to the model ID; Sonnet 5 always runs with the
  1M window (L447-L449).
- Guardrails attach via headers `X-Amzn-Bedrock-GuardrailIdentifier` and
  `X-Amzn-Bedrock-GuardrailVersion` in the settings file (L467-L472).
- Mantle is allowlisted: "A `403` from the Mantle endpoint with valid
  credentials means your AWS account has not been granted access to the model
  you requested" (L584); "Mantle has its own model lineup separate from the
  standard Amazon Bedrock catalog, so inference profile IDs such as
  `us.anthropic.claude-sonnet-4-6` will not work" (L586).

Negative-scope claim (verified absence):

- The snapshot contains no reference to OpenAI-compatible endpoints, Ollama,
  LM Studio, or local model servers. The only gateway support is an LLM gateway
  that injects AWS credentials for Bedrock/Mantle traffic (L525-L530), which
  still terminates at AWS-hosted Claude. See Limitations.

My inference, flagged: the Bedrock path is a closed, Anthropic-models-only
integration surface; every model ID example on the page carries the
`anthropic.` namespace (L271-L273, L309-L310, L335-L338, L494), and every
access mechanism (use-case form for "an Anthropic model", wizard checking
"which Claude models", the IAM policy) is scoped to Anthropic models. This
inference is mine, drawn from the document's consistent framing; the page never
explicitly states "non-Anthropic models are unsupported", so I record it as
inference, not a quoted rule.

## Evaluation and evidence

This is configuration documentation, not an evaluation. It carries version
claims rather than metrics; character-exact values found:

- Version gates: credential caching and the 60-second chain timeout "Requires
  Claude Code v2.1.207 or later" (L175, L179); the `sso_region` fix landed "In
  v2.1.207" (L155); `awsCredentialExport` direct use requires v2.1.206 (L222);
  flat `export-credentials` output accepted "As of Claude Code v2.1.181"
  (L218); `Expiration`-aware caching as of v2.1.176 (L220); region file reading
  and Mantle region precedence as of v2.1.172 (L244, L488);
  `ANTHROPIC_BEDROCK_REGION_PREFIX` requires v2.1.224 (L369); `/context` token
  counts fixed "Update to v2.1.196 or later" (L576-L578).
- Model defaults history: "On v2.1.207 through v2.1.218, the primary model on
  Amazon Bedrock defaulted to Opus 4.8 ... Before v2.1.207, the primary model
  defaulted to Sonnet 4.5, the `opus` alias resolved to Opus 4.6" (L303).
- Concrete IDs: `us.anthropic.claude-opus-4-8`, `us.anthropic.claude-sonnet-4-6`,
  `us.anthropic.claude-haiku-4-5-20251001-v1:0`,
  `us.anthropic.claude-sonnet-4-5-20250929-v1:0`, `us.anthropic.claude-opus-5`,
  `eu.anthropic.claude-opus-5` (L271-L273, L283, L291-L292); Mantle examples
  `anthropic.claude-sonnet-5`, `anthropic.claude-haiku-4-5` (L494).
- Timers: credential reuse "until five minutes before they expire, or for one
  hour" (L175); chain resolve "times out after 60 seconds" (L179); prompt
  cache TTLs "5-minute default" and "1-hour" (L318-L322).
- No datasets, baselines, or latency numbers appear. [CITATION NEEDED] for any
  quantitative claim about Bedrock latency, throughput, or cost beyond the
  qualitative "trade off cost against latency" (L453) and "billed at a higher
  rate" (L300, L322); I searched the full 595-line snapshot and found none.

## Limitations

Documented feature losses and caveats on Bedrock (the page itself states all
of these):

- WebSearch tool unavailable (L257); `/logout` unavailable (L256); Converse
  API unsupported, Invoke API only (L564).
- Streaming is fragile through gateways: responses must keep content-type
  `application/vnd.amazon.eventstream`; an API Gateway re-emitting as
  server-sent events produces `Bedrock streaming response has content-type`
  errors, previously `API Error: Truncated event message received`. The stopgap
  `CLAUDE_CODE_DISABLE_BEDROCK_CONTENT_TYPE_GUARD=1` trades the guard for
  decode failures if the body was actually transformed (L568-L572).
- Prompt caching may not exist in all regions; zero cache token counts are a
  documented symptom (L324). `/context` tool-group token counts showed 0
  before v2.1.196 because Bedrock's count-tokens API rejected the tool schema
  fields Claude Code sent (L576-L578).
- Model availability friction: aliases "can lag the newest release and may not
  yet be available in your account" (L263); unpinned startup falls back to an
  earlier or lower-tier model for the session only (L351); "on-demand
  throughput isn't supported" errors require switching to an inference profile
  ID (L560-L562); unpinned deployments after v2.1.207 bill at Opus rates
  (L300); missing `GetInferenceProfile` permission adds a retry round-trip per
  new model (L437).
- Mantle is allowlisted with its own separate model lineup (L494, L584-L586),
  and its availability depends on "what your organization has been granted"
  (L494).
- SSO under corporate proxies can loop indefinitely via `awsAuthRefresh`
  (L548-L550).

As a compatibility evidence source, the page's limits for this study: it is
documentation attestation only, not code; the brief notes Claude Code's loader
is closed and Bedrock behavior is attested only through documented surfaces
(brief.md L65-L66). The snapshot is also a single fetch-date capture, so
version-gated claims may drift in later releases.

## Relevance to the brief

My inference throughout. RQ1 asks which integration surfaces each agent
supports; for Claude Code this page is evidence that the documented
third-party path is a cloud provider (Bedrock) carrying Anthropic models only,
not an open-model surface. The brief explicitly bounds open-weight models
reached through cloud APIs to context, not a primary surface, so this note
fills the context cell for Claude Code's Bedrock column and nothing more
(brief.md L28-L29). Concretely:

- The Bedrock surface shares none of the RQ2 contract elements that matter for
  local servers. The wire shape is the Bedrock Invoke API or Mantle's "native
  Anthropic API shape" (L477, L564); there is no OpenAI-compatible chat
  completions path, no tool-calling negotiation against a foreign server, and
  no configurable base URL pointing at anything other than Bedrock, Mantle, or
  an AWS-credential-injecting gateway (L238-L239, L488, L525-L530).
- Model-ID gating is visible and explicit here, which informs RQ3 by contrast:
  features key off ID patterns (`[1m]` suffix, L449; `anthropic.` prefix for
  Mantle routing, L494, L519; region prefixes, L361-L367), and context and
  token accounting have documented gaps (1M window gated by model family,
  L447; `/context` zeros, L576), mirroring the classes of degradation the
  brief expects on open models.
- Negative scope for the matrix: nothing in this snapshot mentions Ollama, LM
  Studio, an OpenAI-compatible endpoint, or a local server. The Claude Code
  compatibility matrix must rest on claudeCodeModelDocs and, if admissible,
  the blog-tier router note; this note only confirms Bedrock is not an
  open-weight path. It leaves open whether any undocumented Claude Code knob
  accepts non-Anthropic endpoints; the page neither confirms nor denies, and
  the loader remains uninspectable.

## Quotables for the report

- On enablement (frame as the minimal configuration): "export
  CLAUDE_CODE_USE_BEDROCK=1" (L230), presented as the single switch with
  region optional when a profile provides one (L231, L244).
- On the model namespace (frame as closed Anthropic scope): "Set these
  environment variables to specific Amazon Bedrock model IDs" with examples
  `us.anthropic.claude-opus-4-8`, `us.anthropic.claude-sonnet-4-6`,
  `us.anthropic.claude-haiku-4-5-20251001-v1:0` (L266, L271-L273).
- On Mantle (frame as the exception that proves the rule, an Anthropic-shaped
  API still serving Claude): "Mantle is an Amazon Bedrock endpoint that serves
  Claude models through the native Anthropic API shape rather than the Amazon
  Bedrock Invoke API" (L477).
- On feature loss (frame as provider-side degradation, parallel to the
  degradation the brief expects from open models): "The WebSearch tool is not
  available on Amazon Bedrock" (L257); "Claude Code uses the Amazon Bedrock
  Invoke API and does not support the Converse API" (L564).
- On streaming fragility (frame as wire-format strictness): "Amazon Bedrock
  streams responses in a binary event-stream format with the content-type
  `application/vnd.amazon.eventstream`" (L568).
