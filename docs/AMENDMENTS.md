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
| C2.1 | §3.1.1, end of the paragraph after Eq. 2 (channel set) | Adds: every channel is a function of z, so a zero-weight channel still carries the state; each profile contains two null channels (constant mapping + noise; measured values of a channel with unit identity and order permuted away), zero weight, used for the leakage test. | C2: the r1 permutation test cannot separate leakage from benign redundancy. | Buys a construction-level leakage test. Cost: two generated-only channels with no measured counterpart; they are excluded from fidelity measures, and a reviewer may note that they make windows wider than the measured ones. |
| C2.2 | §3.5.2, permutation-importance sentence | Gate now on the null channels; redundant zero-weight channels are reported (predictability from the other channels; conditional permutation importance), not gated. | C2 resolution parts 1–2. | Buys a test that fails only on leakage. Cost: redundancy on graded channels is expected to be high and is reported, not bounded. |
| C2.3 | §3.6, first paragraph | Adds: the two columns differ in kind; the reference model is the primary scoring target (ϕ* is its faithful attribution); the trained column also reflects which observationally equivalent function was learned; ensemble spread (initialization × size) reported as the limit on any method. | C2 resolution parts 3–4. | Buys an honest reading of trained-model scores. Cost: ensemble of 10 LSTMs per profile at S6 plus attribution on each at S8 (compute); "single trained architecture" still holds since members differ only in size. |
| C2.4 | §5, new opening paragraph "What the benchmark can adjudicate" | Scoping: ground truth identifiable under the reference model; trained-model scores carry the model's choice among equivalent functions. | C2 paper-edit list. | States a limitation the r1 text implied it did not have. |
| C3.1 | §3.1.1, definition paragraph and Eq. 3 | `q_1` = first smoothed value, EOL at ρ·q₁, `z = (q₁ − q_t)/((1−ρ)q₁)` → `q_nom` documented nominal capacity, `q₁` = max of smoothed capacity over the first `k` positions, EOL at ρ·q_nom, `z = (q₁ − q_t)/(q₁ − ρ q_nom)`. | C3: MATR/HUST cells were cycled to 80 % of nominal; ρ against a higher observed initial capacity puts EOL below where cycling stopped; early capacity rise makes a first-position origin give `z < 0`. | Buys attainment on the datasets' own stopping rule and a non-negative early state. `T` no longer depends on `q₁` at all (`z ≥ 1 ⇔ q_t ≤ ρ q_nom`). Cost: `q_nom` must be verified per dataset (recorded in `configs/profiles/*.yaml`); NASA's "nominal" is the repository's rated 2 Ah. |
| C3.2 | §3.1.1, sentence reading Eq. 3 | "from 0 at the first position" → "from 0 at the early-life reference"; endpoints "ρ q_nom by declaration and q₁ by observation"; computable from data up to `t` "once the first `k` positions have been observed". | Follows from C3.1. The `k`-position qualifier is added because a maximum over the first `k` positions is not available before position `k`; not asked for by C3 but needed for the sentence to stay true. | Honest about a `k`-position start-up interval; the `t/T` leakage paragraph is untouched. |
| C3.3 | §3.1.1, new sentence after it | Why a maximum over the first positions rather than the first value (early capacity rise); frequency reported with the property audit. | C3 edit list ("one sentence on the robust early-life reference"). | No number stated; frequency comes from S2. |
| C3.4 | §3.1.1, ρ-conventions paragraph | States what ρ is taken against (documented nominal capacity) and why (stopping rules are stated against nominal; a higher initial capacity would put EOL below where cycling stopped); denominator guard; sensitivity sweep includes the first-position-anchored definition. | C3 edit list. | Previous convention reported rather than deleted. |
| C3.5 | §3.3, "Declared by design" list | Adds nominal capacity per dataset, `k`, and the exclusion margin. | The list must name what is declared. | none |
| C3.6 | §3.4, property-audit list | Adds "how often the early-life reference differs materially from the first-position capacity". | Makes the C3.3 forward reference true. | none |
| C4.1 | §3.2.1, paragraph after Eq. 5 (inside the C1 span) | Adds: a method whose values sum to f(window) − f(baseline) recovers ϕ* only when the baseline is `x⁰` (forward reference to §3.6). | C4 edit list ("one sentence tying ϕ* to the declared reference point"). | none |
| C4.2 | §3.6, new paragraph after the reference-values paragraph; `\label{sec:models}` added to the subsection | Declared baseline = pristine window (IG baseline, occlusion value, TimeSHAP background instance) and why (target zero there; lies near the first windows of every unit, unlike a zero input); ground truth `w(m + Σp − b)` supplied for any baseline `b`, so methods keep their defaults; secondary TimeSHAP run from the conventional average event as a sensitivity readout; mean-conditional background not adopted (circularity); occlusion has no efficiency property, so it is compared in rank and retrieval, not in sum. | C4: scoring efficiency-satisfying attributions against ϕ* presumes f(baseline) = 0, which an average event violates under a drifting mean. | Buys a baseline under which Σϕ = y holds for the reference model. Cost: the trained model's f(x⁰) is only approximately 0 (reported at S8); the secondary run adds one TimeSHAP pass. |
| C1×C3 | §3.3 step three | Capacity mapping "taken at the median early-life reference of the fitting units so that it is shared across units like every other mapping". | Blast radius of C1 + C3: with a per-unit `q₁` in Eq. 3 the capacity mapping would differ by unit, contradicting §3.1 ("mappings shared across all units") and C1 (`x⁰` identical across units). | Cost: generated units do not vary in initial capacity; the property table reports the measured spread of `q₁`. |

Build note (C2): over/underfull boxes rose from 1 to 4 (review build). All of the new ones are `Underfull \vbox … while \output is active` float-page artefacts from shifted page breaks; LaTeX and package warnings stay at 0.

## Dependencies on later measurements (no numbers were written into the paper by round 1)

- C1.3: whether any weighted channel is demoted by the guard → S3/S4 tables.
- C1.4: graded/sparse correlation per weighting → Table 3 (S6), investigation D06 if above bound.
- C2.2: null-channel permutation importance, redundant-channel predictability and conditional importance → Table 3 (S6).
- C2.3: ensemble identifiability floor → S6 training, Table 6 companion (S8).
- C3.3/C3.6: frequency of material difference between robust and first-position q₁; attainment per definition and ρ → S2 audit tables.
- C4.2: f(x⁰) of trained models; ranking under primary vs average-event background → S8.

## Round 1 blast-radius review

Re-read after C1–C4: Introduction, Related Work, all of Section 3, and the Results/Discussion scaffolding.

| location | sentence | status |
|---|---|---|
| §1 ¶5 | "The target variable is an explicit additive function of the first two terms" | Holds (additive about `x⁰`). No edit. |
| §1 ¶5 | "a dense graded field from the mean component … and a sparse set of positions carrying the inserted patterns" | Holds under recency/uniform weighting; the final-position collapse of both is now stated in §3.2.1. No edit. |
| §2 last ¶ | "attribution ground truth defined at every observation for a continuous target" | Holds. No edit. |
| Fig. 1, Fig. 2 captions | ϕ* as graded field + sparse set | Hold (Fig. 2 is illustrative, "vertical scales arbitrary"). No edit. |
| §3.1 Eq. 2 ¶ | "mappings φ_c … shared across all units of a profile" | Was contradicted by per-unit `q₁` for capacity; fixed by the C1×C3 row above. |
| §3.2.1 | "Since m = φ_c(z_u), the first term is a fixed function of the degradation state" | Holds. No edit. |
| §3.3 declared list | named `a` and `b`; lacked `q_nom`, `k`, margin | Fixed (C1.7, C3.5). |
| §3.4 audit list | lacked the early-life reference comparison referenced by C3.3 | Fixed (C3.6). |
| §3.5.2 | "the two terms of Equation 4" | Holds (Eq. 4 keeps two terms). No edit. |
| §3.6 ¶1 | "a single trained architecture" | Holds: ensemble members differ only in size and initialization. No edit. |
| §4.2 Table 3 row "Permutation importance, zero-weight channels" | results scaffold | Contradicted by C2.2 (gate is on null channels; redundant channels reported). Results placeholder, rewritten at S9. |
| §4.4 ¶1 "since the reference model reproduces the decomposable target up to ε" | results scaffold | Imprecise after C1 (up to `Σ w ε`). Results text, rewritten at S9. |
| Table 6 caption "mass on zero-weight channels is error by construction" | results scaffold | Holds for null and redundant channels alike (w = 0 ⇒ ϕ* = 0). Kept. |

Held citations found during the review (not edited in round 1; handled by D10): `pan2022` (§3.1.2, §3.3) uses a rest-time/decomposition method on CALCE data; the temperature-as-input claim cited to `olivares2013` (§3.1.2).
