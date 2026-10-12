# D34 — The TRI formation profile (FORM) is eligible: E1–E6 hold, the offset pre-screen reads 0.12, and D05 enables post-diagnostic regeneration as an inserted pattern type

**Stage / claim affected:**
- W2 (brief "DegradX v2.1");
- declarations r4 `declared_by_design.v2_1.eligibility`, `offset_prescreen`, `weight_guard`, `mechanism_diagnostic` and
  `readings`;
- §3.4 Profiles; the RQ1–RQ3 claims for the third profile; the sparse-set claims (FIX-1).

**Timing.** Taken 2026-10-13 at W2, from `artifacts/v2.1/w2_audit/tables/audit_summary.json`. Every reading below was
declared in r4 before download, except where marked.

**Decision.** Is FORM eligible (E1–E6, the offset pre-screen and the weight guard; brief W2)? If so, which pattern types
does it carry?

## Evidence

| criterion | declared rule | measured | verdict |
|---|---|---|---|
| E1 | one cell type | one build of SC-NMC532/AG pouch cells; only cells the authors document | pass |
| E2 | strict: full-capacity measurement under one procedure at every position | every position is a 3C/4 full-window discharge after a CC-CV charge; modal protocol = documented 0.24 A / 0.18 A / 4.4 V / 3.0 V; incomplete cycles 1 of ≈ 189 000 (W1, with D33) | pass |
| E3 | ≥ 66 units reach EOL after the guard | **182 of 182**: 127 fitting, 55 held out (D02b needs 20) | pass |
| E4 | every unit reaching EOL has T ≥ 44 | min T 463, median 689 (IQR 613–862) | pass |
| E5 | charge time and mean discharge voltage in every unit; \|φ(1) − φ(0)\| ≥ post-offset noise SD | charge time: 2.91 min against SD 0.875 min (ratio **3.33**); mean discharge voltage: 41.7 mV against SD 7.1 mV (ratio **5.86**); none demoted | pass |
| E6 | licence permits releasing fitted parameters | CC BY-NC 4.0: non-commercial release with attribution | pass, with the NC condition |
| offset pre-screen | Var(y_offset)/Var(y) ≤ 0.5 on measured windows (V4's estimator) | **0.120** (recency), **0.125** (uniform); 127 units, 91 992 windows | pass |

**The pre-screen in detail.** Reported, never gated:
- **Per-channel shares.** The offset part of charge time carries 0.49 of Var(y) and that of mean discharge voltage 0.43.
  They covary negatively, so the total is 0.12. A cell that charges longer also discharges at a lower voltage, and both
  weights are negative. Capacity's part is 0.002.
- **Influence.** Without the five tagged cells (shorted, bulged, formation stopped) the share is 0.121. The largest
  leave-one-unit-out change is 0.004 (TRI_317 under recency, TRI_291 under uniform). The level outlier TRI_270 (about
  3.61 V, 80 min) moves it less than that.
- **Offset sampling noise.** It is small against the offset variance: charge time 0.064 against 1.50 min², mean discharge
  voltage 6.4e-6 against 2.6e-4 V².
- **Formation protocol.**
  - The one-way R² of the unit-mean offset term on the 61 protocols represented is 0.689, against a permutation null of
    0.476 (10 000 permutations; p = 0.0003). The calibrated share is 0.41, so the reading is "formation protocol explains
    part of the offsets".
  - By channel: q₁ calibrated 0.41 (p = 0.0002), charge-time offset 0.24 (p = 0.057), voltage offset 0.16 (p = 0.15).
  - Formation conditions set the cells' early capacity. This is the manufacturing variation the profile is meant to carry;
    it is reported, not gated.

**Patterns (D05, fitting split, declared k 2.5 / m 2 / maximum duration 11).**
- The positive type is **enabled**: 312 runs, rate 0.33 per 100 positions, against 0.145 on the profile's AR(1)
  capacity noise. The ratio is **2.28** against a factor of 2.
- The negative type is not enabled (ratio 0.96).
- Fitted positive patterns: amplitude median 2.7 mAh (5–95 %: 1.3–6.0 mAh); duration median 4 positions (at most 11);
  105 of 127 fitting units carry at least one.
- The detection sweep and the per-unit rates are in `tables/audit_units`.

**Mechanism diagnostic (fitting units, window 0–10).**
- **All rest events.** Ratio **4.57 [3.99, 5.18]** (183 of 312 runs start within 10 positions after a rest event); the
  placebo window −11 to −1 gives 0.98 [0.63, 1.34].
- **Diagnostic blocks alone.** 4.66 [4.08, 5.27]; placebo 0.49.
- **Rests without a diagnostic** (41 pauses and gaps). 2.04 [0, 4.51].
- **Sensitivities.**
  - With DST artefacts included: 4.42 overall.
  - On all 182 guard-passing units: 4.73 [4.25, 5.21], placebo 1.00.

## Readings (declared in r4)

- **X6(ii) regeneration.** "present at scale" (D05 enables the positive type). It is "rest-induced": the pooled interval
  lies above 1 and the placebo interval includes 1.
- **Separability: branch (iii).**
  - There are at least 10 rests without a rate change (41), and their interval includes 1. So rests without a rate change
    are not followed by clustered positive runs.
  - The clustering after diagnostic blocks is attributed to the block: its lower-rate or held discharge and its rests.
    It is not attributed to rest alone.
  - **Post-hoc sensitivity, not declared** (`tables/mechanism_posthoc.json`, `scripts/v2_1/w2_mechanism_posthoc.py`).
    Most gap events sit one position after a diagnostic event. The first aging cycle after a block charges from the
    RPT's deep discharge, lasts longer, and the declared gap rule reads the next interval as a pause.
    - Restricted to the 33 rests without a diagnostic event in the 11 preceding positions, the ratio is 2.54 [0, 5.78],
      the same branch.
    - Their placebo is high (15.8), so runs tend to precede, not follow, these interruptions. This is reported and not
      interpreted further.
- **D05 governance.** W3 must reproduce the enabled positive type. Inserted patterns are generated at the fitted rate and
  amplitude, with no inflation (D21).

## Options

- (a) **Eligible**: proceed to W3–W8 with the positive pattern type enabled.
- (b) Stop and report: no declared rule fails.
- (c) Eligible without patterns: contradicts the D05 rule and r4's D05 governance.

**Chosen: (a).**
1. *Logical:* every declared criterion and the pre-screen hold.
2. *Consistent:* the same D05 rule enabled NASA PCoE's positive type in v1; MATR, HUST and ISU-ILCC were not enabled.
3. *Clear:* "FORM meets every eligibility criterion, its offsets carry 12 % of the target's variance, and its capacity
   shows recovery after diagnostic blocks often enough to be inserted as a pattern type."
4. *Measured:* the table above.

## Cost

- **What the inserted patterns mean.** They are post-diagnostic recovery: capacity recovered after a block that both
  rests the cell and discharges it at a lower rate. They are not shown to be regeneration by rest alone, so the paper
  names them "recovery after a diagnostic block".
- **Pattern paths run for the first time.** FORM is the first evaluated v2 profile with inserted patterns, so the
  following go live: pattern insertion at V4, the variance ratio, term ablation and graded/sparse correlation at V6,
  paired retrieval at V7, and paired TimeSHAP maps at W8 (4 680 explanations).
- **Formation protocol explains part of the offsets.** About 0.41 of the unit-mean offset variance (calibrated), mostly
  through q₁. The share of the target is 0.12, far below the 0.5 bound.
- **Post-data rules.** W1's D33 and the post-hoc mechanism sensitivity are post-data, and are listed as such.

**Paper impact:** AMENDMENTS round 8:
- §3.4 Profiles: FORM, its eligibility and its pattern type;
- §1 and the FIX-1 span: sparse-set claims now apply to one profile;
- §4: the FORM column of every table;
- the Notes box.
