#!/usr/bin/env bash
# Wrapper around the vendored dossier scripts.
# Usage: tools/research/research.sh <study-dir> <script> [args...]
#   script: research_state.py | capture_run.py | audit_research.py
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
study_dir="$1"; shift
script="$1"; shift

case "$script" in
  research_state.py|capture_run.py|audit_research.py) ;;
  *) echo "research.sh: unknown script '$script'" >&2; exit 2 ;;
esac

# --root must follow any subcommand: research_state.py defines it per
# subparser, so placing it first dies with "invalid choice".
exec python3 "$here/$script" "$@" --root "$study_dir"
