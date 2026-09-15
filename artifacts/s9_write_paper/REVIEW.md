# Stage 9 — results export, paper tables, figures and provenance (brief S9)

## What ran

```bash
python scripts/s9_write_paper.py --tables fidelity properties figure_fidelity resolution figure_degradation \
    usability range figure_range reference          # seconds, CPU
bash scripts/build_paper.sh                          # paper.pdf (review) and paper_clean.pdf
bash scripts/latexdiff_round.sh 0bdb0c3 round5_6     # artifacts/amendments/latexdiff_round5_6.pdf
```

The stage reads only stage artifacts (S2–S8). It writes no measurement of its own; every cell it emits carries a
provenance entry naming the artifact, the key inside it, the script that produced it and the seeds.

## What came out

| output | content |
|---|---|
| `paper/tables/table_{fidelity,properties,usability,resolution,range,reference}.tex` | Table 1–6 bodies, `\input` by `paper.tex` through `\csname @@input\endcsname` (a plain `\input` inside a tabular misplaces `\noalign`). |
| `paper/tables/table_*_notes.tex` | One `\def\Tab<X>Notes` macro per table, holding the void footnotes; `\input` in the preamble and used in captions via `\protect`. |
| `paper/img/fig_res_{fidelity,degradation,range}.pdf` | Figures 6, 7, 8 in the paper style. |
| `results/table{1,2,3,4,5,6}_*.json`, `results/fig_res_*.png` | The same values machine-readable, with the source artifact of each. |
| `results/provenance.json`, `docs/RESULTS_PROVENANCE.md` | 159 rows: every table cell group and figure in §4 with its artifact and commit. |

Sections written in `paper/paper.tex`: §4 introduction and scope, §4.1–§4.4, and §5 except the frozen C2 paragraph and
Future work, which were already there. The Conclusion stub is untouched, as the brief requires.

## Checks

- Both builds compile with 0 LaTeX or package warnings and no undefined references (`scripts/build_paper.sh` fails on
  any of those): the review build `paper.pdf` and the clean build `paper_clean.pdf`.
- The only remaining `\hl` placeholder is the repository and DOI footnote in §1, which is the author's to fill.
- Prose numbers were checked against the artifacts: the scope paragraph (unit counts, splits, regeneration rates and the
  D05 ratios) against `artifacts/s2_audit_datasets/tables/summary.json`, `artifacts/s3_fit_profiles/tables/split_*.csv`
  and the fitted profiles; §4.2 against `usability_*.json`; §4.3 against `part1_degradation.json` and
  `part2_generator_settings.json`; §4.4 against `reference_values.json`.
- Two numbers were corrected during that check: the largest reference-model attribution error (1.6e-6, not 2.4e-7) and
  the largest distance from the ceiling on a trained model (0.57, not 0.55).

## Anomalies

1. **`latexdiff` needed two fixes** before the round 5–6 diff would build: `paper/tables` must be copied into the diff
   workspace, and word-level markup inside a `tabular` whose body moved into an `\input` produces a misplaced
   `\noalign`, so tables are now diffed as whole blocks (`PICTUREENV`). A third fix was a `[ ... ] && ...` as the last
   command of a loop body, which ends the script under `set -e`.
2. **Rounds 5 and 6 share one diff PDF** (`latexdiff_round5_6.pdf`, against `0bdb0c3`), because round 5 was committed
   without its own diff and the brief asks for a diff per round; the combined file covers both and is named for them.
3. **Figure 6 needed a layout fix**: the legend sat on the $z=1$ line and the level labels sat on the data. The legend
   is now one row under the HUST panel and the labels are outside the axes.

## Decisions needed

None for a human. Taken at this stage: D10 (held citations, round 5), D24 (Table 6 per profile, round 6).
