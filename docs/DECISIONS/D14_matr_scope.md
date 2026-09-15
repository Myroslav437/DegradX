# D14 — The MATR profile uses the three batches of Severson et al. 2019

**Stage / claim affected:** the MATR profile's unit count, its channel set, and every MATR row of Tables 1–3. This resolves S0 "Decisions needed" item 3.

**Decision.** BatteryML's MATR bundle holds four batches. The paper cites Severson et al. 2019, whose dataset is the first three batches; the fourth (2019-01-24) is the validation batch of Attia et al. 2020 and is not cited. Which batches form the profile?

**Options considered**
- **a.** All four batches (180 cells).
- **b.** The three Severson batches (135 cells), with unit exclusions only by the benchmark's declared rules (guard, record-end rule, glitch rule).
- **c.** The Severson-124 list: option b plus the 11 cells removed by the Severson notebook as unfinished or "noisy channels".

**Evidence** (`experiments/decisions/D14/{run.py,result.json}` on the S2 audit tables). Real: all three are subsets of one audit.

| | a | b | c |
|---|---|---|---|
| cells / reaching EOL | 180 / 173 | 135 / 128 | 124 / 124 |
| IR available in every cell | **no** (45 cells with IR = 0 in every cycle, all batch 4) | yes | yes |
| temperature available in every cell | yes | yes | yes |
| best in-sample family (rollover / exp2 / power) | 147 / 32 / 1 | 110 / 24 / 1 | 103 / 20 / 1 |
| median residual scale [mAh] | 1.17 | 1.15 | 1.18 |
| median T [cycles] | 771 | 762.5 | 734.5 |
| positive events per 100 cycles | 0.094 | 0.112 | 0.095 |
| distinct charge policies | 79 | 70 | 69 |

Clear, option (b): the MATR profile is the dataset the paper cites, all three of its batches, and units are excluded only by the rules every profile uses. Failure mode: a cell with a documented data-collection problem enters unless a declared rule catches it.

**Chosen: b.**
1. *Logical:* it is the cited dataset, with no exclusions outside the benchmark's own rules. Option c imports a hand-made list, and its "unfinished" cells are already censored by the record-end rule.
2. *Consistent:* paper l.253 says MATR "supplies the reference channel set, recording discharge capacity, internal resistance, charge time, and temperature statistics per cycle". Under option a, IR is missing in a quarter of the cells, so the availability rule would drop IR from the MATR profile.
3. *Clear:* one sentence.
4. *Measured:* audit properties differ little between a and b (residual scale 1.17 vs 1.15 mAh, median T 771 vs 762.5), so dropping batch 4 does not select for an easier profile.

**Cost.**
- 45 cells (25 %) and Attia's nine four-step charging protocols are lost.
- Seven units stay censored (128 of 135 reach EOL).
- The six b3 cells Severson called noisy remain. Their noise enters the profile's noise estimate, and a reviewer familiar with the dataset may ask why. The answer is that no declared rule identifies them.

**Paper impact:** none in the methodology; Results state "135 cells from the three batches of [severson2019]".
