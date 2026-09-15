| check | expected | observed | result |
|---|---|---|---|
| raw MATR/MATR_batch_20170512.mat present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'first verification (no published hash)'} | pass |
| raw MATR/MATR_batch_20170630.mat present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'first verification (no published hash)'} | pass |
| raw MATR/MATR_batch_20180412.mat present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'first verification (no published hash)'} | pass |
| raw MATR/MATR_batch_20190124.mat present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'first verification (no published hash)'} | pass |
| raw HUST/hust_data.zip present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'published/S0'} | pass |
| raw NASA_PCoE/5.Battery_Data_Set.zip present, size and sha256 as recorded | present, size and hash match | {'present': True, 'size_ok': True, 'sha256_ok': True, 'sha256_reference': 'published/S0'} | pass |
| no duplicate cell ids across datasets | unique | 291 ids, unique=True | pass |
| MATR: cycle_number strictly increasing within every cell | True | True | pass |
| MATR: units plausible, median cycle and >= 99% of cycles with voltage within 1.5-4.5 V | median inside, >= 0.99 | median inside=True, fraction 0.99992 | pass |
| MATR: every finite cycle has voltage within 1.5-4.5 V | all cycles | 12 cycles in 1 cells outside; 0 cycles with NaN samples | warn |
| MATR: units plausible, median cycle and >= 99% of cycles with |current| <= 10 C | median inside, >= 0.99 | median inside=True, fraction 0.99998 | pass |
| MATR: every finite cycle has |current| <= 10 C | all cycles | 3 cycles in 3 cells outside; 0 cycles with NaN samples | warn |
| MATR: units plausible, median cycle and >= 99% of cycles with cycler capacity within [0, 1.5 x nominal] Ah | median inside, >= 0.99 | median inside=True, fraction 0.99999 | pass |
| MATR: every finite cycle has cycler capacity within [0, 1.5 x nominal] Ah | all cycles | 1 cycles in 1 cells outside; 0 cycles with NaN samples | warn |
| MATR: units plausible, median cycle and >= 99% of cycles with temperature within -5..80 degC | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| MATR: every finite cycle has temperature within -5..80 degC | all cycles | 0 cycles in 0 cells outside; 0 cycles with NaN samples | pass |
| MATR: median cycle duration in seconds within documented range | (1800, 7200) s | 2721 s | pass |
| MATR: time non-decreasing within cycles | 0 negative steps | max fraction 1.51e-03 | warn |
| HUST: cycle_number strictly increasing within every cell | True | True | pass |
| HUST: units plausible, median cycle and >= 99% of cycles with voltage within 1.5-4.5 V | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| HUST: every finite cycle has voltage within 1.5-4.5 V | all cycles | 0 cycles in 0 cells outside; 0 cycles with NaN samples | pass |
| HUST: units plausible, median cycle and >= 99% of cycles with |current| <= 10 C | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| HUST: every finite cycle has |current| <= 10 C | all cycles | 0 cycles in 0 cells outside; 0 cycles with NaN samples | pass |
| HUST: units plausible, median cycle and >= 99% of cycles with cycler capacity within [0, 1.5 x nominal] Ah | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| HUST: every finite cycle has cycler capacity within [0, 1.5 x nominal] Ah | all cycles | 0 cycles in 0 cells outside; 0 cycles with NaN samples | pass |
| HUST: median cycle duration in seconds within documented range | (1800, 14400) s | 3175 s | pass |
| HUST: time non-decreasing within cycles | 0 negative steps | max fraction 0.00e+00 | pass |
| NASA_PCoE: cycle_number strictly increasing within every cell | True | True | pass |
| NASA_PCoE: units plausible, median cycle and >= 99% of cycles with voltage within 1.5-4.5 V | median inside, >= 0.99 | median inside=True, fraction 0.99380 | pass |
| NASA_PCoE: every finite cycle has voltage within 1.5-4.5 V | all cycles | 17 cycles in 5 cells outside; 12 cycles with NaN samples | warn |
| NASA_PCoE: units plausible, median cycle and >= 99% of cycles with |current| <= 10 C | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| NASA_PCoE: every finite cycle has |current| <= 10 C | all cycles | 0 cycles in 0 cells outside; 12 cycles with NaN samples | pass |
| NASA_PCoE: units plausible, median cycle and >= 99% of cycles with cycler capacity within [0, 1.5 x nominal] Ah | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| NASA_PCoE: every finite cycle has cycler capacity within [0, 1.5 x nominal] Ah | all cycles | 0 cycles in 0 cells outside; 0 cycles with NaN samples | pass |
| NASA_PCoE: units plausible, median cycle and >= 99% of cycles with temperature within -5..80 degC | median inside, >= 0.99 | median inside=True, fraction 1.00000 | pass |
| NASA_PCoE: every finite cycle has temperature within -5..80 degC | all cycles | 0 cycles in 0 cells outside; 12 cycles with NaN samples | pass |
| NASA_PCoE: median cycle duration in seconds within documented range | (3600, 86400) s | 14190 s | pass |
| NASA_PCoE: time non-decreasing within cycles | 0 negative steps | max fraction 0.00e+00 | pass |
| MATR: 180 unique cells (BatteryML convention) | 180 | 180 | pass |
| MATR: carry-over keys b2c7/8/9/15/16 not emitted | absent | absent | pass |
| MATR 2017-05-12: cells emitted | 46 | 46 | pass |
| MATR 2017-05-12: stored + dropped + skipped index 0 equals file cycle entries | 42204 | 42204 | pass |
| MATR 2017-06-30: cells emitted | 43 | 43 | pass |
| MATR 2017-06-30: stored + dropped + skipped index 0 equals file cycle entries | 21527 | 21527 | pass |
| MATR 2018-04-12: cells emitted | 46 | 46 | pass |
| MATR 2018-04-12: stored + dropped + skipped index 0 equals file cycle entries | 51007 | 51007 | pass |
| MATR 2019-01-24: cells emitted | 45 | 45 | pass |
| MATR 2019-01-24: stored + dropped + skipped index 0 equals file cycle entries | 39673 | 39673 | pass |
| MATR merged b1c0..4 lengths equal merged entries | {'MATR_b1c0': 1851, 'MATR_b1c1': 2159, 'MATR_b1c2': 2236, 'MATR_b1c3': 1433, 'MATR_b1c4': 1708} | {'MATR_b1c0': 1851, 'MATR_b1c1': 2159, 'MATR_b1c2': 2236, 'MATR_b1c3': 1433, 'MATR_b1c4': 1708} | pass |
| HUST: 77 cells equal to ESI Table S1 channels | Table S1 channels | 77 cells; diff [] | pass |
| HUST: per-cell cycle counts equal Table S1 cycle life (7-5 minus 2) | 0 mismatches | 0 mismatches | pass |
| HUST: total stored cycles = 146,120 | 146120 | 146120 | pass |
| HUST: cycler capacity attached to every cycle | 0 | 0 | pass |
| NASA: 34 unique cells | 34 | 34 | pass |
| NASA: one cycle per discharge operation (counts equal the file scan) | 0 mismatches | 0 mismatches | pass |
| NASA BatteryData carries every BatteryData field present in MATR | ['already_spent_cycles', 'anode_material', 'cathode_material', 'cell_id', 'charge_protocol', 'cycle_data', 'depth_of_charge', 'depth_of_discharge', 'description', 'discharge_protocol', 'electrolyte_material', 'form_factor', 'max_current_limit_in_A', 'max_voltage_limit_in_V', 'min_current_limit_in_A', 'min_voltage_limit_in_V', 'nominal_capacity_in_Ah', 'reference'] | missing [] | pass |
| NASA CycleData has the core CycleData fields of MATR | ['charge_capacity_in_Ah', 'current_in_A', 'cycle_number', 'discharge_capacity_in_Ah', 'internal_resistance_in_ohm', 'temperature_in_C', 'time_in_s', 'voltage_in_V'] | missing [] | pass |
| NASA BatteryData carries every BatteryData field present in HUST | ['already_spent_cycles', 'anode_material', 'cathode_material', 'cell_id', 'charge_protocol', 'cycle_data', 'depth_of_charge', 'depth_of_discharge', 'description', 'discharge_protocol', 'electrolyte_material', 'form_factor', 'max_current_limit_in_A', 'max_voltage_limit_in_V', 'min_current_limit_in_A', 'min_voltage_limit_in_V', 'nominal_capacity_in_Ah', 'reference'] | missing [] | pass |
| NASA CycleData has the core CycleData fields of HUST | ['charge_capacity_in_Ah', 'current_in_A', 'cycle_number', 'discharge_capacity_in_Ah', 'internal_resistance_in_ohm', 'temperature_in_C', 'time_in_s', 'voltage_in_V'] | missing [] | pass |
| NASA cycle_number strictly increasing from 1 | 1..N | 1..168 | pass |
| NASA series stored as list[float] like BatteryML | list[float] | float | pass |
| NASA time_in_s non-decreasing within every cycle | True | True | pass |
| NASA B0005 first discharge: converted V/I/T equal raw arrays | max abs diff 0 | 0.0 | pass |
| NASA B0005 capacity_cycler_Ah equals raw Capacity for every discharge | equal | max diff 0.0 | pass |
