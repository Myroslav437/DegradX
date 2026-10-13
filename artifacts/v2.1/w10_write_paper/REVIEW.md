# W10 — results, the highlighted paper, provenance (brief "DegradX v2.1", 2026-10-13)

## What ran

1. **Results export.** `scripts/v2_1/w10_write_paper.py` is the generalised V10 writer.
   - It writes `results/v2.1/` (one JSON per table, `profile_facts.json`, `provenance.json`), the table bodies and notes in
     `paper/tables/`, Figures 6–8 in `paper/img/` (PNG copies in `results/v2.1/`), and the v2.1 section of
     `docs/RESULTS_PROVENANCE.md` (150 rows; the v2 and v1 sections are kept below it).
   - MATR and HUST are read from the v2 artifacts (tag `v2-results`), FORM from the W-stage artifacts.
   - Trained-model paired retrieval for FORM is printed as void with its reason (`v2_1.readings.sparse_set_trained`).
     The computed values are not printed.
2. **Tables for three profiles.**
   - **Table 1:** one block per profile, one row per generator: offsets + correlated noise; independent noise (seed 0);
     and, as an ablation for MATR and HUST, no offsets with independent noise (3.42 / 1.46). The independent-noise
     transfer is 1.60 / 1.12 (`w5_fidelity/tstr_without_x3`). The offsets' and the correlated noise's shares, and the
     declared "v2 (generation seed 0)" row (r4 `tstr_without_x3.rows`), are in the note.
   - **Tables 2–6:** a FORM column or block. Table 3 uses the declared input-set names, as Figure 5 does.
   - Table 4 carries the pattern-term rows.
   - Table 6 carries paired retrieval in its note.
3. **§4 and §5 written new** for three profiles, each section under a review banner and without word colouring.
   - The Limitations post-data list is in `\rev`. It adds D33 and the post-hoc mechanism sensitivity, and gives the
     r4 timing: after every earlier result, the documentation and one cell's measured values, before any download.
   - The Future-work paragraph "Mappings per protocol" is new.
4. **Abstract and Conclusion** are drafted and marked `\draftmark` ("DRAFT (agent) — for the authors to rewrite"). The
   Acknowledgments are untouched.
5. **Notes box** (`revnotes`, review build only) sits right after `\maketitle`, on page 1. It covers:
   - licence;
   - nominal-capacity source;
   - the HUST anchor, with FORM's ratio;
   - post-data rules and declaration timing;
   - E3 = 66;
   - the D28 E2 reading for ISU-ILCC;
   - FORM's cell universe;
   - FORM's inserted patterns;
   - the proposed AI-use disclosure, which names the Acknowledgments paragraph it would replace.
6. **Highlighting in §1–§3** relative to `6221c50`.
   - `\rev` is for methodology and protocol changes, and `\revw` (lighter) for wording fixes that change no claim.
   - A `\revwhy` margin note names the record. Captions are exempt, because a `\marginpar` cannot sit in a float.
7. **Builds** (`scripts/v2_1/w10_build_review.sh`), in `paper/review/` as regular files (`git check-attr filter`:
   unspecified):
   - `DegradX_review.pdf` (30 pages);
   - `DegradX_clean.pdf` (29 pages; checked to carry no review markup);
   - `latexdiff_vs_original.pdf` (against `6221c50`, 31 pages);
   - `EXPERIMENT_LOG_v2.1.pdf` (10 pages; from `docs/EXPERIMENT_LOG_v2.1.html` by headless Chrome).
8. **README** (new) gives the licence of derived data: CC BY-NC 4.0 for the FORM profile and its generated units, with
   attribution to Cui *et al.* 2024 and data.matr.io/8.

## Highlight coverage (`scripts/v2_1/w10_rev_coverage.py`, `tables/rev_coverage.json`)

- **Criterion.** The unhighlighted tokens of §1–§3 must form an in-order subsequence of the tokens of `6221c50`. Every word
  not highlighted is then the authors' word in its place. Comments and `\label{}` are ignored.
- **Result.**
  - 0 uncovered spans;
  - 42 pure deletions, all next to a highlight;
  - 0 highlighted paragraphs without a margin note;
  - 6 998 highlighted tokens.
- **What the check found and fixed.**
  - Six edits from earlier rounds had never been highlighted: "We" (D13), ";" (D04), ", distinguished …" and ": it"
    (D10), "is enabled in a profile only" (D05), and the site of the moved pan2022 clause (D10).
  - Five highlighted paragraphs had no note (D10 olivares2013; C1 ×3; C3).
  - Seven spans were re-classed as wording (`\revw`).

## Whole-paper consistency pass

The pass was a workflow of three lenses, each followed by an adversarial refuter: numbers; consistency and claims; brief
compliance.

| lens | findings | confirmed | fix corrected | refuted |
|---|---|---|---|---|
| numbers | 10 | 8 | 1 | 1 |
| consistency and claims | 29 | 18 | 2 | 9 |
| brief compliance | 21 | 15 | 2 | 4 |
| **total** | **60** | **41** | **5** | **14** |

**All 46 surviving findings were applied** (35 distinct after merging cross-lens duplicates). AMENDMENTS round 8, row
R8-C, lists them. The ones that change a claim:

- **"Not learned" → "not shown to be learned"** throughout. The ablation interval [−0.0001, 0.0002] cannot detect a term
  carrying 1.7e-5 of the mean term's variance. The declared rule voids the scores; it does not establish non-learning.
- **Discriminator.** §3.4 said no profile resolves the discriminative error. FORM's is readable, so it now says void for
  MATR and HUST.
- **Declaration timing.** "Criteria declared before any of its measurements were read" became "written before any of its
  files were downloaded but after its documentation, and measured values of one of its cells, had been read". The same
  correction is made in the Limitations and the Notes box.
- **Covariance.** "Closed through the offsets" is now limited to MATR and HUST, where it was measured.
- **Profile counts.** "62 designed formation protocols and a baseline one" (63 groups among the 182 cells), and "of the
  evaluated profiles, only FORM carries a sparse set" (NASA PCoE had one in v1).
- **Abstract and conclusion:**
  - FORM's gap is "mostly in their levels early in a cell's life";
  - the floor exception is "channel allocation in MATR";
  - "not distinguished in transfer" replaces "transfers as well";
  - the sparse set is checked on the reference model and on degraded maps.
- **Added to §3.4:** the formation-protocol share (W2). The brief asks that nothing exist only in REVIEW files.

The refuted findings are on record. They were:

- a rounding claim (the medians follow round-half-to-even consistently);
- D14 in the post-data list (a scope choice settled toward the cited dataset, not a rule);
- "adjudicates" (×2, the paper's own term for the reference model);
- "point to" (×3, the paper's own hedge);
- the two offset-share values (already labelled by unit set, though the label was then sharpened under N1);
- the EIV attribution for FORM;
- the count of five departures (correct for Table 2's rows);
- "offsets removed";
- Table 1's row labels;
- note c of Table 1.

## Deviations from the brief's wording, recorded here

- **Table 1 rows.** r4 lists "v2 (generation seed 0)" and "v2 (three seeds)" as rows. The three-seed value is the main row
  of each block, and the seed-0 value is in the note, to keep one row per generator.
- **Stage order.** The order was W7 and W9 before W6 and W5, with W8 after W6 (GPU scheduling). No stage reads an artifact
  of a later one, and the log notes the order.

## Checks

- Both builds pass with no undefined references or citations, no overfull hbox, and no LaTeX errors in the latexdiff.
- The clean build's text contains no "Review build", "Notes for the authors" or "DRAFT (agent)".
- `w10_rev_coverage.py` exits 0.

## Open for the authors

The items of the Notes box. The repository and DOI footnote in §1 is still the authors' placeholder.
