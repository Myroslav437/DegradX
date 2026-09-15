# D12 — Single-cycle glitches and recovered collapses are removed before smoothing and fitting

**Stage / claim affected:** S2 audit and S3 fitting. It governs which stored cycles enter the capacity series. That series sets `q₁`, `T`, the family fits, the residual scale and pattern detection. Monotonicity (Table 2 audit) and pattern counts depend on it.

**Decision.** S1 found single-cycle capacity readings that no degradation process produces:
- MATR b1c18 reads 2.88 Ah on a 1.1 Ah cell;
- MATR b1c0 reads 1.54 Ah at cycle 11;
- MATR b2 cells show one-cycle dips of −105 to −140 mAh near cycle 250;
- NASA has 8 V spikes, NaN samples, and near-zero discharges followed by a return to normal capacity.

Should the capacity series exclude such readings, and by which rule?

**Options considered** (all drop degenerate cycles: fewer than 10 samples or no capacity value)
- **none:** no further rule.
- **iso05:** drop a single position whose capacity deviates by more than 5 % of nominal from the centred 11-position rolling median while neither neighbour does.
- **iso10:** the same at 10 %.
- **iso05_rc:** iso05, plus drop readings below 50 % of nominal that the record later recovers from (a later reading ≥ 80 % of nominal).

**Evidence** (`experiments/decisions/D12/{run.py,result.json,per_unit.csv}`; D15 harness for the T = 1 cases). All four options are Real.

| | none | iso05 | iso10 | iso05_rc |
|---|---|---|---|---|
| MATR cycles dropped (units) | 0 | 20 (18) | 14 (13) | 20 (18) |
| MATR units monotone within 1 % | 0.894 | 0.983 | 0.950 | 0.983 |
| MATR positive / negative events (k=2.5, m=2) | 120 / 316 | 112 / 322 | 114 / 323 | 112 / 322 |
| MATR units whose q₁ moves > 1 % q_nom vs none | — | 1 | 1 | 1 |
| HUST | no change under any option | | | |
| NASA cycles dropped incl. 39 degenerate (units affected) | 39 (8) | 89 (25) | 80 (22) | 117 (26) |
| NASA units with T ≤ 3 set by an anomalous early reading | 4 (B0036, B0042–44) | 3 (B0038–40) | 3 | 1 (B0038; fixed by D15) |
| NASA core cells B0005/6/7/18 positive events | 4 | 4 | 4 | 4 |
| NASA median residual scale [mAh] | 17.6 | 14.5 | 16.3 | 14.5 |

Clear, iso05_rc in two sentences:
1. A reading that differs from its neighbourhood by more than 5 % of nominal capacity at a single position is a measurement glitch. A single position is below the minimum run length, so the detection rule could never call it a pattern.
2. A reading below half of nominal capacity that the record later recovers from is a failed measurement, since cell capacity does not recover by 30 % of nominal.

Failure modes:
- a genuine one-cycle regeneration peak larger than 5 % of nominal (110 mAh MATR/HUST, 200 mAh NASA) would be removed;
- a genuine collapse followed by recovery would be removed.

The NASA core cells lose no detected event under any option.

**Chosen: iso05_rc.**
1. *Logical:* both clauses follow from definitions already in the benchmark. The minimum run length makes single positions outliers, not patterns. Capacity cannot recover from below 50 % to above 80 % of nominal.
2. *Consistent:*
   - Without the collapse clause, NASA units get EOL at position 1–3 from failed early readings. That contradicts Eq. 3's reading of `T` as a consequence of the trajectory.
   - Without the isolated clause, one reading sets `q₁` (MATR b1c0) and breaks monotonicity in 16 MATR units.
3. *Clear:* two sentences and two declared constants (5 %, 50 %). The 80 % recovery level is the declared ρ.
4. *Measured:* MATR monotone fraction 0.89 → 0.98. NASA residual scale 17.6 → 14.5 mAh. Core regeneration events unchanged.

iso05 and iso05_rc are identical on MATR and HUST. The collapse clause changes only NASA, where it is needed for the T = 1 cases.

**Cost.**
- Positions are re-indexed over kept cycles, so a unit's position `t` can differ from its cycle count by the dropped cycles: at most 20 of 154,231 MATR cycles, and 117 of 2,794 NASA discharges (39 of them degenerate).
- One-cycle chamber dips in MATR b2 are removed, not modelled as negative patterns. They could not be patterns under m = 2 anyway, but a reviewer could argue they are real measurement-condition effects.

**Paper impact:** §3.3 step one, one sentence (round-2 amendment); §3.3 declared list, one item.
