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
