| check | expected | observed | result |
|---|---|---|---|
| MATR: measured split identical to v1 (same units held out) | identical | True | pass |
| MATR: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data) | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | pass |
| MATR: capacity affine in z per unit with the unit's own q1 (Eq. 3; X2 capacity mapping) | < 1e-9 Ah | 0.00e+00 | pass |
| MATR: phi_charge_time monotone on [0, 1] (backfitted) | monotone | True | pass |
| MATR: phi_mean_discharge_voltage monotone on [0, 1] (backfitted) | monotone | True | pass |
| MATR: phi_internal_resistance monotone on [0, 1] (backfitted) | monotone | True | pass |
| MATR: phi_temperature_mean monotone on [0, 1] (backfitted) | monotone | True | pass |
| MATR: backfit of charge_time converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 6 it., last change δ 8.28e-05 / φ 3.38e-04 (tol 7.80e-04) | pass |
| MATR: median offset of charge_time over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| MATR: backfit of mean_discharge_voltage converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 6 it., last change δ 2.95e-06 / φ 1.19e-05 (tol 2.12e-05) | pass |
| MATR: median offset of mean_discharge_voltage over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| MATR: backfit of internal_resistance converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 6 it., last change δ 7.48e-09 / φ 3.35e-08 (tol 3.09e-07) | pass |
| MATR: median offset of internal_resistance over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| MATR: backfit of temperature_mean converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 6 it., last change δ 4.89e-06 / φ 3.55e-05 (tol 1.47e-04) | pass |
| MATR: median offset of temperature_mean over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| MATR: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units | >= 0.90 | 1.000 | pass |
| MATR: theta not collapsing to bounds (units with any parameter at a bound <= 20%) | <= 0.20 | 0.022 | pass |
| MATR: theta from >= 5 units reaching EOL (D02) | >= 5 | 90 | pass |
| MATR: trajectory family unchanged from v1 (capacity cleaning unchanged) | two_term_exponential | two_term_exponential | pass |
| HUST: measured split identical to v1 (same units held out) | identical | True | pass |
| HUST: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data) | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | pass |
| HUST: capacity affine in z per unit with the unit's own q1 (Eq. 3; X2 capacity mapping) | < 1e-9 Ah | 1.11e-16 | pass |
| HUST: phi_charge_time monotone on [0, 1] (backfitted) | monotone | True | pass |
| HUST: phi_mean_discharge_voltage monotone on [0, 1] (backfitted) | monotone | True | pass |
| HUST: backfit of charge_time converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 5 it., last change δ 3.18e-06 / φ 2.29e-05 (tol 1.28e-03) | pass |
| HUST: median offset of charge_time over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| HUST: backfit of mean_discharge_voltage converged within 200 iterations (declared tolerance 1e-4 of the mapping range) | converged | 4 it., last change δ 6.78e-07 / φ 3.49e-06 (tol 5.57e-06) | pass |
| HUST: median offset of mean_discharge_voltage over fitting units = 0 (constraint) | 0 | 0.00e+00 | pass |
| HUST: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units | >= 0.90 | 1.000 | pass |
| HUST: theta not collapsing to bounds (units with any parameter at a bound <= 20%) | <= 0.20 | 0.000 | pass |
| HUST: theta from >= 5 units reaching EOL (D02) | >= 5 | 54 | pass |
| HUST: trajectory family unchanged from v1 (capacity cleaning unchanged) | rollover | rollover | pass |
