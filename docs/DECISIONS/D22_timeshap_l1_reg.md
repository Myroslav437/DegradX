# D22 — TimeSHAP runs at the cell-level library default l1_reg = 'auto'

**Stage / claim affected:** S8 TimeSHAP reference values (Table 6). Resolves S0 "Decisions needed" item 4.

**Decision.** At cell level, timeshap's `local_cell_level` path fixes `l1_reg='auto'`, which selects features by LassoLarsIC(AIC) when the coalition budget is a small share of all coalitions, and zeroes the rest. A dense map needs `l1_reg=False` through the kernel. Which is TimeSHAP's "default configuration" (paper §3.6)?

**Options considered**
- **a.** `'auto'`, the value the package's cell-level API uses.
- **b.** `False` (dense).

**Evidence** (`experiments/decisions/D22/{run.py,result.json}`): NASA PCoE recency, 12 test windows, nsamples 32 000, background = pristine event (C4), attribution seeds 0 and 1.

| | reference model 'auto' | reference model False | trained LSTM 'auto' | trained LSTM False |
|---|---|---|---|---|
| max \|error\| to exact w(x − x⁰) (scale 0.115) | 9.8e-6 | 1.8e-7 | — | — |
| rank agreement with graded field, seed 0 / seed 1 | 0.714 / 0.714 | 0.672 / 0.673 | 0.181 / 0.196 | 0.181 / 0.196 |
| share of cells exactly 0 | 0.50 | 0.22 | 0.084 | 0.00 |
| max \|seed 0 − seed 1\| | 3.0e-7 | 1.8e-9 | 2.4e-3 | 2.4e-3 |
| seconds per window (GPU shared with S6 training) | 6.6 | 5.3 | 6.5 | 5.4 |

The exact attribution's own rank agreement is 0.714 on these windows, the value 'auto' reproduces. On the reference model, 'auto' keeps the exact zeros of the zero-weight channels as exact zeros. `False` leaves them as ~1e-7 values, and Spearman ranks those values arbitrarily, hence 0.672.

Real: both run. Works:
- Both are exact on the reference model to within 1e-5 of a 0.115-scale field.
- On the trained model the two are indistinguishable (rank 0.181 vs 0.181).

Clear, option (a): "TimeSHAP is run through its own cell-level default, which regularises the local fit with an AIC-selected lasso." Failure mode: on a model with many small but nonzero contributions, 'auto' zeroes them.

**Chosen: a.**
1. *Logical:* §3.6 runs methods at their defaults, and 'auto' is what the package does at cell level.
2. *Consistent:* the r1 declaration.
3. *Clear.*
4. *Measured:* no difference on the trained model; on the reference model 'auto' preserves exact zeros.

**Cost.**
- About 20 % more time per window.
- On trained models with diffuse attributions, 'auto' sparsifies the map (8 % zero cells here). A reviewer preferring dense Shapley maps would choose `False`; the harness shows the scores coincide.

**Paper impact:** none; S8 setup text states nsamples, l1_reg and the background instance.
