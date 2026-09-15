# D01 — The sparse set is scored on paired maps: a method's map on the window minus its map on the same window with the inserted patterns removed

**Stage / claim affected:**
- the retrieval score everywhere (S7 responsiveness, S8 reference values, Table 4 row "Retrieval, sparse set", Table 6 retrieval columns);
- the rank-agreement score against the graded field, which is scored on the pattern-free map;
- only the NASA PCoE profile carries a sparse set (D05).

**Decision.** The ground truth is ϕ* = w(m − x⁰) + w·p. On the capacity channel the graded part is typically far larger than the pattern part. Ranking cells by attribution magnitude therefore places the sparse cells last even for ϕ* itself. How is the sparse set scored so that a correct map reaches the ceiling?

**Options considered** (declared scores: retrieval = average precision via sklearn; rank agreement = Spearman ρ over the L × C cells via scipy)
- **c. Plain retrieval (no change):** the AP of |map| against the sparse-set cells.
- **a. Paired:** the AP of |map(x) − map(x without patterns)|. The generator emits the pattern-free counterpart window x − p for every window (S4). For ϕ*, the difference is exactly the sparse field. Rank agreement against the graded field uses map(x without patterns), which for ϕ* is exactly the graded field. In S7 the two maps are degraded with independent draws. For methods, sampling seeds are shared across the pair (S8).
- **b. Detrended:** the AP of |map − SG-smooth(map)| along positions, with the declared window 11 and order 2: the §3.3 residual rule applied to the map.

**Evidence** (`experiments/decisions/D01/{run.py,result.json}`): 1,500 NASA PCoE generated windows containing at least one sparse cell (generation seed 0, recency weighting). Sparse cells are 1.95 % of cells; chance AP is 0.048.

| | plain (c) | paired (a) | detrended (b) |
|---|---|---|---|
| ϕ* undegraded, mean AP (SD) | 0.064 (0.063) | **1.000 (0.000)** | 0.487 (0.324) |
| exact attribution of the reference model w(x − x⁰), noise included | 0.056 | **1.000** | 0.055 |
| added noise σ = 2.0 × SD(ϕ*) | 0.050 | 0.053 | 0.050 |
| mass shifted to start, fraction 1.0 | 0.047 | 0.087 | 0.069 |
| smoothing σ = 8 positions | 0.063 | 0.922 | 0.081 |
| permuted fraction 1.0 | 0.047 | 0.045 | 0.050 |
| increases of the mean score along the magnitude grid (noise / start / end / smoothing / permuted) | 1 / 4 / 6 / 3 / 1 | **0 / 0 / 1 / 0 / 0** | 0 / 0 / 0 / 1 / 2 |

Graded-field rank agreement, undegraded ϕ*: plain 0.984, paired 1.000. For the reference model's exact attribution, paired rank agreement is 0.740, since noise enters w(x − x⁰).

Real: all three variants run on the benchmark's own windows.

Works:
- (c) gives the correct map a retrieval score at chance (0.064 vs 0.048), so a responsiveness check on it has no ceiling.
- (b) reaches 0.49 with an SD of 0.32.
- (a) reaches exactly 1 for ϕ* and for the reference model's exact attribution, and falls monotonically toward chance under noise and permutation.

Clear, option (a) in three sentences:
1. Every generated window has a counterpart with the inserted patterns removed, so a method is run on both.
2. The difference of the two maps is the method's attribution to the patterns and is scored against the sparse set.
3. The map on the counterpart is scored against the graded field.

Failure mode: a method whose output depends nonlinearly on the joint presence of patterns and trend credits part of that interaction to the patterns. Sampling noise that is not shared between the two runs appears in the difference; shared seeds reduce it.

**Chosen: a.** Plain retrieval is kept as a reported secondary series for comparability with existing benchmarks.
1. *Logical:* the sparse set is defined as the contribution of the inserted patterns (Eq. 5), and the paired difference isolates exactly that contribution. It is available for any method at its default configuration and makes no method correct by construction. For ϕ* it is the definition itself.
2. *Consistent:* it uses the same counterfactual the usability checks use (retraining with the pattern term removed) and the pattern-free window the generator records anyway.
3. *Clear:* three sentences, no new parameter.
4. *Measured:* the ceiling is 1.000 against 0.49 and 0.064, and only (a) responds monotonically.

**Cost.**
- Two attribution runs per NASA window, and TimeSHAP needs matched seeds.
- The score answers "what does the method attribute to the patterns?", not "does the method's unpaired map single out the pattern positions?". The unpaired question is the one plain retrieval asks, and there even the ground truth scores at chance. A reviewer from the planted-pattern literature may prefer the unpaired reading; the plain series is reported next to it.
- Resolution in S7 is defined relative to the undegraded map's own score, as the brief requires. That score is 1 for ϕ* under (a) but need not be for the reference model's graded rank agreement (0.740).

**Paper impact:** §3.5 (protocol) and §3.6 need one sentence each: retrieval is scored on the difference between the map of a window and of its pattern-free counterpart, and rank agreement on the latter (round-4 amendment).
