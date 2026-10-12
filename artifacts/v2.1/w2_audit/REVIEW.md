# W2 — audit, offset pre-screen and eligibility of FORM (brief "DegradX v2.1", 2026-10-13)

## What ran

- **Script.** `scripts/v2_1/w2_audit.py` on the W1 cycle table (182 cells), CPU, 236 s. It ran the following:
  - the S2-style audit per unit (`audit_unit`);
  - the three EOL readings;
  - the declared split and the X2 backfit fit on the fitting split (as V3 runs it);
  - E3–E5;
  - D05;
  - the mechanism diagnostic, with run starts placed correctly (T7);
  - the offset pre-screen: V4's `offset_terms` on the fitted mean components of the measured units.
- **Post-hoc addition.** `scripts/v2_1/w2_mechanism_posthoc.py` is a sensitivity that was not declared (see below).

## Results

| quantity | value |
|---|---|
| units / passing the guard / too short | 182 / 182 / 0 |
| EOL, primary (ρ q_nom = 0.192 Ah, D13, D15) | 182 reach; T median 689, IQR 613–862, min 463, max 1 295; none by the record-end clause |
| EOL, the paper's wording with "initial" read as q₁ (DegradX's reading) | 182 reach; T 16 positions earlier (median; IQR 10–24) |
| EOL, the authors' code rule (80 % of max, last cycle_index at or above) | 182 cells have a life; median cycle_index 699.5 (Rhyu et al. used 178 cells) |
| attainment over the ρ grid 0.70–0.90, both definitions | 182 at every ρ |
| q₁ materially different from the first position | 0 units |
| monotone within 1 % of q₁ | 58 of 182 (post-diagnostic recoveries) |
| family selected (5 % margin, identifiability) | two-term exponential (median CV-RMSE 0.0105, against 0.0136 for the power law; rollover ineligible, 61 % of units at a bound) |
| split | 127 fitting, 55 held out, all reaching EOL |
| E5 weight guard | charge time 2.91 min against SD 0.875 (3.33); mean discharge voltage 41.7 mV against SD 7.1 mV (5.86) |
| D05 | positive enabled (ratio 2.28, 312 runs, amplitude median 2.7 mAh, duration median 4); negative not enabled (0.96) |
| mechanism (all rests, 0–10) | 4.57 [3.99, 5.18]; placebo 0.98 [0.63, 1.34] |
| separability | branch (iii): 41 rests without a rate change, ratio 2.04 [0, 4.51] |
| offset pre-screen | **0.120** (recency) / **0.125** (uniform); stop at 0.5 |
| formation-protocol share of the unit-mean offset term | R² 0.689 against a null of 0.476, p = 0.0003; calibrated share 0.41 |

**Decision D34: FORM is eligible, and the positive pattern type is enabled.** The full readings, the influence rows and
the formation shares are in the D-record and `tables/audit_summary.json`.

## Post-hoc sensitivity (not declared)

- **The issue.** The gap events of the declared rule mostly sit one position after a diagnostic event: 112 gap events,
  median distance 1. The first aging cycle after a block charges from the RPT's deep discharge and lasts longer, so the
  next interval reads as a pause. These events echo the block, which inflates the placebo window of the rests without a
  diagnostic (14.3).
- **The sensitivity.** Restricted to rests with no diagnostic event in the 11 preceding positions (33 events), the
  post-window ratio is 2.54 [0, 5.78]: the same branch. The declared reading stands, and the sensitivity is reported beside
  it.

## Checks

E3, E4, E5 and the pre-screen pass (`logs/checks.md`).

## Decisions

- D34 (W2): eligibility and pattern type.

## Next

W3: refit as V3, with the same split and the X2/X3 profile. The enabled positive type must be reproduced (D05
governance).
