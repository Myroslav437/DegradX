# D25 — v2 scope: final-position weighting, the generator-setting sweep, representation distance, NASA PCoE and cross-fitting are dropped from every v2 stage

**Stage / claim affected:** V0 (declarations r3, `declared_by_design.v2.scope`); every v2 stage; Tables 1, 3–6 and
Figures 7–8 of the v2 paper. Taken 2026-10-07, before any v2 stage ran, with every v1 result known (brief v2 X8).

**Decision.** v1 ran five things whose results could not change any claim. Each costs compute in v2 (three are multiplied
by the full-scale TimeSHAP of X7) and each adds a table column a reader must discount. Which of them does v2 keep?

**Options considered**
- **a. Keep all five** as in v1.
- **b. Drop each one that v1 shows answered nothing,** keep the v1 artifacts untouched and citable, and say in the paper
  why it was dropped.
- **c. Keep them but report them only in the supplement.**

**Evidence (v1 artifacts, tag `v1-results`)**

| dropped | v1 evidence | artifact |
|---|---|---|
| final-position weighting | Tie-dominated in rank agreement: every method scores 0.14–0.18 on the trained model while the ceiling stays at 0.84–0.87. ϕ* is zero on 23 of 24 positions, so Spearman over the L × C cells ranks mostly ties and magnitudes are not comparable across weightings. (The argument concerns rank agreement; the v2 temporal profile error would be defined there, see Cost.) | `artifacts/s8_reference_methods/tables/reference_values.json` (final_position rows) |
| generator-setting sweep (S7 part two) | Rank agreement on the trained probe is responsive at all 57 examined values; paired retrieval is saturated at 20 of 23 values and void everywhere after D21. With both probes (D20) the operating range excluded only transition sharpness ×0.25–0.5 in MATR and HUST (reference-model saturation) and NASA PCoE noise ×8–16 (accuracy gate), which no v2 question needs. | `artifacts/s7_responsiveness/tables/part2_generator_settings.json`, `operating_range.json`; D20 |
| representation distance | Void for MATR (unit-bootstrap half-width 1.45 × value at 40 held-out units) and NASA PCoE; HUST readable but its interval [2.13, 4.50] spans a factor of two at 23 units. | `artifacts/s5_fidelity/tables/fidelity.json` |
| NASA PCoE | Void on every fidelity measure (D19); the pattern term is not learned at the fitted amplitudes (D21), so the only sparse-set scores are on the reference model, where they are 1 by construction. | D19, D21 |
| cross-fitting | Unreadable: 5-fold cross-fitting over the 18 guard-passing NASA units pools 10 held-out units reaching EOL (below the transfer minimum of 20), 1.22 [1.06, 3.07], with the trajectory family changing across folds. | D19 harness |

Real: all three options are possible.

Works:
- (a) spends about a fifth of the full-scale TimeSHAP budget on the final-position rows alone: 2 models × 120 windows
  × 3 seeds = 720 of 3 720 explanations per profile. It also keeps a profile whose fidelity measures are void.
- (b) leaves every v2 question answerable. Recency weighting stays primary and uniform weighting becomes the sensitivity
  readout, as the brief states.
- (c) keeps the compute and the reader's discounting.

Clear:
- (a) would need a caveat per dropped item in every table it touches, saying why the column cannot be read.
- (c) moves those caveats to the supplement without removing them.
- (b) in two sentences: "v2 drops five measurements that v1 showed carry no information at the available
sample sizes; their v1 values remain in the repository under the tag `v1-results`. Recency weighting is primary, and
uniform weighting is a sensitivity readout."

**Chosen: b.**
1. *Logical:* each item is dropped because of what it measured in v1, not because of what v2 might show.
2. *Consistent:* the brief names the five (X8). The declared minimum-count and void conventions (D02, D02b) already
   void two of them where they matter: MATR's representation distance and every NASA PCoE fidelity cell.
3. *Clear:* one sentence per item in the paper's scope paragraph.
4. *Measured:* about 20 % less TimeSHAP compute (720 of 3 720 explanations per profile; no final-position rows) and no
   void columns.

**Cost.**
- The paper loses its only profile with inserted patterns until the third profile is known (X6). If the third profile
  does not enable patterns either, v2 has no sparse set at all, and Table 3 rows on the pattern term are void with
  that reason.
- The final-position weighting of §3.2.1 (Figure 4) is still defined in the methodology but no longer scored. The
  paper must say so, or a reader will look for its rows. The tie argument concerns rank agreement only. Under
  final-position weighting ϕ* is a point mass at the last position, so the v2 temporal profile error would be well
  defined and arguably most informative there. It is not evaluated in v2: the drop follows the brief (X8) and the
  TimeSHAP budget, and is a stated limitation.
- The operating range of §3.5.3 is no longer reported. Its definition stays in the methodology, marked as not run
  in v2, with the v1 result cited.

**Paper impact:** AMENDMENTS round 7 (X8): scope paragraph of §4; §3.5.3 operating-range sentence; §3.4 profile roles;
Table 5 and Figure 8 removed or replaced.
