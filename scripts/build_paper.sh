#!/usr/bin/env bash
# Build the paper in both variants and fail on errors, undefined references or citations.
#   review build: amended spans highlighted (\reviewtrue)  -> paper/paper.pdf (committed via LFS)
#   clean build : highlighting off (\cleanbuild defined)   -> paper/paper_clean.pdf (not committed)
# Usage: bash scripts/build_paper.sh [--review-only|--clean-only]
set -euo pipefail
cd "$(dirname "$0")/../paper"
export PATH="$(cd .. && pwd)/.tools/.TinyTeX/bin/x86_64-linux:$PATH"

build() {  # $1 = jobname, $2 = tex preamble injection
  local job=$1 pre=$2
  for pass in 1 2; do
    pdflatex -interaction=nonstopmode -halt-on-error -jobname="$job" "${pre}\input{paper}" > "$job.stdout" || { tail -40 "$job.log"; exit 1; }
    [ "$pass" = 1 ] && { bibtex "$job" > "$job.bibtex.stdout" || { cat "$job.bibtex.stdout"; exit 1; }; }
  done
  pdflatex -interaction=nonstopmode -halt-on-error -jobname="$job" "${pre}\input{paper}" > "$job.stdout"
  if grep -E "undefined|Undefined|Rerun to get|multiply defined" "$job.log"; then
    echo "[FAIL] $job: unresolved references/citations"; exit 1
  fi
  local warns
  warns=$(grep -c -E "^(LaTeX|Package [A-Za-z]+) Warning" "$job.log" || true)
  local boxes
  boxes=$(grep -c -E "^(Over|Under)full" "$job.log" || true)
  echo "[ok] $job.pdf  latex/package warnings=$warns  over/underfull boxes=$boxes"
}

mode=${1:-both}
[ "$mode" != "--clean-only" ] && build paper ""
[ "$mode" != "--review-only" ] && build paper_clean "\def\cleanbuild{1}"
rm -f ./*.stdout
