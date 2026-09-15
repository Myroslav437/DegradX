# D15 — The EOL search starts at the position of the early-life reference

**Stage / claim affected:** S2 audit and every later use of `T` on measured units.

**Decision.** C3 made `q₁` the maximum of smoothed capacity over the first k positions. As first implemented, `T` searched from position 1. A record whose earliest readings lie below the threshold, before capacity rises to `q₁`, then gets EOL at position 1, before the fall Eq. 3 measures has begun. Where should the search start?

**Options considered**
- **a. No change:** `T = min{t ≥ 1 : z_t ≥ 1}`.
- **b.** `T = min{t ≥ t₁ : z_t ≥ 1}`, with `t₁` the position of `q₁`.
- **c.** Option (a), plus exclude units with `T ≤ k` as data failures.

**Evidence** (`experiments/decisions/D15/{run.py,result.json}`; capacity D11, cleaning D12, record-end rule D13). All three options are Real.

| | a | b | c |
|---|---|---|---|
| MATR reach / T ≤ k | 173 / 0 | 173 / 0 | 173 |
| HUST reach / T ≤ k | 77 / 0 | 77 / 0 | 77 |
| NASA reach / T ≤ k | 11 / 2 | 11 / 1 | 9 |
| units whose T differs a vs b | — | NASA B0038 only: T 1 → 45 (first kept readings 1.10, 1.09, 1.06 Ah; q₁ at position 16) | — |

Clear, option (b): the degradation state measures the fall from `q₁`, so EOL is searched from where `q₁` was observed. On any record whose readings before `t₁` stay above the threshold, (a) and (b) coincide. Failure mode: a record with a genuine early crossing before `t₁` would have it ignored, which cannot happen when `q₁ > threshold + 5 % q_nom` (guard) unless the record is anomalous.

**Chosen: b.**
1. *Logical:* it is what Eq. 3's text says: "how much of the fall from `q₁` … has been consumed".
2. *Consistent:* it keeps C3's reading and needs no exclusion rule.
3. *Clear:* one clause.
4. *Measured:* only one unit changes.

(c) would exclude units for a reason the paper does not state.

**Cost.** None on MATR and HUST. On NASA, B0038 (a mixed-temperature, multi-load cell) gets `T = 45` instead of 1. The remaining NASA unit with `T ≤ k` (B0043, starting at 1.71 Ah at 4 °C) crosses after `t₁` and is kept. Its early EOL is a property of the record.

**Paper impact:** Eq. 3, `T = min{t ≥ t₁ : z_t ≥ 1}`, with `t₁` defined in the sentence introducing `q₁` (round-2 amendment).
