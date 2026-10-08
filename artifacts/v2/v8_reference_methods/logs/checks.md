| check | expected | observed | result |
|---|---|---|---|
| MATR [recency]: integrated_gradients on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 1.13e-08 (max|exact| 0.0515) | pass |
| MATR [recency]: feature_occlusion on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 1.10e-07 (max|exact| 0.0515) | pass |
| MATR [recency]: TimeSHAP seed 0 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.64e-05 (max|exact| 0.0515) | pass |
| MATR [recency]: TimeSHAP seed 1 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.64e-05 (max|exact| 0.0515) | pass |
| MATR [recency]: TimeSHAP seed 2 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.77e-05 (max|exact| 0.0515) | pass |
| MATR [uniform]: integrated_gradients on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 4.13e-09 (max|exact| 0.0185) | pass |
| MATR [uniform]: feature_occlusion on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 1.00e-07 (max|exact| 0.0185) | pass |
| MATR [uniform]: TimeSHAP seed 0 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.57e-05 (max|exact| 0.0185) | pass |
| MATR [uniform]: TimeSHAP seed 1 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.57e-05 (max|exact| 0.0185) | pass |
| MATR [uniform]: TimeSHAP seed 2 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.57e-05 (max|exact| 0.0185) | pass |
| MATR: all declared TimeSHAP jobs present | all | all | pass |
| HUST [recency]: integrated_gradients on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 7.50e-08 (max|exact| 0.0829) | pass |
| HUST [recency]: feature_occlusion on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 1.78e-07 (max|exact| 0.0829) | pass |
| HUST [recency]: TimeSHAP seed 0 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 2.10e-05 (max|exact| 0.0829) | pass |
| HUST [recency]: TimeSHAP seed 1 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 2.49e-05 (max|exact| 0.0829) | pass |
| HUST [recency]: TimeSHAP seed 2 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 2.47e-05 (max|exact| 0.0829) | pass |
| HUST [uniform]: integrated_gradients on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 2.88e-08 (max|exact| 0.0297) | pass |
| HUST [uniform]: feature_occlusion on the reference model equals w(x - x0) (correctness check) | <= 1e-4 x max|w(x - x0)| | 1.81e-07 (max|exact| 0.0297) | pass |
| HUST [uniform]: TimeSHAP seed 0 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.59e-05 (max|exact| 0.0297) | pass |
| HUST [uniform]: TimeSHAP seed 1 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.59e-05 (max|exact| 0.0297) | pass |
| HUST [uniform]: TimeSHAP seed 2 on the reference model reproduces w(x - x0) (sampled Shapley with l1_reg auto; reported) | <= 1e-2 x max|w(x - x0)| | 1.59e-05 (max|exact| 0.0297) | pass |
| HUST: all declared TimeSHAP jobs present | all | all | pass |
