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
