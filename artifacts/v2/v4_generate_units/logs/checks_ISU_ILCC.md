| check | expected | observed | result |
|---|---|---|---|
| ISU_ILCC seed 0 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 388277 windows | pass |
| ISU_ILCC seed 0 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.03e-15 | pass |
| ISU_ILCC seed 0 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.341e-03, SE 2.070e-03 | pass |
| ISU_ILCC seed 0 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.773 (Var(y_offset)/Var(y_state) 2.838) | FAIL |
| ISU_ILCC seed 0 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 388277 windows | pass |
| ISU_ILCC seed 0 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.07e-15 | pass |
| ISU_ILCC seed 0 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -1.302e-03, SE 2.062e-03 | pass |
| ISU_ILCC seed 0 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.772 (Var(y_offset)/Var(y_state) 2.845) | FAIL |
| ISU_ILCC seed 0: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| ISU_ILCC seed 0: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.011 noise SD (SE 0.013) | pass |
| ISU_ILCC seed 0: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.003 noise SD (SE 0.018) | pass |
| ISU_ILCC seed 0: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.024 noise SD (SE 0.029) | pass |
| ISU_ILCC seed 0: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| ISU_ILCC seed 0: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| ISU_ILCC seed 0: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 2.7 mAh +- 20% | 13.7 mAh | warn |
| ISU_ILCC seed 1 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 389261 windows | pass |
| ISU_ILCC seed 1 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.03e-15 | pass |
| ISU_ILCC seed 1 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -2.428e-03, SE 2.157e-03 | pass |
| ISU_ILCC seed 1 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.765 (Var(y_offset)/Var(y_state) 3.159) | FAIL |
| ISU_ILCC seed 1 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 389261 windows | pass |
| ISU_ILCC seed 1 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.09e-15 | pass |
| ISU_ILCC seed 1 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean -2.461e-03, SE 2.156e-03 | pass |
| ISU_ILCC seed 1 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.764 (Var(y_offset)/Var(y_state) 3.164) | FAIL |
| ISU_ILCC seed 1: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| ISU_ILCC seed 1: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | -0.037 noise SD (SE 0.014) | pass |
| ISU_ILCC seed 1: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | +0.022 noise SD (SE 0.019) | pass |
| ISU_ILCC seed 1: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | +0.020 noise SD (SE 0.025) | pass |
| ISU_ILCC seed 1: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| ISU_ILCC seed 1: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| ISU_ILCC seed 1: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 2.7 mAh +- 20% | 11.0 mAh | warn |
| ISU_ILCC seed 2 [recency]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 382357 windows | pass |
| ISU_ILCC seed 2 [recency]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.05e-15 | pass |
| ISU_ILCC seed 2 [recency]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 1.925e-03, SE 2.170e-03 | pass |
| ISU_ILCC seed 2 [recency]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.823 (Var(y_offset)/Var(y_state) 3.473) | FAIL |
| ISU_ILCC seed 2 [uniform]: sum(phi*) == y on every window | < 1e-9 (relative) | 0.00e+00 over 382357 windows | pass |
| ISU_ILCC seed 2 [uniform]: g(x) - y == sum(w eps) on every window | < 1e-9 | 1.03e-15 | pass |
| ISU_ILCC seed 2 [uniform]: mean over units of g(x) - y ~ 0 | |mean| <= 3 SE | mean 2.025e-03, SE 2.177e-03 | pass |
| ISU_ILCC seed 2 [uniform]: offset contribution Var(y_offset)/Var(y) <= 0.5 (brief §6 stop rule) | <= 0.5 | 0.823 (Var(y_offset)/Var(y_state) 3.483) | FAIL |
| ISU_ILCC seed 2: unit at z = 0 with zero offsets, no patterns, no noise has y = 0 | 0 | 0.00e+00 | pass |
| ISU_ILCC seed 2: E[eps_capacity] ~ 0 | |mean| <= 3 SE over units | +0.007 noise SD (SE 0.012) | pass |
| ISU_ILCC seed 2: E[eps_charge_time] ~ 0 | |mean| <= 3 SE over units | -0.009 noise SD (SE 0.020) | pass |
| ISU_ILCC seed 2: E[eps_mean_discharge_voltage] ~ 0 | |mean| <= 3 SE over units | -0.026 noise SD (SE 0.026) | pass |
| ISU_ILCC seed 2: z starts at the pristine level and T is the first crossing of z = 1 | z_1 <= 0.05; z_T >= 1 > z_{T-1} | max z_1 0.000; first crossing True | pass |
| ISU_ILCC seed 2: disabling patterns leaves z, T, R, mean and noise unchanged | identical | True | pass |
| ISU_ILCC seed 2: generated q1 shows the measured spread (IQR within 20% of the fitting units reaching EOL) | 2.7 mAh +- 20% | 12.7 mAh | warn |
| ISU_ILCC: X3 construction - within-unit correlation of generated noise (mean over seeds) within 0.05 of the fitted rho_bar | <= 0.05 | max |delta r| 0.019 (pooled comparison 0.040; implied-by-construction gap 0.035) | pass |
| ISU_ILCC: S3/V3 estimator on generated observations recovers the fitted residual correlation within 0.05 (reported) | <= 0.05 | max |delta r| 0.231 | warn |
