---
source_key: "opencodeOssProviders"
read_date: "2026-08-20"
confidence: "high"
relevance: 3
repo: "opencode"
commit: "d545d8fba57283528db69281f59c803c646eb7e9"
---

# Notes: OpenCode: generic OpenAI-compatible provider plumbing (baseURL, runtime install, hosted catalog) (opencode)

## Source identification

- Key: `opencodeOssProviders`
- Repository: `opencode` at `d545d8fba57283528db69281f59c803c646eb7e9` (see `sources/repos.yaml`; pin
  path `/Users/hong.huy.nguyen/Work/Code/references/coding-agents/opencode`, branch `dev`, dirty: false)
- Component scope: `packages/opencode/src/provider/provider.ts` (the `@ai-sdk/openai-compatible`
  factory registration, baseURL/endpoint resolution, autoload skip), `packages/opencode/src/provider/auth.ts`,
  `packages/opencode/src/provider/model-status.ts`, `packages/opencode/package.json` (bundled `@ai-sdk`
  provider list). Consulted additionally: `packages/core/src/v1/config/provider.ts` (provider config
  schema), `packages/core/src/models-dev.ts` (hosted catalog client), `packages/core/src/npm.ts`
  (runtime package install), `packages/opencode/src/auth/index.ts` (API-key store),
  `packages/opencode/src/provider/transform.ts` (output-token cap, cross-reference to the
  `opencodeModelGating` note), and the pinned test fixture
  `packages/opencode/test/tool/fixtures/models-api.json` (catalog snapshot) plus
  `packages/opencode/test/provider/provider.test.ts` (config examples).
- Tier: codebase

## Purpose and role in the harness

The provider service is OpenCode's model-connection layer. It turns three inputs, the hosted
models.dev catalog, the user's `opencode.json` config, and credentials from env vars or the auth
store, into a table of `Provider` infos with `Model` records
(`packages/opencode/src/provider/provider.ts:1370-1699`). At call time it resolves an SDK bundle
for a model, builds a `LanguageModelV3` handle, and wraps every HTTP request with timeout and
stream-watchdog logic (`packages/opencode/src/provider/provider.ts:1704-1895`). For open-source
models this is the entire integration surface: there is no Ollama-, LM Studio-, llama.cpp-, or
vLLM-specific client code anywhere in the provider layer; everything reaches such servers through
the generic `@ai-sdk/openai-compatible` factory plus user-supplied `baseURL` and model metadata
(grep of `ollama|lmstudio` over `packages/**/*.ts` finds only a UI icon key and one test line,
`packages/ui/src/components/provider-icons/types.ts:39,57`,
`packages/opencode/test/provider/transform.test.ts:3301`).

## Mechanism

All anchors are to the pinned commit. Paths are relative to the repository root.

### Q1. Pointing OpenCode at a generic OpenAI-compatible server

A user declares a provider block under the `provider` key of `opencode.json` (the config file name
is attested in-code by the comment "options.region from opencode.json provider config",
`packages/opencode/src/provider/provider.ts:378`). The schema of each provider entry is
`ConfigProviderV1.Info` (`packages/core/src/v1/config/provider.ts:82-126`):

- provider id: the record key under `provider` (parsed at
  `packages/opencode/src/provider/provider.ts:1452-1461`, stored with `source: "config"` at line
  1459)
- `npm: Schema.optional(Schema.String)` (`packages/core/src/v1/config/provider.ts:87`): which
  AI-SDK package wraps the provider
- `api: Schema.optional(Schema.String)` (`packages/core/src/v1/config/provider.ts:83`): default
  endpoint URL
- `env: optional array of env var names` (`packages/core/src/v1/config/provider.ts:85`)
- `options.apiKey` and `options.baseURL` (`packages/core/src/v1/config/provider.ts:93-94`), plus
  `options.timeout`, `options.headerTimeout`, `options.chunkTimeout` (lines 101-120) and an open
  rest `Schema.Record(Schema.String, Schema.Any)` (line 122) so arbitrary SDK options pass through
- `models`: `Schema.optional(Schema.Record(Schema.String, Model))`
  (`packages/core/src/v1/config/provider.ts:125`), where each model carries optional `id`,
  `tool_call`, `limit: { context, input?, output }`
  (`packages/core/src/v1/config/provider.ts:14,21,47-53`), and a per-model
  `provider: { npm?, api? }` override (lines 64-66)

An in-repo test shows the exact shape and example values for a local server
(`packages/opencode/test/provider/provider.test.ts:879-890`):

```ts
      provider: {
        "local-llm": {
          name: "Local LLM",
          npm: "@ai-sdk/openai-compatible",
          env: [],
          models: { "llama-3": { name: "Llama 3", tool_call: true, limit: { context: 8192, output: 2048 } } },
          options: { apiKey: "not-needed", baseURL: "http://localhost:11434/v1" },
        },
      },
```

and the test asserts the provider materializes with
`models["llama-3"].api.npm === "@ai-sdk/openai-compatible"` and
`options.baseURL === "http://localhost:11434/v1"`
(`packages/opencode/test/provider/provider.test.ts:874-876`). `http://localhost:11434/v1` is
Ollama's default OpenAI-compatible address; nothing in the code hardcodes it (no `11434` default
exists outside this test).

Resolution order for the wire URL and key, inside `resolveSDK`
(`packages/opencode/src/provider/provider.ts:1729-1751`):

```ts
        const baseURL = iife(() => {
          let url =
            typeof options["baseURL"] === "string" && options["baseURL"] !== "" ? options["baseURL"] : model.api.url
          if (!url) return
```

then provider-level vars loaders and env-var interpolation of `${VAR}` tokens
(`packages/opencode/src/provider/provider.ts:1734-1746`):

```ts
          url = url.replace(/\$\{([^}]+)\}/g, (item, key) => {
            const val = envs[String(key)]
            return val ?? item
          })
```

and finally:

```ts
        if (baseURL !== undefined) options["baseURL"] = baseURL
        if (options["apiKey"] === undefined && provider.key) options["apiKey"] = provider.key
```

(`packages/opencode/src/provider/provider.ts:1750-1751`). So `options.baseURL` from config wins;
the fallback is the model's catalog URL `model.api.url`; `options.apiKey` from config wins; the
fallback is `provider.key`, which comes from env activation or the auth store (next paragraph).
The model's on-the-wire id is `model.api.id`, defaulting through
`model.id ?? existingModel?.api.id ?? modelID` (`packages/opencode/src/provider/provider.ts:1465`)
and re-checked at line 1651 (`model.api.id = model.api.id ?? model.id ?? modelID`), so an alias key
in config can differ from the server-side model id.

Two credential paths outside config options:

- Env vars: for every known provider, if one of its `env` names is set in the environment the
  provider activates with `source: "env"` and `key: provider.env.length === 1 ? apiKey : undefined`
  (`packages/opencode/src/provider/provider.ts:1553-1563`).
- Auth store: `opencode auth` results persist in `auth.json` at mode `0o600`
  (`packages/opencode/src/auth/index.ts:10,79`), typed as `{ type: "api", key, metadata? }` or
  OAuth (`packages/opencode/src/auth/index.ts:14-35`); API-type entries merge into the provider
  with `key: provider.key` (`packages/opencode/src/provider/provider.ts:1565-1576`). The file
  content can be overridden wholesale by `OPENCODE_AUTH_CONTENT`
  (`packages/opencode/src/auth/index.ts:59-63`). Auth flows themselves exist only for providers
  that ship a plugin hook (`packages/opencode/src/provider/auth.ts:41-45,116-127,203-220`), so a
  custom local server gets credentials through config options or env only.

### Q2. The `@ai-sdk/openai-compatible` factory and runtime installation

Registration is one entry of the `BUNDLED_PROVIDERS` map
(`packages/opencode/src/provider/provider.ts:107,117`):

```ts
  "@ai-sdk/openai-compatible": () => import("@ai-sdk/openai-compatible").then((m) => m.createOpenAICompatible),
```

The map holds 24 dynamically imported packages
(`packages/opencode/src/provider/provider.ts:107-134`): `@ai-sdk/amazon-bedrock`,
`@ai-sdk/amazon-bedrock/mantle`, `@ai-sdk/anthropic`, `@ai-sdk/azure`, `@ai-sdk/google`,
`@ai-sdk/google-vertex`, `@ai-sdk/google-vertex/anthropic`, `@ai-sdk/openai`,
`@ai-sdk/openai-compatible`, `@openrouter/ai-sdk-provider`, `@ai-sdk/xai`, `@ai-sdk/mistral`,
`@ai-sdk/groq`, `@ai-sdk/deepinfra`, `@ai-sdk/cerebras`, `@ai-sdk/cohere`, `@ai-sdk/gateway`,
`@ai-sdk/togetherai`, `@ai-sdk/perplexity`, `@ai-sdk/vercel`, `@ai-sdk/alibaba`,
`gitlab-ai-provider`, `@ai-sdk/github-copilot` (mapped to an internal copilot-provider module),
and `venice-ai-sdk-provider`. All are pinned dependencies in
`packages/opencode/package.json`, e.g. `"@ai-sdk/openai-compatible": "2.0.41"` (line 71) and
`"@ai-sdk/openai": "3.0.84"` (line 70); the `@ai-sdk/*` block spans lines 58-76, with
`@openrouter/ai-sdk-provider` (line 96), `ai-gateway-provider` (line 114), `gitlab-ai-provider`
(line 123), and `venice-ai-sdk-provider` (line 147). For open models the bundled packages that
matter are `@ai-sdk/openai-compatible` (the generic path, and the default npm for unknown
providers and config-defined models, see Q3), `@ai-sdk/openai` (servers speaking the full OpenAI
API), and the open-weight hosters `@ai-sdk/groq`, `@ai-sdk/mistral`, `@ai-sdk/cerebras`,
`@ai-sdk/deepinfra`, `@ai-sdk/togetherai`, and `@openrouter/ai-sdk-provider` (this classification
is my inference from package purpose; the code makes no open-model distinction).

`@ai-sdk/openai-compatible` is also the default whenever nothing else is specified. Catalog models
fall back to it (`packages/opencode/src/provider/provider.ts:1243-1248`):

```ts
      url: model.provider?.api ?? provider.api ?? "",
      npm:
        cloudflareGatewayNpm(provider.id, model.id) ??
        model.provider?.npm ??
        provider.npm ??
        "@ai-sdk/openai-compatible",
```

and config-defined models carry the same fallback
(`packages/opencode/src/provider/provider.ts:1466-1474`):

```ts
            const apiNpm =
              model.provider?.npm ??
              provider.npm ??
              existingModel?.api.npm ??
              // Config-defined gateway models bypass fromModelsDevModel, so resolve the
              // native passthrough npm here before falling back to the catalog default.
              cloudflareGatewayNpm(providerID, apiID) ??
              modelsDev[providerID]?.npm ??
              "@ai-sdk/openai-compatible"
```

Runtime installation happens only when `model.api.npm` is not a key of `BUNDLED_PROVIDERS`
(`packages/opencode/src/provider/provider.ts:1801-1832`). The npm install path is:

```ts
        const installedPath = await (async () => {
          if (model.api.npm.startsWith("file://")) {
            return model.api.npm
          }
          const item = await Npm.add(model.api.npm)
          if (!item.entrypoint) throw new Error(`Package ${model.api.npm} has no import entrypoint`)
          return item.entrypoint
        })()
```

(`packages/opencode/src/provider/provider.ts:1812-1819`), followed by dynamic import and factory
discovery by name prefix (`packages/opencode/src/provider/provider.ts:1823-1830`):

```ts
        const fn = mod[Object.keys(mod).find((key) => key.startsWith("create"))!]
```

`Npm.add` installs into a per-package cache directory
`path.join(global.cache, "packages", sanitize(pkg))` (`packages/core/src/npm.ts:79`), skips the
install when `node_modules/<name>` already exists
(`packages/core/src/npm.ts:125-127`), and runs npm Arborist with `ignoreScripts: true`
(`packages/core/src/npm.ts:83-93`). So a `npm: "file://..."` value loads a local package without
network, and any registry package is installed with lifecycle scripts disabled.

One provider-wide behavior: for any model whose npm includes `@ai-sdk/openai-compatible`, OpenCode
forces usage reporting in streams unless explicitly disabled
(`packages/opencode/src/provider/provider.ts:1725-1727`):

```ts
        if (model.api.npm.includes("@ai-sdk/openai-compatible") && options["includeUsage"] !== false) {
          options["includeUsage"] = true
        }
```

### Q3. The hosted models.opencode.ai catalog

The catalog client fetches `api.json` from a fixed source
(`packages/core/src/models-dev.ts:160,176`):

```ts
    const source = Flag.OPENCODE_MODELS_URL || "https://models.opencode.ai"
```

```ts
      return yield* HttpClientRequest.get(`${source}/api.json`).pipe(
```

with a 10-second fetch timeout (`packages/core/src/models-dev.ts:180`), a disk cache named
`models.json` and a 5-minute freshness TTL (`packages/core/src/models-dev.ts:161-165`:
`const ttl = Duration.minutes(5)`), retry of 2 attempts on transient errors
(`packages/core/src/models-dev.ts:150-156`), and a background refresh every 60 minutes
(`packages/core/src/models-dev.ts:255-257`). The source and local path are overridable via
`OPENCODE_MODELS_URL` and `OPENCODE_MODELS_PATH`, and fetching can be disabled with
`OPENCODE_DISABLE_MODELS_FETCH` (`packages/core/src/flag/flag.ts:29,45-46`; consumed at
`packages/core/src/models-dev.ts:184,222`).

The live catalog content is not in the repository, so which providers it lists is runtime data and
[EVIDENCE NEEDED] for the production catalog. The strongest in-repo evidence is the test fixture
`packages/opencode/test/tool/fixtures/models-api.json`, pinned into the test run via
`process.env["OPENCODE_MODELS_PATH"]` at `packages/opencode/test/preload.ts:38` and typed as
`Record<string, ModelsDev.Provider>` (`packages/opencode/test/session/llm.test.ts:701-703`). In
that snapshot:

- An `lmstudio` provider exists, pointed at LM Studio's default local address
  (`packages/opencode/test/tool/fixtures/models-api.json:41242-41248`):

```json
  "lmstudio": {
    "id": "lmstudio",
    "env": ["LMSTUDIO_API_KEY"],
    "npm": "@ai-sdk/openai-compatible",
    "api": "http://127.0.0.1:1234/v1",
    "name": "LMStudio",
    "doc": "https://lmstudio.ai/models",
```

  Its listed models are open-weight entries, e.g. `openai/gpt-oss-20b` with
  `"open_weights": true` and `"limit": { "context": 131072, "output": 32768 }`
  (`packages/opencode/test/tool/fixtures/models-api.json:41250-41280`).
- There is no bare local `ollama` provider (grep for `"ollama"` in the fixture matches only
  `ollama-cloud`), only the hosted Ollama Cloud service
  (`packages/opencode/test/tool/fixtures/models-api.json:75768-75774`):

```json
  "ollama-cloud": {
    "id": "ollama-cloud",
    "env": ["OLLAMA_API_KEY"],
    "npm": "@ai-sdk/openai-compatible",
    "api": "https://ollama.com/v1",
    "name": "Ollama Cloud",
    "doc": "https://docs.ollama.com/cloud",
```

- Other local-server-adjacent entries exist under the same pattern, e.g. `privatemode-ai` with
  `"npm": "@ai-sdk/openai-compatible"` and `"api": "http://localhost:8080/v1"`
  (`packages/opencode/test/tool/fixtures/models-api.json:20495-20501`), llama.cpp's standard port.

Note `"open_weights": true` appears in fixture entries but the parsed catalog `Model` schema
(`packages/core/src/models-dev.ts:67-120`) declares no `open_weights` field, so the code does not
consume that flag; it is descriptive metadata in the hosted data.

Unknown-model behavior: there is no fallback provider that invents a model entry. `getModel`
fails with `ModelNotFoundError` carrying up to 3 fuzzy suggestions
(`packages/opencode/src/provider/provider.ts:1842-1864`; suggestion logic at lines 1330-1357,
`fuzzysort.go(modelID, available, { limit: 3, threshold: -10000 })` at line 1339). Unknown
providers fail the same way with fuzzy provider-ID suggestions (lines 1845-1852). What does fall
back, for providers and models the user or catalog defines, are the npm package
(`"@ai-sdk/openai-compatible"`, above) and the model limits (next section).

### Q4. Autoload skip around baseURL (`provider.ts:729-770`)

Two built-in custom loaders early-return when `baseURL` is preconfigured. For
`cloudflare-workers-ai` (`packages/opencode/src/provider/provider.ts:729-732`):

```ts
      // When baseURL is already configured (e.g. corporate config routing through a proxy/gateway),
      // skip the account ID check because the URL is already fully specified.
      if (input.options?.baseURL) return { autoload: false }
```

and for `cloudflare-ai-gateway` (`packages/opencode/src/provider/provider.ts:767-769`):

```ts
      // When baseURL is already configured (e.g. corporate config), skip the ID checks.
      if (input.options?.baseURL) return { autoload: false }
```

`autoload` is one half of the activation condition for custom loaders
(`packages/opencode/src/provider/provider.ts:1606-1614`):

```ts
          if (result && (result.autoload || providers[providerID])) {
```

Meaning: `autoload: false` means the loader alone will not activate the provider; it activates
only if something else already registered it (env key or stored auth in the earlier loops at
`packages/opencode/src/provider/provider.ts:1553-1576`). For the two Cloudflare providers, a
pre-set `baseURL` (a corporate proxy or gateway URL from config) therefore bypasses the
`CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_GATEWAY_ID` / token requirements entirely; the config
re-application loop that runs after the custom loaders
(`packages/opencode/src/provider/provider.ts:1617-1625`) then materializes the provider straight
from config and catalog data (`mergeProvider` seeds a provider from the database when absent,
`packages/opencode/src/provider/provider.ts:1397-1408`). The same skip also returns without a
`getModel`, so models ride the plain `sdk.languageModel(model.api.id)` path
(`packages/opencode/src/provider/provider.ts:1886`). For a generic local server this machinery is
irrelevant: the `custom()` map (`packages/opencode/src/provider/provider.ts:168-975`) has no
entries for `ollama`, `lmstudio`, or arbitrary user ids, so such providers are plain config
providers whose `options.baseURL` flows untouched into the SDK factory.

### Q5. Learning model capabilities from an arbitrary compatible server

OpenCode never queries the server. There is no `/v1/models` or capability-discovery call for
generic providers in `src/provider/` (grep for `/v1/models|listModels` over
`packages/opencode/src` finds only a comment in a github-copilot plugin file,
`packages/opencode/src/plugin/github-copilot/models.ts:239`, plus the gitlab plugin's workflow
discovery inside `custom()` which is gitlab-only,
`packages/opencode/src/provider/provider.ts:661-726`). Context window and max output come from
exactly two places:

1. The hosted catalog entry, where `limit.context` and `limit.output` are required fields
   (`packages/core/src/models-dev.ts:87-91`) and are copied verbatim into the model
   (`packages/opencode/src/provider/provider.ts:1254-1258`).
2. User config, with zero defaults when nothing is supplied
   (`packages/opencode/src/provider/provider.ts:1528-1532`):

```ts
              limit: {
                context: model.limit?.context ?? existingModel?.limit?.context ?? 0,
                input: model.limit?.input ?? existingModel?.limit?.input,
                output: model.limit?.output ?? existingModel?.limit?.output ?? 0,
              },
```

The downstream consequence of `limit.output === 0` is in
`packages/opencode/src/provider/transform.ts:18,1418-1420`:

```ts
export function maxOutputTokens(model: Provider.Model, outputTokenMax = OUTPUT_TOKEN_MAX): number {
  return Math.min(model.limit.output, outputTokenMax) || outputTokenMax
}
```

with `export const OUTPUT_TOKEN_MAX = 32_000`
(`packages/opencode/src/provider/transform.ts:18`): `Math.min(0, 32000)` is 0, which is falsy, so
the default `32_000` wins. That is, an arbitrary compatible server whose model has no declared
output limit gets `max_tokens` requests up to 32,000 tokens, and a context limit of 0. (The
chars/4 estimation and compaction use of these limits is covered by the companion note
`opencodeModelGating`.) The only signal OpenCode pulls back from the server about usage is the
forced `includeUsage: true` stream option from Q2
(`packages/opencode/src/provider/provider.ts:1725-1727`); what the AI SDK does with it is inside
the vendored package and outside this component.

Other capability defaults for config-defined models
(`packages/opencode/src/provider/provider.ts:1487-1517`): `status` defaults to `"active"` (line
1487; status vocabulary `["alpha", "beta", "deprecated", "active"]`,
`packages/opencode/src/provider/model-status.ts:5`), `temperature`, `reasoning`, `attachment`
default false (lines 1491-1493), `toolcall` defaults **true** (line 1494,
`toolcall: model.tool_call ?? existingModel?.capabilities.toolcall ?? true`), text input/output
default true (lines 1496, 1503), costs default 0 (lines 1519-1526), and deepseek models on the
openai-compatible path get interleaved reasoning field `reasoning_content` by default (lines
1515-1517). Models with status `deprecated` are dropped, and `alpha` models are dropped unless
the experimental-models runtime flag is on
(`packages/opencode/src/provider/provider.ts:1663-1664`).

## Key facts with anchors

- F1 (`packages/opencode/src/provider/provider.ts:117`): the `@ai-sdk/openai-compatible` factory is
  bundled as `"@ai-sdk/openai-compatible": () => import("@ai-sdk/openai-compatible").then((m) => m.createOpenAICompatible)`
  in `BUNDLED_PROVIDERS` (map at lines 107-134, 24 packages).
- F2 (`packages/opencode/src/provider/provider.ts:1466-1474`): every config-defined model without an
  explicit npm resolves to `"@ai-sdk/openai-compatible"` as the final fallback; catalog models get
  the same fallback (lines 1243-1248).
- F3 (`packages/opencode/src/provider/provider.ts:1729-1731,1750-1751`): `options["baseURL"]` wins
  over `model.api.url`; `options["apiKey"]` wins over the env/auth-derived `provider.key`; both are
  taken from config `provider.<id>.options.{baseURL,apiKey}`
  (`packages/core/src/v1/config/provider.ts:93-94`).
- F4 (`packages/opencode/src/provider/provider.ts:1743-1746`): `${VAR}` tokens inside `baseURL` are
  interpolated from the environment, with loader-provided vars substituted first (lines 1734-1741).
- F5 (`packages/opencode/src/provider/provider.ts:1812-1819`, `packages/core/src/npm.ts:79,125-127,92`):
  non-bundled provider packages are installed at runtime via `Npm.add(model.api.npm)` into a cache
  dir, skipped when already present, with `ignoreScripts: true`; `file://` npm values load a local
  package directly.
- F6 (`packages/core/src/models-dev.ts:160,176,165,180,257`): the model catalog is
  `https://models.opencode.ai/api.json`, cached 5 minutes, 10-second timeout, refreshed every
  60 minutes; overridable via `OPENCODE_MODELS_URL` / `OPENCODE_MODELS_PATH`, disable via
  `OPENCODE_DISABLE_MODELS_FETCH` (`packages/core/src/flag/flag.ts:29,45-46`).
- F7 (`packages/opencode/test/tool/fixtures/models-api.json:41242-41248`): the test-pinned catalog
  snapshot lists an `lmstudio` provider with `"api": "http://127.0.0.1:1234/v1"`,
  `"env": ["LMSTUDIO_API_KEY"]`, `"npm": "@ai-sdk/openai-compatible"`; it lists `ollama-cloud`
  (`api: "https://ollama.com/v1"`, lines 75768-75774) but no bare local `ollama` provider.
- F8 (`packages/opencode/src/provider/provider.ts:1528-1532`): config-defined model limits default
  to `context: 0` and `output: 0`; output-limit 0 then yields the 32,000-token `OUTPUT_TOKEN_MAX`
  fallback (`packages/opencode/src/provider/transform.ts:18,1418-1420`).
- F9 (`packages/opencode/src/provider/provider.ts:729-732,767-769,1606-1614`): when `baseURL` is
  preconfigured, the cloudflare loaders return `{ autoload: false }` before any account/gateway
  checks; `autoload: false` plus not-yet-registered means the loader's special handling is skipped
  and the provider activates as a plain config provider (config re-applied at lines 1617-1625).
- F10 (`packages/opencode/src/provider/provider.ts:1725-1727`): for openai-compatible models,
  `options["includeUsage"] = true` is forced unless explicitly set to `false`.
- F11 (`packages/opencode/src/provider/provider.ts:1494`): config models default to
  `toolcall: true`, so OpenCode sends tools to any server unless the user or catalog says
  otherwise; `status` defaults to `"active"` (line 1487).
- F12 (`packages/opencode/src/provider/provider.ts:1842-1864`): unknown model ids raise
  `ModelNotFoundError` with up to 3 fuzzy suggestions; there is no hidden fallback that creates a
  model entry for an unknown id.
- F13 (`packages/opencode/test/provider/provider.test.ts:874-891`): the canonical in-repo example
  of a generic local server is provider id `local-llm` with
  `options: { apiKey: "not-needed", baseURL: "http://localhost:11434/v1" }` and per-model
  `limit: { context: 8192, output: 2048 }`.

Facts F1-F6, F8-F12 are what the code at the pinned commit establishes. F7 reports the content of
a pinned test fixture (a snapshot of the hosted catalog's shape at an unspecified capture date),
not live catalog state. F13 quotes test config; the test's assertions are the project's own.

## Configuration and defaults

Character-exact keys, defaults, and environment variables:

- Config file: `opencode.json` (attested by in-code comment,
  `packages/opencode/src/provider/provider.ts:378`); provider entries under key `provider`
  (`packages/opencode/src/provider/provider.ts:1414,1452`).
- Provider keys (`packages/core/src/v1/config/provider.ts:82-126`): `api`, `name`, `env`, `id`,
  `npm`, `whitelist`, `blacklist`, `options`, `models`.
- `options` schema (lines 90-123): `apiKey: Schema.optional(Schema.String)` (line 93),
  `baseURL: Schema.optional(Schema.String)` (line 94), `enterpriseUrl` (line 95),
  `setCacheKey` (line 98), `timeout` (line 101), `headerTimeout` (line 108), `chunkTimeout`
  (line 117), plus an open rest record (line 122) that passes arbitrary keys (e.g.
  `includeUsage`, `headers`) straight to the SDK.
- Model keys (`packages/core/src/v1/config/provider.ts:13-80`): `id`, `name`, `family`,
  `release_date`, `attachment`, `reasoning`, `temperature`, `tool_call`, `interleaved`, `cost`,
  `limit: { context, input?, output }` (lines 47-53), `modalities`, `status`,
  `provider: { npm?, api? }` (lines 64-66), `options`, `headers`, `variants`.
- Defaults applied to config models (`packages/opencode/src/provider/provider.ts:1487-1531`):
  `status "active"`, `temperature false`, `reasoning false`, `attachment false`, `toolcall true`,
  text input/output `true`, all costs `0`, `limit.context 0`, `limit.output 0`,
  `npm "@ai-sdk/openai-compatible"`, `url ""` when no `api` is given anywhere (line 1485).
- Env vars: per-provider `env` names from catalog or config activate the provider
  (`packages/opencode/src/provider/provider.ts:1553-1563`); single-env providers get `key`
  auto-set (line 1561). Fixture examples: `LMSTUDIO_API_KEY`, `OLLAMA_API_KEY`
  (`packages/opencode/test/tool/fixtures/models-api.json:41244,75770`).
- Flags (`packages/core/src/flag/flag.ts:29,45-46`): `OPENCODE_DISABLE_MODELS_FETCH`,
  `OPENCODE_MODELS_URL`, `OPENCODE_MODELS_PATH`.
- Auth store: `auth.json` in the data dir (`packages/opencode/src/auth/index.ts:10`), mode `0o600`
  (line 79), override env `OPENCODE_AUTH_CONTENT` (lines 59-63).
- OpenAI header timeout default for the built-in openai loader only:
  `const OPENAI_HEADER_TIMEOUT_DEFAULT = 300_000`
  (`packages/opencode/src/provider/provider.ts:35,208`) [not a generic-endpoint default].
- Provider filtering: `enabled_providers` / `disabled_providers` config keys
  (`packages/opencode/src/provider/provider.ts:1415-1422`) and per-provider model `whitelist` /
  `blacklist` (lines 1666-1669).
- Defaults set by the hosted catalog rather than code (e.g. whether `lmstudio` or `ollama-cloud`
  ship with limits): [EVIDENCE NEEDED] for the live catalog; only the test fixture values above
  are verifiable here (looked in `packages/core/src/models-dev.ts` for embedded snapshots and in
  `packages/opencode/test/tool/fixtures/models-api.json`).

## Limitations and unknowns

- No execution evidence: the brief prohibits running any agent, model, or server, so every
  mechanism above is a static trace. Actual request/response shapes on the wire are whatever the
  vendored `@ai-sdk/openai-compatible` package implements; this note does not cover that package's
  internals (e.g. what `includeUsage` puts in the request body, how it maps tool calls).
- Live catalog content is unverifiable from the checkout. Whether production models.opencode.ai
  currently lists `lmstudio`, `ollama-cloud`, or a local `ollama` provider is runtime data
  [EVIDENCE NEEDED]; the fixture is a test snapshot with no recorded capture date.
- No in-code default endpoint for local servers exists (no hardcoded `localhost:11434`,
  `127.0.0.1:1234`, or `8080` outside test data), so a local Ollama deployment requires explicit
  user config; this is inference from the grep, stated so explicitly.
- `provider.env.length === 1 ? apiKey : undefined`
  (`packages/opencode/src/provider/provider.ts:1561`) means multi-env providers never auto-map an
  env value to `apiKey` (test-attested at
  `packages/opencode/test/provider/provider.test.ts:913-935`); how such providers are expected to
  receive keys in practice is not documented in the component.
- The runtime npm install path fetches arbitrary package names from the registry at call time
  (`packages/opencode/src/provider/provider.ts:1816`); `ignoreScripts: true` mitigates install
  scripts but the trust boundary is still a package name from catalog or user config.
- `autoload` semantics for other custom loaders (e.g. `nvidia`'s
  `autoload: provider.source === "config"` at line 479, `snowflake-cortex` at line 970) were read
  but are peripheral to the generic-endpoint question and only partially traced here.

## Relevance to the brief

This is my inference, separated from code facts.

- RQ1 (integration surface): OpenCode's surface for open-source models is the generic
  OpenAI-compatible endpoint, reached through user config (`provider.<id>` with
  `options.baseURL`) plus a hosted catalog that (per the pinned test fixture) treats LM Studio as
  a first-class provider at its default local URL but treats local Ollama as bring-your-own-config.
  There is no native provider code for any local server. This directly fills the OpenCode column
  of the compatibility matrix alongside the Codex and Claude Code notes.
- RQ2 (minimum contract): the implied contract is an HTTP endpoint speaking the OpenAI
  chat-completions wire format with `baseURL` + `/...` paths as implemented by the AI SDK, plus
  model metadata supplied by the user or catalog. `toolcall` defaults true (F11), so servers that
  lack tool calling must be marked `tool_call: false` per model or the agent will send tools;
  context window must be declared because the default is 0 (F8); stream usage is requested via
  `includeUsage` (F10).
- RQ3 (degradation points): context accounting degrades silently to `context: 0` plus the
  32,000-token output fallback for undeclared models (F8), and model-ID-gated behavior lives in
  the companion `opencodeModelGating` component. The `autoload` skip (F9) shows corporate
  base-URL gateways are an explicitly supported pattern the code makes room for.
- Left open: wire-level verification against Ollama/LM Studio/llama.cpp/vLLM (forbidden by the
  brief), the live catalog inventory, and the AI SDK's own compatibility behavior.

## Quotables for the report

- Default npm fallback (`packages/opencode/src/provider/provider.ts:1474`): the chain ends
  `"@ai-sdk/openai-compatible"`. Frame as: OpenCode's catch-all for unknown and configured
  providers is the generic OpenAI-compatible SDK.
- Runtime install (`packages/opencode/src/provider/provider.ts:1816`): `const item = await Npm.add(model.api.npm)`,
  with `ignoreScripts: true` (`packages/core/src/npm.ts:92`). Frame as: arbitrary provider SDKs
  are installed on first use, not just at build time.
- Catalog endpoint (`packages/core/src/models-dev.ts:160,176`):
  `const source = Flag.OPENCODE_MODELS_URL || "https://models.opencode.ai"` and
  `${source}/api.json`, 5-minute TTL (line 165). Frame as: model knowledge is centralized and
  fetched, with a short cache.
- Zero defaults (`packages/opencode/src/provider/provider.ts:1529,1531`):
  `context: model.limit?.context ?? existingModel?.limit?.context ?? 0` and the analogous
  `output` line. Frame as: undeclared open endpoints get a zero context window, surfaced later
  through the 32,000-token output fallback
  (`packages/opencode/src/provider/transform.ts:1418-1420`).
- Test-attested local server config
  (`packages/opencode/test/provider/provider.test.ts:886`):
  `options: { apiKey: "not-needed", baseURL: "http://localhost:11434/v1" }`. Frame as: the
  project's own example of wiring a local Ollama-style server.
- Fixture catalog entry (`packages/opencode/test/tool/fixtures/models-api.json:41246`):
  `"api": "http://127.0.0.1:1234/v1"` for provider `lmstudio`. Frame as: the hosted catalog (as
  snapshotted in tests) knows LM Studio's default local address; caveat that this is a fixture,
  not the live service.
