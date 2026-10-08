# Decision records

Brief v2 §3: a result that is internally consistent but wrong, implausible, or underdetermined by the
methodology is settled by a five-step protocol (state, enumerate options, test each for real / works /
clear, choose by logical → consistent → clear → measured quality, record with a cost line). Harnesses live in
`experiments/decisions/D<nn>/`. A decision that alters the methodology is also written into
`paper/paper.tex` in `\rev{}` and listed in `docs/AMENDMENTS.md`.

Carried over from S0 `REVIEW.md` "Decisions needed" (brief v2 makes these the agent's to settle):
- S0 item 2 — `UNDERSPECIFIED-IN-PAPER` values in `configs/declarations.yaml` r2 are adopted as declared; any
  change after data is seen is a D-record that supersedes the declaration with a dated entry.
- S0 item 3 — MATR scope (all four batches vs the Severson three) → decided at S2.
- S0 item 4 — TimeSHAP `l1_reg` ('auto' library default vs dense `False`) → decided at S8 (with D09).

| id | decision | stage | status |
|---|---|---|---|
| D11 | capacity channel = cycler-reported per-cycle capacity | S1 | taken |
| D12 | glitch-cycle rule before smoothing and fitting | S2 | taken (paper round 2) |
| D13 | EOL attainment for records truncated at the stopping threshold | S2 | taken (paper round 2) |
| D14 | MATR scope: the three Severson 2019 batches | S2 | taken |
| D15 | EOL search starts at the position of q1 | S2 | taken (paper round 2) |
| D16 | pattern residual fitted from q1; runs capped at the smoothing window | S2 | taken (paper round 2) |
| D03 | NASA PCoE keeps its regeneration role | S2 | taken |
| D17 | non-capacity channel glitch rule (5 % isolated excursions) | S3 | taken (paper round 3) |
| D02 | censored units feed T-free quantities; minimum counts 5 units / 10 events / 5 held-out (provisional) | S3 | taken (paper round 3); held-out minimum re-tested at S5 |
| D04 | family selection: 5 % simplicity margin, identifiability (≤ 20 % at bounds) | S3 | taken (paper round 3) |
| D05 | detection at k = 2.5; enable only above 2× the noise-only rate | S3 | taken (paper round 3) |
| D01 | sparse set scored on paired maps (window vs pattern-free counterpart); plain retrieval secondary | S4 | taken (paper round 4) |
| D18 | generated state anchored at its own trajectory's early-life reference | S4 | taken |
| D06 | graded/sparse correlation above bound | S4 | not triggered: NASA 0.07-0.08 (recency), -0.03-0.00 (uniform), 0.14 (final position) < 0.30 |
| D02b | per-measure held-out minima: transfer 20, covariance 12, discriminator 8, representation distance by unit bootstrap | S5 | taken |
| D19 | NASA PCoE fidelity void at the declared split (cross-fitting unreadable, family unstable across folds) | S5 | taken |
| D21 | NASA pattern term negligible at fitted amplitudes: generator unchanged; trained-model sparse scores void | S6 | taken |
| D08 | non-responding scores explained by field construction; drop reported beside resolution | S7 | taken |
| D20 | operating range read on both probes (reference model and IG on the trained model) with the accuracy gate | S7 | taken (paper round 6) |
| D22 | TimeSHAP l1_reg 'auto' (cell-level default) | S8 | taken |
| D23 | S8 budget: TimeSHAP on 40 of 120 windows, seeds 0-1 trained / 0 reference | S8 | taken |
| D10 | held citations: pan2022 verified and re-described; olivares2013 temperature-input claim removed | S9 | taken (paper round 5) |
| D24 | Table 6 per profile, not averaged over profiles | S9 | taken (paper round 6) |

## v2 (brief "DegradX v2", 2026-10-07; branch `v2`, v1 frozen at tag `v1-results`)

Declarations r3 (`configs/declarations.yaml` → `declared_by_design.v2`, supersession log dated 2026-10-07) were committed
before any v2 stage ran. Records from D25 on follow the same five-step protocol.

| id | decision | stage | status |
|---|---|---|---|
| D25 | v2 scope: final-position weighting, setting sweep, representation distance, NASA PCoE, cross-fitting dropped | V0 | taken |
| D27 | non-capacity glitch rule extended to runs of up to three departing positions (one paused cycle in held-out MATR_b1c2 set the 53.5 min² held-out charge-time variance) | V1 | taken (post-data; paper round 7) |
| D28 | third profile: ISU-ILCC, aging-cycle positions with RPT-calibrated capacity, authors' validated cells with mean DoD ≥ 50 % (145 cells); Tongji ineligible from documentation | V2 | taken (pre-data, before download; paper round 7) |
| D26 | X1: MATR's TSTR gap sits in the non-capacity channels (Δlog 1.14 [0.66, 1.75]); constant per-cell offsets explain about half (0.52 [0.21, 0.92]); initial-capacity spread does not contribute; HUST control null | V1 | taken (readings as declared) |
| D29 | HUST is the v2 fidelity anchor (transfer 1.17 [0.94, 1.34], discriminator 0.49, covariance within baseline); MATR reported with its remaining gap (1.49 [1.04, 2.29]); generator not iterated; X3's own share negligible | V5 | taken |
| D30 | the property table reads generated series with D13's record-end clause, as measured records are (the generator stores each unit up to its EOL; without the clause 222 / 177 of 300 generated units were kept) | V5 | taken (post-data; paper round 7) |
