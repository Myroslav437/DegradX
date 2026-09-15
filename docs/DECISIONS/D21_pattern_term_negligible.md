# D21 — At NASA PCoE's fitted amplitudes the pattern term is not learned; the generator keeps the fitted amplitudes, and sparse-set scores on trained models are void

**Stage / claim affected:**
- S6 Table 3 NASA column (variance ratio, pattern-term ablation);
- S8 Table 6 retrieval column on trained models;
- the RQ2 answer for the sparse set;
- the S7 operating range (pattern amplitude).

**Decision.** On NASA PCoE, the only profile with inserted patterns (D05), Var(pattern term) / Var(mean term) of Eq. 4 is 0.0004 under recency weighting, against a declared band of [0.05, 0.50]. Retraining without the pattern term does not change the error on y. A trained model therefore has no reason to use the patterns, and scoring its attributions against the sparse set measures nothing the model computes. What does the benchmark do?

**Options considered**
- **a. Keep the fitted amplitudes.** Report the ratio and the null ablation. Declare trained-model sparse-set scores void, since §3.5.2 requires that both terms are shown to be used. Keep reference-model sparse scores, which are exact by construction. Report where patterns become learnable through the declared S7 amplitude setting.
- **b.** Make the benchmark default the smallest declared amplitude multiplier at which the pattern-term ablation is significant, while no generated amplitude exceeds the largest measured regeneration (×4).
- **c.** Make the default the smallest multiplier that reaches the declared variance-ratio band (×16).
- **d.** Raise the pattern channel's weight relative to its mean component. Dropped: C1 requires one weight per cell, and the reference model's exactness depends on it.

**Evidence** (`experiments/decisions/D21/{run.py,result.json}`): NASA, 300 units per multiplier, generation seed 0; ablation from LSTM configuration A, model seeds 0–1; intervals over 41 test units.

| multiplier | generated amplitude, median | share above largest measured regeneration (651 mAh) | variance ratio: recency / uniform / final position | NMSE increase on y, pattern term removed | full-model NRMSE |
|---|---|---|---|---|---|
| 1 (fitted) | 40 mAh | 0 % | 0.0003 / 0.0002 / 0.0024 | 0.0004 [−0.0003, 0.0011] | 0.147 |
| 2 | 80 mAh | 0 % | 0.0014 / 0.0009 / 0.0098 | 0.0008 [−0.0010, 0.0030] | 0.146 |
| 4 | 161 mAh | 0 % | 0.0055 / 0.0037 / 0.039 | **0.0071 [0.0040, 0.0113]** | 0.146 |
| 8 | 322 mAh | 17 % | 0.022 / 0.015 / 0.157 | 0.030 [0.020, 0.047] | 0.156 |
| 16 | 644 mAh | 50 % | **0.088** / 0.059 / 0.627 | 0.103 [0.071, 0.170] | 0.160 |

Measured NASA regeneration amplitudes: median 74.5 mAh over the 21 audit events; median 40 mAh over the 6 fitting-split events, which is below the reporting minimum (D02).

Real: all run.

Works:
- (a) is what the fitted profile produces.
- (b) makes patterns learnable at amplitudes still inside the measured range, but 2.2× the audit median.
- (c) meets the declared band only with half the amplitudes beyond anything NASA recorded.

Clear, option (a) in three sentences:
1. The generator uses the amplitudes fitted from measurement.
2. At those amplitudes the patterns carry 0.03 % of the target's variance, and a trained model does not use them, so sparse-set scores on trained models are void.
3. The reference model's sparse-set scores and the amplitude at which patterns become learnable are reported.

Failure mode: the benchmark offers no trained-model sparse-set evaluation at its default setting.

**Chosen: a.**
1. *Logical:* amplitude is estimated from data (§3.3 E6). Moving it until a usability check passes fits the benchmark to the check. §3.5.2's rule ("confirming that both are used") decides what a trained-model sparse score means.
2. *Consistent:*
   - fidelity to the fitted profile is kept;
   - the void convention already exists;
   - the amplitude is a declared S7 setting whose responsive range the protocol reports.
3. *Clear:* three sentences, no new constant.
4. *Measured:* (b) and (c) buy learnability at a fidelity cost of 4× and 16×; (c) goes outside the measured range.

**Cost.**
- **The benchmark cannot evaluate trained-model recovery of regeneration at realistic amplitude.** Table 6's retrieval column is void on trained models. The only non-void sparse-set evaluation is on the reference model, where the result for exact methods is known in advance.
- A reviewer could argue that the fitted amplitudes (6 events, median 40 mAh) understate NASA's regeneration (audit median 74.5 mAh). Even at 2× (80 mAh) the ablation is null.
- The declared variance-ratio band fails in the only profile where it applies. The band was set before any data (r1) and is reported as failed, not relaxed.

**Paper impact:** none in the methodology. Results §4.2 (Table 3), §4.3 (amplitude operating range) and §4.4 (void retrieval column) report it, and the Discussion states the limitation.
