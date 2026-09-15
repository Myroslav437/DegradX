#!/usr/bin/env bash
# Full DegradX programme, S1 -> S9, with the invocations that produced the committed artifacts (docs/RUNBOOK.md).
# Run from the repository root after `bash scripts/s0_setup_env.sh`:   bash scripts/run_all.sh
# Wall clock on the reference machine (16 cores, GTX 1660 Ti 6 GB, 15 GB RAM): about 11 h, most of it S6 and S8.
#
#   DEGRADX_FROM=s5 bash scripts/run_all.sh    resume from a stage (earlier stages' artifacts must exist)
#   DEGRADX_WORKERS=8                          process-pool size for S1-S4 (default 12)
set -euo pipefail

PY="${DEGRADX_PY:-.venv/bin/python}"
W="${DEGRADX_WORKERS:-12}"
FROM="${DEGRADX_FROM:-s1}"
stages=(s1 s2 s3 s4 s5 s6 s7 s8 s9)
run=0
for s in "${stages[@]}"; do [[ "$s" == "$FROM" ]] && run=1; declare "do_$s=$run"; done
if [[ "$run" != 1 ]]; then echo "unknown stage in DEGRADX_FROM: $FROM" >&2; exit 2; fi

step() { echo; echo "=== $* ==="; "$@"; }

if [[ $do_s1 == 1 ]]; then step "$PY" scripts/s1_fetch_data.py --device cpu --workers 4; fi
if [[ $do_s2 == 1 ]]; then step "$PY" scripts/s2_audit_datasets.py --workers "$W"; fi
if [[ $do_s3 == 1 ]]; then step "$PY" scripts/s3_fit_profiles.py --workers "$W"; fi
if [[ $do_s4 == 1 ]]; then step "$PY" scripts/s4_generate_units.py --workers "$W"; fi
if [[ $do_s5 == 1 ]]; then step "$PY" scripts/s5_fidelity.py --datasets MATR HUST NASA_PCoE; fi
if [[ $do_s6 == 1 ]]; then
    step "$PY" scripts/s6_usability.py --datasets MATR HUST
    step "$PY" scripts/s6_usability.py --datasets NASA_PCoE
fi
if [[ $do_s7 == 1 ]]; then
    rm -f artifacts/s7_responsiveness/logs/part2_rows.jsonl      # part two resumes from this cache; start clean
    step "$PY" scripts/s7_responsiveness.py
fi
if [[ $do_s8 == 1 ]]; then
    # D23: TimeSHAP on 40 of the 120 scored windows, sampling seeds 0-1 on trained models and 0 on the reference model
    for ds in MATR HUST NASA_PCoE; do
        step "$PY" scripts/s8_reference_methods.py --datasets "$ds" --timeshap-windows 40 --timeshap-seeds 0 1 \
            --timeshap-seeds-reference 0 --secondary-background
    done
    step "$PY" scripts/s8_reference_methods.py --checks-only
fi
if [[ $do_s9 == 1 ]]; then
    step "$PY" scripts/s9_write_paper.py --tables fidelity properties figure_fidelity resolution figure_degradation usability \
        range figure_range reference
    step bash scripts/build_paper.sh
fi
