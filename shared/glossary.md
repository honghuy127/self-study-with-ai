# Glossary

Cross-study terms. Add a term when a study establishes a stable definition
worth reusing, and link the study that established it.

- **scaled dot-product attention**: attention with compatibility function
  softmax(QK^T / sqrt(d_k)); the 1/sqrt(d_k) division keeps dot-product
  magnitudes in the region where softmax retains usable gradients at large
  key dimensionality.
  Source: studies/2026-08_scaled-dot-product-attention
- **coding-agent harness**: the engineering layer between a language model
  and a repository: the turn loop, the tool surface and file-edit protocol,
  context compaction, permission and sandbox policy, extensibility (hooks,
  plugins, skills, subagents, MCP), configuration and provider plumbing,
  session state, and user-facing interfaces. Eight-dimension decomposition
  established by static source traces of three production systems.
  Source: studies/2026-08_coding-agents-harnesses-and-open-models (merged 2026-08-20 from 2026-08_coding-agent-harnesses)
- **turn loop**: the harness control structure implementing
  prompt-sample-execute-continue: a continuation condition plus explicit
  defenses against model repetition loops (rejection taxonomies,
  identical-call tripwires, or stop-hook caps). All three studied systems
  realize the same abstract loop with different substrates.
  Source: studies/2026-08_coding-agents-harnesses-and-open-models (merged 2026-08-20 from 2026-08_coding-agent-harnesses)
- **context compaction**: the mechanism a harness uses to reclaim its
  context window mid-session. Trigger styles observed: fractional (a fixed
  fraction of the effective window) and reserved-buffer (overflow past the
  input limit minus a reserved token budget); closed systems may expose
  only lifecycle seams without numeric thresholds.
  Source: studies/2026-08_coding-agents-harnesses-and-open-models (merged 2026-08-20 from 2026-08_coding-agent-harnesses)
- **closed-core attestation**: evidence protocol for systems whose source
  is not inspectable: official documentation snapshots plus the pinned
  public surface (plugins, examples) are the admissible tiers, third-party
  teardowns are context-tier only, and unattested internals are recorded
  as "undisclosed" rather than inferred.
  Source: studies/2026-08_coding-agents-harnesses-and-open-models (merged 2026-08-20 from 2026-08_coding-agent-harnesses)
