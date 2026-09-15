#!/usr/bin/env bash
# latexdiff PDF for one amendment round: bash scripts/latexdiff_round.sh <old-commit> <round-name>
# Writes artifacts/amendments/latexdiff_<round-name>.pdf (LFS). Margin notes (\revwhy) are stripped from
# the diff input only: \marginpar cannot sit inside latexdiff's underline markup, and the notes are
# visible in the review build.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
old=$1; name=$2
export PATH="$root/.tools/.TinyTeX/bin/x86_64-linux:$PATH"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git -C "$root" show "$old:paper/paper.tex" > "$work/old.tex"
cp "$root/paper/paper.tex" "$work/new.tex"
cp "$root/paper/PRIMEarxiv.sty" "$root/paper/references.bib" "$work/"
cp -r "$root/paper/img" "$work/"
python3 - "$work/new.tex" "$work/old.tex" <<'EOF'
# Remove \revwhy{...} and unwrap \rev{...} (brace-matched) outside the preamble, so latexdiff marks
# word-level changes instead of one unbreakable coloured block.
import sys
def strip(s, name, keep):
    out, i, key = [], 0, "\\" + name + "{"
    while True:
        j = s.find(key, i)
        if j < 0:
            out.append(s[i:]); return "".join(out)
        if s[j + len(key) - 1 - len(name) - 1:j].endswith("\\"):   # escaped backslash
            out.append(s[i:j + len(key)]); i = j + len(key); continue
        out.append(s[i:j]); k, depth = j + len(key), 1
        while depth:
            depth += {"{": 1, "}": -1}.get(s[k], 0); k += 1
        if keep:
            out.append(strip(s[j + len(key):k - 1], name, keep))
        i = k
for p in sys.argv[1:]:
    s = open(p).read()
    head, sep, body = s.partition("\\begin{document}")
    body = strip(strip(body, "revwhy", False), "rev", True)
    open(p, "w").write(head + sep + body)
EOF
cd "$work"
latexdiff "old.tex" "new.tex" > diff.tex 2> latexdiff.err
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode diff > /dev/null || true
  [ "$pass" = 1 ] && bibtex diff > /dev/null
done
if grep -q "^!" diff.log; then grep -A3 "^!" diff.log | head -30; echo "[FAIL] latexdiff build has errors"; exit 1; fi
mkdir -p "$root/artifacts/amendments"
cp diff.pdf "$root/artifacts/amendments/latexdiff_${name}.pdf"
echo "[ok] artifacts/amendments/latexdiff_${name}.pdf (against $old)"
