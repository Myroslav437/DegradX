# S0 research: MATR, HUST and NASA PCoE, from their own documentation

Scope: this report fixes the reference facts that Stage S1 checks its ingestion against, and gives a memory-safe preprocessing plan. It was written 2026-09-15.

Nothing under `/home/mmishchuk/projects/DegradX/data/` was read or written. Every measured number below comes from one of three sources: an official publication, an official README, or a remote metadata or range read made by me from the official download URLs. Those reads were done with scripts kept under `s0_research/datasets/`.

Abbreviations:
- `BML/...` means `/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/BatteryML/...` at commit `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`.
- `R/...` means `/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/s0_research/datasets/...`.

---

## 0. Artefacts kept (all under `R/`)

| Path | What it is |
|---|---|
| `pubs/Severson_NatureEnergy_2019.pdf`, `pubs/sev_raw.txt` | Full text of Severson et al. 2019 (from https://web.mit.edu/braatzgroup/Severson_NatureEnergy_2019.pdf) |
| `pubs/attia2020.pdf` | Attia et al. 2020, Nature 578:397 (from OSTI https://www.osti.gov/servlets/purl/1647088). The PDF is scanned, so pages 7–10 were read as images |
| `pubs/hust2022.pdf`, `pubs/hust.txt`, `pubs/hust2022_esi.pdf`, `pubs/hust_esiL.txt`, `pubs/hust_tableS1.csv` | Ma et al. 2022 EES paper and its ESI. Taken from Wayback captures of pubs.rsc.org, because RSC returns 403 to scripts. The CSV is ESI Table S1 parsed |
| `pubs/qin2016.pdf`, `pubs/qin.txt` | Qin et al. 2016, Energies 9:896 (from mdpi-res.com) |
| `pubs/saha_goebel_2009.pdf`, `pubs/saha.txt` | Saha & Goebel 2009, PHM Society conference paper by the NASA dataset authors |
| `pubs/pan2022.pdf`, `pubs/pan.txt` | Pan et al. 2022, Energies 15:2498 |
| `severson_repo/` | Official Severson/Braatz data-loading code, https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation, commit `1ef13d27` |
| `attia_repo/` | Official Attia code and data, https://github.com/chueh-ermon/battery-fast-charging-optimization, commit `0068fd01` |
| `matr/probe_matr.py`, `matr/cachedrange.py`, `matr/probe_2017*.json`, `matr/probe_2018*.json`, `matr/probe_2019*.json`, `matr/probe_summary.txt`, `matr/cycle0_check.txt` | Remote HDF5 metadata probe of the four official MATR `.mat` files. Uses HTTP range reads through h5py's file-object driver and about 0.96 GB of transfer; no full download |
| `hust/hust_zip_listing.tsv`, `hust/inspect_hust_out.txt`, `hust/inspect_hust_7-5.txt` | Central directory of the official HUST zip, plus inspection of two member pickles (`2-5.pkl`, `7-5.pkl`) fetched by range read. Both pickles were deleted afterwards |
| `nasa/readme/*.txt`, `nasa/inspect_nasa*.py`, `nasa/inspect_nasa*_out.txt` | The ten official READMEs from the NASA zip, plus a per-cell structure and anomaly scan of all 34 `.mat` files. I downloaded a private copy of the zip into `R/nasa/` and deleted the zip and `.mat` files after the scan |

---

## 1. MATR (Severson et al. 2019; Attia et al. 2020; data.matr.io)

### 1.1 Files, from the data.matr.io Girder API (`/1/api/v1/file/<id>`)

| BatteryML name (`BML/batteryml/preprocess/download.py` l.13-22) | Original name on data.matr.io | Bytes | File id |
|---|---|---|---|
| MATR_batch_20170512.mat | 2017-05-12_batchdata_updated_struct_errorcorrect.mat | 3,025,320,241 | 5c86c0b5fa2ede00015ddf66 |
| MATR_batch_20170630.mat | 2017-06-30_batchdata_updated_struct_errorcorrect.mat | 2,007,331,155 | 5c86bf13fa2ede00015ddd82 |
| MATR_batch_20180412.mat | 2018-04-12_batchdata_updated_struct_errorcorrect.mat | 3,236,690,412 | 5c86bd64fa2ede00015ddbb2 |
| MATR_batch_20190124.mat | 2019-01-24_batchdata_updated_struct_errorcorrect.mat | 2,601,295,745 | 5dcef152110002c7215b2c90 |

- The four files total 10,870,637,553 bytes (10.12 GiB).
- All four are MATLAB v7.3, which is HDF5. The first 16 bytes read "MATLAB 7.3 MAT-f".
- **S1 check:** each downloaded file size must equal the byte count above.

### 1.2 Experimental facts from the publications

- **Cells.** A123 APR18650M1A LFP/graphite cells, 1.1 Ah nominal capacity and 3.3 V nominal voltage (Severson Methods, `sev_raw.txt` l.1156-1158). The same model is used in Attia 2020 (Methods "Experimental", pdf p.7).
- **Temperature.** Cycled at a constant 30 °C in an Amerex environmental chamber on a 48-channel Arbin LBT cycler. Can temperature was measured with a type-T thermocouple (Severson l.1162-1167).
- **Charge (Severson).** 0→80 % SOC with one of 72 one-step or two-step policies. An IR measurement at 80 % SOC averages 10 pulses of ±3.6 C lasting 30 or 33 ms. Charging then continues with 1 C CC-CV to 3.6 V, cut off at C/50 (Severson l.1168-1180).
- **Discharge (Severson).** CC-CV at 4 C to 2.0 V, cut off at C/50 (l.1180-1181).
- **Attia 2020 differences.** 224 four-step, 10-minute policies. CC-CV 1 C charge to 3.6 V with a C/20 cutoff, CC-CV 4 C discharge to 2.0 V with a C/20 cutoff, and 5-s rests. Cycle life is defined as the number of cycles until discharge capacity falls below 80 % of nominal (pdf p.7, "Experimental").
- **EOL definition.** "cycle life … defined as the number of cycles until 80% of nominal capacity" (Severson Introduction). The Severson MATLAB loader uses a threshold of 0.88 Ah (`severson_repo/LoadData.m`, "Extract the number of cycles to 0.88").
- **Cycle-life range (Severson).** "from approximately 150 to 2,300 cycles (average cycle life of 806 with a standard deviation of 377)" (l.255-256). The paper reports about 96,700 cycles in the 124-cell dataset (l.428).
- **Chamber temperature.** The paper attributes error increases around cycles 55 and 70 to "temperature fluctuations of the environmental chamber" (Fig. 5 caption, l.1042-1043). Cell temperature varies by up to 10 °C within a cycle (l.256-258).
- **Rest times differ by batch** (Severson l.1183-1190):
  - 2017-05-12: 1 min after reaching 80 % SOC, 1 s after discharge.
  - 2017-06-30: 5 min at both points.
  - 2018-04-12: 5 s rests after 80 % SOC, after the IR test, and before and after discharge.

### 1.3 Batches and cell counts

| Batch (BatteryML key prefix) | Cells in file | Belongs to | Source |
|---|---|---|---|
| 2017-05-12 (`b1`) | 46 | Severson 2019 | Notebook output `b1c0..b1c45` (`severson_repo/BuildPkl_Batch1.ipynb` cell 6); remote probe `num_cells=46` (`matr/probe_20170512.json`) |
| 2017-06-30 (`b2`) | 48 | Severson 2019 | `BuildPkl_Batch2.ipynb` cell 6; probe `num_cells=48` |
| 2018-04-12 (`b3`) | 46 | Severson 2019 (the "secondary test" set, generated after model development) | `BuildPkl_Batch3.ipynb` cell 6; probe `num_cells=46`; Severson l.314 |
| 2019-01-24 (`b4`) | 45 | Attia 2020 validation experiment | Probe `num_cells=45`. Attia Methods "Validation experiments" (pdf p.9): 9 protocols, 5 batteries each, 45 total. `attia_repo/figures/fig4/final_results.csv` lists 9 × 5 final cycle lives from 443 to 1166, identical to the min/max of the `cycle_life` field in the probed 2019-01-24 file. BatteryML `dataprepare.md` also calls this "the last batch used in [2]". The paper text never names the date itself, so the date↔experiment link is inferred from these matches |

- **Severson 124 cells** = 41 (b1) + 43 (b2) + 40 (b3). The notebook prints `numBat1=41`, `numBat2=43`, `numBat3=40` and `numBat=124` (`severson_repo/Load Data.ipynb` cells 2, 7, 9, 10).
- **Paper splits.** Training 41, primary test 43, secondary test 40 (Severson l.310-314). One primary-test cell "reaches 80% state-of-health rapidly" (Table 1 note, l.278-279). BatteryML identifies it as `b2c1` (`BML/batteryml/train_test_split/MATR_split.py` l.54-60).
- **Unique cells over the four files** = 46 + 48 + 46 + 45 − 5 carry-overs = 180. This matches the "Cell Count 180" in the BatteryML README table (`BML/README.md` l.35).
- **Carry-overs.** Five cells continued from batch 1 into batch 2:

  | Batch 2 key | Batch 1 key | Cycles appended (`add_len`) |
  |---|---|---|
  | `b2c7` | `b1c0` | 662 |
  | `b2c8` | `b1c1` | 981 |
  | `b2c9` | `b1c2` | 1060 |
  | `b2c15` | `b1c3` | 208 |
  | `b2c16` | `b1c4` | 482 |

  Sources: `Load Data.ipynb` cell 4 and BatteryML `preprocess_MATR.py` l.125-127. The code comment says "four cells", but five keys are listed. MATLAB `LoadData.m` uses `add_len = [661, 980, 1059, 207, 481]` and appends `add_len+1` entries, i.e. the same counts.
  - The probe confirms the batch-2 files hold exactly 662, 981, 1060, 208 and 482 cycle entries (`matr/probe_summary.txt`).
  - Merged lengths are b1c0 1851, b1c1 2159, b1c2 2236, b1c3 1433 and b1c4 1708 cycle entries.
- **Cells that do not reach 80 %.** The five batch-1 cells `b1c8, b1c10, b1c12, b1c13, b1c22` are deleted in `Load Data.ipynb` cell 1. `LoadData.m` calls them "batteries that do not finish in Batch 1". BatteryML comments these deletions out (`preprocess_MATR.py` l.115-120), so all five are emitted.
- **Batch-3 exclusions.**
  - The Python notebook deletes `b3c37, b3c2, b3c23, b3c32, b3c42, b3c43` as "noisy channels" (cell 8).
  - `LoadData.m` gives three separate reasons for its removals:
    - channel 46, because "there was a problem with the data collection for this channel";
    - cells whose final QDischarge is above 0.885, i.e. cells that did not finish;
    - three "noisy Batch 8 batteries".
  - The paper says "four cells had unexpectedly high measurement noise and were excluded" (l.1192-1193).
  - The probe is consistent with this: `b3c23` and `b3c32` have `cycle_life = NaN` (2189 and 2237 cycles recorded), so they never reached EOL.
  - BatteryML's secondary-test list excludes the same six cells. Its CLO split keeps all b3 cells except `b3c37`. BatteryML maintainers say `b3c43` was kept deliberately (GitHub issue microsoft/BatteryML#37).

### 1.4 Raw structure and measured per-batch statistics (remote probe, `matr/probe_summary.txt`)

- **Top-level HDF5 keys:** `#refs#, #subsystem#, batch, batch_date`.
- **`batch` keys:** `Vdlin, barcode, channel_id, cycle_life, cycles, policy, policy_readable, summary`.
- **`summary` fields (one value per cycle):** `IR, QCharge, QDischarge, Tavg, Tmax, Tmin, chargetime, cycle`. These match `severson_repo/README.md`.
- **`cycles` fields (one array per cycle):** `I, Qc, Qd, Qdlin, T, Tdlin, V, discharge_dQdV, t`.
- **Array lengths.** `Qdlin`, `Tdlin` and `discharge_dQdV` always have 1000 samples. Severson Methods explains the fixed grid: "1,000 linearly spaced voltage points from 3.5 V to 2.0 V".

| | b1 2017-05-12 | b2 2017-06-30 | b3 2018-04-12 | b4 2019-01-24 |
|---|---|---|---|---|
| Cycle entries (all cells) | 38,811 | 24,920 | 51,007 | 39,673 |
| Entries per cell, min/median/max | 533/857/1226 | 170/508/1060 | 540/1017/2237 | 530/904/1231 |
| `len(summary)` equals `len(cycles)` for every cell | yes | yes | yes | yes |
| `cycle_life` minus entries | +1 for all 46 | −20 to −37 for 43 cells; +1 for the 5 carry-overs | +1 for 44; NaN for 2 (`b3c23`, `b3c32`) | −23 to −273 (cells cycled past EOL) |
| `cycle_life` min–max | 534–1227 | 148–1061 | 541–1935 | 443–1166 |
| Cycle index 0 (probed cells) | **Empty MATLAB placeholder**: shape (2,) uint64, value [0 0], attribute `MATLAB_empty=1`; `summary` index 0 is all zeros (`matr/cycle0_check.txt`) | Real data (cell 0: 1308 samples) | Real data (cell 0: 762 samples) | Real data (cell 0: 743 samples) |
| Raw per-cycle samples in probed cycles (I, V, T, Qc, Qd, t) | 895–1105 | 1263–1596 | 717–1018 | 707–1229 |
| HDF5 compression of per-cycle arrays | none (contiguous) | **gzip** (chunked) | none | none |
| Distinct `policy_readable` strings | 23 | 43 | 8 | 9 |

- **Severson-124 set from the file's own `cycle_life` field** (notebook removals applied, carry-overs merged): n = 124, min 148, max 2237, mean 801.6, sd 379.7. The paper reports "≈150 to 2,300, mean 806, sd 377". This is close but not exact, so treat the file field as the reference and the paper as approximate.
- **b2 carry-over `policy_readable` strings come out truncated**, e.g. `80%)-3.6C`, when decoded as BatteryML does. BatteryML never calls `organize_cell` on b2 carry-over keys, so this is harmless in its code.
- **Measured example, `b1c0`.** `summary.cycle` runs 1..1189 and `QDischarge[1]` is 1.0707 Ah.

### 1.5 What BatteryML's MATR preprocessor keeps and drops

Source: `BML/batteryml/preprocess/preprocess_MATR.py`.

- **Loading.** `load_batch` (l.45-111) reads `cycle_life`, `policy_readable`, all eight summary fields and all nine per-cycle arrays into numpy. The keys it creates are `b{k}c{i}` with k = 1..4 in file order (l.109).
- **Cleaning.** `clean_batches` (l.114-161) merges the five carry-over cells into batch 1:
  - it adds `add_len` to `cycle_life`;
  - it concatenates the summary fields, offsetting `cycle` by the batch-1 length;
  - it appends the cycle dicts.
  It then calls `organize_cell` and dumps every cell not in `batch2_keys` (l.152-159). Batch-2 carry-over keys are skipped, and no other cell is removed.
- **What `organize_cell` (l.164-221) keeps per cycle:**
  - `voltage_in_V` ← `V`
  - `current_in_A` ← `I`
  - `temperature_in_C` ← `T`
  - `discharge_capacity_in_Ah` ← `Qd`
  - `charge_capacity_in_Ah` ← `Qc`
  - `time_in_s` ← `t`
  - `internal_resistance_in_ohm` ← `summary['IR'][cycle]`, a scalar
  - `Qdlin` ← `Qdlin`, stored in `additional_data` because of `**kwargs`

  All of these are converted with `.tolist()` (l.170-180).
- **What `organize_cell` drops:**
  - Per-cycle arrays: `Tdlin` and `discharge_dQdV`.
  - Summary fields: `QDischarge`, `QCharge`, `Tavg`, `Tmin`, `Tmax`, `chargetime` and `cycle`.
  - Per-cell values: `cycle_life`, the raw `charge_policy` string (only parsed into `CyclingProtocol` objects, l.186-208), `barcode`, `channel_id`, `Vdlin` and `batch_date`.
  - **Consequence for DegradX.** Paper §3.4 needs discharge capacity, IR, charge time and temperature statistics per cycle. Of these, BatteryML output keeps only IR directly. Summary capacity, chargetime and Tavg/Tmin/Tmax must be read separately. They can be recomputed from the raw series, but the result is not guaranteed to be identical.
- **Constants it writes.** `form_factor='cylindrical_18650'`, `cathode_material='LFP'`, `anode_material='graphite'`, `nominal_capacity_in_Ah=1.1`, voltage limits 2.0–3.5 V (l.210-221), and discharge protocol 4 C (l.183-185). The paper states a 3.6 V charge cutoff, while BatteryML writes 3.5 V (l.220).
- **`cycle_number` convention.**
  - Python index 0 is skipped (l.167-168), and `cycle_number` equals the index (l.171).
  - In batch 1, index 0 is the empty placeholder and `summary.cycle[0]=1`. So BatteryML cycle_number n corresponds to the dataset's summary cycle n+1, and the first emitted cycle is the dataset's "cycle 2".
  - **Risk:** in b2, b3 and b4, index 0 holds real data in the probed cell 0, so BatteryML silently discards the first real cycle of every b2, b3 and b4 cell. Probed for cell 0 only; S1 must check all cells.
  - For merged cells, the carry-over segment's own index 0 is kept, because it sits in the middle of the merged list. Only b2 cell 0 was probed, and there index 0 is a real cycle. Whether index 0 of `b2c7/8/9/15/16` is real or an empty `[0,0]` placeholder is UNVERIFIED. If it is empty, BatteryML would emit a `CycleData` with Qd=[0,0] in mid-life, and `RULLabelAnnotator` would place EOL there. S1 must check this. The `summary.cycle` value at that position is also UNVERIFIED.
- **IR alignment** relies on `len(summary) == len(cycles)`. This was confirmed for all 185 cell entries in all four files.

### 1.6 Peak RAM of BatteryML's MATR preprocessing as written (estimate)

**Model.** `process()` loads all four batches into numpy before `clean_batches` (l.26-40). The numpy payload per batch is (cycle entries) × 8 bytes × (6 × mean raw samples + 3 × 1000). Entries come from the probe; mean samples from the probed cycles.

| Batch | Estimated numpy payload | File size |
|---|---|---|
| b1 | 2.90 GB | 3.03 GB |
| b2 | 2.29 GB (gzip on disk, so RAM exceeds file size) | 2.01 GB |
| b3 | 3.22 GB | 3.24 GB |
| b4 | 2.68 GB | 2.60 GB |
| **Total** | **≈ 11.1 GB (10.3 GiB)** | |

**Components.**
- About 154,411 cycle entries hold 9 ndarray objects each. That is roughly 1.4 M arrays at about 112 bytes of header, plus one dict per cycle, for about 0.3 GB of Python overhead.
- `organize_cell` turns seven arrays per cycle into Python lists at about 32 bytes per float (8-byte pointer plus a 24-byte float object). For the largest cell, merged `b1c2` (1176 b1 cycles + 1060 b2 cycles), that is about 0.60 GB. `b3c32` (2237 cycles) needs about 0.42 GB.
- In the loop `battery = organize_cell(...)` (l.155), the previous `BatteryData` is still referenced while the next one is built, so two cells' lists can coexist: about 1.0–1.2 GB.
- `pickle.dump(self.to_dict())` streams to disk; its memo holds references only.

**Estimated peak ≈ 11.1 + 0.3 + 1.1 ≈ 12.5 GB (≈ 11.6 GiB)** plus interpreter and h5py baseline. This is an estimate, not a measurement; the per-cycle sample counts come from 4 cycles in each of up to 4 cells per batch.

**Machine.** `free -g` during this work showed 15 GiB total, 5 GiB used, 9 GiB available, and 3 GiB swap. **As written, the MATR preprocessing is expected to exceed available RAM and swap or be OOM-killed.**

### 1.7 Proposed memory-bounded approach (description only; not implemented)

The approach still calls BatteryML's own `load_batch`, `organize_cell`, `clean_batches` and `dump_single_file`. Run one batch per child process (for example `multiprocessing` with `maxtasksperchild=1`, or four separate subprocesses), so freed small-array heap is returned to the OS between batches.

1. **P2 (batch 2 first).**
   - `b2 = load_batch(file_20170630, 2)`, about 2.3 GB.
   - For each key not in `batch2_keys`: `dump_single_file(organize_cell(b2[key], key))`, then drop the reference (43 cells).
   - Keep `carry = {k: b2[k] for k in ['b2c7','b2c8','b2c9','b2c15','b2c16']}`, about 3,393 cycles or 0.31 GB.
   - Pickle `carry` to a temporary file and exit.
2. **P1 (batch 1 plus carry-over).**
   - `b1 = load_batch(file_20170512, 1)`, about 2.9 GB, then load the `carry` pickle.
   - Call **BatteryML's own** `clean_batches([b1, carry], dump_single_file, silent)`. Its merge loop (l.129-148) only touches `data_batches[0][b1c0..4]` and `data_batches[1][b2c7..16]`. Its dump loop (l.152-159) dumps every b1 cell and skips the carry keys, because they are in `batch2_keys`. The merge semantics are therefore identical to BatteryML's. Exit.
3. **P3 and P4.** `load_batch` → `organize_cell` + `dump_single_file` per cell. Do not call `clean_batches` here, because it would index `data_batches[1]['b2c7']`. Exit.
4. **Expected per-process peak** ≈ largest batch (b3 ≈ 3.2 GB, or b1 + carry ≈ 3.2 GB) + about 1.2 GB of list transients + about 0.3 GB of overhead ≈ **4.5–5 GB**, down from about 12.5 GB.
   - Optional: `del battery` after each dump removes the two-cells-alive overlap.
   - Optional: running P2, P3 and P4 concurrently would need about 13 GB, so run them sequentially.
5. **Separately, extract per-cycle `summary`** (QDischarge, IR, chargetime, Tavg/Tmin/Tmax, cycle) plus `cycle_life`, `policy_readable`, `barcode` and `channel_id` with a summary-only h5py reader. These arrays are a few MB per batch. BatteryML drops all of them, and DegradX's channel set needs them.
6. **Decisions S1 must record, not silently change:**
   - (a) whether to keep BatteryML's skip of index 0 in b2, b3 and b4 (see §1.5);
   - (b) whether to keep the five "never reach 80 %" b1 cells, which BatteryML keeps and Severson drops;
   - (c) whether to keep the six noisy or unfinished b3 cells.

### 1.8 S1 acceptance checks for MATR

- File sizes as in §1.1.
- `num_cells` per file: 46 / 48 / 46 / 45.
- Cycle entries per file: 38,811 / 24,920 / 51,007 / 39,673.
- BatteryML-style output: 180 pickles named `MATR_b{k}c{i}.pkl`, with no `b2c7/8/9/15/16`.
- Merged `b1c0..b1c4`: 1850 / 2158 / 2235 / 1432 / 1707 `CycleData` (merged entries − 1 for the skipped index 0).
- Every non-merged cell: `len(cycle_data) == n_cycles − 1`.
- Severson-124 subset by notebook rules: 124 cells, `cycle_life` 148–2237.

---

## 2. HUST (Ma et al. 2022, Energy Environ. Sci. 15:4083; Mendeley Data nsc7hnsg4s v2)

### 2.1 From the data record and the publication

- **Mendeley API** (`https://data.mendeley.com/public-api/datasets/nsc7hnsg4s`):
  - Name: "The Dataset for: Real-time personalized health status prediction of lithium-ion batteries using deep transfer learning". DOI 10.17632/nsc7hnsg4s.2, version 2 published 2022-05-24, licence CC BY 4.0.
  - Description: "A dataset with 77 LFP/graphite cells (1.1 Ah nominal capacity and 3.3 V nominal voltage)… identical charge protocol but different multi-stage discharge protocols at a constant temperature of 30°C."
  - One file, `our_data.zip`: 1,188,136,932 bytes, sha256 `071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db`.
  - **S1 check:** `hust_data.zip` must match this size and hash.
- **Cells and chamber.** 77 cells, "LFP/graphite A123 APR18650M1A, 1.1 Ah nominal capacity and 3.3 V nominal voltage", in "two thermostatic chambers at 30 °C" (`pubs/hust.txt` l.186-190, "Experimental data"). Methods adds an "80-channel CT4008 Neware battery tester at a constant temperature of 30 °C" (l.779).
- **Cycle life.** "ranging from 1100 to 2700 cycles (average 1898 with a standard deviation of 387). The dataset contains 146 122 discharge cycles in total" (l.191-195).
- **Charge.** 5 C CC from 0→80 % SOC, then 1 C CC from 80 % SOC to 3.6 V, then CV until 100 % SOC with a C/20 cutoff (l.782-785).
- **Discharge.** Four CC steps: 100→60 %, 60→40 % and 40→20 % SOC at protocol-specific rates, then 20→0 % "using a CC of 1C with a voltage cutoff of 2 V". 1 C = 1.1 A, with 30 s rests between steps (l.785-796).
- **EOL.** "collected … until the maximum capacity first reached 80% of nominal capacity (i.e., failure threshold)" (l.796-798).
- **Excluded cells.** "A total of 80 cells were cycled … 3 of 80 cells were excluded from the dataset due to sudden faults before degradation failure" (l.798-800). Table S1 shows the missing channels are **2-1, 5-8 and 6-7**.
- **Split.** 55 training and 22 test cells (l.200-203; ESI Table S1).
- **Measured quantities.** "Voltage, current and capacity were collected" (l.795-796). **No temperature or internal-resistance channel is described.**
- **ESI Table S1** (`pubs/hust_tableS1.csv`, parsed from `hust_esiL.txt` l.315-470):
  - 77 rows; cycle life min 1142 (`4-3`), max 2689 (`5-3`), mean 1897.7, population sd 387.3.
  - The cycle lives sum to **146,122**, equal to the paper's total discharge cycles. So Table S1's "cycle life" is the number of cycles recorded per cell.
  - Train/Test counts are 55/22. C4 is "1C" for all 77 rows, and C1 takes values in {2, 3, 4, 5} C.
- **BatteryML consistency.** `DISCHARGE_RATES` (`preprocess_HUST.py` l.129-207) matches Table S1's C1–C3 for all 77 channels, with 0 mismatches. `HUSTTrainTestSplitter` training IDs equal Table S1's "Train" set exactly (`BML/batteryml/train_test_split/HUST_split.py` l.16-23).

### 2.2 Raw structure, verified by reading the official zip remotely

- **Zip contents.** One directory, `our_data/`, holding **77 `*.pkl`** files and no other files (`hust/hust_zip_listing.tsv`).
  - Total uncompressed size is 4.246 GB. Per-cell pickles range from 36.7 MB (`2-5`) to 88.3 MB (`1-2`).
- **Pickle layout** (checked on `2-5.pkl` and `7-5.pkl`, `hust/inspect_hust_out.txt`): `{cell_id: {'rul': {cycle: int}, 'dq': {cycle: float}, 'data': {cycle: pandas.DataFrame}}}`.
  - Cycle keys run contiguously from 1..N. N = 1386 for `2-5` and 1875 for `7-5`, equal to Table S1.
  - `rul[k] = N − k + 1`, so `rul[1] = N`.
  - `dq` holds the per-cycle discharge capacity in mAh. For `2-5` it runs from 1158.86 down to 880.28; for `7-5` the last value is 880.5.
  - DataFrame columns are `Status` (object), `Cycle number` (int64), `Current (mA)` (float64), `Voltage (V)`, `Capacity (mAh)` and `Time (s)` (int64). Columns are identical across all cycles of `2-5`.
  - `Time (s)` restarts at 0 in each cycle and has a median step of 5 s.
  - Rows per cycle for `2-5`: min 443, median 571, max 674, total 791,546.
  - `Status` values: `Constant current charge`, `Constant current-constant voltage charge`, `Constant current discharge_0` … `_3`.
  - Sign convention: charge current is positive (+5497 mA), discharge current is negative.
  - The pickles unpickle with pandas 3.0.5 / numpy 1.26.4 (project `.venv`).
- **There is no temperature column and no IR column.**

### 2.3 BatteryML's HUST preprocessor (`BML/batteryml/preprocess/preprocess_HUST.py`)

- **Input.** Expects `parentdir/hust_data.zip` (l.22).
  - **Side effect:** it extracts the whole zip into the raw directory (`data/raw/HUST/our_data/`, about 4.25 GB of disk) and `shutil.rmtree`s that directory at the end (l.24-33, l.123).
  - S1 needs 4.3 GB of free disk space there and must not run it while the raw directory is in use.
- **Loop.** One cell at a time (l.41-117), skipping cells whose output pickle already exists (l.46-49).
- **Per-cycle output** (l.54-68): `cycle_number=cycle+1` (1-based, cycle 1 not skipped), `voltage_in_V`, `current_in_A` (mA/1000), `time_in_s`, and `discharge_capacity_in_Ah` / `charge_capacity_in_Ah` recomputed by rectangle integration of I·dt (`calc_Q`, l.210-220).
  - **Dropped:** temperature (absent from the source), IR (absent from the source), `Status`, `Capacity (mAh)`, `Cycle number`, and the pickle's own `dq` and `rul`.
- **Dropped cycles.** `HUST_7-5` loses its first two cycles, `cycles = cycles[2:]`, with the comment "Skip first problematic cycles" (l.71-73). The reason is not documented, and no anomaly was visible in `7-5` cycles 1–5: dq 1177–1187 mAh, normal status sequence, voltage 1.99–3.60 V. Cycle 2 has 1195 rows against about 770 for its neighbours. The reason is UNVERIFIED. No cells are dropped.
- **Constants it writes.** `nominal_capacity_in_Ah=1.1`, 18650 LFP/graphite, charge protocol 5C→0.8 / 1C→3.6 V / CV (l.80-94), discharge rates from `DISCHARGE_RATES` plus a final 1 C step (l.95-112), and voltage limits 2.0–3.6 V.
- **Observed discrepancies.** Both were seen only on the cells inspected; S1 must check all 77.
  1. **Final step current.** In `2-5` (Table S1: 5C-3C-3C-1C), the medians of `Constant current discharge_0/1/2/3` are −5498.5, −3298.7, −3298.7 and **−2199.2 mA**. The last step is therefore 2 C, not the 1 C that the paper and BatteryML state. This holds in cycles 2 and 700.
  2. **EOL detection.** BatteryML's `calc_Q` gives max Qd = 1.1787 Ah on cycle 1 and 0.9001 Ah on the last cycle of `2-5`. The file's own `dq` is 1.1589 and 0.8803 Ah, so `calc_Q` reads about 0.020 Ah high.
     - With BatteryML's `RULLabelAnnotator` (Qd ≤ 0.8 × 1.1 = 0.88 Ah, `BML/batteryml/label/rul.py` l.24-29), `2-5` would never reach EOL.
     - Even `dq` ends at 880.28 mAh (2-5) and 880.5 mAh (7-5), just above 880. A strict ≤ 0.88 Ah test on HUST's own capacity misses the recorded EOL.
     - **Implication for ρ = 0.8:** HUST's EOL is "the last recorded cycle". A declared-ρ rule needs either a tolerance or the last-cycle convention. The choice must be documented.
- **Memory.** Per-cell processing; the largest pickle is 88 MB. Lists for about 1.9 M rows × 5 series × 32 B come to about 0.3 GB. That row count is an estimate scaled from `2-5` by pickle size. **Peak is estimated below about 1.5 GB**; not measured.

### 2.4 S1 acceptance checks for HUST

- 77 output pickles `HUST_<ch>.pkl`, with channels exactly those of Table S1; `2-1`, `5-8` and `6-7` absent.
- `len(cycle_data)` equals Table S1 cycle life for 76 cells, and equals cycle life − 2 for `7-5` (1873).
- Total cycles over all cells: 146,122 − 2 = 146,120.
- Cycle-life range 1142–2689.
- 55/22 split as in Table S1.

---

## 3. NASA PCoE Battery Data Set (Saha & Goebel 2007)

### 3.1 Distribution

- **NASA repository entry** (https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/, item 5):
  - Description: "Experiments on Li-Ion batteries. Charging and discharging at different temperatures. Records the impedance as the damage criterion."
  - Link: `https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip`.
  - Citation: "B. Saha and K. Goebel (2007). 'Battery Data Set', NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA".
- **Zip.** S3 HEAD reports Content-Length 209,708,670 and ETag `"d97c40652800c2cce87ad16b0ff15dff-13"`. The copy I downloaded has md5 `7fbc095e95af3e52b5a1207a29180fc3` and sha256 `82302a7db4fc1b34e0b6676326610438d43b816bdf11a69d1d012a464ef2f92e`.
  - It contains six inner zips (`1. BatteryAgingARC-FY08Q4.zip` … `6. BatteryAgingARC_53_54_55_56.zip`).
  - **B0025–B0028 appear twice**, in inner zips 2 and 3; the copies are byte-identical by md5.
- **Unique cells: 34.** B0005, B0006, B0007, B0018, B0025–B0034, B0036, B0038–B0056. **B0035 and B0037 do not exist.**
  - The 34 unique `.mat` files total 198,523,797 bytes.

### 3.2 Experiment groups, from the official READMEs (`nasa/readme/`)

All groups charge at 1.5 A CC to 4.2 V, then CV until 20 mA. Every group also runs EIS from 0.1 Hz to 5 kHz.

| Cells | Ambient (README) | Discharge | Cut-off V | Stopping criterion (README) | README file |
|---|---|---|---|---|---|
| 5, 6, 7, 18 | "room temperature" | CC 2 A | 2.7 / 2.5 / 2.2 / 2.5 | "30% fade in rated capacity (from 2Ahr to 1.4Ahr)" | `1_README.txt` |
| 25, 26, 27, 28 | room temperature (24 °C) | 0.05 Hz square wave, 4 A amplitude, 50 % duty | 2.0 / 2.2 / 2.5 / 2.7 | not stated | `2_README.txt`, `3_README_25_26_27_28.txt` |
| 29, 30, 31, 32 | 43 °C | 4 A | 2.0 / 2.2 / 2.5 / 2.7 | not stated | `3_README_29_30_31_32.txt` |
| 33, 34 | 24 °C | 4 A | 2.0 / 2.2 | "capacity had reduced to 1.6Ahr (20% fade)" | `3_README_33_34_36.txt` |
| 36 | 24 °C | 2 A | 2.7 | same, 1.6 Ah | `3_README_33_34_36.txt` |
| 38, 39, 40 | 24 & 44 °C | multiple loads: 1, 2, 4 A | 2.2 / 2.5 / 2.7 | 1.6 Ah (20 % fade) | `3_README_38_39_40.txt` |
| 41, 42, 43, 44 | 4 °C | multiple fixed loads: 4 A and 1 A | 2.0 / 2.2 / 2.5 / 2.7 | 1.4 Ah (30 % fade); "several discharge runs where the capacity was very low. Reasons for this have not been fully analyzed." | `3_README_41_42_43_44.txt` |
| 45, 46, 47, 48 | 4 °C | 1 A | 2.0 / 2.2 / 2.5 / 2.7 | 1.4 Ah (30 %); same very-low-capacity note | `4_README_45_46_47_48.txt` |
| 49, 50, 51, 52 | 4 °C | 2 A | 2.0 / 2.2 / 2.5 / 2.7 | "until the experiment control software crashed"; "capacity as well as voltage levels were very low" | `5_README_49_50_51_52.txt` |
| 53, 54, 55, 56 | 4 °C | 2 A | 2.0 / 2.2 / 2.5 / 2.7 | 1.4 Ah (30 %); very-low-capacity note | `6_README_53_54_55_56.txt` |

- **Rated capacity** is 2 Ah (`1_README.txt`).
- **Form factor.** "Commercially available Li-ion 18650 sized rechargeable batteries" (Saha & Goebel 2009, `pubs/saha.txt` l.713).
- **Chemistry** is not stated in any README or in the 2009 paper: UNVERIFIED.
- **Room temperature.** The 2009 paper says "room temperature, 23 °C" (l.733), while the `.mat` `ambient_temperature` for B0005–B0018 is 24.

### 3.3 `.mat` structure, README versus actual (`nasa/inspect_nasa_out.txt`)

- **Top level.** The variable is named after the cell (e.g. `B0005`), with struct field `cycle`, a 1×N struct array. Each element has `type` ∈ {`charge`, `discharge`, `impedance`}, `ambient_temperature` (°C), `time` (MATLAB datevec of the operation start: Y, M, D, h, m, s) and `data`.
- **`charge` fields:** `Voltage_measured, Current_measured, Temperature_measured, Current_charge, Voltage_charge, Time`. These match the README.
- **`discharge` fields:** `Voltage_measured, Current_measured, Temperature_measured, Current_load, Voltage_load, Time, Capacity`.
  - **The README is wrong here.** It lists `Current_charge` and `Voltage_charge` for discharge; the files use `Current_load` and `Voltage_load`.
  - The README also says Capacity is "for discharge till 2.7V", although cut-offs differ per cell.
- **`impedance` fields:** `Sense_current, Battery_current, Current_ratio, Battery_impedance, Rectified_Impedance, Re, Rct`. The README spells it `Rectified_impedance`; the files use a capital I.
- **Units** per README: V, A, °C, s, Ah, Ω.
- **Sign convention.** The 5th percentile of `Current_measured` during discharge is −2.0 A (B0005) or −4.0 A, so discharge is negative, the same convention as HUST and BatteryML.

### 3.4 Per-cell counts and data-quality facts (measured on all 34 files)

| Cell | Ops | Charge / Discharge / Impedance | Ambient values seen (°C) | Capacity first / max / min / last (Ah) | Discharge index first ≤ 1.4 Ah | Issues seen |
|---|---|---|---|---|---|---|
| B0005 | 616 | 170/168/278 | 24 | 1.857 / 1.857 / 1.288 / 1.325 | 125 | — |
| B0006 | 616 | 170/168/278 | 24 | 2.035 / 2.035 / 1.154 / 1.186 | 109 | First capacity above rated 2 Ah |
| B0007 | 616 | 170/168/278 | 24 | 1.891 / 1.891 / 1.401 / 1.433 | **never** (min 1.4005) | Never reaches the README EOL of 1.4 Ah |
| B0018 | 319 | 134/132/53 | 24 | 1.855 / 1.855 / 1.341 / 1.341 | 97 | — |
| B0025–B0028 | 80 | 31/28/21 | 24 | 1.80–1.85 start, 1.72–1.77 end | never (B0026: one dip to 1.386 at discharge 6) | Only 28 discharges; no EOL criterion stated |
| B0029–B0032 | 97 | 40/40/17 | 43 | 1.66–1.70 start, 1.56–1.67 end | never | Only 40 discharges |
| B0033 | 486 | 197/197/92 | 24 | **0.068** / 1.885 / 0.068 / 1.315 | 1 | 11 discharges below 1 Ah |
| B0034 | 486 | 197/197/92 | 24 | 0.746 / 1.820 / 0.746 / 1.280 | 1 | First discharge anomalous |
| B0036 | 486 | 197/197/92 | 24 | 1.002 / **2.444** / 1.002 / 1.559 | 1 | Maximum above rated capacity |
| B0038–B0040 | 122 | 47/47/28 | discharges: 24 (12), 44 (35) | first 0.898 / 0.119 / 0.674 | 1 | 1, 12 and 14 discharges below 1 Ah; mixed 1/2/4 A loads |
| B0041 | 163 | 67/67/29 | 4 | 0.056 / 1.216 / 0.044 / 0.837 | 1 | 60 of 67 discharges below 1 Ah; 3 discharges with ≤ 9 samples |
| B0042–B0044 | 275 | 113/112/50 | 4 and **22** (41 discharges at 22 °C, not in README) | max 1.69–1.73, **min 0.0** | 6 | 47 discharges below 1 Ah; 3 discharges with ≤ 9 samples |
| B0045–B0048 | 184 | 72/72/40 | 4 | max 1.08 (B0045) to 1.73; **min 0.0** | 1–17 | B0045: 71 of 72 below 1 Ah |
| B0049–B0052 | 62 | 25/25/12 | 4 | max **2.38 / 2.64 / 2.33** (49–51), 1.42 (52); min 0.0 | 1 | **Empty `Capacity` arrays**: B0050 has 4, B0052 has 21 of 25; software crash per README |
| B0053 | 137 | **55/56**/26 | 4 | 1.069 / 1.154 / 0.0 / 0.0 | 1 | One more discharge than charge; one 3-sample discharge |
| B0054 | 253 | **102/103**/48 | 4 | 0.740 / 1.167 / 0.0 / 0.0 | 1 | Same pattern |
| B0055, B0056 | 252 | 102/102/48 | 4 | max 1.32 / 1.34 | 1 | Never above 1.4 Ah |

- **Impedance ambient.** In the 4 °C groups (41–56) and the 24/44 °C group (38–40), all impedance operations carry `ambient_temperature` 24. The 43 °C group (29–32) records its impedance operations at 43 (`inspect_nasa2_out.txt`).
- **Shared timestamps.** Cells in a group share identical operation start timestamps; for example B0005, B0006 and B0007 run 2008-04-02 13:08:17 → 2008-05-28 11:09:42. Qin 2016 notes the same: "the three batteries have the same beginning time of every cycle" (§4.2, `pubs/qin.txt` ~l.2033).
- **Rest gaps.** The gap between the end of one discharge and the start of the next has a median of 4.07 h for B0005–B0007, with **4 gaps over 24 h and a maximum of 309.5 h**. B0018 has median 3.0 h, 7 gaps over 24 h and a maximum of 243.8 h (`inspect_nasa2_out.txt`). Rest time is therefore recoverable from the `time` datevecs.
- **Currents.** The median of `Current_load` is 0 for most B0033/B0034 discharges even though the README says 4 A CC, while the 5th percentile of `Current_measured` is −4 A. Classify load level with a percentile, not the median.
- **Usable for DegradX §3.4 at a 1.4 Ah-type ρ:** only **B0005, B0006, B0018** actually cross the README's 1.4 Ah EOL with clean monotone-start data. B0007 stops at 1.4005 Ah.
  - At ρ = 0.8 of 2 Ah (1.6 Ah), the 24 °C group crosses at discharge 75 (B0005), 63 (B0006), 86 (B0007) and 45 (B0018).
  - All 4 °C cells start at or below about 1.73 Ah, contain zero or near-zero capacity runs, and are unsuitable without cleaning.

### 3.5 Capacity regeneration in the literature

- **Saha & Goebel 2009** (dataset authors, PHM Society conference, `pubs/saha.txt` l.553-580, 620-690, 905-915):
  - They model "self-recharge during rest": "By letting the battery rest, the reaction products have a chance to dissipate, thus increasing the available capacity for the next cycle".
  - The model is C_{k+1} = η_C C_k + β1 exp(−β2/Δt_k), where Δt_k is the rest period.
  - EOL: "multiple crossings [of 1.4 Ah] caused by the capacity gain during relaxation periods … it is difficult to define the true EOL".
  - Setup: 2 A discharge to 2.7 V at 23 °C, stopped at a 30 % fade from 2 to 1.4 Ah. Results are shown "from a single battery", which the text does not identify: UNVERIFIED.
- **Qin et al. 2016** (Energies 9:896, open access):
  - Uses NASA batteries **No. 5, 6 and 7**, with "total charge/discharge cycles … all 168"; cycles 1–100 train and 101–168 test (§4.1).
  - Rest time is proxied by "the beginning time interval of two adjacent cycles" (Abstract).
  - It cites Eddahech et al. that "capacity regeneration takes around 2 h of rest-time to appear" (§1).
  - It extracts "SOH values of regeneration cycles, the number of cycles in regeneration regions" (§3.1).
  - It cites Olivares et al. [26] as detecting and isolating regeneration (§1).
- **Olivares et al. 2013** (IEEE TIM 62:364). Only the abstract is verified (Semantic Scholar API): particle-filter prognosis "while simultaneously detecting and isolating the effect of self-recharge phenomena", validated "through experimental data from an accelerated battery degradation test".
  - The full text sits behind an anti-bot challenge at repositorio.uchile.cl and was not accessed.
  - **UNVERIFIED:** which NASA cells it used, and whether it models ambient temperature as an explicit input. DegradX paper §3.1.2 makes that last claim, so it should be checked by hand.
- **Pan et al. 2022** (Energies 15:2498), cited by DegradX for trend/regeneration decomposition, uses **CALCE CS2_33/34/35/36/38, not NASA** (`pubs/pan.txt` l.1268-1277).
- **Commonly used cells.** B0005, B0006 and B0007 are verified (Qin 2016). B0018 is used alongside them "in many papers": UNVERIFIED from a primary source in this session. It shares the 2 A / 24 °C protocol per `1_README.txt`.

---

## 4. BatteryML schema and conventions for a NASA converter

- **Supported sources** (`BML/batteryml/preprocess/__init__.py` l.17-20):
  - `DATASETS`: CALCE, HNEI, HUST, MATR, OX, RWTH, SNL, UL_PUR.
  - `CYCLERS`: ARBIN, BATTERYARCHIVE, BIOLOGIC, INDIGO, LANDT, MACCOR, NEWARE, NOVONIX.
  - **NASA is not supported.**
  - Registered preprocessor classes: CALCE, HNEI, HUST, MATR, OX, RWTH, SNL, UL_PUR, ARBIN, NEWARE. The CLI builds `f'{input_type}Preprocessor'` (`BML/bin/batteryml.py` l.107-112).
- **`CycleData`** (`BML/batteryml/data/battery_data.py` l.9-45):
  - Positional `cycle_number: int`.
  - Keyword lists: `voltage_in_V`, `current_in_A`, `charge_capacity_in_Ah`, `discharge_capacity_in_Ah`, `time_in_s`, `temperature_in_C`.
  - Scalar `internal_resistance_in_ohm: float`.
  - `**kwargs` go into `additional_data` and are serialized by `to_dict`; MATR's `Qdlin` is stored this way.
- **`CyclingProtocol`** (l.48-77): `rate_in_C, current_in_A, voltage_in_V, power_in_W, start_voltage_in_V, start_soc, end_voltage_in_V, end_soc`. There is no end-current or cutoff-current field, so the NASA 20 mA CV cutoff cannot be expressed.
- **`BatteryData`** (l.80-168):
  - Fields: `cell_id` plus keywords `cycle_data, form_factor, anode_material, cathode_material, electrolyte_material, nominal_capacity_in_Ah, depth_of_charge=1.0, depth_of_discharge=1.0, already_spent_cycles=0, charge_protocol, discharge_protocol, max_voltage_limit_in_V, min_voltage_limit_in_V, max_current_limit_in_A, min_current_limit_in_A, reference, description`.
  - Extra kwargs become attributes and are serialized.
  - `dump` pickles `to_dict()`; `load` rebuilds the objects.
  - Preprocessors write `output_dir/{cell_id}.pkl` (`BML/batteryml/preprocess/base.py` l.49-50).
- **Cell-id convention:** `f'{DATASET}_{raw id}'`, e.g. `MATR_b1c0` (MATR l.211) and `HUST_1-1` (HUST l.43). Splitters parse the part after `_` (`MATR_split.py` l.17-19; `HUST_split.py` l.40-42).
- **`cycle_number` conventions:**
  - **MATR:** Python index into the raw `cycles` array, index 0 skipped, so emitted numbers start at 1 (MATR l.166-171). In batch 1, number n is dataset summary cycle n+1.
  - **HUST:** 1-based, `cycle + 1`, with nothing skipped except `7-5`'s first two list entries. The numbers then start at 3 (HUST l.62, l.72-73).
  - `RULLabelAnnotator` counts list positions, not `cycle_number`: label = (1-based position of the first cycle with max(Qd) ≤ 0.8 × nominal) + 1, or the padded length + 2 if never reached. Labels ≤ 100 become NaN (`BML/batteryml/label/rul.py` l.13-36). **Every NASA cell has at most 197 discharges, and many have 25–72, so BatteryML-style RUL labels would be NaN for a large share of NASA cells.** DegradX's own R_t = T − t does not have this limit.
- **Recommended NASA mapping** (mirrors the fields above; a design suggestion, not implemented):
  - `cell_id=f'NASA_{B00xx}'`.
  - One `CycleData` per `discharge` operation, with 1-based `cycle_number` in discharge order. Optionally prepend the preceding `charge` operation's series, since MATR and HUST cycles contain charge followed by discharge.
  - `voltage_in_V←Voltage_measured`, `current_in_A←Current_measured` (discharge negative, as in HUST), `temperature_in_C←Temperature_measured`, `time_in_s←Time`.
  - `discharge_capacity_in_Ah` as a cumulative list integrated from I·dt, like HUST's `calc_Q`, with NASA's scalar `Capacity` kept in `additional_data`, e.g. `capacity_nasa_Ah`.
  - `internal_resistance_in_ohm=None`, with `Re` and `Rct` of the nearest preceding impedance operation in `additional_data`. They are EIS-derived, not MATR's pulse DC IR, so the two must not be mixed.
  - Also store `ambient_temperature` and the operation start datevec in `additional_data`; the datevec is needed for rest-time analysis.
  - Cell level: `nominal_capacity_in_Ah=2.0`, `form_factor='cylindrical_18650'`, `max_voltage_limit_in_V=4.2`, `min_voltage_limit_in_V` = per-cell README cut-off.
  - Charge protocol: `CyclingProtocol(current_in_A=1.5, end_voltage_in_V=4.2)` then `CyclingProtocol(voltage_in_V=4.2)`.
  - Discharge protocol: `CyclingProtocol(current_in_A=<README>, end_voltage_in_V=<README>)`.
  - Leave `cathode_material` as None, because chemistry is unverified.

---

## 5. Risks and open items (for S1 and for the paper)

1. **MATR RAM:** as written, an estimated ~12.5 GB peak against ~9 GiB available. Use the per-batch plan in §1.7.
2. **MATR index 0:** empty in b1 but real in the probed b2/b3/b4 cell. BatteryML drops the first real cycle of b2/b3/b4 cells. Verify for all cells.
3. **MATR summary channels:** BatteryML drops the chargetime and temperature statistics DegradX needs, so extract `summary` separately.
4. **MATR exclusions** differ between the Severson paper (four noisy cells), the Python notebook (six b3 cells), MATLAB (1 bad channel + 2 unfinished + 3 noisy) and BatteryML (none removed). Report which rule is used.
5. **HUST EOL:** the last cycle's `dq` is about 880.3–880.5 mAh, just above 0.88 Ah, and BatteryML's `calc_Q` reads about 20 mAh higher than `dq`. A strict 0.8 × 1.1 Ah threshold misses EOL for the inspected cells.
6. **HUST final step:** 2 C observed in cell `2-5`, where the paper and BatteryML say 1 C.
7. **HUST disk:** BatteryML extracts 4.25 GB into the raw directory and then deletes it.
8. **HUST channels:** no temperature or IR, so the reference channel set of §3.4 cannot be matched on HUST.
9. **NASA README errors:** `Current_load`/`Voltage_load` and `Rectified_Impedance` naming.
10. **NASA group gaps:** 25–32 have no EOL criterion. 49–52 end in a software crash with empty `Capacity` arrays. The 4 °C groups contain zero-capacity discharges and extra 22 °C runs.
11. **NASA usable units:** only a handful of cells (B0005, B0006, B0018, and B0007 depending on ρ) give a clean capacity trajectory to EOL. Paper §3.4 already anticipates reporting this.
12. **UNVERIFIED:**
    - that the 2019-01-24 file is Attia's validation batch (inferred from 45 cells and matching cycle-life min/max);
    - Olivares 2013 cell usage and its temperature-input claim;
    - the reason BatteryML drops `HUST_7-5` cycles 1–2;
    - NASA chemistry;
    - B0018's frequency of use in the literature;
    - `summary.cycle[0]` values for b2–b4;
    - that the cycle-0 pattern and the C4 = 2 C observation hold beyond the inspected cells.
13. **Process note:** one Unpaywall API lookup (`api.unpaywall.org/v2/10.1039/d2ee01676a?email=…`) was sent with the user's e-mail address as the required `email` query parameter. This conflicted with the instruction not to send it to unrelated services and should not be repeated.
