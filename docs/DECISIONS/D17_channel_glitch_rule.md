# D17 — Non-capacity channels use the same isolated-excursion rule as capacity (5 % of the unit's channel median)

**Stage / claim affected:** S3 steps three and four (φ_c, channel noise, cross-channel covariance), the channel-role guard, and fidelity property rows.

**Decision.** Charge time and temperature carry single-cycle readings far from their neighbourhood. Examples: MATR charge time up to 1,301 min against a median of 27 min; NASA charge operations truncated to about a third of their normal duration. Isotonic mappings are robust to a few such readings, but noise variance is not. Which rule applies to non-capacity channels? In every option, IR recorded as exactly 0 is treated as missing, as found at S1.

**Options considered**
- **none:** no excursion rule.
- **iso05:** a single-position departure beyond 5 % of the unit's channel median from the centred 11-position rolling median, with neither neighbour departing, is set to missing. Capacity positions are kept.
- **iso50:** the same at 50 %.

**Evidence** (`experiments/decisions/D17/{run.py,result.json}`, fitting splits, S3 fit)

| | none | iso05 | iso50 |
|---|---|---|---|
| MATR readings masked (charge time / MDV / IR / temperature) | 0 | 409 / 5 / 42 / 53 | 15 / 0 / 0 / 0 |
| MATR charge-time noise variance [min²] | 20.6 | 0.816 | 0.830 |
| MATR φ endpoints (charge time φ(0), φ(1)) | 29.34, 21.02 | 29.34, 21.00 | 29.34, 21.02 |
| HUST charge-time readings masked; noise variance | 0; 1.397 | 26; 1.397 | 0; 1.397 |
| NASA readings masked (charge time / temperature) | 0 / 0 | 63 / 52 | 6 / 1 |
| NASA charge-time noise variance [min²] | 188.1 | 47.3 | 56.3 |
| NASA charge-time role after the weight guard | **demoted** | weighted | **demoted** |

Real: all three run. Works:
- One or two dozen glitch readings inflate MATR charge-time noise variance 25×. Both rules remove the inflation.
- On NASA, the choice decides whether charge time stays a weighted channel: its |φ(1) − φ(0)| of 7.9 min sits just above a noise standard deviation of 6.9 min under iso05.

Clear, iso05: every channel, capacity included, uses one rule. A single reading departing more than 5 % from its neighbourhood, where neither neighbour departs, is a glitch; runs are kept. Failure mode: a genuine one-cycle change of a channel beyond 5 % is masked. For MATR charge time that is 409 of about 78,000 readings.

**Chosen: iso05.**
1. *Logical:* the same definition of a glitch as D12, applied to every channel.
2. *Consistent:* one threshold across channels and profiles, where iso50 would add a second constant.
3. *Clear:* D12's sentence already states it.
4. *Measured:* the noise variance is no longer dominated by a handful of readings, and mapping endpoints are unchanged.

**Cost.**
- NASA's charge-time role is borderline (|Δφ| = 7.9 min vs noise SD 6.9 min). The benchmark's channel roles for NASA depend on this rule, and a reviewer could call the guard outcome fragile. It is reported with both numbers.
- MATR masks 409 charge-time readings, 0.5 % of positions.

**Paper impact:** none beyond D12's sentence, which is worded for the capacity channel. Round 3 extends it to "every channel" in §3.3 step one.
