# D03 — NASA PCoE keeps its role as the regeneration profile

**Stage / claim affected:** the S2 decision gate (paper §3.4: "a dataset that does not exhibit the property it was selected for has its role reassigned or is dropped"), the NASA rows of Tables 1–3, and which pattern parameters the benchmark can fit from measurement.

**Decision.** NASA PCoE was included for one property, documented capacity regeneration. Does the audit find it, and with enough events and units to fit a profile?

**Options considered**
- **a. Keep the role:** the NASA profile supplies measured regeneration parameters, and its fidelity rows are reported with its unit count.
- **b. Reassign:** treat NASA's pattern statistics as a source only for the regeneration type in other profiles, with no NASA profile of its own.
- **c. Drop NASA.**
- Substituting CALCE on the grounds of small unit count is excluded by the brief (CALCE was replaced by HUST on correctness grounds).

**Evidence** (S2 audit, declared rule after D12/D13/D15/D16; `artifacts/s2_audit_datasets/tables/{summary.json,units.csv,patterns_default_threshold.csv}`)

| | MATR (135) | HUST (77) | NASA PCoE (34) |
|---|---|---|---|
| positive events (units with ≥ 1) | 124 (62) | 78 (52) | **21 (16)** |
| pooled positive rate per 100 cycles | 0.11 | 0.054 | **1.03** |
| positive amplitude, median [IQR] mAh | 2.95 [1.97, 4.17] | 2.29 [1.78, 2.69] | **74.5 [37.2, 95.2]** |
| amplitude as % of nominal (median) | 0.27 % | 0.21 % | **3.7 %** |
| positive duration, median [max] positions | 3 [11] | 3 [11] | 2 [4] |
| units passing the guard / reaching EOL | 135 / 128 | 77 / 77 | 18 / 11 |

Real: the measurements exist. Works: NASA's positive runs are 25–35× larger relative to nominal capacity, and ~10–20× more frequent, than those in MATR and HUST. They are short (2–4 positions), matching the regeneration regions the rest-time literature describes (3–5 cycles, Qin 2016). MATR/HUST positive runs are at the scale of the residual (a few mAh), consistent with residual misfit and noise rather than documented regeneration.

Clear: "NASA PCoE is the only profile whose positive residual runs are large relative to its noise and capacity; the property it was included for is present in its measured record, measured in events (21), not units."

**Chosen: a. Keep the role.**
1. *Logical:* the property is present on the data, which is the paper's own criterion.
2. *Consistent:* §3.4 already anticipates that NASA's fidelity rows are limited by its unit count. Reassignment (b) would need pattern parameters transplanted across datasets, which §3.3 does not allow ("a type that is not detected in a dataset is not enabled in its profile").
3. *Clear:* no new machinery.
4. *Measured:* see the table.

**Cost.**
- NASA's regeneration statistics rest on 21 events from 16 units (at k = 2.5, m = 2), so their distributions are wide.
- Only 11 units reach EOL and 18 pass the guard. The transfer and distributional measurements will rest on very few held-out units and may be void under D02's minimum counts.
- The paper's statement that the other datasets "lack" regeneration is about documentation. The detector does find small positive runs in MATR and HUST, so those profiles enable the positive type at a few-mAh scale. That is reported, not suppressed.

**Paper impact:** none in the methodology. Results report the audit table, and §4.1 states the event and unit counts behind NASA's rows.
