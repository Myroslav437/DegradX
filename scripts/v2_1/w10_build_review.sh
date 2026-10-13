#!/usr/bin/env bash
# W10 (brief "DegradX v2.1"): the three PDFs the authors review, written to paper/review/ as regular files (no LFS filter;
# check with `git check-attr filter paper/review/*.pdf`):
#   DegradX_review.pdf         review build (\reviewtrue): highlighted changes in Sections 1-3, banners on Sections 4-5,
#                               the notes box on the first page
#   DegradX_clean.pdf          clean build (\cleanbuild -> \reviewfalse): no highlighting, no banners, no notes box
#   latexdiff_vs_original.pdf  latexdiff against the paper as given (commit 6221c50 unless another is passed)
# Usage: bash scripts/v2_1/w10_build_review.sh [<old-commit>]
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
old=${1:-6221c50}
export PATH="$root/.tools/.TinyTeX/bin/x86_64-linux:$PATH"
out="$root/paper/review"
mkdir -p "$out"

# 1-2. review and clean builds (scripts/build_paper.sh fails on errors, undefined references or citations)
bash "$root/scripts/build_paper.sh"
cp "$root/paper/paper.pdf" "$out/DegradX_review.pdf"
cp "$root/paper/paper_clean.pdf" "$out/DegradX_clean.pdf"

# the clean build must carry no review markup: no notes box, banner or draft mark text, no margin notes
if command -v pdftotext > /dev/null; then
  if pdftotext "$out/DegradX_clean.pdf" - | grep -E "Review build\.|Notes for the authors|DRAFT \(agent\)" ; then
    echo "[FAIL] clean build still carries review markup"; exit 1
  fi
fi

# 3. latexdiff against the original
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git -C "$root" show "$old:paper/paper.tex" > "$work/old.tex"
cp "$root/paper/paper.tex" "$work/new.tex"
cp "$root/paper/PRIMEarxiv.sty" "$root/paper/references.bib" "$work/"
cp -r "$root/paper/img" "$root/paper/tables" "$work/"
python3 - "$work/new.tex" "$work/old.tex" <<'EOF'
# In the body: remove \revwhy{...}, \revbanner{...} and \draftmark, drop the revnotes environment, and unwrap \rev{...}
# and \revw{...} (brace-matched), so latexdiff marks word-level changes instead of one coloured block and the diff shows
# the text of the clean build.
import re, sys

def strip(s, name, keep):
    out, i, key = [], 0, "\\" + name + "{"
    while True:
        j = s.find(key, i)
        if j < 0:
            out.append(s[i:]); return "".join(out)
        out.append(s[i:j]); k, depth = j + len(key), 1
        while depth:
            depth += {"{": 1, "}": -1}.get(s[k], 0) if s[k - 1] != "\\" else 0; k += 1
        if keep:
            out.append(strip(s[j + len(key):k - 1], name, keep))
        i = k

for p in sys.argv[1:]:
    s = open(p).read()
    head, sep, body = s.partition("\\begin{document}")
    body = re.sub(r"\\begin\{revnotes\}.*?\\end\{revnotes\}\n?", "", body, flags=re.S)
    body = body.replace("\\draftmark", "")
    for name, keep in (("revwhy", False), ("revbanner", False), ("revw", True), ("rev", True)):
        body = strip(body, name, keep)
    open(p, "w").write(head + sep + body)
EOF
cd "$work"
# tables are diffed as whole blocks (see scripts/latexdiff_round.sh)
latexdiff --config="PICTUREENV=(?:picture|DIFnomarkup|tabular)[\w\d*@]*" "old.tex" "new.tex" > diff.tex 2> latexdiff.err
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode diff > /dev/null || true
  if [ "$pass" = 1 ]; then bibtex diff > /dev/null || true; fi
done
if grep -q "^!" diff.log; then grep -A3 "^!" diff.log | head -30; echo "[FAIL] latexdiff build has errors"; exit 1; fi
cp diff.pdf "$out/latexdiff_vs_original.pdf"
cd "$root"
for f in "$out"/*.pdf; do
  echo "[ok] ${f#$root/}  $(git check-attr filter -- "${f#$root/}" | sed 's/.*filter: //')  $(pdfinfo "$f" 2>/dev/null | awk '/^Pages/{print $2" pages"}')"
done
