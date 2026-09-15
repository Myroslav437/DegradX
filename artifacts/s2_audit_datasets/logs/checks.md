| check | expected | observed | result |
|---|---|---|---|
| MATR: every unit audited | all units | 135 | pass |
| MATR: family fits finite for every audited unit | finite | finite | pass |
| MATR: T >= t1 for every unit reaching EOL (D15) | all | 0 violations | pass |
| MATR: no record-end T for a unit whose smoothed state crossed | record-end T equals last kept position | ok | pass |
| MATR: every detected pattern lies inside its unit's fit range [t1, T] | all inside | True | pass |
| MATR: pattern durations within [m, smoothing window] (D16) | [2, 11] | [2, 11] | pass |
| HUST: every unit audited | all units | 77 | pass |
| HUST: family fits finite for every audited unit | finite | finite | pass |
| HUST: T >= t1 for every unit reaching EOL (D15) | all | 0 violations | pass |
| HUST: no record-end T for a unit whose smoothed state crossed | record-end T equals last kept position | ok | pass |
| HUST: every detected pattern lies inside its unit's fit range [t1, T] | all inside | True | pass |
| HUST: pattern durations within [m, smoothing window] (D16) | [2, 11] | [2, 11] | pass |
| NASA_PCoE: every unit audited | all units | 34 | pass |
| NASA_PCoE: family fits finite for every audited unit | finite | finite | pass |
| NASA_PCoE: T >= t1 for every unit reaching EOL (D15) | all | 0 violations | pass |
| NASA_PCoE: no record-end T for a unit whose smoothed state crossed | record-end T equals last kept position | ok | pass |
| NASA_PCoE: every detected pattern lies inside its unit's fit range [t1, T] | all inside | True | pass |
| NASA_PCoE: pattern durations within [m, smoothing window] (D16) | [2, 11] | [2, 9] | pass |
