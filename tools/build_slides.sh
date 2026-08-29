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

# New scaffolds keep a deck-local slides/refs.bib. Older studies may still
# carry only report/refs.bib, so retain that directory as a fallback.
if [ -f "$slides_dir/refs.bib" ]; then
  bib_abs="$(cd "$slides_dir" && pwd)"
elif [ -f "$study_dir/report/refs.bib" ]; then
  bib_abs="$(cd "$study_dir/report" && pwd)"
else
  echo "build_slides: no slides/refs.bib or report/refs.bib; run tools/gen_bib.py first" >&2
  exit 1
fi
export BIBINPUTS=".:$bib_abs:"

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
