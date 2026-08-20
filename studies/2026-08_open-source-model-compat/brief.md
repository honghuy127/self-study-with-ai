# Brief: Claude Code, Codex, and OpenCode with open-source models

Drafted by the agent from the human's scoping decisions (2026-08-20):
static traces only, all open-model surfaces in scope (Ollama, LM Studio,
generic OpenAI-compatible endpoints), briefing depth. Review and approve
before gathering starts.

## Question

- Primary question: How compatible are Claude Code, Codex, and OpenCode
  with open-source models, and through which integration surface (native
  provider code, generic OpenAI-compatible endpoint, or documentation
  only)?
- Secondary questions:
  - What is the minimum contract an OpenAI-compatible server must satisfy
    for each agent (wire API shape, tool calling, context-window
    reporting, streaming)?
  - Where does support degrade with open models: model-ID-gated features
    (patch-tool selection), context accounting defaults, compaction
    triggers, reasoning-token handling?

## Scope

- In scope:
  - Ollama and LM Studio as named providers.
  - Generic OpenAI-compatible endpoints (llama.cpp server, vLLM,
    LiteLLM-style gateways) as configured by base URL.
  - Open-weight models reached through cloud APIs (e.g., Bedrock) only
    as context, not a primary surface.
  - Evidence: pinned source traces and official documentation snapshots,
    same discipline as study 2026-08_coding-agent-harnesses.
- Out of scope:
  - Running any agent, model, or server (decided: static traces only).
  - Fine-tuning, model quality comparisons, benchmarks.
  - Claude Code third-party routers and bridges: review candidates at
    blog tier only, hedged context, not compatibility findings.
- Audience: your future self, choosing a coding agent to point at a
  local model.
- Deadline: none.

## Depth

- Depth: `briefing`
- Deliverable: short technical report PDF with a compatibility matrix;
  notes for each traced component. No frozen experiment plans, no run
  manifests.

## Prior understanding

- What you already know (from study 2026-08_coding-agent-harnesses, not
  to be re-derived):
  - Codex has exactly five built-in provider IDs: openai,
    amazon-bedrock, amazon-bedrock-runtime, ollama, lmstudio; reserved
    against override except Bedrock.
  - Codex's wire protocol is pinned to the Responses API; the chat path
    is rejected as a hard error. Open question this study must answer:
    how the ollama/lmstudio provider entries fit that constraint.
  - OpenCode ships 24 bundled AI-SDK provider packages, installs
    arbitrary provider SDKs at runtime, and fetches a hosted model
    catalog (models.opencode.ai, 5-minute cache).
  - OpenCode gates its apply_patch port on gpt-* model IDs except
    gpt-4/oss; open models therefore exercise the edit/write path.
  - OpenCode estimates unknown token counts as chars/4 and defaults
    OUTPUT_TOKEN_MAX to 32,000.
  - Claude Code's loader is closed; Bedrock/Vertex environment variables
    are attested only through plugin hook surfaces.
- Repos, notes, glossary pages to reuse:
  - shared/knowledge/coding-agent-harnesses.md
  - studies/2026-08_coding-agent-harnesses/notes/codexConfigProviders.md
  - studies/2026-08_coding-agent-harnesses/notes/opencodeConfigProviders.md
  - studies/2026-08_coding-agent-harnesses/notes/codexToolsPatch.md
  - studies/2026-08_coding-agent-harnesses/notes/opencodeTools.md
  - the harness study's registry keys as a starting candidate list only;
    every claim this study makes must still carry an anchor in this
    study's own notes.

## Constraints

- Sources: official documentation and pinned codebases primary; blogs and
  teardowns admitted only as hedged context per the harness study's
  protocol. No leaked-source material.
- Experiments: none (static traces only, decided above).
- Anything prohibited: executing any agent CLI, calling any model API,
  installing providers, downloading model weights.

## Definition of done

- [ ] Every non-trivial claim traces to an eligible note or verified
      snapshot anchor in this study
- [ ] Compatibility matrix covers all three agents x three surfaces
      (Ollama, LM Studio, generic OpenAI-compatible) with evidence tier
      per cell
- [ ] Report builds clean and lint passes
- [ ] Glossary and library.bib merged on completion
