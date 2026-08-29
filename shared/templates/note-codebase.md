---
# per-codebase-component note. Every field required. Every claim carries a
# code anchor. Delete guidance when final.
source_key: ""          # key from sources/registry.yaml
read_date: ""           # YYYY-MM-DD
confidence: ""          # high | medium | low (your trust in this summary)
relevance: ""           # 1 (peripheral) | 2 (useful) | 3 (central to brief)
repo: ""                # repo key from sources/repos.yaml
commit: ""              # commit SHA the note was written against
---

# Notes: <component title> (<repo key>)

## Source identification

- Key:
- Repository: `<repo key>` at `<commit>` (see `sources/repos.yaml`)
- Component scope: <which directories/files this note covers>
- Tier: codebase

## Purpose and role in the harness

[What this component does in the agent's runtime. Anchor each claim:
(`codex-rs/core/src/state.rs:120`), (`packages/opencode/src/session/index.ts#fork`),
(file path + line or symbol).]

## Mechanism

[Control flow, data structures, protocols, defaults, and failure behavior.
Anchors throughout. Quote code only when shorter than describing it.]

## Key facts with anchors

- Fact 1 (`path/file.ext:123`): ...
- Fact 2 (`path/file.ext#symbol`): ...

[Only what the code at the pinned commit actually does. Where you infer
relevance to the brief, say so explicitly and separately.]

## Configuration and defaults

[Config keys, environment variables, and default values, character-exact,
with anchors. If a default is set by a server or model rather than code,
write `[EVIDENCE NEEDED]` and say where you looked.]

## Limitations and unknowns

[Gaps in what the code shows, closed-source boundaries, behavior that
depends on runtime state you cannot observe. This section must exist even
when empty-looking.]

## Relevance to the brief

[Your own inference, clearly separated from code facts. Which brief
questions does this illuminate? What does it leave open?]

## Quotables for the report

[Short code excerpts or identifiers with anchors the writer can reuse, and
the suggested in-text framing.]
