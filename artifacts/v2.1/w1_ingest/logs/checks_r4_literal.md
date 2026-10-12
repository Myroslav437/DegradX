| check | expected | observed | result |
|---|---|---|---|
| archive: every declared aging member was extracted (extraction manifest) | none missing | [] | pass |
| files: every aging file parses as BEEP JSON | all | all | pass |
| cell_scope (i): every aging file name matches the declared seq pattern (undocumented files counted) | reported | 0 undocumented: [] | pass |
| cell_scope.several_files_per_seq: no seq has more than one file | none | [] | pass |
| converter: capacity in the cycle table equals summary.discharge_capacity | identical | 0.00e+00 | pass |
| converter: mean discharge voltage equals summary discharge_energy / discharge_capacity | <= 1e-12 relative | 2.89e-15 | pass |
| charge-time validation: failing evaluable files <= 10 % (channels.charge_time.failure; stop above) | <= 10 % | 0 of 178 evaluable (0.0%); not evaluable 4 | pass |
| index: summary and diagnostic_summary cycle_index sets are disjoint | disjoint | [] | pass |
| index: summary cycle_index strictly increasing | all | [] | pass |
| index: cycle_index contiguous from 0 over summary + diagnostic_summary (reported) | reported | 181 of 182 | pass |
| diagnostics: rpt_0.05C discharge current about 0.012 A (C/20) | within 10 % | median 0.0120 A, range [0.0120, 0.0120] | pass |
| diagnostics: rpt_0.2C discharge current about 0.048 A (C/5) | within 10 % | median 0.0480 A, range [0.0480, 0.0480] | pass |
| diagnostics: per-cell layout matches HPPC 0, 8, 24, 127+103k / RPT 1, 25, 128+103k / 2, 26, 129+103k (reported) | reported | 543 of 546 (cell, type) pairs | pass |
| aging protocol: modal tuple within tolerance of the documented one (E2 on the files) | 0.24 A / 0.18 A / 4.4 V / 3.0 V | I_chg 0.24 I_dis 0.18 V_cv 4.4 V_end 3.0 | pass |
| aging protocol: incomplete cycles <= 5 % of regular cycles, pooled (E2 on the files) | <= 5 % | 0.00% | pass |
| aging protocol: no second aging protocol (two or more agreeing out-of-tolerance sources) | none | sources 40, agreeing pairs [(100, 146), (100, 209), (100, 299), (100, 313), (101, 109), (101, 110), (101, 137), (101, 224), (101, 275), (102, 103), (102, 104), (102, 183), (102, 201), (102, 221), (102, 274), (102, 314), (103, 221), (103, 226), (103, 274), (103, 286), (103, 314), (103, 318), (104, 146), (104, 183), (104, 201), (104, 221), (104, 274), (109, 137), (109, 149), (109, 224), (109, 275), (110, 137), (110, 148), (110, 273), (115, 139), (115, 148), (115, 161), (115, 177), (115, 273), (115, 282), (115, 283), (115, 317), (116, 226), (116, 286), (116, 290), (116, 318), (116, 320), (116, 322), (137, 224), (137, 275), (139, 161), (139, 177), (139, 282), (139, 283), (139, 317), (140, 215), (140, 290), (140, 297), (140, 319), (140, 322), (146, 201), (146, 209), (148, 161), (148, 273), (149, 224), (149, 275), (149, 299), (149, 313), (161, 177), (161, 282), (161, 283), (161, 317), (177, 282), (177, 283), (177, 317), (183, 201), (183, 221), (183, 274), (201, 221), (201, 274), (209, 299), (209, 313), (215, 290), (215, 297), (215, 319), (215, 322), (221, 274), (221, 314), (224, 275), (226, 286), (226, 314), (226, 318), (226, 320), (226, 322), (274, 314), (275, 299), (275, 313), (282, 283), (282, 317), (283, 317), (286, 314), (286, 318), (286, 320), (290, 297), (290, 318), (290, 320), (290, 322), (297, 319), (297, 322), (299, 313), (314, 318), (318, 320), (318, 322), (320, 322)] | FAIL |
| structuring_parameters: nominal_capacity 0.24 in every file (reported otherwise) | 0.24 | {0.24: 182} | pass |
| source: raw_data absent or empty in every documented file, so cycles_interpolated is the profile-wide source (channels.charge_time.source) | reported | files with raw_data: 0 | pass |
| formation mapping: protocol_id equals the authors' consecutive-triplet grouping (reported) | one protocol per triplet | 0 mixed triplets; 63 protocol groups incl. baseline | pass |
