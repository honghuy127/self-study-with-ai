# CLAUDE.md

Read [AGENTS.md](AGENTS.md) first and in full. It is the operating manual for
this repository and applies to every harness; this file only records what is
specific to running the workflow under Claude Code.

## What is different here

The agent definitions live once in [`runtime/`](runtime/) and are rendered
into both harnesses by `python3 tools/sync_runtimes.py`. Never edit
`.claude/agents/`, `.claude/commands/`, `.opencode/agents/`, or
`.opencode/commands/` directly: they are generated, and `check_all.py` fails
when they drift from their source.

Permission enforcement differs between the two harnesses, and the difference
is real rather than cosmetic:

- **OpenCode** takes each agent's write zone as per-glob edit permissions, so
  the boundary is enforced by the harness. A summarizer physically cannot
  write into `report/`.
- **Claude Code** has no per-glob edit permission. Each generated agent
  carries its write zone in its prose, and the repo-wide invariants are
  enforced by a `PreToolUse` hook, `tools/zone_guard.py`, configured in
  [`.claude/settings.json`](.claude/settings.json). The hook refuses edits to
  `study.yaml`, `events.jsonl`, `archive.yaml`, and any `.pdf` under a study,
  because those are owned by `tools/study.py` and `tools/cleanup_study.py`.
  Everything else rests on the agent contract, so read the write zone in your
  own definition and stay inside it.

If `python3` is not on PATH (common on Windows), change the hook command in
`.claude/settings.json` to `python tools/zone_guard.py` or `py -3
tools/zone_guard.py`. Every documented command in this repo works the same
way with `python` substituted for `python3`.

## Working here

- Subagents are dispatched with the Task tool by the agent name in
  `.claude/agents/`: `researcher`, `summarizer`, `paper-analyst`,
  `experimenter`, `writer`, `reviewer`, `tutor`, `assessor`.
- Slash commands mirror the OpenCode ones: `/new-study`, `/gather`, `/draft`,
  `/read-paper`, `/review`, `/learn`, `/practice`, `/assess`, `/ask`,
  `/review-due`.
- The research playbooks the agents cite live in the
  `conduct-cs-ai-research` submodule under
  `.opencode/skills/conduct-cs-ai-research/`. That path is shared by both
  harnesses; run `git submodule update --init --recursive` if it is empty.
- Never flip a gate, edit a status, or hand-write `events.jsonl`. Gate
  decisions are the human's, recorded through `python3 tools/study.py`.
