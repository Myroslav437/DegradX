# Stage 2 — Dataset property audit (paper §3.4)

## What ran

- Command: `python scripts/s2_audit_datasets.py --workers 12`, CPU.
- Config: `configs/stages/s2_audit_datasets.yaml`, which mirrors D11/D12. Declarations: r2 plus the dated D11–D16 entries.
- Deterministic: the family multistart is a fixed grid. Wall-clock ≈ 2 min per run (`logs/timing.json`).
- Decision harnesses run during this stage, each under `experiments/decisions/`:
  - D11: capacity source;
  - D12: glitch rule;
  - D13: truncated records;
  - D14: MATR scope;
  - D15: EOL search start;
  - D16: detection residual.

## What came out

Scope after decisions:
- MATR: 135 cells from the three Severson batches (D14).
- HUST: 77 cells.
- NASA PCoE: 34 cells, of which 32 are long enough after cleaning.

| figure | what to look for |
|---|---|
| `figures/eol_attainment.png` | Fraction reaching EOL per ρ under r2 (nominal-anchored) and r1 (first-position). At ρ = 0.80, MATR reaches 0.95 under r2 against 0.34 under r1, which is C3's motivation, now measured. HUST is 1.0 at ρ ≥ 0.80 and 0 below, because the records end at 0.88 Ah. NASA decreases with ρ because the guard excludes more units. |
| `figures/monotonicity_histogram.png` | Largest rise above the running minimum as % of q₁. MATR 97.8 % of units within 1 %, HUST 54.5 % (early rise up to 19.6 mAh), NASA 34 %. |
| `figures/length_distribution.png` | Kept cycles and T. MATR T median 762.5 [498, 1002]; HUST T = record length, median 1873; NASA T median 45 over the 11 reaching units. |
| `figures/regeneration_distributions.png` | Positive-event rate per unit, signed amplitudes, durations at k = 2.5, m = 2. NASA's positive amplitudes (median 74.5 mAh) sit far from MATR's (2.95 mAh) and HUST's (2.29 mAh). |
| `figures/residual_traces_with_threshold.png` | Residual traces for two units per dataset (the one with most positive events and the median-length unit) with ±k·s and detected runs. Shows what the detector responds to, including the HUST 7-5 case below. |
| `figures/detection_sweep.png` | Event rates over k ∈ {2, 2.5, 3, 3.5, 4} × m ∈ {2, 3}; decision D05 reads this at S3. |

Headline numbers (`tables/summary.json`, `tables/eol_attainment.csv`, `tables/detection_sweep.csv`, `tables/units.csv`, `tables/patterns_default_threshold.csv`):

| property | MATR | HUST | NASA PCoE |
|---|---|---|---|
| units audited | 135 | 77 | 32 (2 too short after cleaning) |
| cycles removed by the glitch rule (units) | 15 (15) | 0 | 117 incl. 39 degenerate (26) |
| excluded by denominator guard | 0 | 0 | 14 |
| reach EOL (ρ = 0.80, r2) | 128 | 77 | 11 |
| reach EOL via the record-end rule (subset of the above) | see `units.csv` (`T_from_record_end`) | all 77 | 0 |
| monotone within 1 % of q₁ | 132 / 135 | 42 / 77 | 11 / 32 |
| q₁ differs materially (> 1 % q_nom) from first position | 0 / 135 | 35 / 77 | 4 / 32 |
| q₁ − first-position value, median [max] mAh | 3.7 [7.6] | 0.0 [19.6] | 0.0 [757] |
| channels available in every unit | capacity, charge time, mean discharge V, IR, temperature | capacity, charge time, mean discharge V | capacity, charge time, mean discharge V, temperature |
| best in-sample family (per unit) | rollover 110, exp2 24, power 1 | rollover 77 | rollover 26, exp2 4, power 2 |
| residual scale, median mAh | 1.15 | 0.86 | 13.3 |
| positive events (units) / pooled rate per 100 cycles | 124 (62) / 0.11 | 78 (52) / 0.054 | 21 (16) / 1.03 |
| positive amplitude median [IQR] mAh; duration median | 2.95 [1.97, 4.17]; 3 | 2.29 [1.78, 2.69]; 3 | 74.5 [37.2, 95.2]; 2 |
| negative events (units); amplitude median mAh | 179 (79); −3.79 | 196 (27); −1.80 | 3 (3); −36.3 |

Decision gate (paper §3.4): NASA PCoE exhibits the property it was included for (**D03: role kept**). MATR and HUST also show short positive runs, but at the scale of their residual, a few mAh.

## Checks

18 pass, 0 warnings (`tables/checks.csv`).
- Every unit audited; family fits finite.
- T ≥ t₁ for every unit reaching EOL.
- Record-end T equals the last kept position.
- Every detected pattern lies inside [t₁, T].
- Pattern durations lie within [2, 11].

The first version of this stage had a vacuous check ("T equals first crossing — by construction"); it was replaced by the checks above before the stage was committed.

## Anomalies

1. **Records truncated at the stopping threshold** (HUST, MATR b1/b3): strict attainment was noise-driven. Resolved by D13.
2. **Residual misfit dominated the declared detector on MATR/HUST.** The early rise gave −20 mAh runs, and slow oscillations gave runs of up to 120 positions. Resolved by D16. **Remaining failure mode:** a slow misfit that hovers at the threshold splits into several short runs, each within the limit. HUST 7-5 shows 18 negative runs along one dip, and HUST's 196 negative events sit in only 27 units. S3's sweep (D05) and the property table will show how much this contributes.
3. **NASA quality varies by experiment group.**
   - 14 units fail the guard because their early-life capacity is within 5 % of nominal of 1.6 Ah (the 4 °C and 43 °C groups).
   - Two negative events of −1059 and −548 mAh come from failing cells that stay below 0.8 q_nom after a collapse, so the recovered-collapse rule does not remove them. They pass the guard and are censored, so they contribute to pattern statistics but not to T.
   - Carried to S3 as D02 (which uses censored and guard-passing units feed).
4. **HUST monotonicity (55 %)** reflects an early capacity rise of up to 19.6 mAh within the first ~50 cycles, above the 1 % tolerance (11 mAh). It is a property of the data, not an error.
5. **MATR b2 one-cycle chamber dips** (−105 to −140 mAh near cycle 250) are removed by the glitch rule rather than modelled (D12 cost line).

## Decisions needed

None for a human. Taken at this stage:
- D12 glitch rule;
- D13 truncated records;
- D14 MATR scope;
- D15 EOL search start;
- D16 detection residual;
- D03 NASA role.

The methodology-changing ones are in the paper (round 2, `artifacts/amendments/latexdiff_round2.pdf`). Carried to S3: D02 (censored units, minimum counts), D04 (family margin), D05 (detection threshold).
