#!/usr/bin/env bash
# Full DegradX pipeline, S01 -> S16, with the invocations that produced the committed artifacts and results/.
# Run from the repository root after `bash scripts/setup_env.sh`:   bash scripts/run_all.sh
# Compute on the reference machine (16 cores, GTX 1660 Ti 6 GB, 15 GB RAM): about 10 h, most of it TSTR, the LSTM
# ensembles and TimeSHAP, plus downloading and ingesting the raw data (~12 GB for MATR and HUST) and the TRI/Stanford
# formation archives.
#
#   DEGRADX_FROM=s09 bash scripts/run_all.sh   resume from a stage (earlier stages' artifacts must exist)
#   DEGRADX_WORKERS=8                          process-pool size (default 12)
#
# Stages S09-S15 run once for MATR and HUST and once for FORM (TRI_FORMATION); both runs write the same stage directory,
# with run records and checks named by dataset group (*_MATR_HUST, *_TRI_FORMATION).
set -euo pipefail

PY="${DEGRADX_PY:-.venv/bin/python}"
W="${DEGRADX_WORKERS:-12}"
FROM="${DEGRADX_FROM:-s01}"
stages=(s01 s02 s03 s04 s05 s06 s07 s08 s09 s10 s11 s12 s13 s14 s15 s16)
run=0
for s in "${stages[@]}"; do [[ "$s" == "$FROM" ]] && run=1; declare "do_$s=$run"; done
if [[ "$run" != 1 ]]; then echo "unknown stage in DEGRADX_FROM: $FROM" >&2; exit 2; fi

step() { echo; echo "=== $* ==="; "$@"; }
MH=(--datasets MATR HUST)
F=(--datasets TRI_FORMATION)

# measured data
if [[ $do_s01 == 1 ]]; then step "$PY" scripts/s01_ingest_matr_hust.py --device cpu --workers 4; fi
if [[ $do_s02 == 1 ]]; then
    step "$PY" scripts/s02a_fetch_form.py
    step "$PY" scripts/s02b_extract_form.py
    step "$PY" scripts/s02c_ingest_form.py --workers 3
fi
if [[ $do_s03 == 1 ]]; then step "$PY" scripts/s03_audit_matr_hust.py --workers "$W"; fi
if [[ $do_s04 == 1 ]]; then
    step "$PY" scripts/s04_audit_form.py --workers 8 --device cpu
    step "$PY" scripts/s04b_audit_form_mechanism.py
fi
# baseline generator (no per-unit offsets, independent noise): the comparison rows of Tables 1 and 3
if [[ $do_s05 == 1 ]]; then step "$PY" scripts/s05_fit_baseline.py --workers "$W"; fi
if [[ $do_s06 == 1 ]]; then step "$PY" scripts/s06_generate_baseline.py --workers "$W" --skip-rho; fi
if [[ $do_s07 == 1 ]]; then step "$PY" scripts/s07_fidelity_baseline.py "${MH[@]}"; fi
if [[ $do_s08 == 1 ]]; then step "$PY" scripts/s08_tstr_isolation_baseline.py; fi
# profiles with per-unit offsets and correlated noise
if [[ $do_s09 == 1 ]]; then
    step "$PY" scripts/s09_fit_profiles.py "${MH[@]}" --device cpu --workers "$W"
    step "$PY" scripts/s09_fit_profiles.py "${F[@]}" --device cpu --workers 8
fi
if [[ $do_s10 == 1 ]]; then
    step "$PY" scripts/s10_generate_units.py "${MH[@]}" --workers "$W"
    step "$PY" scripts/s10_generate_units.py "${F[@]}" --device cpu --workers 8
fi
if [[ $do_s11 == 1 ]]; then
    step "$PY" scripts/s11_fidelity.py "${MH[@]}"
    step "$PY" scripts/s11b_fidelity_readability.py "${MH[@]}"
    step "$PY" scripts/s11_fidelity.py "${F[@]}" --workers 8
    step "$PY" scripts/s11b_fidelity_readability.py "${F[@]}"
fi
if [[ $do_s12 == 1 ]]; then step "$PY" scripts/s12_tstr_without_correlated_noise.py "${MH[@]}"; fi
if [[ $do_s13 == 1 ]]; then
    step "$PY" scripts/s13_usability.py "${MH[@]}"
    step "$PY" scripts/s13_usability.py "${F[@]}"
fi
if [[ $do_s14 == 1 ]]; then
    step "$PY" scripts/s14_degraded_map_test.py "${MH[@]}"
    step "$PY" scripts/s14_degraded_map_test.py "${F[@]}" --device cpu
fi
if [[ $do_s15 == 1 ]]; then
    # TimeSHAP at full scale; the pool configuration is read from tables/feasibility_<group>.json ("chosen")
    step "$PY" scripts/s15_reference_values.py "${MH[@]}" --equivalence --run --score
    step "$PY" scripts/s15_reference_values.py "${F[@]}" --equivalence --run --score
fi
# results
if [[ $do_s16 == 1 ]]; then step "$PY" scripts/s16_export_results.py; fi
