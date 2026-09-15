| check | expected | observed | result |
|---|---|---|---|
| MATR seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 249438 windows | pass |
| MATR seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.65e-16 | pass |
| MATR seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.019e-03, SE 1.304e-03 | pass |
| MATR seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 249438 windows | pass |
| MATR seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 3.40e-16 | pass |
| MATR seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.007e-03, SE 1.302e-03 | pass |
| MATR seed 0 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 249438 windows | pass |
| MATR seed 0 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 6.94e-16 | pass |
| MATR seed 0 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.055e-03, SE 1.306e-03 | pass |
| MATR seed 0: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| MATR seed 0: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.021 noise SD (SE 0.017) | pass |
| MATR seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | -0.018 noise SD (SE 0.020) | pass |
| MATR seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.007 noise SD (SE 0.030) | pass |
| MATR seed 0: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | -0.043 noise SD (SE 0.017) | pass |
| MATR seed 0: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | +0.017 noise SD (SE 0.019) | pass |
| MATR seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 0: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| MATR seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 238319 windows | pass |
| MATR seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.44e-16 | pass |
| MATR seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.755e-03, SE 1.505e-03 | pass |
| MATR seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 238319 windows | pass |
| MATR seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 3.47e-16 | pass |
| MATR seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.751e-03, SE 1.501e-03 | pass |
| MATR seed 1 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 238319 windows | pass |
| MATR seed 1 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 6.94e-16 | pass |
| MATR seed 1 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.749e-03, SE 1.512e-03 | pass |
| MATR seed 1: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| MATR seed 1: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.026 noise SD (SE 0.019) | pass |
| MATR seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.036 noise SD (SE 0.019) | pass |
| MATR seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.073 noise SD (SE 0.032) | pass |
| MATR seed 1: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | -0.034 noise SD (SE 0.019) | pass |
| MATR seed 1: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | +0.020 noise SD (SE 0.019) | pass |
| MATR seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 1: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| MATR seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 243588 windows | pass |
| MATR seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.30e-16 | pass |
| MATR seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.855e-03, SE 1.231e-03 | pass |
| MATR seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 243588 windows | pass |
| MATR seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.30e-16 | pass |
| MATR seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.886e-03, SE 1.232e-03 | pass |
| MATR seed 2 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 243588 windows | pass |
| MATR seed 2 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 7.36e-16 | pass |
| MATR seed 2 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.806e-03, SE 1.231e-03 | pass |
| MATR seed 2: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| MATR seed 2: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.038 noise SD (SE 0.017) | pass |
| MATR seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.000 noise SD (SE 0.017) | pass |
| MATR seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.048 noise SD (SE 0.027) | pass |
| MATR seed 2: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | +0.023 noise SD (SE 0.020) | pass |
| MATR seed 2: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | -0.042 noise SD (SE 0.021) | pass |
| MATR seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 2: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| HUST seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562769 windows | pass |
| HUST seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 7.98e-16 | pass |
| HUST seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.133e-04, SE 1.225e-03 | pass |
| HUST seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562769 windows | pass |
| HUST seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 6.90e-16 | pass |
| HUST seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.053e-04, SE 1.226e-03 | pass |
| HUST seed 0 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562769 windows | pass |
| HUST seed 0 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.60e-15 | pass |
| HUST seed 0 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.241e-04, SE 1.224e-03 | pass |
| HUST seed 0: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| HUST seed 0: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | +0.001 noise SD (SE 0.010) | pass |
| HUST seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.019 noise SD (SE 0.034) | pass |
| HUST seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.024 noise SD (SE 0.020) | pass |
| HUST seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 0: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| HUST seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562851 windows | pass |
| HUST seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 8.40e-16 | pass |
| HUST seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -7.454e-04, SE 1.133e-03 | pass |
| HUST seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562851 windows | pass |
| HUST seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 7.36e-16 | pass |
| HUST seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -7.376e-04, SE 1.133e-03 | pass |
| HUST seed 1 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562851 windows | pass |
| HUST seed 1 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.56e-15 | pass |
| HUST seed 1 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -7.554e-04, SE 1.133e-03 | pass |
| HUST seed 1: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| HUST seed 1: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | +0.006 noise SD (SE 0.010) | pass |
| HUST seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.002 noise SD (SE 0.033) | pass |
| HUST seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.022 noise SD (SE 0.018) | pass |
| HUST seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 1: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| HUST seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562398 windows | pass |
| HUST seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 8.51e-16 | pass |
| HUST seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -2.616e-03, SE 1.245e-03 | pass |
| HUST seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562398 windows | pass |
| HUST seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 7.91e-16 | pass |
| HUST seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -2.623e-03, SE 1.245e-03 | pass |
| HUST seed 2 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562398 windows | pass |
| HUST seed 2 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.52e-15 | pass |
| HUST seed 2 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -2.608e-03, SE 1.245e-03 | pass |
| HUST seed 2: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| HUST seed 2: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.012 noise SD (SE 0.008) | pass |
| HUST seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.039 noise SD (SE 0.036) | pass |
| HUST seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.049 noise SD (SE 0.020) | pass |
| HUST seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 2: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| NASA_PCoE seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14208 windows | pass |
| NASA_PCoE seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 2.28e-15 | pass |
| NASA_PCoE seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 2.163e-02, SE 2.176e-02 | pass |
| NASA_PCoE seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14208 windows | pass |
| NASA_PCoE seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.66e-15 | pass |
| NASA_PCoE seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.218e-02, SE 2.080e-02 | pass |
| NASA_PCoE seed 0 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 1.11e-16 over 14208 windows | pass |
| NASA_PCoE seed 0 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.88e-15 | pass |
| NASA_PCoE seed 0 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.291e-02, SE 2.482e-02 | pass |
| NASA_PCoE seed 0: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| NASA_PCoE seed 0: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| NASA_PCoE seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.007 noise SD (SE 0.016) | pass |
| NASA_PCoE seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.002 noise SD (SE 0.013) | pass |
| NASA_PCoE seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.027 noise SD (SE 0.062) | pass |
| NASA_PCoE seed 0: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | -0.002 noise SD (SE 0.015) | pass |
| NASA_PCoE seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| NASA_PCoE seed 0: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| NASA_PCoE seed 0 [recency]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.074 | pass |
| NASA_PCoE seed 0 [uniform]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | -0.030 | pass |
| NASA_PCoE seed 0 [final_position]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.138 | pass |
| NASA_PCoE seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14082 windows | pass |
| NASA_PCoE seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 2.14e-15 | pass |
| NASA_PCoE seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.082e-03, SE 1.862e-02 | pass |
| NASA_PCoE seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14082 windows | pass |
| NASA_PCoE seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.67e-15 | pass |
| NASA_PCoE seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 8.573e-03, SE 1.886e-02 | pass |
| NASA_PCoE seed 1 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14082 windows | pass |
| NASA_PCoE seed 1 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.66e-15 | pass |
| NASA_PCoE seed 1 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.417e-02, SE 1.785e-02 | pass |
| NASA_PCoE seed 1: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| NASA_PCoE seed 1: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| NASA_PCoE seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.022 noise SD (SE 0.017) | pass |
| NASA_PCoE seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.018 noise SD (SE 0.014) | pass |
| NASA_PCoE seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.023 noise SD (SE 0.051) | pass |
| NASA_PCoE seed 1: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | -0.005 noise SD (SE 0.015) | pass |
| NASA_PCoE seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| NASA_PCoE seed 1: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| NASA_PCoE seed 1 [recency]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.078 | pass |
| NASA_PCoE seed 1 [uniform]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | -0.023 | pass |
| NASA_PCoE seed 1 [final_position]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.143 | pass |
| NASA_PCoE seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14142 windows | pass |
| NASA_PCoE seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 2.38e-15 | pass |
| NASA_PCoE seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.037e-02, SE 1.795e-02 | pass |
| NASA_PCoE seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 2.22e-16 over 14142 windows | pass |
| NASA_PCoE seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.73e-15 | pass |
| NASA_PCoE seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.140e-02, SE 1.484e-02 | pass |
| NASA_PCoE seed 2 [final_position]: sum(phi*) == y on every window | < 1e-9 (relative) | 1.11e-16 over 14142 windows | pass |
| NASA_PCoE seed 2 [final_position]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.66e-15 | pass |
| NASA_PCoE seed 2 [final_position]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 9.431e-03, SE 2.071e-02 | pass |
| NASA_PCoE seed 2: final-position weighting collapses graded and sparse fields to the last position | 0 outside last | 0.0 | pass |
| NASA_PCoE seed 2: pristine unit (z = 0, no patterns, no noise) has y = 0 | 0 | 0.00e+00 | pass |
| NASA_PCoE seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.014 noise SD (SE 0.015) | pass |
| NASA_PCoE seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.013 noise SD (SE 0.013) | pass |
| NASA_PCoE seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.030 noise SD (SE 0.038) | pass |
| NASA_PCoE seed 2: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | +0.023 noise SD (SE 0.013) | pass |
| NASA_PCoE seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| NASA_PCoE seed 2: disabling patterns leaves z, T, R and noise unchanged | identical | True | pass |
| NASA_PCoE seed 2 [recency]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.081 | pass |
| NASA_PCoE seed 2 [uniform]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | -0.004 | pass |
| NASA_PCoE seed 2 [final_position]: |graded|/|sparse| correlation below the declared bound | <= 0.3 | 0.140 | pass |
