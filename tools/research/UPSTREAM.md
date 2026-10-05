# Upstream of the vendored dossier scripts

The scripts in this directory are vendored copies from the
`conduct-cs-ai-research` skill (https://github.com/honghuy127/cs-ai-research-skills, MIT). They are the copies
that actually run, so the dossier workflow keeps working on a machine
without the skill checkout.

- Commit: `20f25a6f55c24b5eb11f6ecff4fad7ee60377fc3`
- Vendored: 2026-10-05
- Files: research_contract.py, research_state.py, capture_run.py, audit_research.py

Refresh with `python3 tools/sync_skill.py --update`, which pulls the checkout,
copies the scripts, and rewrites this record. Local edits to these files are
allowed and will be overwritten by the next refresh; anything worth keeping
belongs upstream.
