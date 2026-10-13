| check | expected | observed | result |
|---|---|---|---|
| TRI_FORMATION [recency]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.179 | pass |
| TRI_FORMATION [recency]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| TRI_FORMATION [recency]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0000 [-0.0004, 0.0003] | pass |
| TRI_FORMATION [recency]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0001 [-0.0001, 0.0003] | pass |
| TRI_FORMATION [recency]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.1457 [0.1285, 0.1811] | pass |
| TRI_FORMATION [recency]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0937 [0.0738, 0.1195] | pass |
| TRI_FORMATION [recency]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0963 [0.0762, 0.1224] | pass |
| TRI_FORMATION [recency]: mean term removed increases error on y (95% CI > 0) | CI > 0 | 2.5808 [2.2302, 3.0334] | pass |
| TRI_FORMATION [recency]: pattern term removed increases error on y (95% CI > 0) | CI > 0 | 0.0000 [-0.0001, 0.0002] | warn |
| TRI_FORMATION [recency]: |graded/sparse correlation| <= 0.3 (test windows) | <= 0.3 | 0.0451 | pass |
| TRI_FORMATION [recency]: variance ratio within the declared band [0.05, 0.5] | [0.05, 0.5] | 0.0000 | warn |
| TRI_FORMATION [uniform]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.183 | pass |
| TRI_FORMATION [uniform]: all 10 ensemble members pass the gate | 10/10 | 10/10 | pass |
| TRI_FORMATION [uniform]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0003 [-0.0008, 0.0003] | pass |
| TRI_FORMATION [uniform]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0004 [0.0001, 0.0008] | pass |
| TRI_FORMATION [uniform]: X4 weighted channel capacity used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.1433 [0.1265, 0.1720] | pass |
| TRI_FORMATION [uniform]: X4 weighted channel charge_time used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.1003 [0.0790, 0.1272] | pass |
| TRI_FORMATION [uniform]: X4 weighted channel mean_discharge_voltage used by the primary model (lower bound > 0; reported, voids channel-level trained scores if not) | > 0 | 0.0998 [0.0802, 0.1251] | pass |
| TRI_FORMATION [uniform]: mean term removed increases error on y (95% CI > 0) | CI > 0 | 2.5808 [2.2159, 3.0524] | pass |
| TRI_FORMATION [uniform]: pattern term removed increases error on y (95% CI > 0) | CI > 0 | 0.0003 [-0.0006, 0.0012] | warn |
| TRI_FORMATION [uniform]: |graded/sparse correlation| <= 0.3 (test windows) | <= 0.3 | 0.0081 | pass |
| TRI_FORMATION [uniform]: variance ratio within the declared band [0.05, 0.5] | [0.05, 0.5] | 0.0000 | warn |
