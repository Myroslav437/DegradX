| check | expected | observed | result |
|---|---|---|---|
| archive: every declared aging member was extracted (extraction manifest) | none missing | [] | pass |
| files: every aging file parses as BEEP JSON | all | all | pass |
| cell_scope (i): every aging file name matches the declared seq pattern (undocumented files counted) | reported | 0 undocumented: [] | pass |
| cell_scope.several_files_per_seq: no seq has more than one file | none | [] | pass |
| converter: capacity in the cycle table equals summary.discharge_capacity | identical | 0.00e+00 | pass |
| converter: mean discharge voltage equals summary discharge_energy / discharge_capacity | <= 1e-12 relative | 1.55e-14 | pass |
| charge-time validation: failing evaluable files <= 10 % (channels.charge_time.failure; stop above) | <= 10 % | 0 of 178 evaluable (0.0%); not evaluable 4 | pass |
| index: summary and diagnostic_summary cycle_index sets are disjoint | disjoint | [] | pass |
| index: summary cycle_index strictly increasing | all | [] | pass |
| index: cycle_index contiguous from 0 over summary + diagnostic_summary (reported) | reported | 181 of 182 | pass |
| diagnostics: rpt_0.05C discharge current about 0.012 A (C/20) | within 10 % | median 0.0120 A, range [0.0120, 0.0120] | pass |
| diagnostics: rpt_0.2C discharge current about 0.048 A (C/5) | within 10 % | median 0.0480 A, range [0.0480, 0.0480] | pass |
| diagnostics: per-cell layout matches HPPC 0, 8, 24, 127+103k / RPT 1, 25, 128+103k / 2, 26, 129+103k (reported) | reported | 543 of 546 (cell, type) pairs | pass |
| aging protocol: modal tuple within tolerance of the documented one (E2 on the files) | 0.24 A / 0.18 A / 4.4 V / 3.0 V | I_chg 0.24 I_dis 0.18 V_cv 4.4 V_end 3.0 | pass |
| aging protocol: incomplete cycles <= 5 % of regular cycles, pooled (E2 on the files) | <= 5 % | 0.00% | pass |
| aging protocol: no second aging protocol (two or more agreeing out-of-tolerance sources) | none | sources 0, agreeing pairs [] | pass |
| structuring_parameters: nominal_capacity 0.24 in every file (reported otherwise) | 0.24 | {0.24: 182} | pass |
| source: raw_data absent or empty in every documented file, so cycles_interpolated is the profile-wide source (channels.charge_time.source) | reported | files with raw_data: 0 | pass |
| formation mapping: protocol_id equals the authors' consecutive-triplet grouping (reported) | one protocol per triplet | 0 mixed triplets; 63 protocol groups incl. baseline | pass |
