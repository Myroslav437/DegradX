| check | expected | observed | result |
|---|---|---|---|
| MATR: window length and effective unit counts recorded next to every measure | recorded | {'measured_fitting': 95, 'measured_held_out': 40, 'measured_held_out_reaching_eol': 38, 'generated_per_seed': 300} | pass |
| MATR: discriminator does not separate trivially (accuracy < 0.99; else look for a scaling/padding artefact) | < 0.99 | 0.928 | pass |
| MATR: TSTR ratio finite with interval | finite | 3.4201964487768874 | pass |
| HUST: window length and effective unit counts recorded next to every measure | recorded | {'measured_fitting': 54, 'measured_held_out': 23, 'measured_held_out_reaching_eol': 23, 'generated_per_seed': 300} | pass |
| HUST: discriminator does not separate trivially (accuracy < 0.99; else look for a scaling/padding artefact) | < 0.99 | 0.836 | pass |
| HUST: TSTR ratio finite with interval | finite | 1.4612937680490141 | pass |
| NASA_PCoE: window length and effective unit counts recorded next to every measure | recorded | {'measured_fitting': 13, 'measured_held_out': 5, 'measured_held_out_reaching_eol': 3, 'generated_per_seed': 300} | pass |
| NASA_PCoE: discriminator does not separate trivially (accuracy < 0.99; else look for a scaling/padding artefact) | < 0.99 | 0.818 | pass |
| NASA_PCoE: TSTR ratio finite with interval | finite | 1.6411627211090731 | pass |
