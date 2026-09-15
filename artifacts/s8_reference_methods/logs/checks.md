| check | expected | observed | result |
|---|---|---|---|
| MATR [recency]: integrated_gradients on the reference model equals w(x - x0) | < 1e-3 relative | 2.32e-08 | pass |
| MATR [recency]: feature_occlusion on the reference model equals w(x - x0) | < 1e-3 relative | 8.64e-08 | pass |
| MATR [uniform]: integrated_gradients on the reference model equals w(x - x0) | < 1e-3 relative | 8.29e-09 | pass |
| MATR [uniform]: feature_occlusion on the reference model equals w(x - x0) | < 1e-3 relative | 1.16e-07 | pass |
| MATR [final_position]: integrated_gradients on the reference model equals w(x - x0) | < 1e-3 relative | 2.16e-07 | pass |
| MATR [final_position]: feature_occlusion on the reference model equals w(x - x0) | < 1e-3 relative | 2.35e-07 | pass |
| MATR: TimeSHAP background instance recorded | recorded | recorded | pass |
