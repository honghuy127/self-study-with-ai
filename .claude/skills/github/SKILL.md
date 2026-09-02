---
name: github
description: Inspect and manage GitHub issues, pull requests, Actions, and releases with live evidence and explicit authorization for every remote write. Use for GitHub-hosted collaboration, not local-only Git work.
---

<!-- Generated from .agents/skills by tools/sync_runtimes.py. Edit the source, not this file. -->

# GitHub collaboration

Read and follow the externally maintained
[GitHub collaboration playbook](../../../.opencode/skills/conduct-cs-ai-research/references/github-collaboration.md)
in full before performing GitHub work. Treat that file as the canonical
workflow; this adapter exists only to make it discoverable under the same
`github` name in Codex, OpenCode, and Claude Code.

If the playbook is unavailable, stop and ask the user to initialize the
submodule with `git submodule update --init --recursive`. Do not replace it
with instructions recalled from memory.

For issue-validity requests, inspect the current code and relevant tests. Fix
an issue that still reproduces when the user requested a fix. Close an issue
only when the user authorized closure and current evidence shows it is
resolved, invalid, or obsolete.
