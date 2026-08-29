#!/usr/bin/env bash
# Build a study's LaTeX report to PDF.
# Usage: tools/build_report.sh <study-dir>
set -euo pipefail

study_dir="$1"
report_dir="$study_dir/report"

if [ ! -f "$report_dir/main.tex" ]; then
  echo "build_report: $report_dir/main.tex not found" >&2
  exit 1
fi

mkdir -p "$report_dir/build"

if command -v latexmk >/dev/null 2>&1; then
  (cd "$report_dir" && latexmk -pdf -interaction=nonstopmode -halt-on-error \
     -outdir=build main.tex)
elif command -v tectonic >/dev/null 2>&1; then
  (cd "$report_dir" && tectonic --outdir build main.tex)
else
  echo "build_report: need latexmk or tectonic on PATH" >&2
  exit 1
fi

echo "built: $report_dir/build/main.pdf"
