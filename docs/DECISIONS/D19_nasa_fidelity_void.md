# D19 — NASA PCoE fidelity is reported void at its declared split; no cross-fitted estimate replaces it

**Stage / claim affected:** Table 1 NASA row; §4.1 text on NASA.

**Decision.** NASA's declared split leaves 5 held-out units, 3 of them reaching EOL, below every D02b minimum. Should the fidelity row be void, or estimated by cross-fitting (every unit held out once)?

**Options considered**
- **a.** Void at the declared split, reported with counts.
- **b.** 5-fold cross-fitting over the 18 guard-passing units:
  - refit the S3 profile on 4 folds;
  - generate 300 units from that fold's profile;
  - train TSTR/TRTR (model seeds 0–4) and evaluate on the held-out fold;
  - pool per-unit errors over folds with a BCa interval over units.

**Evidence** (`experiments/decisions/D19/{run.py,result.json,run.log}`)

| fold | fitting units | held-out units reaching EOL | family selected | positive patterns enabled | fold TSTR ratio |
|---|---|---|---|---|---|
| 0 | 13 | 2 | power law | yes | 1.44 |
| 1 | 14 | 2 | rollover | yes | 3.94 |
| 2 | 15 | 2 | two-term exponential | yes | 3.64 |
| 3 | 15 | 2 | power law | yes | 1.05 |
| 4 | 15 | 2 | rollover | yes | 2.36 |
| pooled | — | **10** | — | — | **1.22 [1.06, 3.07]**, relative half-width **0.82** |

Real: both run (the declared-split numbers are in S5).

Works:
- (b) pools 10 units, still below the transfer minimum of 20. Its interval is unreadable (half-width 82 % of the value).
- Its folds select three different families, so the pooled number describes the fitting procedure on a moving target rather than the released profile.

Clear:
- (a) "NASA PCoE's held-out split is too small for any fidelity measure; the row is void with its counts."
- (b) needs a paragraph explaining why the evaluated profiles are not the released one.

**Chosen: a.**
1. *Logical:* the profile evaluated must be the profile released.
2. *Consistent:* D02/D02b minima; paper §3.4 already states that NASA's unit count limits what its fidelity can establish.
3. *Clear:* one sentence.
4. *Measured:* (b) is unreadable anyway (0.82).

**Cost.**
- Nothing about NASA PCoE's fidelity to its dataset can be claimed. Its role in the benchmark rests on the audit (regeneration present, D03) and on the exactness of the ground truth, not on a validated resemblance.
- A reviewer may ask why cross-fitting was not reported as a secondary number. It was measured and is reported here as unreadable.

**Paper impact:** none in the methodology; §4.1 states the void NASA row with its counts.
