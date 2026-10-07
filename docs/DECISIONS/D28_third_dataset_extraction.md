# D28 — Third profile: ISU-ILCC, aging-cycle positions with RPT-calibrated capacity, the authors' validated cells with mean DoD ≥ 50 %; Tongji ineligible from its documentation

**Stage / claim affected:**
- V2 (brief "DegradX v2", X6);
- declarations r3 `declared_by_design.v2.third_profile.candidate_rules` and the superseded reading
  `readings.X6_ii_regeneration_at_scale`;
- `configs/profiles/isu_ilcc.yaml`;
- the third column of every v2 table;
- the RQ1 claim "the construction holds on a different chemistry and format".

**Timing.** Taken 2026-10-07 from documentation only, **before any measurement file of either candidate was
downloaded**. The documentation consulted:
- figshare and Zenodo API metadata;
- README_V2.0.pdf, process_data.py and Valid_cells.csv;
- the authors' cell list `feature_extraction/valid_cells_paper.csv` (GitHub tingkai-li/early-prediction-varying-usage-data,
  commit 7702efd, SHA-256 0447237d…);
- arXiv:2307.08382 v2 and Zhu et al. 2022;
- BatteryLife's preprocessing code, as a non-binding cross-check only.

**Process.** Four documentation readers, a synthesis, and 12 adversarially verified claims. A first draft of this record
was then attacked from three angles (brief compliance, measurement science, an advocate for the rejected options), and
a judge ruled on each objection. The revisions it required are applied here.

**Decision.** The brief names ISU-ILCC first and asks for a D-record that settles its partial depth-of-discharge risk
before ingestion. The options are (a) the full-DoD subset, (b) RPT capacity as the position axis, or (c) another
declared extraction, with eligibility re-checked under the choice. Tongji is second. Which candidate and which
extraction?

## Facts (documentation, verified)

**ISU-ILCC.**
- **Cells and licence.** 251 released cells of one type: 502030 NMC/graphite Li-polymer, rated 250 mAh, 3.0–4.2 V.
  63 conditions at 30 °C (README_V2.0; Valid_cells.csv). Licence CC BY 4.0.
- **Aging cycles.** Each is a CC-CV charge to 4.2 V, then a CC discharge at the condition's rate to a per-group voltage
  cutoff set for a target DoD. Measured mean DoD runs from 4.16 % to 98.16 % (Table A1).
- **RPTs.** After every 7 days of cycling, plus week 0 (and week 0.5 for G20–G64), an RPT runs one C/5 and one C/2
  full cycle. The authors take full capacity from the C/5 discharge, and EOL is C/5 < 200 mAh (80 % of rated).
- **The authors' list.** 225 cells, all cycled past EOL, with lifetimes of 1.5–60.9 weeks.
- **Known losses.** G20–G29 lost their week-4 RPTs. G25C1 and G26 lost the week-23/24 RPTs and the week-24 cycling.
- **Channels.** Per-cycle Q, V, I, E and t, plus `capacity_discharge` and `capacity_charge`, and charge/discharge step
  start/stop times. Temperature and IR are not released.

**Tongji.** 130 cells in three types: NCA (Samsung INR18650-35E) has 66, NCM (LG INR18650-MJ1) 55, NCM+NCA (Samsung 25R)
9 (Zhu et al. 2022 Table 1; Zenodo 6379165). **No single type reaches the 67 cells E3 requires, so Tongji is
ineligible from its documentation.** This finding entered the v0 commit (`9c25b6c`, r3 `documentation_finding`) from the
documentation sweep, before this record was written. No Tongji data was seen. The r3 note "one cell type meeting
eligibility" is superseded.

## Options

At the scope this record adopts (the authors' validated cells with mean DoD ≥ 50 %, 145 cells) unless the row says
otherwise:

| option | positions / capacity | E1 | E2 | E3 (≥ 67 reach EOL) | E4 (every EOL unit T ≥ 44) | X6 |
|---|---|---|---|---|---|---|
| T. Tongji, one type | cycles / cycler capacity | pass | pass | **fail**: 66 cells at most | — | — |
| (a) ISU full-DoD subset (≥ 95.8 %, all released) | aging cycles / aging capacity | pass | near-full only | **fail**: 56 released (49 validated) | likely | (i) only |
| (b) ISU RPT axis | weekly RPTs / C/5 capacity | pass | pass (strict) | likely | **fail**: T ≈ lifetime in weeks, mostly 6–40 | (ii) void |
| (c-i) C/5 interpolated onto aging cycles | aging cycles / PCHIP of weekly C/5 | pass | declared extraction | 145 documented | likely | see Works |
| (c-ii) DoD-normalised aging capacity (BatteryLife style) | aging cycles / Q_d ÷ Q_ch(cycle 1) | pass | **fail**: partial throughput | — | — | — |
| (c-iii) multiplicative RPT calibration of the measured aging capacity | aging cycles / Q_age(n) × f(n) | pass | declared extraction (verdict below) | 145 documented | likely | see Works |
| (c-iii-add) additive calibration | aging cycles / Q_age(n) + g(n) | pass | declared extraction | 145 | likely | kept as a sensitivity |

**DoD threshold** (authors' validated list; nominal amplification of the calibration = 1 / mean DoD):

| threshold | groups | cells | nominal amplification max | E3 |
|---|---|---|---|---|
| **≥ 50 %** | 38 | **145** | 1.94 | margin 78 |
| ≥ 70 % (= ≥ 75 %) | 22 | 85 | 1.43 | margin 18 |
| ≥ 80 % | 20 | 77 | 1.25 | margin 10 |
| ≥ 90 % | 15 | 57 | 1.09 | fails |
| ≥ 95.8 % | 13 | 49 | 1.04 | fails (option a) |

Selection rule: the loosest threshold whose nominal amplification (1 / Table A1 mean DoD) is at most 2. It is chosen for
the E3 and held-out margin. The group list is fixed from Table A1 of README v2 and never moves with any measured DoD.

## Testing the options

Real: every option is possible.

Works:
- **T, (a) and (b)** fail E3 or E4 on documentation. **(c-ii)** is not a full-capacity measurement.
- **(c-i) against (c-iii), at the same scope.** The deciding argument is X6 question (i).
  - (c-i) makes the capacity channel an interpolant between weekly knots. The generator would then fit near-zero
    capacity innovation.
  - That would flatter the V3–V5 fidelity checks, and it would deepen the capacity dominance of v1 problem (a): the
    capacity channel becomes a near-deterministic function of position.
  - Under (c-i), X6 question (ii) would be a void with a stated reason (the brief admits a profile that answers (i)
    only). It would not be a "no by construction".
  - (c-iii) keeps each aging cycle's measured discharge capacity. Its level equals the C/5 measurement at every anchor.
- **Multiplicative against additive calibration.**
  - Multiplicative is the ratio calibration, about 1 on the full-DoD stratum. It stays primary.
  - Additive avoids scaling within-week deviations by f. It is declared as an audit-level sensitivity.
  - Pattern detection uses a per-unit robust residual scale, so a slowly varying f largely cancels in the D05 outcome.
    The sensitivity checks whether it does.

Clear, (c-iii) in two sentences: "Positions are aging cycles. Each cycle's measured discharge capacity is rescaled to full
capacity by a factor that is smooth over the cycle index and anchored at the weekly C/5 reference tests, in the
authors' validated cells of the 38 conditions whose aging cycles discharge at least half of the cell."

**E2 verdict for (c-iii): pass, under E2's declared-extraction branch.**
1. Every unit has one aging procedure, and one full-capacity procedure (the C/5 RPT, `capacity_discharge_C_5`) sets the
   level.
2. The calibrated capacity equals the C/5 measurement at every anchor.
3. Between anchors it is an estimate whose variation is the measured partial-window aging throughput.

E2 is read as: *a declared extraction may construct per-position values whose level is tied, at anchor positions, to
full-capacity measurements of one procedure.* Under the strict reading — a direct full-capacity measurement at every
position — only (b) passes E2, (b) fails E4, and brief §6 (stop and report) would apply. **This is flagged for the
authors as the V2 decision they may want to override.** Proceeding stays the decision, because brief V2 delegates
"(c) other" to a D-record.

**Departure from the documentation research.** The research synthesis recommended (c-i) or stop. This record departs
from it in two ways:
1. f is smooth (PCHIP over the cycle index), which removes the weekly steps at rest events that the research objected
   to.
2. The DoD scope removes the up-to-24× amplification.
The research's third objection stands: the channel carries two procedures (calibration level and partial-window
variation). It is in the cost line.

**Other verdicts.**
- **E1 pass:** one cell type.
- **E6 pass:** CC BY 4.0 (README_V2.0 §6; api.figshare.com/v2/articles/22582234).
- **E3 and E4:** judged after ingestion under the declared rules. All 145 in-scope cells are documented at C/5 EOL;
  BatteryLife's aging-cycle labels are only a non-binding indication for E4.
- **E5:** judged after ingestion under `E5_operational` on `charge_time_min` and `mean_discharge_voltage_V` from aging
  cycles. Roles are not reassigned.

**Chosen: (c-iii), multiplicative, scope = the authors' `valid_cells_paper.csv` ∩ Table A1 mean DoD ≥ 50 %
(38 groups, 145 cells).**
1. *Logical:*
   - It is the only option meeting E1–E4 on documentation while §3.3's noise and pattern estimation still acts on
     measured residuals.
   - Its level is the authors' full-capacity measurement, and its EOL is their criterion.
   - Restricting to the authors' validated list removes, by a documentation rule, the one group (G11) whose EOL status
     is undocumented. G11 is absent from the paper's Table S1 without a reason and flagged abnormal by BatteryLife.
2. *Consistent:*
   - Positions are cycles, as for MATR and HUST. RPT cycles are never positions.
   - D12/D17/D27 apply unchanged.
   - The non-causal calibration (it uses the next RPT, at most one RPT interval ahead) matches the centred
     Savitzky–Golay and rolling-median rules already declared.
3. *Clear:* two sentences.
4. *Measured:* E3 margin 78; nominal amplification ≤ 1.94 on group means, with per-unit f reported.

## Declared extraction and readings

`declared_by_design.v2.third_profile.candidate_rules`, committed with this record before any download.

- **Cycle predicates.**
  - *Degenerate:* fewer than 10 samples, `capacity_discharge` non-finite, ≤ 0 or an empty list, or a missing charge or
    discharge start time.
  - *Incomplete:* last discharge voltage more than 0.02 V above the unit's median last-discharge voltage, or last
    charge current above 2 × C/20 = 25 mA.
  - *Non-aging:* overlaps an RPT start–stop interval, or its median discharge current departs by more than 10 % from
    the group's discharge C-rate × 0.25 A.
  - Each is masked or excluded and counted. No halt.
- **Order of operations.**
  1. Masks act on the raw aging capacity.
  2. Anchors are taken from unmasked cycles.
  3. f is computed.
  4. Calibrated capacity = raw × f.
  5. D12 runs on the calibrated series; D17/D27 run on the channels.
  D12 mask counts are reported per stratum.
- **Anchors.** For every RPT w with a finite C/5 capacity and at least 5 unmasked aging cycles before its start:
  f_w = C/5 ÷ median raw capacity of the last 5 such cycles, with the knot at the last of them.
  - Plus a **week-0 anchor**: week-0 C/5 ÷ median of the first 5 unmasked aging cycles, knot at the last of those.
  - f is PCHIP over the knots and constant beyond the first and last knot.
  - A unit with fewer than 2 anchors is reported with its C/5 EOL status and aging-cycle count. It counts against E4 if
    it reached EOL with T < 44; it is not silently excluded.
- **Channels.**
  - `charge_time_min` is the charge step duration from `time_series_charge` start/stop.
  - `mean_discharge_voltage_V` is the time-weighted mean voltage over the discharge samples.
  - **charge_time is missing by protocol at every RPT-following rest event**, because that charge starts from the
    RPT's discharged state. Counted separately from the D17/D27 masks. Capacity and mean discharge voltage are kept
    there.
- **Rest events r.**
  1. The first unmasked aging cycle of each Cycling `start_stop_time` block after the first.
  2. The first cycle after a recorded pause: a gap from one cycle's discharge stop to the next cycle's charge start
     exceeding the unit's median gap by more than 30 min.
  - RPT stop times are a cross-check only; mismatches are counted.
  - Position 1 is not a rest event.
  - The G20–G29 week-4 losses are placed from block starts.
  - G25C1's week-23/24 hole: positions are the recorded cycles only, with no imputation. The first cycle after the hole
    is a rest event, and the cell is flagged.
  - Counts are reported by source.
- **Strata.** S_full: Table A1 mean DoD ≥ 95.8 %, 13 groups, 49 cells, all at 0.5C discharge. S_partial: 25 groups, 96
  cells. Reported per stratum beside the pooled value:
  - the D05 rate ratio;
  - the mechanism diagnostic;
  - capacity noise variance and φ, in raw and calibrated units;
  - D12 masks.
- **X6(ii) reading (supersedes `readings.X6_ii_regeneration_at_scale`).** "Present at scale" iff D05 enables the
  positive type on the pooled fitting split **and** on the S_full fitting split, and the operator-null check does not
  reach the enable level. Otherwise X6(ii) is "not shown", and the type is reported as "post-RPT recovery of
  partial-window discharge capacity, not separable from voltage-cutoff kinetics".
- **X6(ii) controls (reported).**
  - The per-RPT recovery index ln(median raw Q over the first 5 cycles after the RPT ÷ median over the last 5 before
    it), regressed on 1 / mean DoD and on the discharge C-rate.
  - The overshoot statistic: median calibrated capacity over r … r + 4 minus the C/5 value of that RPT.
  - The mechanism diagnostic with a placebo window −11 ≤ s − r ≤ −1 beside the declared 0 … 10 window; the
    post-minus-pre contrast is reported.
- **Operator-null check.**
  - For each fitting-split unit, a synthetic raw series = the SG(11,2)-smoothed raw aging capacity plus AR(1) noise at
    the unit's raw-residual variance and φ (seed stream generation/D28-null/<cell>).
  - The identical extraction (measured f_w applied at the same knots), cleaning and D05 detection are run on it.
  - Reported: its positive-run rate relative to the D05 AR(1) reference, and the null mechanism-diagnostic ratio.
  - If the operator alone reaches noise_factor × the reference, X6(ii) is void with that reason.
- **Additive sensitivity.** Q_age(n) + g(n), where g is PCHIP through (C/5 − anchor median). It reports the capacity
  noise variance and φ, the pattern rate and amplitude rows, and the D05 outcome. If the D05 outcome differs from the
  primary, X6(ii) says so. Pattern amplitudes are always reported both calibrated and in raw aging units, with the
  per-unit f (min, p05, median, p95, max).
- **Cross-checks (reported, not gates).**
  - (q₁ − week-0 C/5) / q_nom per unit, and the count above 0.01 (C3's material-difference level), with and without the
    week-0 anchor.
  - EOL agreement: whether T falls in the RPT interval where C/5 first drops below 0.200 Ah, or in the one before.
- **Side table.** The 10 released in-range cells outside the authors' list (G9C3, G11C1–C4, G14C2–C4, G36C1, G37C1)
  are converted and their EOL status and T reported, outside the profile.
- **Nominal capacity:** q_nom = 0.25 Ah (`configs/profiles/isu_ilcc.yaml`; README_V2.0 §3.1; Li et al.).
  ρ·q_nom = 0.200 Ah, the dataset's own EOL. D13's record-end rule applies as for MATR and HUST.
- **After ingestion:** E3, E4 and E5 are re-checked under these rules. Any failure means stop and report (brief §6); no
  candidate remains.

## Cost

- **The capacity channel carries two procedures.**
  - Its level comes from the C/5 RPT, which is a full-capacity measurement at every anchor.
  - Its within-week variation is the aging cycle's partial-window discharge to a mid-state-of-charge voltage cutoff,
    scaled by f. Nominally f ≤ 1.94; per-unit values are reported.
  - That variation includes overpotential and recovery kinetics. A post-RPT "recovery" can therefore be kinetic rather
    than regenerated capacity. Hence the stratified reading, the operator-null check and the recovery-index
    regression.
  - The paper says so in §3.4.
- **Coverage is restricted.** The profile covers 145 of 251 cells, with no condition below 50 % DoD and no cell outside
  the authors' validated list. The paper states both.
- **The E2 reading is a choice.** Under the strict reading, the brief would require stop and report. Flagged for the
  authors.
- **Rules set from documentation.** The 50 % threshold, the 5-cycle anchor, the 0.02 V / 25 mA completeness tolerances
  and the 30 min pause were set before the data were seen. They are declarations, not estimates, and are listed with
  the v2 rules in the Limitations.
- **Data cost.** About 11.2 GB to download (Cycling_json 10.2 GB), ingested one cell at a time.

**Paper impact:** AMENDMENTS round 7 (X6). §3.4 profile roles and the dataset paragraph; Tables 1–6 third column; data
availability (CC BY 4.0; Li et al. and the ISU-ILCC dataset DOI).
