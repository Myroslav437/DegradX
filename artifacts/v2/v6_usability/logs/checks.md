| check | expected | observed | result |
|---|---|---|---|
| MATR [recency]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.091 | pass |
| MATR [recency]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| MATR [recency]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0002, 0.0001] | pass |
| MATR [recency]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0001, 0.0000] | pass |
| MATR [recency]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0763 [0.0659, 0.0925] | pass |
| MATR [recency]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0525 [0.0369, 0.0920] | pass |
| MATR [recency]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0488 [0.0378, 0.0791] | pass |
| MATR [uniform]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.090 | pass |
| MATR [uniform]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| MATR [uniform]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0002, 0.0001] | pass |
| MATR [uniform]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0001, 0.0000] | pass |
| MATR [uniform]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0760 [0.0655, 0.0918] | pass |
| MATR [uniform]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0532 [0.0380, 0.0895] | pass |
| MATR [uniform]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0496 [0.0393, 0.0774] | pass |
| HUST [recency]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.095 | pass |
| HUST [recency]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| HUST [recency]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0001, 0.0000] | pass |
| HUST [recency]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0000 [-0.0000, 0.0000] | pass |
| HUST [recency]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0685 [0.0573, 0.0843] | pass |
| HUST [recency]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0145 [0.0118, 0.0184] | pass |
| HUST [recency]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.6305 [0.5447, 0.7438] | pass |
| HUST [uniform]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.095 | pass |
| HUST [uniform]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| HUST [uniform]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0001, 0.0000] | pass |
| HUST [uniform]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0000 [-0.0000, 0.0000] | pass |
| HUST [uniform]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0679 [0.0569, 0.0833] | pass |
| HUST [uniform]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0146 [0.0118, 0.0185] | pass |
| HUST [uniform]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.6340 [0.5473, 0.7452] | pass |
