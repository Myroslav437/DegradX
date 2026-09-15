| check | expected | observed | result |
|---|---|---|---|
| NASA_PCoE [recency]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.131 | pass |
| NASA_PCoE [recency]: all 10 ensemble members pass the gate (identifiability floor requires it) | 10/10 | 10/10 | pass |
| NASA_PCoE [recency]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0022 [0.0009, 0.0041] | pass |
| NASA_PCoE [recency]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0015 [0.0006, 0.0026] | pass |
| NASA_PCoE [recency]: mean term removed increases error on y (95% CI > 0) | CI > 0 | 10.3046 [9.4298, 10.9013] | pass |
| NASA_PCoE [recency]: pattern term removed increases error on y (95% CI > 0) | CI > 0 | -0.0000 [-0.0004, 0.0003] | warn |
| NASA_PCoE [recency]: variance ratio of the two terms within the declared band [0.05, 0.5] | [0.05, 0.5] | 0.0004 | warn |
| NASA_PCoE [recency]: graded/sparse correlation <= 0.3 | <= 0.3 | 0.074 | pass |
| NASA_PCoE [uniform]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.125 | pass |
| NASA_PCoE [uniform]: all 10 ensemble members pass the gate (identifiability floor requires it) | 10/10 | 10/10 | pass |
| NASA_PCoE [uniform]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0004 [-0.0005, 0.0014] | pass |
| NASA_PCoE [uniform]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | 0.0011 [0.0005, 0.0021] | pass |
| NASA_PCoE [uniform]: mean term removed increases error on y (95% CI > 0) | CI > 0 | 8.2940 [7.3297, 8.9594] | pass |
| NASA_PCoE [uniform]: pattern term removed increases error on y (95% CI > 0) | CI > 0 | -0.0005 [-0.0011, 0.0000] | warn |
| NASA_PCoE [uniform]: variance ratio of the two terms within the declared band [0.05, 0.5] | [0.05, 0.5] | 0.0003 | warn |
| NASA_PCoE [uniform]: graded/sparse correlation <= 0.3 | <= 0.3 | -0.030 | pass |
| NASA_PCoE [final_position]: primary model reaches the accuracy gate (NRMSE <= 0.3) | <= 0.3 | 0.248 | pass |
| NASA_PCoE [final_position]: all 10 ensemble members pass the gate (identifiability floor requires it) | 10/10 | 10/10 | pass |
| NASA_PCoE [final_position]: permutation importance of null_flat <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0002 [-0.0082, 0.0042] | pass |
| NASA_PCoE [final_position]: permutation importance of null_permuted <= 0.02 (upper 95% bound; leakage test) | <= 0.02 | -0.0020 [-0.0086, 0.0026] | pass |
| NASA_PCoE [final_position]: mean term removed increases error on y (95% CI > 0) | CI > 0 | 12.4332 [11.8624, 12.9581] | pass |
| NASA_PCoE [final_position]: pattern term removed increases error on y (95% CI > 0) | CI > 0 | -0.0030 [-0.0065, -0.0006] | warn |
| NASA_PCoE [final_position]: variance ratio of the two terms within the declared band [0.05, 0.5] | [0.05, 0.5] | 0.0024 | warn |
| NASA_PCoE [final_position]: graded/sparse correlation <= 0.3 | <= 0.3 | 0.138 | pass |
