# Stage 0 — Setup and pre-declaration

## What ran

- `bash scripts/s0_setup_env.sh`: 9.4 s wall-clock (venv already existed). Log: `logs/setup_env.log`.
  - Device: NVIDIA GeForce GTX 1660 Ti (sm_75), torch 2.14.0+cu130.
- Seven research investigations ran before any data-consuming code: `docs/S0_RESEARCH/`.
- `pytest -q`: 4 passed.
- Raw data downloaded, not yet ingested; S1 owns ingestion and checksums. Byte counts match the servers' `content-length`:
  - MATR: 4 batch `.mat` files
  - HUST: `hust_data.zip`
  - NASA PCoE: `5.Battery_Data_Set.zip`

## What came out

- **Environment** (`pyproject.toml`, `requirements-lock.txt`, `scripts/s0_setup_env.sh`):
  - Python 3.12.3, numpy 1.26.4 (BatteryML pin), BatteryML @ 2861ae3b, captum 0.9.0, timeshap 1.0.4 + shap 0.49.1.
  - The environment rebuilt from the lock matches it exactly (`docs/S0_RESEARCH/env.md`).
- **LaTeX:** TinyTeX / pdfTeX 1.40.29.
  - The paper as given compiles to 16 pages with the same fonts as the committed PDF.
  - No LaTeX or package warnings, 2 over/underfull boxes (baseline for "no new warnings").
- **Frozen declarations:** `configs/declarations.yaml` (revision r1), split exactly as paper §3.3 l.238 into `estimated_from_data` and `declared_by_design`.
- **Figure style:** `src/degradx/viz/style.py`, reconstructed from the published PDFs. It reproduces Figures 1–4 byte-identically under matplotlib 3.10.8. Figure 5 has a different style and no script.
- **Package skeleton and utilities** (`src/degradx/utils`):
  - stage CLI standard
  - `run.json` / `timing.json` provenance
  - seeds separated by source
  - check tables with non-zero exit

No figures at this stage.

## Checks

| check | expected | observed | pass/fail |
|---|---|---|---|
| CUDA available, device arch in torch build | sm_75 in arch list | sm_75 in `['sm_75', …]` | pass |
| deterministic LSTM forward+backward on CUDA | runs, bitwise repeatable | OK; identical across processes (env.md) | pass |
| BatteryML importable at pinned commit | 2861ae3b | 2861ae3b | pass |
| TimeSHAP explainer importable | import OK | OK only with the `Kernel` alias shim | pass (with shim) |
| TimeSHAP exactness on a linear model | Shapley = w·(x − background) | error ~1e-14 (env.md) | pass |
| Paper as given compiles with pdfTeX | 16 pages, no errors | 16 pages, 0 LaTeX warnings | pass |
| Declarations split matches §3.3 | 7 estimated items, declared list covers l.238 | E1–E7; D-items present | pass |
| unit tests | pass | 4 passed | pass |

## Anomalies

1. **tectonic (XeTeX) silently drops glyphs.** Every em/en dash and `ć`/`ł` vanished from the PDF. I switched to TinyTeX/pdfTeX, the engine of the committed PDF.
2. **timeshap 1.0.4 does not import with shap ≥ 0.43.** The package is unmaintained. Fixed by a one-line alias, validated for exactness.
3. **TimeSHAP's library defaults do not produce a dense L×C map.**
   - Its default `l1_reg='auto'` zeroes most cells.
   - Cell level needs explicit `top_x_events=L, top_x_feats=C`.
   - "Default configuration" therefore has to be declared explicitly (attribution section).
4. **Captum IG on a cuDNN LSTM in `eval()` fails.** It runs with cuDNN disabled inside attribution.
5. **BatteryML's MATR preprocessor would peak at ~12.5 GB** against ~9 GB available.
   - S1 will run it batch by batch through BatteryML's own functions.
   - BatteryML drops the MATR summary channels (charge time, temperature statistics).
   - BatteryML skips cycle 0, which holds real data in batches 2–4.
6. **Dataset facts that shape S2** (documentation only; S2 measures):
   - HUST has no temperature or IR.
   - NASA PCoE has only a handful of cells with clean trajectories that cross a fixed-capacity threshold; most 4 °C cells contain zero-capacity runs.
   - NASA's unit count may be too small for the fidelity measurements to establish much. The paper already anticipates this (l.253).
7. **Process violation:** one research agent sent the account e-mail as the `email` parameter of a single Unpaywall API lookup. It was disclosed in `docs/S0_RESEARCH/datasets.md` §5 and is not to be repeated.
8. **Citation-accuracy flags** for the authors, not acted on:
   - `pan2022` uses CALCE data and a rest-time threshold, not residual decomposition (paper l.241).
   - The temperature-input claim attributed to `olivares2013` may originate in Pola 2016 (l.173).

## Decisions needed

1. **OPEN items 1–4 in `declarations.yaml`:**
   - channel roles and exactness of the reference model
   - redundancy of zero-weight channels
   - ρ anchor versus nominal capacity
   - attribution baseline

   Resolved by review comments C1–C4 in revision r2.
2. **Confirm every `UNDERSPECIFIED-IN-PAPER` value** flagged `affects_fitted_parameters: true` before S4. S1–S3 may run on them; nothing past S3 may:
   - ρ and grid
   - SG window/order/mode
   - residual, residual scale, multiple k, minimum run
   - pattern types and enable rule
   - family equations, bounds, solver, selection protocol
   - φ_c method
   - noise form
   - channel candidates and availability rule
   - measured split fractions
3. **MATR scope.** BatteryML's MATR bundle holds four batches; the paper cites Severson 2019 (the first three). r1 includes all four batches and reports the Severson subset alongside. Confirm or restrict to Severson.
4. **TimeSHAP configuration.** Accept `l1_reg='auto'` (library default, sparse maps with ties) as primary with `l1_reg=False` as sensitivity, or the reverse.
