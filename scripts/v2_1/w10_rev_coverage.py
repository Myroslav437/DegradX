#!/usr/bin/env python
"""W10 (brief "DegradX v2.1") — mechanical check that every span of §1-§3 (Introduction, Related Work, Methodology including
the protocol and Models sections) that differs from the authors' original paper (commit 6221c50) lies inside a \\rev{} or
\\revw{} span of paper/paper.tex.

Method: both versions of §1-§3 are tokenised (LaTeX commands, words, single punctuation characters; whitespace, comments and
\\label{...} ignored). In the current version, \\revwhy{...} margin notes are removed and the \\rev{ / \\revw{ wrappers are dropped
while every token inside them is marked as highlighted. The criterion: the unhighlighted tokens of the current version, in
order, must be a subsequence of the original tokens, so that every word not highlighted is the authors' word in its place. A
token-level diff (difflib, no autojunk) of the original against the unhighlighted tokens gives (i) inserted or replacing
unhighlighted tokens, which are uncovered changes, and (ii) original tokens with no counterpart, which are covered when
highlighted text stands at that site in the current version (a replacement; its margin note says what was removed) and are
otherwise pure deletions not next to a highlight. Writes a JSON report and prints the uncovered spans with their line numbers.
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKEN = re.compile(r"\\[A-Za-z]+\*?|[A-Za-z0-9]+|[^\sA-Za-z0-9]")
HL_MACROS = ("rev", "revw")
NOTE_MACROS = ("revwhy",)


def section_span(tex: str) -> tuple[int, int]:
    a = tex.index("\\section{Introduction}")
    b = tex.index("\\section{Results}")
    return a, b


def brace_end(s: str, i: int) -> int:
    """Index just past the brace group starting at s[i] == '{'."""
    depth, k = 0, i
    while k < len(s):
        ch = s[k]
        if ch == "\\":
            k += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    raise ValueError("unbalanced braces")


def strip_and_mark(s: str, offset: int):
    """Return (text, highlighted mask, original char index per text char): notes removed, highlight wrappers removed."""
    out, mask, idx = [], [], []
    hl_depth = 0
    i = 0
    closers = []          # positions in s where a highlight group closes
    while i < len(s):
        if closers and i == closers[-1]:
            closers.pop()
            hl_depth -= 1
            i += 1
            continue
        if s[i] == "\\":
            m = re.match(r"\\([A-Za-z]+)\{", s[i:])
            if m and m.group(1) in NOTE_MACROS:
                i = brace_end(s, i + len(m.group(0)) - 1)
                continue
            if m and m.group(1) in HL_MACROS:
                j = i + len(m.group(0)) - 1
                closers.append(brace_end(s, j) - 1)
                hl_depth += 1
                i = j + 1
                continue
            out.append(s[i:i + 2]); mask += [hl_depth > 0] * 2; idx += [offset + i, offset + i + 1]
            i += 2
            continue
        out.append(s[i]); mask.append(hl_depth > 0); idx.append(offset + i)
        i += 1
    return "".join(out), mask, idx


def tokens(text: str):
    return [(m.group(0), m.start(), m.end()) for m in TOKEN.finditer(text)]


def main() -> int:
    orig_full = subprocess.run(["git", "-C", str(ROOT), "show", "6221c50:paper/paper.tex"], capture_output=True, text=True, check=True).stdout
    cur_full = (ROOT / "paper" / "paper.tex").read_text()
    oa, ob = section_span(orig_full)
    ca, cb = section_span(cur_full)
    orig = orig_full[oa:ob]
    nolabel = lambda t: re.sub(r"\\label\{[^}]*\}", lambda m: " " * len(m.group(0)), t)  # noqa: E731  (labels are not text; positions kept)
    orig = nolabel(orig)
    blank = lambda t: re.sub(r"(?<!\\)%.*", lambda m: " " * len(m.group(0)), t)  # noqa: E731  (comments are not text; positions kept)
    cur_text, cur_mask, cur_idx = strip_and_mark(nolabel(blank(cur_full[ca:cb])), ca)
    # comments are not text
    orig_t = [t for t in tokens(re.sub(r"(?<!\\)%.*", "", orig))]
    cur_t = tokens(cur_text)
    # drop tokens of LaTeX comments in the current text
    line_start = [0] + [m.end() for m in re.finditer("\n", cur_full)]

    def line_of(pos: int) -> int:
        import bisect
        return bisect.bisect_right(line_start, pos)

    a = [t[0] for t in orig_t]
    hl = [all(cur_mask[k] for k in range(t[1], t[2])) for t in cur_t]
    plain = [j for j, h in enumerate(hl) if not h]          # indices into cur_t of unhighlighted tokens
    b = [cur_t[j][0] for j in plain]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    uncovered, deletions = [], []
    n_changed_tokens = sum(hl)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op in ("insert", "replace"):
            # unhighlighted current tokens that are not the original's: group by contiguity in the current text
            groups, g = [], [plain[j1]]
            for j in plain[j1 + 1:j2]:
                if j == g[-1] + 1:
                    g.append(j)
                else:
                    groups.append(g); g = [j]
            groups.append(g)
            for g in groups:
                s_, e_ = cur_t[g[0]][1], cur_t[g[-1]][2]
                uncovered.append({"line": line_of(cur_idx[s_]), "op": op, "text": cur_text[s_:e_][:200],
                                  "context": cur_text[max(0, s_ - 60):min(len(cur_text), e_ + 60)].replace("\n", " "),
                                  "original": " ".join(a[i1:i2])[:200] if op == "replace" else ""})
        if op in ("delete", "replace"):
            # original tokens without counterpart: covered if highlighted text stands at the site
            # the site, widened by one unhighlighted token on each side: a closing brace or a comma next to a replaced
            # span is often matched across it by the diff
            lo = plain[j1 - 2] if j1 > 1 else -1
            hi = plain[j1 + 1] if j1 + 1 < len(plain) else len(cur_t)
            site_hl = any(hl[k] for k in range(lo + 1, hi))
            if op == "delete":
                pos = cur_idx[cur_t[min(max(lo, 0), len(cur_t) - 1)][1]]
                deletions.append({"line": line_of(pos), "deleted": " ".join(a[i1:i2])[:200], "next_to_highlight": bool(site_hl)})
    # every highlighted paragraph outside floats carries at least one margin note (\\revwhy names the record and the reason;
    # a \\marginpar cannot sit in a float, so captions are exempt, as in round 7)
    body = re.sub(r"\\begin\{(figure|table)\}.*?\\end\{\1\}", lambda m: " " * len(m.group(0)), cur_full[ca:cb], flags=re.S)
    no_note = []
    pos = 0
    for para in re.split(r"\n\s*\n", body):
        k = body.index(para, pos); pos = k + len(para)
        if re.search(r"\\rev w?\{".replace(" ", ""), para) and "\\revwhy{" not in para:
            no_note.append({"line": line_of(ca + k + len(para) - len(para.lstrip())), "start": para.strip()[:100]})
    report = {"baseline": "6221c50", "scope": "\\section{Introduction} .. \\section{Results} (exclusive)", "highlighted_tokens": n_changed_tokens, "criterion": "unhighlighted current tokens form an in-order subsequence of the original tokens",
              "uncovered_spans": uncovered, "pure_deletions": deletions,
              "highlighted_paragraphs_without_note": no_note, "uncovered_count": len(uncovered), "deletions_not_next_to_highlight": sum(not d["next_to_highlight"] for d in deletions)}
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "v2.1" / "w10_write_paper" / "tables" / "rev_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))
    print(f"highlighted tokens {n_changed_tokens}; uncovered spans {len(uncovered)}; pure deletions {len(deletions)} "
          f"({report['deletions_not_next_to_highlight']} not next to a highlight)")
    print(f"highlighted paragraphs without a margin note: {len(no_note)}")
    for n in no_note:
        print(f"  L{n['line']} [no note] {n['start']!r}")
    for u in uncovered:
        print(f"  L{u['line']} [{u['op']}] {u['text']!r}  ||  orig: {u['original']!r}")
    for d in deletions:
        if not d["next_to_highlight"]:
            print(f"  L{d['line']} [delete] {d['deleted']!r}")
    return 0 if not uncovered and not report["deletions_not_next_to_highlight"] and not no_note else 1


if __name__ == "__main__":
    sys.exit(main())
