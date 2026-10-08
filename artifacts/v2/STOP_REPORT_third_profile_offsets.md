# Stop and report (brief §6): X2's offset contribution exceeds half of Var(y) on the third profile (ISU-ILCC)

**Status:** the third profile is **parked, pending the authors' decision**. MATR and HUST are unaffected (offset share
0.10–0.12 and 0.31–0.35, both weightings) and continue through V5–V8, as brief §5 prioritises. Nothing has been decided alone.

**Raised:** 2026-10-07, at V4 for ISU-ILCC, by the declared rule `declared_by_design.v2.per_unit_offsets.stop_rule`.

## State

- **Eligibility.** ISU-ILCC passed under D28: E3 145 units reaching EOL, E4 minimum T 265, E5 pass.
- **V3 refit.** All 32 checks pass (backfit converges in 7–8 iterations).
- **V4 generation.** Construction checks pass: Σϕ* = y, g(x) − y = Σwε, pristine y = 0, X3 construction 0.019.
- **The stop rule fails** in every seed and weighting:

| generation seed | Var(y_offset) / Var(y), recency (uniform) | Var(y_offset) / Var(y_state) |
|---|---|---|
| 0 | **0.773** (0.772) | 2.84 |
| 1 | **0.765** (0.764) | 3.16 |
| 2 | **0.823** (0.823) | 3.47 |

**Where the offset term comes from** (generation seed 0, recency):

| channel | Var(offset part) / Var(y) | offsets explained by the test condition (group) | within-condition offset variance |
|---|---|---|---|
| charge time | 0.50 | **99.2 %** (Var δ 405.6 min²) | 3.4 min² |
| mean discharge voltage | 0.58 | **97.6 %** (Var δ 4.6e-3 V²) | 1.1e-4 V² |
| capacity (q₁) | 0.002 | — | — |

(The two channel parts covary negatively, so they do not add up.)

- **What the offsets are.** ISU-ILCC's 38 conditions differ in charge rate (0.5–2.4C), discharge rate (0.5–2.475C)
  and depth of discharge (51–98 %). So the level of charge time and mean discharge voltage is set almost entirely by the
  test protocol: offsets of −24 to +80 min (fitting units; corrected 2026-10-08 from "−25 to +78") against a degradation range of the charge-time mapping of 14.6 min.
- **What the target becomes.** β = 1/3 on each of those channels (a fixed value of the brief) converts the protocol
  into about 76–82 % of the target's variance. **The target would mostly encode which test condition a cell ran
  under**, which is exactly what the stop rule guards against.
- **The same mechanism on the other profiles is small.** MATR's charging policies vary within one protocol family,
  giving an offset share of 0.10–0.12. HUST has one protocol and gives 0.31–0.35.

Also measured: generated q₁ spread 11.0–13.7 mAh against 2.7 mAh measured (fitting units reaching EOL). The power-law
trajectories extrapolated back to the first position vary more than the cells' measured early-life references. This is
reported, not a stop case.

## Options

| | option | what it costs | within the brief? |
|---|---|---|---|
| **A** | **Report ISU-ILCC as the X6 outcome and continue v2 with two profiles (MATR, HUST).** Eligibility, the D28 extraction, the regeneration finding (not shown at scale; kinetic post-RPT recovery confounded by the extraction) and this stop are reported. X6(i) is answered: the construction with per-unit offsets does not hold on a multi-protocol dataset, because the target then mostly encodes the test condition. | No third chemistry or format in the v2 tables; the benchmark's measured profiles stay LFP/18650 only. | **Yes**: the profile's role is reported, and the brief's §5 cut order already lists the third profile last. |
| B | **Condition-level mappings** for ISU-ILCC: φ_{c,g}(z) per test condition g, with offsets only within a condition, and the reference point x⁰ per condition. | A methodological change the brief does not list. The reference model needs the condition (a non-window input), or the target's reference point varies by unit. It changes Eq. 2/4 for one profile. | No (§6: "a methodological change not listed") |
| C | Restrict ISU-ILCC to a protocol-homogeneous subset. | No such subset meets E3: each condition has ≤ 4 cells, and no shared protocol spans 67. | Infeasible |
| D | Use the v1 shared mappings (no offsets) for ISU-ILCC only. | X2 becomes inconsistent across profiles. The generator then reproduces none of the protocol spread (between-cell charge-time variance 377 min² measured, about 0 generated), so the fidelity checks fail on construction. | Contradicts X2 |
| E | Lower β on the non-capacity channels for ISU-ILCC. | β = 1/3 is a fixed value of the brief (§2). | No |
| F | Proceed as is and report the share. | The stop rule exists to prevent this. | No |

## Recommendation

**Option A.**
- The offsets are protocol identity, so no estimation choice inside X2 can fix them: 99 % of their variance is
  between conditions.
- Option B is the scientifically interesting fix, but it changes the model. It belongs to the authors (or to future
  work), not to this run.
- Option A also gives X6(i) an informative answer: a calibrated benchmark with per-unit offsets needs either a single
  protocol family or protocol-conditional mappings.

## What happens while this waits

- **MATR and HUST continue through V5–V8**, then V9 (HUST) and V10, as brief §5 orders.
- **ISU-ILCC V5–V8 are not run.** Its V2, V3 and V4 outputs are committed for the record.
- **If the authors choose A**, the paper sync reports ISU-ILCC in §3.4 and §4 as above.
- **If they choose B**, it is declared as a new D-record, and V3–V8 for ISU-ILCC run afterwards. About 6–8 h of
  compute, mostly V8 TimeSHAP (≈ 3 000 explanations).
