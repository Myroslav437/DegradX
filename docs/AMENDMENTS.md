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

## Round 2 — S2 decisions (2026-09-15), against commit `a460111` (round 1)

`artifacts/amendments/latexdiff_round2.pdf`.

| id | where (paper/paper.tex) | what changed | why | cost / what it buys |
|---|---|---|---|---|
| D15 | §3.1.1, sentence introducing q₁; Eq. 3 | q₁ "attained at position t₁"; `T = min{t ≥ t₁ : z_t ≥ 1}` | The fall is measured from q₁; a record whose earliest readings sit below the threshold got T = 1 (NASA B0038). | One unit changes; none on MATR/HUST. |
| D13 | §3.1.1, ρ paragraph after the guard sentence | Measured records that end within a declared tolerance of the threshold reach EOL at their last position; generated units follow Eq. 3 alone. | HUST and MATR b1/b3 were recorded only to the stopping threshold: strict attainment 11/77 and 96/180; record-end rule 77/77 (T = Table S1 exactly) and 173/180. | A second EOL clause for measured records; z_T ∈ [0.983, 1) for them. |
| D12 | §3.3, step one | Readings no degradation produces are removed before smoothing: isolated single-position departures beyond a declared fraction of nominal capacity, and readings below half of nominal capacity that the record later recovers from. | A 2.88 Ah reading on a 1.1 Ah cell set q₁; failed NASA discharges gave T = 1–3. | 15 of MATR's 135 cells and 26 NASA units lose cycles; positions are re-indexed. |
| D16 | §3.3, step two | Families fitted "from the early-life reference to EOL". | Early-rise misfit dominated MATR/HUST residuals. | θ describes the fall only; generated units start at the fall. |
| D16 | §3.3, detection rule | Runs longer than the smoothing window are not patterns, with the reason (they change z_t, which patterns must not). | Long misfit runs (up to 120 positions) were detected as patterns. | Slow misfit hovering at the threshold can still split into short runs (HUST 7-5). |
| D12, D13 | §3.3, declared list | Adds the glitch fraction and the record-end tolerance. | The list must name what is declared. | none |

Blast radius (round 2): §3.2.2 "This is the same quantity that measured datasets provide as a RUL label" is made truer by D13 (HUST T equals the dataset's cycle life). Figure 3 caption ("reach EOL at different positions") is unaffected. No contradiction found in the Introduction or Related Work.

## Round 3 — S3 decisions (2026-09-15), against the S2 commit

`artifacts/amendments/latexdiff_round3.pdf`.

| id | where (paper/paper.tex) | what changed | why | cost / what it buys |
|---|---|---|---|---|
| D04 | §3.3 step two | Selection among families whose parameters are determined by the data (not at a bound in more than a declared share of units), with a margin within which the simpler family is preferred. | NASA rollover held its transition width at the lower bound in 6 of 8 units; EOL reproduction p90 26 % vs 9.6 % (power law). | NASA profile has no knee. |
| D05 | §3.3 detection, last sentence | A type is enabled only if detected at least a declared factor more often than in noise simulated with the profile's fitted variance and autocorrelation. | MATR/HUST detections at the declared k occur at 0.85×/0.47× their noise-only rate; NASA 6.8×. | MATR and HUST carry no inserted patterns; every sparse-set measurement rests on NASA PCoE. |
| D02 | §3.1.1, ρ paragraph | Units not reaching EOL are excluded from EOL-dependent quantities only (θ, lengths, transfer target) and retained for mappings, noise and patterns. | Their degradation state is defined under C3; NASA noise estimates rest on 13 instead of 8 units. | Mappings near z = 1 rest on reaching units. |
| D02 | §3.5.1, after "effective number of independent units" | Every measurement has a declared minimum count (interval within half its value); below it the cell is void with its count. | Resampling: median T readable from 5 units, pattern amplitude from 10 events. | NASA regeneration statistics (6 events) void. |
| D17 | §3.3 step one | The single-reading rule applies in any channel, relative to the channel's typical value. | A few charge-time readings inflated MATR noise variance 25×. | NASA charge-time role borderline. |
| D02/D04/D05 | §3.3 declared list | Adds the at-bound share and simplicity margin, the noise factor, the minimum counts. | The list names what is declared. | none |

Blast radius (round 3):
- §3.4 profiles paragraph (NASA "included for one property the others lack") is now what the data show (D05). It stays unchanged.
- §3.1.2 "A profile enables only the inserted pattern types its dataset exhibits" stays true under the noise-calibrated reading. Unchanged.
- §1 contribution text: "a sparse set of positions carrying the inserted patterns" holds for NASA PCoE only; the Results must say so, and §1 is not edited.
- Table 3 rows "Correlation of graded and sparse fields" and "Error change, pattern term removed" will be void for MATR/HUST with the reason "no inserted patterns (D05)".

## Round 4 — S4 decisions (2026-09-15), against commit `134d12d` (end of S3)

`artifacts/amendments/latexdiff_round4.pdf`.

| id | where | what changed | why | cost / what it buys |
|---|---|---|---|---|
| D01 | §3.2.1, after the channel-roles sentence | Each window is supplied with its pattern-free counterpart. The counterpart map is scored against the graded field, and the difference of the two maps against the sparse set, with the reason. | Plain retrieval scores ϕ* itself at chance (AP 0.064 vs 0.048); paired AP 1.000 and monotone under degradation. | Two attribution runs per NASA window; the unpaired question is reported as a secondary series. |
| C1 (blast radius, missed in round 1) | Figure 4 (`paper/img/fig_weights.pdf`) | Vertical axis label "weight $a_{u,c}$" → "position profile $\pi_u$"; drawing unchanged. Regenerated by `paper/img/scripts/fig_weights_r3.py` with the reconstructed style. | The figure still showed the notation C1 removed. | none |

Blast radius (round 4): §1's description of the protocol ("rank agreement against the graded field and precision-recall retrieval metrics … against the sparse set") still holds, since both scores remain; only the maps they are computed on are specified. Unchanged.

## Round 5 — held citations (D10), 2026-09-15

In `artifacts/amendments/latexdiff_round5_6.pdf`, which covers rounds 5 and 6 together (both were produced at S9, against commit `0bdb0c3`).

| id | where | what changed | why | cost / what it buys |
|---|---|---|---|---|
| D10 | §3.3, detection families | The families are distinguished by what triggers a detection (the capacity sequence itself vs rest time). pan2022 is described as decomposition plus a rest-time trigger, with one sentence noting that the families are not disjoint in the information they use. | pan2022 full text: regeneration is predicted by GPR on rest time and triggered by a rest-time threshold, not by assigning trend-uncorrelated components. | The argument for adopting residual detection is unchanged. |
| D10 | §3.1.2, negative fluctuations | Removed "entering prognostic models as an explicit input on the usable capacity of a cycle~\cite{olivares2013}". | The claim cannot be verified from any accessible text of olivares2013. | Temperature's role is supported by dataset evidence only (severson2019). |

## Round 6 — S7 and S8 results presentation (2026-09-16), against commit `603f8fe` (Results 4.3 part one)

In `artifacts/amendments/latexdiff_round5_6.pdf` (against commit `0bdb0c3`, covering rounds 5 and 6).

| id | where | what changed | why | cost / what it buys |
|---|---|---|---|---|
| D20 | Table 5 caption | The operating range is read on two probes, the reference model and Integrated Gradients on the trained model, with the declared accuracy gate; the table gains a profile and a score column and a failure column naming the probe. | On the trained model alone every examined setting value is "responsive", so the range would exclude nothing, including two values where the trained model is below the accuracy gate and its scores are void. | Two probes per setting value (6 CPU-min); interval boundaries near the saturation level are marked rather than smoothed. |
| D24 | Table 6 caption | Reference values are reported per profile under recency weighting instead of averaged over profiles, with the exact attribution of the reference model, the ensemble range and the average-event background as rows. | The averaged ordering of the methods differs from the per-profile ordering, the ensemble range is per profile, and retrieval exists only in NASA PCoE, so an "average over profiles" would be one profile in that column. | Table 6 is three times longer and set in \scriptsize; later work quotes reference values per profile. |
| — | Figure 8 | Placeholder box replaced by the measured panel (`img/fig_res_range.pdf`), caption states the two probes and the marked levels. | The figure is now measured. | none |

Blast radius (round 6): §3.5.3's sentence "The range over which they remain responsive is reported as the operating range of the benchmark" is unchanged and is what D20 implements. §3.6's "reported in aggregate, without stratification by position within the trajectory" is unaffected: D24 separates profiles, not positions within a window. No sentence in §1–§3 states that reference values are averaged over profiles.
