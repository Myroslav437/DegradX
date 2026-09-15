# Stage 1 — Data acquisition

## What ran

- Command: `python scripts/s1_fetch_data.py --device cpu --workers 4`. No random numbers are drawn at S1.
- Config: `configs/stages/s1_fetch_data.yaml` (empty; nothing declared here).
- Declarations: r2 (`declarations-frozen-r2`).
- Provenance: `logs/run.json`, `logs/timing.json`.
- Wall clock:
  - `timing.json` covers only the last, cached rerun (26 s).
  - First full ingestion, from the per-batch logs in `data/work/matr_b*_log.json`: MATR b2 85 s, b1 143 s, b3 176 s, b4 125 s, each in its own process. HUST BatteryML CLI ~80 s plus capacity attachment ~3 min. NASA converter 8 s. Cycle tables ~4 min.
- Raw files were verified against published or recorded size and SHA-256, and the hashes are committed in `configs/raw_checksums.sha256`. The first verification computed all six hashes; later runs reuse the recorded hash for a file of the same size (`--rehash` recomputes).

## What came out

| figure | what to look for |
|---|---|
| `figures/capacity_trajectories_raw.png` | Per-cycle cycler capacity of every unit. HUST and MATR b1/b3 records end at 0.88 Ah, the stopping rule. MATR shows single-cycle spikes (axis cut at 1.4×nominal) and a shared dip in b2 near cycle 250. NASA's 4 °C groups are dominated by near-zero discharges. |
| `figures/cycles_per_unit.png` | Stored cycles per unit: MATR 169–2236 (median 829), HUST 1142–2689 (median 1873), NASA 25–197 (median 69.5). |
| `figures/channel_availability.png` | Fraction of units where each candidate channel is non-missing. IR is present only in MATR, and temperature only in MATR and NASA. The figure shows MATR IR as "available", but it is **zero in every cycle of b4** (see Anomalies). |
| `figures/capacity_integrated_vs_cycler.png` | Integrated I·dt capacity minus cycler capacity: MATR identical, HUST +18 mAh, NASA +28 mAh with a long tail. This is the evidence for D11. |
| `figures/nasa_converter_vs_raw_B0005.png` | Converted NASA B0005 against its raw `.mat`: V/I/T of the first discharge and the capacity trajectory overlap exactly. |

Tables:
- `tables/raw_files.csv`, `tables/summary.json`, `tables/channel_availability.csv`, `tables/checks.csv`.
- Per-cycle data in `data/processed/cycle_tables/<dataset>.csv.gz` (not committed; reproduced by this script).

Units ingested, none dropped at S1:
- MATR: 180 cells, 154,231 cycles.
- HUST: 77 cells, 146,120 cycles.
- NASA PCoE: 34 cells, 2,794 discharges, 39 of them degenerate (fewer than 10 samples or an empty `Capacity`).

## Checks

59 pass, 5 warnings, 0 failures (`tables/checks.csv`). Summary:

| check | expected | observed | result |
|---|---|---|---|
| raw sizes and SHA-256 (6 files) | match published/recorded | match | pass |
| unique cell ids across datasets | unique | 291 unique | pass |
| cycle_number strictly increasing per cell (3 datasets) | yes | yes | pass |
| MATR cells per batch | 46 / 43 (48 minus 5 carry-overs) / 46 / 45 | same | pass |
| MATR stored + dropped + skipped index 0 = file cycle entries, per batch | 42,204 / 21,527 / 51,007 / 39,673 | same | pass |
| MATR merged b1c0..4 entries | 1851 / 2159 / 2236 / 1433 / 1708 | same | pass |
| HUST cells = ESI Table S1 channels; per-cell cycles = Table S1 cycle life (7-5 minus 2) | 0 mismatches | 0 | pass |
| HUST total cycles | 146,120 | 146,120 | pass |
| NASA: 34 cells; one cycle per discharge (vs the S0 file scan) | 0 mismatches | 0 | pass |
| NASA BatteryData vs BatteryML MATR/HUST objects (fields, types, ordering) | superset, list[float], 1..N | yes | pass |
| NASA B0005 converted V/I/T vs raw arrays; capacity vs raw `Capacity` | identical | max diff 0.0 | pass |
| units plausible (median cycle inside range and ≥ 99% of cycles) for V, \|I\| ≤ 10 C, capacity, T | per dataset | all pass | pass |
| median cycle duration in documented range | MATR 1800–7200 s; HUST 1800–14400 s; NASA 3600–86400 s | 2721 / 3175 / 14190 s | pass |
| every finite cycle inside physical range | all | MATR: 12 V-cycles in 1 cell, 3 current, 1 capacity (2.88 Ah); NASA: 17 V-cycles in 5 cells, 12 cycles with NaN samples | warn |
| time non-decreasing within cycles | 0 negative steps | MATR max fraction 1.5e-3 per cycle | warn |

**Revisions to the unit check made during this stage.** Recorded because the thresholds were set after seeing data.
1. First version: every non-degenerate cycle inside the physical range. It failed on MATR and NASA because of isolated glitch cycles (a 2.88 Ah capacity, 8.4 V spikes, NaN samples); medians and unit scales were correct.
2. Second version: ≥ 99.9% of cycles inside the range. It still failed on NASA, where a NaN sample makes a comparison false and some 4 °C discharges fall below 1.5 V.
3. Final version: the error-level check requires the median cycle inside the range and ≥ 99% of finite cycles. The strict every-cycle version is kept as a reported warning with counts, which S2 uses.

Rationale: a unit error (minutes stored as seconds, mA as A) moves the whole distribution; a glitch does not. The final check still caught the one real unit error found at S1, below.

## Anomalies

1. **MATR time unit (fixed, tooling).** BatteryML copies MATR `cycles.t`, which is in minutes (≈60 per cycle; `summary.chargetime` is also minutes), into `time_in_s` without conversion. `degradx.data.matr` multiplies by 60 and records `time_unit_converted_from_minutes=True` on each object. `docs/DEVIATIONS.md` T1.
2. **MATR index 0.** BatteryML skips raw index 0 of every cell. That index is an empty placeholder in b1 but a real first cycle in b2–b4, so those cells lose their first cycle, as in BatteryML. The five carry-over segments' own index 0 are real cycles, not placeholders, so no mid-life placeholder was emitted (`dropped_placeholder_cycles` = 0 everywhere).
3. **HUST capacity.** BatteryML's integrated capacity reads 18.3 mAh (median) above the cycler's `dq`, so every HUST record would end above the 0.88 Ah threshold. Decided in **D11**: the capacity channel is the cycler-reported capacity in all three datasets.
4. **Records truncated at the stopping threshold.** Every non-crossing HUST cell ends within 1.6 mAh of 0.88 Ah (last-5 mean), and every non-crossing MATR b1/b3 cell ends within ~5 mAh, except the few documented unfinished cells, which stop ~94 mAh above. Under strict `q ≤ ρ·q_nom`, attainment becomes a question of noise: HUST 11/77, MATR 96/180. Carried to S2 as **D13**; the harness has already run (`experiments/decisions/D13/`).
5. **MATR b4 IR is recorded as zero in every cycle** (45 cells), so IR is not "available in every unit" if b4 is included. Carried to S2 with the MATR scope decision (S0 item 3).
6. **Glitch cycles.**
   - MATR: single-cycle capacity spikes (e.g. b1c18 at 2.88 Ah, b1c0 position 11 at 1.54 Ah), and a shared dip across b2 cells near cycle 246–257, consistent with the chamber-temperature excursions Severson reports.
   - NASA: 8.4 V spikes in B0005–B0007 cycle 31, NaN samples in 12 cycles, and near-zero discharges in the 4 °C groups.
   - Carried to S2 as **D12** (glitch rule), since smoothing, `q₁` and the fits are sensitive to single-cycle spikes.
7. **Regression found while writing S1.** `ProcessPoolExecutor(max_tasks_per_child=…)` switches to the spawn start method and deadlocked with no workers. It was replaced by a fork-context `multiprocessing.Pool` (`degradx.data.channels.dataset_table`).

## Decisions needed

None open for a human. Decisions taken or carried:
- D11 (taken, `docs/DECISIONS/D11_capacity_source.md`).
- D12 and D13 (S2), MATR scope (S2), D03 NASA role (S2).
