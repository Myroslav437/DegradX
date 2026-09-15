# Stage 4 — Generator and attribution ground truth (paper §3.1–3.2, Eq. 1–6 as amended)

## What ran

- Generation: `python scripts/s4_generate_units.py --workers 12`, then `--force --skip-rho` after D18. Seed 20260915; generation seeds 0, 1, 2; CPU.
- Units: 300 per profile and seed, split train/validation/test 0.7/0.15/0.15 at unit level.
- Cache: `data/generated/<profile>/seed<g>.pkl` (gitignored; regenerated bit-identically from the seeds).
- ρ-sensitivity refit: ρ grid × two EOL definitions × 3 datasets (first run, unaffected by D18).
- Decision harnesses: D01 (sparse retrieval), D18 (generated state origin).

Target constants per profile (`tables/summary.json`):
- κ_c = β_c / (φ_c(1) − φ_c(0)) with β = 1/3 on the three weighted channels (capacity, charge time, mean discharge voltage) in every profile; no channel demoted.
- x⁰ = φ_c(0).
- Window L = 24; recency half-life 6.

## What came out

| figure | what to look for |
|---|---|
| `figure2_layout_nasa_pcoe` | Paper Fig. 2 layout on generated NASA unit 220 (capacity): mean component, the inserted regeneration patterns (5 events), AR(1) noise, their sum, and ϕ* of the last window (graded field shaded, sparse set as stems). |
| `figure3_layout_matr` | Paper Fig. 3 layout from fitted MATR parameters: two resampled units at different paces (T at the 20th and 80th percentile of θ units), the shared mappings normalised by φ_c(0), their mean components. |
| `<profile>_weightings_as_implemented` | The three position profiles as used (recency half-life 6, uniform, final position) for L = 24. Paper Fig. 4 was regenerated with the C1 notation π_u (round 4). |
| `<profile>_generated_vs_measured` | Paper Fig. 6 panels: all eligible measured units (grey) with 25 generated units (black), z = 0 and z = 1 marked. For illustration, not a measurement. |
| `rho_sensitivity` | T of fitted units (median, IQR) over ρ under r2 (nominal-anchored) and r1 (first-position). |

Generated sets:

| profile | T median [IQR] seeds 0 / 1 / 2 | θ-unit T median | units with patterns (events) per seed |
|---|---|---|---|
| MATR | 823 [535, 1039] / 748 [506, 985] / 727 [515, 1020] | 770.5 | 0 (patterns not enabled, D05) |
| HUST | 1807 [1585, 2221] / 1903 [1602, 2178] / 1881 [1680, 2063] | 1860.5 | 0 (not enabled) |
| NASA PCoE | 66 [35, 74] / 66 [35, 74] / 63 [33, 74] | 61.5 | 152 (276) / 143 (265) / 124 (245) |

ρ sensitivity (`tables/rho_sensitivity.csv`): fitting units reaching EOL and their median T.

| | ρ = 0.70 | 0.75 | 0.80 | 0.85 | 0.90 |
|---|---|---|---|---|---|
| MATR r2 | 0 | 29, T 513 | 90, T 770.5 | 93, T 727 | 95, T 683 |
| MATR r1 | 0 | 0 | 31, T 498 | 92, T 756 | 95, T 737 |
| HUST r2 | 0 | 0 | 54, T 1860.5 | 54, T 1705 | 54, T 1533 |
| HUST r1 | 0 | 53, T 1858 | 54, T 1676 | 54, T 1488 | 54, T 1256 |
| NASA r2 | 6, T 102.5 | 6, T 76.5 | 8, T 61.5 | 7, T 54 | 1, T 37 |
| NASA r1 | 4, T 72.5 (rollover) | 6, T 85.5 | 6, T 68.5 | 6, T 57 | 9, T 33 |

Reading:
- Below 0.80 the MATR and HUST records stop before the threshold, so attainment collapses. That is a property of recording to the 80 % stopping rule (D13), not of the cells.
- The family choice is stable across ρ, except for NASA r1 at ρ = 0.70.

## Checks

162 pass, 0 warnings, 0 failures (`tables/checks.csv`). Per profile and generation seed, over every window of every unit under all three weightings:

| check | expected | observed |
|---|---|---|
| Σϕ* = y | < 1e-9 (relative) | ≤ 2.2e-16 |
| g(x) − y = Σ w ε | < 1e-9 | ≤ 3.8e-15 |
| mean over units of g(x) − y | \|mean\| ≤ 3 SE | pass in all 27 cases |
| pristine unit (z = 0, no patterns, no noise) | y = 0 | 0 |
| final-position weighting | graded and sparse fields 0 outside the last position | 0 |
| E[ε_c] per measured channel | \|mean\| ≤ 3 SE over units | pass (all channels, profiles, seeds) |
| z starts at the pristine level; T is the first crossing of z = 1 | z₁ ≤ 0.05, z_T ≥ 1 > z_{T−1} | pass after D18 |
| disabling patterns leaves z, T, R and noise unchanged | identical | identical |
| graded/sparse \|field\| correlation (NASA; MATR/HUST have no sparse set) | ≤ 0.30 | recency 0.074–0.081, uniform −0.030 to −0.004, final position 0.138–0.143 |

Model inputs never receive T or R: the target builder passes windows of x (and, for the transfer target, the elapsed position t) and no other quantity. That is checked structurally at S5/S6, where the input builders live.

## Anomalies

1. **Generated state started above 0 on NASA (z₁ up to 0.087) and HUST (0.040).** The measured `q₁` is a maximum over noisy smoothed capacity and sits above the fitted trend's start. Fixed by **D18**: the generated state is anchored at its own trajectory's early-life reference. T is identical for every θ unit, and the check, left unchanged, now passes.
2. **Plain sparse-set retrieval scores the ground truth itself at chance** (AP 0.064 vs 0.048) because the graded field dominates the capacity channel. Resolved by **D01**: paired scoring on the window and its pattern-free counterpart gives AP 1.000 and falls monotonically under degradation. Paper round 4.
3. **D06 not triggered.** The graded/sparse correlation stays far below the bound under every weighting, so no decay-rate or amplitude change is needed.
4. **Paper Figure 4 carried the obsolete notation** $a_{u,c}$ (missed in the round-1 blast-radius review). It was regenerated with π_u.
5. The MATR generated set's seed-to-seed spread in median T (727–823) reflects resampling 300 units from 90 θ vectors.

## Decisions needed

None for a human. Taken:
- D01 (paper round 4);
- D18;
- D06, checked and not triggered.
