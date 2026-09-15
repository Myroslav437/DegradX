| check | expected | observed | result |
|---|---|---|---|
| MATR: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data) | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | pass |
| MATR: capacity mapping affine in z per unit (Eq. 3) | < 1e-9 Ah | 0.00e+00 | pass |
| MATR: phi_charge_time monotone on [0, 1] | monotone | True | pass |
| MATR: phi_mean_discharge_voltage monotone on [0, 1] | monotone | True | pass |
| MATR: phi_internal_resistance monotone on [0, 1] | monotone | True | pass |
| MATR: phi_temperature_mean monotone on [0, 1] | monotone | True | pass |
| MATR: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units | >= 0.90 | 1.000 | pass |
| MATR: theta not collapsing to bounds (units with any parameter at a bound <= 20%) | <= 0.20 | 0.022 | pass |
| MATR: theta from >= 5 units reaching EOL (D02 minimum; else theta statistics void) | >= 5 | 90 | pass |
| MATR: D05 enable rule evaluated for both types | evaluated | evaluated | pass |
| HUST: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data) | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | pass |
| HUST: capacity mapping affine in z per unit (Eq. 3) | < 1e-9 Ah | 1.11e-16 | pass |
| HUST: phi_charge_time monotone on [0, 1] | monotone | True | pass |
| HUST: phi_mean_discharge_voltage monotone on [0, 1] | monotone | True | pass |
| HUST: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units | >= 0.90 | 1.000 | pass |
| HUST: theta not collapsing to bounds (units with any parameter at a bound <= 20%) | <= 0.20 | 0.000 | pass |
| HUST: theta from >= 5 units reaching EOL (D02 minimum; else theta statistics void) | >= 5 | 54 | pass |
| HUST: D05 enable rule evaluated for both types | evaluated | evaluated | pass |
| NASA_PCoE: estimated/declared split matches paper §3.3 (E1-E7 only under estimated_from_data) | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | ['E1_theta_distribution', 'E2_family_choice', 'E3_channel_mappings', 'E4_channel_covariance', 'E5_noise', 'E6_patterns', 'E7_length_distribution'] | pass |
| NASA_PCoE: capacity mapping affine in z per unit (Eq. 3) | < 1e-9 Ah | 2.91e-16 | pass |
| NASA_PCoE: phi_charge_time monotone on [0, 1] | monotone | True | pass |
| NASA_PCoE: phi_mean_discharge_voltage monotone on [0, 1] | monotone | True | pass |
| NASA_PCoE: phi_temperature_mean monotone on [0, 1] | monotone | True | pass |
| NASA_PCoE: fit residuals centred (|mean| <= 0.5 residual scale) in >= 90% of units | >= 0.90 | 1.000 | pass |
| NASA_PCoE: theta not collapsing to bounds (units with any parameter at a bound <= 20%) | <= 0.20 | 0.125 | pass |
| NASA_PCoE: theta from >= 5 units reaching EOL (D02 minimum; else theta statistics void) | >= 5 | 8 | pass |
| NASA_PCoE: D05 enable rule evaluated for both types | evaluated | evaluated | pass |
