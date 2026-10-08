# V10 — results export, provenance, experiment log, paper sync (X10)

## What ran

- **Results export.** `python scripts/v2/v10_write_paper.py` (2026-10-08). It writes, from the V5–V8 artifacts:
  - one JSON per table in `results/v2`;
  - the LaTeX bodies and notes in `paper/tables`;
  - Figures 6–8 in `paper/img` (`fig_res_floor.pdf` is new);
  - `results/v2/provenance.json`, from which the v2 section of `docs/RESULTS_PROVENANCE.md` is written (85 rows).
- **Table numbering follows the LaTeX order:**

  | Table | Content | Source |
  |---|---|---|
  | 1 | fidelity | V5, with D02b readability |
  | 2 | properties | V5, D30 re-run |
  | 3 | transfer by input set | V1 and V5; new |
  | 4 | usability | V6 |
  | 5 | registering magnitudes | V7 |
  | 6 | reference values | V8 |

  - **Removed:** the setting-sweep figure and table (D25). Their notes file stays in the preamble, which is unchanged
    since `v1-results`.
  - **Printed notes:** no decision IDs. They carry the unit counts and void reasons.
- **Paper sync, AMENDMENTS round 7 part 2.**
  - **Table and figure environments.** Headers, captions and column counts are set by hand for the v2 bodies.
  - **D30.** It enters the EOL paragraph.
  - **D29.** Its anchor sentence enters §3.4.
  - **Results and Discussion rewrite.** It ran as a workflow:
    - three section groups, each drafted, adversarially verified against `results/v2`, the REVIEWs, the D-records and
      the declared readings, then revised;
    - 39 edits;
    - the two groups' conflicting edits to the §3.4 line were resolved by hand: the version stating the declared
      rule was kept.
  - **Whole-paper adversarial review.**
    - Three lenses: numbers, consistency and claims, brief compliance.
    - A refuter tried to disprove every finding.
    - 55 findings: 33 confirmed and applied, 22 duplicates or refuted.
    - Fixes to generated tables went into the script, not into the generated files.
  - `artifacts/amendments/latexdiff_round7.pdf`: round 7 (parts 1 and 2) against `v1-results`, 29 pages.
- **Experiment log.** `docs/EXPERIMENT_LOG_v2.html`, with `docs/EXPERIMENT_LOG_v2.pdf` (23 A4 pages, headless Chrome).
  - It follows v1's format: stage cards, decision records with cost lines, a v1 → v2 headline table, and a "flags for
    the authors" box.
  - An independent verifier checked about 1 000 numbers and 40 commit references. It found 5 blockers and 10 minor
    errors. Several were in the stage sources themselves: the V1, V3, V5, V8 and V9 REVIEWs, D31 and the stop report.
    All were corrected in the sources and in the log.

## Checks

- **Builds.** `scripts/build_paper.sh` builds both variants with no undefined references or citations.
  - Review build: 4 marginpar-moved warnings.
  - Both builds: underfull vboxes on float pages only, and no overfull boxes.
- **No-touch regions.** The abstract, Conclusion, Acknowledgments and preamble (lines 1–84) are byte-identical to
  `v1-results`.
- **Length.** 25 pages, as before the rewrite.
- **Visual check.** Tables 1, 2 and 6 were inspected in the rendered PDF. Table 6's exact-attribution row stacks each
  interval under its mean, top-aligned.

## Anomalies

1. **The two halves of Table 3 used different measured-side cleaning.** The columns without offsets predate D27's
   extension of the glitch rule to non-capacity runs.
   - MATR without offsets, cleaned the same way: 3.51 [2.30, 4.99] instead of 3.42.
   - The caption now says so, and the text keeps 3.42 as the published figure.
2. **Under uniform weighting, every method's temporal profile error on a trained model exceeds the error of a fully
   permuted ground truth** (4.76–5.47 against 2.59 in MATR; 3.15–3.32 against 1.70 in HUST). The comparison uses V7's
   windows for the permuted map, drawn from the same 45 test units, and is stated as such.
3. **The abstract and Conclusion are still template placeholders.** They are left to the authors (brief).

## Decisions needed

None from V10. The open items for the authors are in the log's flags box:
- the AI disclosure;
- the ISU-ILCC stop report (option A recommended);
- the D28 E2 reading;
- the abstract and Conclusion;
- the wording of the post-data list.
