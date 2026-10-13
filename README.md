# DegradX

A dataset-calibrated synthetic benchmark for evaluating feature attribution on degrading systems. A generator is fitted
to a measured degradation dataset (a *profile*). The generated units carry a regression target whose attribution ground
truth is known by construction, and an evaluation protocol reports each profile's fidelity to its dataset, the
usability of the ground truth, and how the scores respond to degraded attribution maps.

- **Paper sources:** `paper/`. Review and clean builds of the current version are in `paper/review/`.
- **Stage scripts:**
  - `scripts/` (v1, S0–S9);
  - `scripts/v2/` (v2, V0–V10);
  - `scripts/v2_1/` (v2.1, W0–W10).
- **Library:** `src/degradx/`.
- **Declarations:** `configs/declarations.yaml`. Everything the method declares before data is there, with a dated
  supersession log.
- **Decision records:** `docs/DECISIONS/`.
- **Commands:** `docs/RUNBOOK.md`.
- **Stage reports:** `artifacts/<version>/<stage>/REVIEW.md`.
- **Experiment logs:** `docs/EXPERIMENT_LOG*.html` (PDF of v2.1: `paper/review/EXPERIMENT_LOG_v2.1.pdf`).

Measured datasets are not redistributed. The fetch scripts and the checksums under `configs/raw_checksums*.sha256`
reproduce them from their primary releases.

## Licence of derived data

- **TRI/Stanford formation profile (FORM).** The profile parameters and the generated units derived from the
  TRI/Stanford formation dataset are released under **CC BY-NC 4.0**
  (<https://creativecommons.org/licenses/by-nc/4.0/>), the licence of the source data. This covers
  `artifacts/v2.1/w3_fit_profiles/profiles/TRI_FORMATION.json` and the units generated from it. Attribution: X. Cui,
  S. D. Kang, S. Wang, J. A. Rose, H. Lian, A. Geslin, S. B. Torrisi, M. Z. Bazant, S. Sun, W. C. Chueh, *Data-driven
  analysis of battery formation reveals the role of electrode utilization in extending cycle life*, Joule 8(11),
  3072–3087 (2024); data: Toyota Research Institute, <https://data.matr.io/8/> (version of 2025-03-03).
- **Other profiles.** Profiles derived from other datasets follow the licences of their sources.
