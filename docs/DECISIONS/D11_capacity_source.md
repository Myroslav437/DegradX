# D11 — The capacity channel is the cycler-reported per-cycle discharge capacity

**Stage / claim affected:** S1 data layer → every later stage. The capacity channel defines the degradation state
(Eq. 3), EOL `T`, the transfer target `R`, the trajectory fits and the pattern residuals.

**Decision.** declarations r2 `channels.candidates.capacity` says "max discharge capacity of the cycle [Ah]" without
naming a source. BatteryML stores a cumulative `discharge_capacity_in_Ah` series per cycle; for HUST it recomputes it
by rectangle integration of I·dt, and the NASA converter does the same. Each dataset also records the cycler's own
per-cycle capacity (MATR `summary.QDischarge`, HUST `dq`, NASA `Capacity`), attached at S1 as `capacity_cycler_Ah`.
Which one is the capacity channel?

**Options considered**
1. *No change in wording, integrated source:* `max(discharge_capacity_in_Ah)` from BatteryML objects.
2. *Cycler-reported capacity* where the dataset records one (all three do).

**Evidence** (`experiments/decisions/D11/`, `artifacts/s1_fetch_data/figures/capacity_integrated_vs_cycler.png`,
`artifacts/s1_fetch_data/tables/summary.json`)

| | option 1 (integrated) | option 2 (cycler) |
|---|---|---|
| Real | runs on all 291 units | runs on all 291 units; attached with 0 missing cycles |
| MATR integrated − cycler | 0.0 mAh at the 1st, 50th and 99th percentile: identical | — |
| HUST integrated − cycler | median +18.3 mAh (p05 +13.7, p95 +24.4) | — |
| NASA integrated − cycler | median +27.7 mAh (p05 +3.4, p95 +333) | — |
| HUST units reaching EOL under the record-end rule of D13 | **1 / 77** | **77 / 77** |
| MATR units reaching EOL (D13 rule) | 173 / 180 | 173 / 180 |
| NASA units reaching EOL (D13 rule) | 15 / 33 | 12 / 33 |
| MATR first raw crossing of 0.88 Ah vs file `cycle_life` | median \|Δ\| 1 cycle (88 comparable) | identical |

Clear: option 2 reads, "capacity is the per-cycle discharge capacity the cycler reports, the quantity each dataset's
stopping rule is stated on". Its failure mode is a cycler that reports capacity differently from the integral of its
own current; that difference is reported (figure above), not hidden.

**Chosen: option 2.**
1. *Logical:* every dataset's EOL convention (Severson 2019 and the loader's 0.88 Ah threshold; Ma 2022 "until the
   maximum capacity first reached 80% of nominal"; NASA READMEs "from 2 Ahr to 1.4 Ahr") is stated on the capacity
   the cycler reports; Eq. 3 as amended by C3 takes ρ against those conventions, so it must read the same quantity.
2. *Consistent:* with option 1 the HUST record ends ~18 mAh above the threshold for every cell, so HUST would lose its
   transfer measurement for a reason that is an integration artefact (BatteryML's rectangle rule on 5-s samples), not a
   property of the cells.
3. *Clear:* one sentence; no new parameter.
4. *Measured:* MATR is unaffected (sources identical); HUST attainment 77 vs 1; NASA's integrated series carries
   artefacts up to +333 mAh at p95 (integration over the concatenated charge + discharge record).

**Cost.** The channel is no longer computed from the `BatteryData` sample series alone for HUST and NASA; it comes
from a scalar each dataset stores (kept in `CycleData.additional_data`, so R3 still holds). A reviewer could ask why
three +3 NASA units that reach EOL under integration do not under the cycler value; those three rely on integration
artefacts (p95 offset +333 mAh). The integrated series stays available in the cycle tables for comparison.

**Paper impact:** none (the paper says "capacity channel"; the declaration of its derivation is refined in
`docs/DEVIATIONS.md` as a tooling/data-layer entry).
