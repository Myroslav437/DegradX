| check | expected | observed | result |
|---|---|---|---|
| MATR seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 249438 windows | pass |
| MATR seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 5.16e-16 | pass |
| MATR seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 4.370e-04, SE 6.904e-04 | pass |
| MATR seed 0 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.111 (Var(y_offset)/Var(y_state) 0.120) | pass |
| MATR seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 249438 windows | pass |
| MATR seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.72e-16 | pass |
| MATR seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 4.217e-04, SE 6.897e-04 | pass |
| MATR seed 0 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.116 (Var(y_offset)/Var(y_state) 0.126) | pass |
| MATR seed 0: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | +0.023 noise SD (SE 0.018) | pass |
| MATR seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.008 noise SD (SE 0.016) | pass |
| MATR seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.023 noise SD (SE 0.024) | pass |
| MATR seed 0: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | +0.001 noise SD (SE 0.018) | pass |
| MATR seed 0: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | +0.004 noise SD (SE 0.017) | pass |
| MATR seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 0: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| MATR seed 0: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 10.8 mAh +- 20% | 12.4 mAh | pass |
| MATR seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 238319 windows | pass |
| MATR seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.30e-16 | pass |
| MATR seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -9.854e-04, SE 8.906e-04 | pass |
| MATR seed 1 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.112 (Var(y_offset)/Var(y_state) 0.120) | pass |
| MATR seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 238319 windows | pass |
| MATR seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.93e-16 | pass |
| MATR seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.017e-03, SE 8.943e-04 | pass |
| MATR seed 1 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.117 (Var(y_offset)/Var(y_state) 0.126) | pass |
| MATR seed 1: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.046 noise SD (SE 0.018) | pass |
| MATR seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.027 noise SD (SE 0.023) | pass |
| MATR seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.006 noise SD (SE 0.028) | pass |
| MATR seed 1: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | +0.010 noise SD (SE 0.017) | pass |
| MATR seed 1: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | -0.019 noise SD (SE 0.019) | pass |
| MATR seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 1: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| MATR seed 1: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 10.8 mAh +- 20% | 10.0 mAh | pass |
| MATR seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 243588 windows | pass |
| MATR seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 4.84e-16 | pass |
| MATR seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.618e-04, SE 6.734e-04 | pass |
| MATR seed 2 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.104 (Var(y_offset)/Var(y_state) 0.114) | pass |
| MATR seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 243588 windows | pass |
| MATR seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 5.27e-16 | pass |
| MATR seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.624e-04, SE 6.747e-04 | pass |
| MATR seed 2 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.109 (Var(y_offset)/Var(y_state) 0.119) | pass |
| MATR seed 2: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| MATR seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.002 noise SD (SE 0.020) | pass |
| MATR seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.005 noise SD (SE 0.014) | pass |
| MATR seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.001 noise SD (SE 0.023) | pass |
| MATR seed 2: E[eps_internal_resistance] ~ 0 | |mean| <= 3 SE over units | +0.017 noise SD (SE 0.019) | pass |
| MATR seed 2: E[eps_temperature_mean] ~ 0 | |mean| <= 3 SE over units | -0.004 noise SD (SE 0.019) | pass |
| MATR seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| MATR seed 2: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| MATR seed 2: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 10.8 mAh +- 20% | 10.6 mAh | pass |
| MATR: X3 construction - within-unit correlation of generated noise (mean over seeds) within 0.05 of the fitted rho_bar | <= 0.05 | max |delta r| 0.087 (pooled comparison 0.080; implied-by-construction gap 0.127) | warn |
| MATR: S3/V3 estimator on generated observations recovers the fitted residual correlation within 0.05 (reported) | <= 0.05 | max |delta r| 0.168 | warn |
| HUST seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562769 windows | pass |
| HUST seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 9.37e-16 | pass |
| HUST seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -8.495e-04, SE 1.058e-03 | pass |
| HUST seed 0 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.319 (Var(y_offset)/Var(y_state) 0.493) | pass |
| HUST seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562769 windows | pass |
| HUST seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 8.19e-16 | pass |
| HUST seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -8.422e-04, SE 1.058e-03 | pass |
| HUST seed 0 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.320 (Var(y_offset)/Var(y_state) 0.497) | pass |
| HUST seed 0: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.014 noise SD (SE 0.009) | pass |
| HUST seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.020 noise SD (SE 0.033) | pass |
| HUST seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.008 noise SD (SE 0.019) | pass |
| HUST seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 0: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| HUST seed 0: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 21.2 mAh +- 20% | 26.9 mAh | warn |
| HUST seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562851 windows | pass |
| HUST seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 9.33e-16 | pass |
| HUST seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 4.391e-04, SE 1.081e-03 | pass |
| HUST seed 1 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.344 (Var(y_offset)/Var(y_state) 0.550) | pass |
| HUST seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562851 windows | pass |
| HUST seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 8.60e-16 | pass |
| HUST seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 4.335e-04, SE 1.081e-03 | pass |
| HUST seed 1 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.345 (Var(y_offset)/Var(y_state) 0.555) | pass |
| HUST seed 1: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.007 noise SD (SE 0.010) | pass |
| HUST seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | -0.020 noise SD (SE 0.036) | pass |
| HUST seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.007 noise SD (SE 0.016) | pass |
| HUST seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 1: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| HUST seed 1: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 21.2 mAh +- 20% | 27.0 mAh | warn |
| HUST seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562398 windows | pass |
| HUST seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 9.26e-16 | pass |
| HUST seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.423e-03, SE 1.068e-03 | pass |
| HUST seed 2 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.312 (Var(y_offset)/Var(y_state) 0.474) | pass |
| HUST seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 562398 windows | pass |
| HUST seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 8.74e-16 | pass |
| HUST seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.419e-03, SE 1.069e-03 | pass |
| HUST seed 2 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.313 (Var(y_offset)/Var(y_state) 0.478) | pass |
| HUST seed 2: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| HUST seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.004 noise SD (SE 0.009) | pass |
| HUST seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | -0.027 noise SD (SE 0.034) | pass |
| HUST seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.020 noise SD (SE 0.018) | pass |
| HUST seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| HUST seed 2: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| HUST seed 2: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 21.2 mAh +- 20% | 27.1 mAh | warn |
| HUST: X3 construction - within-unit correlation of generated noise (mean over seeds) within 0.05 of the fitted rho_bar | <= 0.05 | max |delta r| 0.008 (pooled comparison 0.033; implied-by-construction gap 0.014) | pass |
| HUST: S3/V3 estimator on generated observations recovers the fitted residual correlation within 0.05 (reported) | <= 0.05 | max |delta r| 0.068 | warn |
