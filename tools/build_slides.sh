#!/usr/bin/env bash
# Build a study's beamer slides to PDF.
# Usage: tools/build_slides.sh <study-dir>
set -euo pipefail

study_dir="$1"
slides_dir="$study_dir/slides"

if [ ! -f "$slides_dir/main.tex" ]; then
  echo "build_slides: $slides_dir/main.tex not found" >&2
  exit 1
fi

mkdir -p "$slides_dir/build"

# Slides cite ../report/refs.bib, but latexmk runs bibtex from build/;
# expose the report dir via BIBINPUTS so bibtex finds the database.
report_abs="$(cd "$study_dir/report" && pwd)"
export BIBINPUTS=".:$report_abs:"

if command -v latexmk >/dev/null 2>&1; then
  (cd "$slides_dir" && latexmk -pdf -interaction=nonstopmode -halt-on-error \
     -outdir=build main.tex)
elif command -v tectonic >/dev/null 2>&1; then
  (cd "$slides_dir" && tectonic --outdir build main.tex)
else
  echo "build_slides: need latexmk or tectonic on PATH" >&2
  exit 1
fi

echo "built: $slides_dir/build/main.pdf"
