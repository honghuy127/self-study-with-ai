# Upstream of the vendored dossier scripts

The scripts in this directory are vendored copies from the
`conduct-cs-ai-research` skill (https://github.com/honghuy127/cs-ai-research-skills, MIT).
They are the copies that actually run, so the dossier workflow keeps working in a
checkout whose submodule was never initialized.

- Commit: `4cedf391851e01ae58b7f223d670094c3ebfdf24`
- Vendored: 2026-09-02
- Files: research_contract.py, research_state.py, capture_run.py, audit_research.py

Refresh with `python3 tools/sync_skill.py --update`, which pulls the submodule,
copies the scripts, and rewrites this record. Local edits to these files are
allowed and will be overwritten by the next refresh; anything worth keeping
belongs upstream.
