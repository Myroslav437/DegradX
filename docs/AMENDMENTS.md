# Methodology amendments

Every edit to `paper/paper.tex` that changes the methodology. Edited spans are wrapped in `\rev{}`
(blue in the review build, plain in the clean build: `bash scripts/build_paper.sh`); a `latexdiff` PDF per
round lives in `artifacts/amendments/`. Declarations changed by the same comment are listed in
`configs/declarations.yaml` → `meta.supersession_log`.

Round 1 = review comments C1–C4 (2026-09-15), applied against commit `8368008` (paper as given at `6221c50`).
Later rounds = decisions under `docs/DECISIONS/` that alter the methodology.

## Round 1

| id | where (paper/paper.tex) | what changed | why | cost / what it buys |
|---|---|---|---|---|
| C1.1 | §3.2.1, Eq. 4 | `y = Σ a m + Σ b Σp` → `y = Σ w (m − x⁰) + Σ w Σp` | A linear map of the observed window cannot reproduce the r1 target: a cell carrying both `a` and `b` returns `(a+b)(m+Σp)`, and a pattern channel with `a = 0` still carries `m`, which the map multiplies by `b`. Measuring the target from `x⁰` makes it an affine function of the noise-free observation. | Buys an exact reference model. Keeps two terms, so "the two terms of Eq. 4" in §3.5.2 and Table 3 stays true. Cost: the pattern term now carries the position profile (see C1.4). |
| C1.2 | §3.2.1, Eq. 5 | `ϕ* = a m + b Σp` → `ϕ* = w (m − x⁰) + w Σp` | Follows from C1.1. | The graded/sparse split is now a split of ϕ*, not of the weights. |
| C1.3 | §3.2.1, paragraph after Eq. 5 (replaces the `a_{u,c}`/`b_{u,c}` sentence) | Defines graded field and sparse set as the two terms; declares `x⁰_c = φ_c(0)` (pristine level, per profile, identical across units) and why (target zero there; reproducible by a map of the window); one weight `w_{u,c} = κ_c π_u`; `κ_c = β_c/(φ_c(1) − φ_c(0))` declared in units of the degradation state; roles differ only in whether `κ_c = 0` and whether the channel carries patterns. | C1 resolution. The comment gives pattern channels "a single constant" weight but also requires the sparse field to collapse under final-position weighting; both hold only with `w = κ_c π_u` (reading reported to the authors at S0 and applied). `κ_c` in state units keeps weights declared rather than fitted while making channels with different physical units commensurable. | Buys: pristine unit ⇒ `y = 0`; comparable shares across profiles. Cost: `κ_c` depends on the fitted mapping range, so a channel that barely changes would be amplified — guarded by demotion to zero weight (declarations `target.weights.guard`). A reviewer may ask why equal shares `β_c = 1/3`; they are a declaration, not a finding. |
| C1.4 | §3.2.1, Figure 4 discussion | "graded field collapses into one cell" → both graded field and sparse set collapse into the last position; a pattern contributes only where it covers that position. | Consequence of `w = κ_c π_u`. | Cost: under final-position weighting most inserted patterns have zero ground-truth contribution, so sparse retrieval is defined on few cells; reported per weighting. |
| C1.5 | §3.2.1, "Neither weight…" / "what `a` exists to specify" | "The weights cannot…"; "what `π` exists to specify". | Terms `a`, `b` no longer exist. | none |
| C1.6 | §3.2.1, Reference model paragraph | Linear map with `a`, `b` → affine map `g(x) = Σ w (x − x⁰)`; differs from `y` only through `Σ w ε` (expectation zero); intercept does not enter attributions from `x⁰`. | C1 resolution. | Buys exactness at ε = 0 (checked at S4). Cost: the reference model's exact attribution is `w(x − x⁰) = ϕ* + wε`, so even a perfect method scores below ceiling against ϕ* by the noise term; S8 reports that ceiling. |
| C1.7 | §3.3, "Declared by design" list | "the weights `a` and `b`" → "the channel shares `β_c` and position profiles of the weights `w`, the definition of the reference point `x⁰`". | The list must name what is now declared. | none |

## Dependencies on later measurements (no numbers were written into the paper by round 1)

- C1.3: whether any weighted channel is demoted by the guard → S3/S4 tables.
- C1.4: graded/sparse correlation per weighting → Table 3 (S6), investigation D06 if above bound.
