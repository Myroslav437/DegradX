| check | expected | observed | result |
|---|---|---|---|
| ingest: every in-scope cell present in the release | none missing | none missing | pass |
| ingest: converter anchor identity (calibrated capacity at every anchor equals the C/5 value) | < 1e-9 Ah | 5.55e-17 | pass |
| ingest: cycler capacity equals the max of the discharge Q samples (raw-array check) | < 1e-6 Ah | 0.00e+00 | pass |
| ingest: charge time from step times equals the sample span (raw-array check) | < 1 min | 0.000 | pass |
| ingest: cycle start times strictly increasing in every cell | all | all | FAIL |
| ingest: in-scope cells with fewer than 2 anchors (reported; count against E4 if at EOL) | none | none | pass |
