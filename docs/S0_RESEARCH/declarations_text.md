# DegradX: every declaration the specification needs, taken from the paper text (Sections 3 and 4)

**Source.** `/home/mmishchuk/projects/DegradX/paper/paper.tex` (462 lines, git HEAD `6221c50`), read in full.
**Cross-check.** Section, table, figure and equation numbers were taken from the compiled `paper/paper.pdf` (16 pages, pdfTeX, CreationDate 2026-09-15 15:49:50 CEST) using `pdftotext -layout`.
**Figure scripts.** `paper/img/scripts/*.py` were also read. Figure captions call these curves illustrative (L166 "Curves are illustrative", L134 "Vertical scales are arbitrary"), so no value in the scripts is normative. They are cited only where an implementer might mistake them for spec values (see X35 and X36).

## 0. Conventions

**Line numbers.** Each `Lnnn` is a physical line of `paper.tex`. Every prose paragraph is a single physical line, so one line number can hold many sentences. Quotes are verbatim LaTeX source.

**Numbering in the compiled PDF.**

| Kind | Items |
|---|---|
| Sections | 3.1 Generator (L121), 3.1.1 Mean component (L138), 3.1.2 Patterns and noise (L170), 3.2 Targets (L180), 3.2.1 (L185), 3.2.2 Transfer target (L220), 3.3 Fitting (L231), 3.4 Profiles (L250), 3.5 Evaluation Protocol (L257), 3.5.1 Fidelity (L260), 3.5.2 Usability (L275), 3.5.3 Responsiveness (L279), 3.6 Models and Baselines (L285, no `\label`) |
| Equations | Eq.1 generator L126, Eq.2 mean L142, Eq.3 state/EOL L150-152, Eq.4 target L189, Eq.5 ground truth L196, Eq.6 transfer L224 |
| Tables | T1 Profile fidelity L303-316; T2 Property-level comparison L318-340; T3 Usability L354-371; T4 Resolution L385-397; T5 Operating range L406-420; T6 Reference values L427-442 |
| Figures | F1 loop L114-119; F2 generator L131-136; F3 mean L163-168; F4 weights L207-212; F5 TSTR L268-273; F6 L342-347; F7 L378-383; F8 L399-404 |

**Classification labels.** These follow the paper's own wording.
- **D-list**: named in the "Declared by design" sentence (L238).
- **E-list**: named in the "Estimated from the measured dataset" sentence (L238).
- **D-inline**: the paper calls it "declared" or "predetermined" somewhere else (L148, L158, L205, L243, L245, L255, L277, T3) but does not name it in the L238 list.
- **E-inline**: the paper says it is fitted, estimated or "set during fitting" somewhere else (L145, L161, L178).
- **DEFAULT**: "at their default configurations" (L289).
- **NONE**: the paper neither declares nor estimates the quantity and gives no value. It is an implementer choice that must be declared.

**AFFECTS-FIT flag.**
- **Y**: the value changes the output of at least one of the six fitting steps (L236), or of the pre-build dataset verification in L255 (called "S2 audit" below). The step outputs are: EOL and unit exclusion, θ distribution, family choice, φ_c, channel covariance, noise variance and autocorrelation, pattern rate, amplitude and duration, and the length distribution.
- **Y-sens**: the value changes only the sensitivity analyses the paper requires (the ρ range in L158, the range of the multiple in L245). It does not change the primary profile.
- **Ind**: the value can change profile content only through a downstream corrective loop (for example L277 "the profile is corrected before use") or by deciding which profiles exist.
- **N**: the value does not change fitted parameters.

---

## 1. The paper's two lists, verbatim (L238)

L238, verbatim:

> `The distinction between what is measured and what is chosen is reported explicitly, since it determines what the benchmark can claim. Estimated from the measured dataset are the distribution of $\theta$, the choice of family, the mappings $\varphi_c$ and the covariance among channels, the noise variance and autocorrelation, the rate, amplitude, and duration of the inserted patterns, and the length distribution. Declared by design are the EOL fraction $\rho$, the smoothing window length and polynomial order, the pattern detection thresholds, the number of channels and which of them enter the target, the weights $a$ and $b$, the window length $L$, and the generator settings varied in the protocol.`

### 1a. ESTIMATED FROM DATA (E-list, L238)

| ID | Verbatim item | Defined or used at | Value in paper |
|---|---|---|---|
| E1 | "the distribution of $\theta$" | L161, L236 (step 2: "The empirical distribution of the fitted parameters over units is the profile's distribution of $\theta$") | none (data) |
| E2 | "the choice of family" | L161, L236 (step 2) | none (data) |
| E3 | "the mappings $\varphi_c$" | L140-145, L236 (step 3) | none (data) |
| E4 | "the covariance among channels" | L236 (step 3: "the covariance among channels is recorded") | none (data) |
| E5 | "the noise variance and autocorrelation" | L178, L236 (step 4) | none (data) |
| E6 | "the rate, amplitude, and duration of the inserted patterns" | L175, L236 (step 5), L243 | none (data) |
| E7 | "the length distribution" | L236 (step 6) | none (data) |

### 1b. DECLARED BY DESIGN (D-list, L238)

| ID | Verbatim item | Defined or used at | Value in paper | AFFECTS-FIT |
|---|---|---|---|---|
| D1 | "the EOL fraction $\rho$" | L148, L150-152, L155, L158, L255 | **none** (L158 names only the conventions "80\%" of nominal and "a fade of $20$ to $30\%$") | **Y** |
| D2 | "the smoothing window length" | L148 ("a declared filter"), L236 (Savitzky–Golay) | **none** | **Y** |
| D3 | "[the smoothing] polynomial order" | L236 | **none** | **Y** |
| D4 | "the pattern detection thresholds" (two of them, per L245: "The procedure has two thresholds") | L243: "a declared multiple of the residual scale" and "a declared minimum" (run length) | **none** | **Y** |
| D5 | "the number of channels" | L124 ($C$), L253, L255 | **none** | **Y** (φ_c, covariance and noise are fitted per channel) |
| D6 | "which of them enter the target" | L200 | **none** | N |
| D7 | "the weights $a$ and $b$" | L189, L196, L200, L203, L205 | **none**. The paper gives only the structure: $a$=0 off-target, a position profile on target channels; $b$=0 on channels without patterns, one constant on channels with patterns | N |
| D8 | "the window length $L$" | L187 | **none** | N |
| D9 | "the generator settings varied in the protocol" | L283 ("noise variance, the sharpness of the transition in the degradation state, sequence length, and the amplitude of the inserted patterns"); T5 rows L413-416 | **none** (no grids) | N |

No item in either list has a numeric value anywhere in the paper.

---

## 2. The only numeric or categorical values the paper does give (Sections 3-4)

The list is exhaustive. None of these is a tunable constant with a chosen number, except that the structural zeros in D7 are fixed.

| Line | What is fixed |
|---|---|
| L124 | "one position corresponds to one charge--discharge cycle"; the sequence runs to $T$ (EOL) |
| L150-152 | $z_t=(q_1-q_t)/((1-\rho)q_1)$; $T=\min\{t: z_t\ge 1\}$; z runs "from $0$ at the first position to $1$ at EOL" (L155) |
| L158 | Context only, no adopted value: "a fall to $80\%$ of nominal capacity" (common convention) and "stopped at a fade of $20$ to $30\%$". A single ρ is used for all profiles. Units that never reach ρ "are excluded" |
| L178 | $\mathbb{E}[\varepsilon_{t,c}]=0$ |
| L200 | $a_{u,c}=0$ on channels that do not enter the target; $b_{u,c}=0$ on channels with no inserted pattern; $b$ is "a single constant value" on channels that carry one |
| L205 | Three weightings: recency, uniform, final-position ("places all weight on the last position"). F4 caption L210: "The recency weighting used by default" |
| L224 | $R_t = T - t$ |
| L236 | Six steps. Savitzky–Golay filter. Nonlinear least squares. Three candidate families: two-term exponential [he2011]; rollover with four parameters "the initial rate, the transition position, the transition width, and the terminal rate" [saxena2022]; power law. Family selected "per dataset by cross-validated fit error across units" |
| L243 | Two detection criteria: residual exceeds a multiple of the residual scale, and the run reaches a minimum length. "the sign of the run gives the type". Recorded per pattern: "position of its extremum, its signed amplitude, and its duration in positions" |
| L248 | Splits at unit level; $t/T$ excluded as an input; elapsed $t$ allowed |
| L253 | Three profiles: MATR, HUST, NASA PCoE. MATR channels: "discharge capacity, internal resistance, charge time, and temperature statistics per cycle" |
| L262 | Three fidelity measures |
| L266 | Report the error ratio with a bootstrap interval; "A ratio near one" |
| L277 | Four checks plus two declared properties |
| L281 | Four degradation operators |
| L283 | Four generator settings |
| L287 | One trained architecture: "a recurrent network with long short-term memory units", plus the reference model |
| L289 | Three methods at "default configurations": TimeSHAP, IG, feature occlusion. Mask-optimising methods excluded |
| L291 | Three separate seed sources: generation, model initialization, attribution sampling |
| L296 | "an interval obtained by bootstrap over units" for every reported quantity |
| T3 L365-367 | Bound column entries: "sign", "sign", "$\approx 0$". L362: "reported". L361, L363, L364: placeholder bounds "band --", "$\le$ --", "$\le$ --" |

---

## 3. Line-by-line inventory of quantities that need a value the paper does not give

Column "Val?" records whether the paper gives a value. Items that are already D-list or E-list are repeated only where a sub-choice inside them is unspecified.

### 3.1 Generator (L121-178)

| ID | Lines | Verbatim (key phrase) | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| G1 | L124, L253, L255 | "$c \in \{1,\dots,C\}$ indexes channels"; MATR: "discharge capacity, internal resistance, charge time, and temperature statistics per cycle" | No | D-list (D5) for the number; NONE for the identity and per-cycle definition of each channel | **Y** | The exact channel list per profile. Which "temperature statistics" (the paper names none). Whether all profiles share a common channel set |
| G2 | L124 | "one position corresponds to one charge--discharge cycle" | Given | given | **Y** | Handling of missing, skipped or duplicated cycle indices, and of first/formation cycles. The paper is silent |
| G3 | L124 | "$T$ is the position at which the unit reaches its end of life" ($x\in\mathbb{R}^{T\times C}$) | Given (definition) | given | **Y** | Whether measured units are truncated at $T$ before fitting steps 2-6 and for TSTR (see F7) |
| G4 | L145 | "The mappings $\varphi_c$ are smooth, are shared across all units of a profile" | No | E-inline/E-list (E3) | **Y** | Function class and smoothness control (see F15) |
| G5 | L148 | "the capacity channel, smoothed by a declared filter" | Type given at L236 (Savitzky–Golay) | D-list (D2, D3) | **Y** | Window length, polynomial order, **boundary/edge mode** (NONE, and it determines $q_1$ at t=1), and whether one setting covers all profiles or each profile gets its own (NONE) |
| G6 | L148 | "let $q_1$ be its value at the first position" | Given (definition) | "by observation" (L155) | **Y** | Whether initial cycles are dropped before t=1. $q_1$ depends on the edge mode in G5 |
| G7 | L150, L158 | "a single declared $\rho$ across all profiles" | **No** | D-list (D1) | **Y** | The value of ρ |
| G8 | L158 | "report the sensitivity of the fitted parameter distributions to $\rho$ across the range these conventions span" | No grid. The range is implied by the "80\%" and "20 to 30\%" fade conventions, i.e. ρ≈0.70-0.80 (inference, not stated) | D-inline (implied) | **Y-sens** | The ρ grid. Which fitted distributions (θ only, or all of E1-E7) are re-reported |
| G9 | L158 | "report the number of units that never reach it, which are excluded" | Rule given | given | **Y** | The count is reported. Other exclusion rules (fit failure, missing channels, outliers) are NONE (see F40) |
| G10 | L161 | "$\theta$ drawn per unit from a distribution estimated from measured units" | No | E-list (E1) | **Y** | How to sample from an "empirical distribution" (L236): resample fitted vectors jointly with replacement, or smooth (KDE, jitter), or fit a parametric model. Whether $q_1$ is a component of θ (see X2, X3) |
| G11 | L161, L236 | "Several established empirical fade models are fitted" | Families named; equations not written | E-list (E2) | **Y** | Exact functional forms and parameterisations (F8-F10) |
| G12 | L175 | "each described by a position, a signed amplitude, and a duration" | No | NONE (shape) | N (detection records extremum and run length regardless of shape); **Ind** if amplitude/duration must be mapped to shape parameters | **Temporal shape** of an inserted pattern (rectangular, decaying, bump). The paper never states it. It fixes the support of the "sparse set" (X22) |
| G13 | L175, L243 | per-pattern "position" is recorded (L243 "the position of its extremum") | No | NONE. Position distribution is **not** in the E-list, which estimates only "rate, amplitude, and duration" | N (not listed); **Ind** if a position model is estimated | Where patterns are placed in generated units (uniform over 1..T? dependent on z?), overlap rules, and patterns cut by window or unit edges |
| G14 | L175, L245 | "A profile enables only the inserted pattern types its dataset exhibits"; "a type that is not detected in a dataset is not enabled" | No (minimum count unspecified) | NONE | **Y** | The enabling criterion: at least one detection, a minimum count, or a minimum rate |
| G15 | L126, L173, L175, L200 | $p_{k,t,c}$ carries a channel index; "$b_{u,c}$ is zero on channels that carry no inserted pattern" | **No** | NONE | **Y** if patterns are also detected or estimated on non-capacity channels; N if capacity only | **Which channels carry patterns.** Detection (L236 step 5, L243) runs on "the residuals of the trajectory fit", which exist only for capacity (see X8) |
| G16 | L178 | "Noise is added per channel with variance and autocorrelation set during fitting" | No | E-inline/E-list (E5) | **Y** | Noise process family (e.g. AR(1) vs ARMA), autocorrelation lag(s), marginal distribution (Gaussian vs empirical) |
| G17 | L178, L236 | noise "per channel" versus "the covariance among channels is recorded" | No | NONE for the use; E4 for the value | **Y** (E4's definition) | Whether noise is cross-channel correlated using E4 or independent per channel (see X7) |
| G18 | L178 | "variance" (single) | No | NONE | **Y** | Constant (homoscedastic) versus state-dependent noise variance |
| G19 | L140-145, L236 | channels generated as $\varphi_c(z_t)$ | No | NONE | **Y** | Units of generated channels (raw physical units vs capacity normalised by $q_1$). Needed for TSTR on measured data (X2, X23) |
| G20 | L152, L161 | $T=\min\{t:z_t\ge1\}$ on the parametric curve | No | NONE | N (generation) | Handling of sampled θ whose curve never reaches $z=1$ or is non-monotone: maximum horizon, rejection or truncation |
| G21 | — | number of generated units per profile (for fitting audit, TSTR training, fidelity, scoring) | No | NONE | N | Must be declared. It changes TSTR and fidelity outcomes |

### 3.2 Targets and attribution ground truth (L180-229)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| T1 | L187 | "Let $W$ be a window of $L$ consecutive positions ending at position $t$" | No | D-list (D8) | N | The value of L. Whether one L covers all profiles |
| T2 | L183, L187 | "from a window of the sequence" | No | NONE | N | Which end positions t are used (all t≥L? stride?). Treatment of t<L (padding or skip). Windows per unit for training and for scoring |
| T3 | L189, L196 | $y=\sum a\,m+\sum b\sum_k p$; $\phi^\star=a\,m+b\sum_k p$ | No | NONE | N | Whether $m$ is in raw units, normalised units, or measured from an origin (e.g. $m-\varphi_c(0)$) (see X10, X11) |
| T4 | L200 | "$a_{u,c}$ is zero on channels that do not enter the decomposable target" | No | D-list (D6) | N | The set of target channels per profile |
| T5 | L200 | "follows one of the position profiles below on the channels that do" | No | D-list (D7) | N | Per-channel magnitude of $a$ across target channels (equal? scaled by channel scale?). Normalisation (sum to 1, max 1, other) |
| T6 | L200 | "$b_{u,c}$ ... takes a single constant value on those that do" | **No** | D-list (D7) | N | The value of b. Whether "single" means one value across profiles or one per profile (X15) |
| T7 | L205 | "\emph{Recency} weighting increases smoothly toward the end of the window at a decay rate declared per profile" | **No** (no functional form, no rate) | D-inline ("declared per profile") | N | Functional form (exponential?) and decay rate per profile. The figure script `fig_weights.py` L13-18 uses exp(−(L−u)/τ), τ=8, L=40, normalised to sum 1. That is **illustrative, not a paper value** |
| T8 | L205 | "\emph{Uniform} weighting makes every position equally relevant" | No | D-list (D7) | N | Level (1/L, 1, or matched total mass) |
| T9 | L205 | "\emph{Final-position} weighting places all weight on the last position" | Partly | D-list (D7) | N | Magnitude of that weight (1? matched total mass?) |
| T10 | L205, L210 | "recency weighting used by default" | Given | given | N | Which weighting feeds T3 and T6, which have no weighting dimension (X39) |
| T11 | L205 | "we report whether the score orderings place the methods in the same sequence" | No | NONE | N | Criterion for "same sequence": identical order, Kendall τ, or a tie tolerance |
| T12 | L218 | "the linear map that applies the weights $a$ and $b$ to the observed values of the window" | No | NONE | N | How to build it when a cell has both $a\ne0$ and $b\ne0$ (contradiction, X9). What the reference model's attributions are scored against (φ* or the analytic w⊙(x−baseline)) |
| T13 | L218, L277, T3 L361-362 | "the two properties above"; "the two properties of the target declared in Section~\ref{sec:target}"; T3: "Variance ratio of the two terms ... band"; "Association of $y$ with RUL ... reported" | **No** | D-inline ("declared properties", L355) | N (but may drive the choice of b, X15) | Band limits. The variance-ratio definition (which term over which, over which windows). The association statistic (Pearson, Spearman, other) |
| T14 | L224, L227, L266 | "$R_t = T - t$"; "This is the same quantity that measured datasets provide as a RUL label"; "using their RUL label" | Formula given | given | N | Whether held-out measured units use $T$ recomputed by Eq.3 (declared ρ, $q_1$) or the dataset's native label (X23) |
| T15 | L229, L248 | "Neither $R$, nor $T$, nor any quantity derived from them is available to a model" | Given | given | N | — |

### 3.3 Fitting (L231-248)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| F1 | L234, L117, L266 | "Fitting uses the training split only" ("fitting split" L117/L266; "held-out split" L117) | **No** | NONE | **Y** (which units are fitted) | Split fraction, stratification (e.g. MATR batches, HUST protocols), split seed |
| F2 | L234, L266 | — | No | NONE | N | Whether a measured validation subset is carved from the fitting split (for early stopping of the TSTR reference model) |
| F3 | L236 step 1 | "the capacity channel is extracted for every unit" | No (MATR "discharge capacity" L253; HUST and NASA not named) | NONE | **Y** | Which capacity quantity per dataset |
| F4 | L236 step 1 | "smoothed by a Savitzky–Golay filter" | Type only | D-list (D2, D3); NONE for edge mode and per-profile vs global | **Y** | Window, order, edge mode, global vs per profile |
| F5 | L236 step 1 | "EOL is located by Equation~\ref{eq:state}" | Given | given | **Y** | Uses the smoothed $q$ (L148) |
| F6 | L236 step 2 | "candidate parametric families are fitted to each unit's capacity trajectory by nonlinear least squares" | No | NONE | **Y** | **Fit target:** raw, smoothed, or $q/q_1$-normalised capacity (X4) |
| F7 | L236 step 2 | same | No | NONE | **Y** | **Fit range:** positions 1..T or the full recorded trajectory. Whether the curve is constrained to z(1)=0 and z(T)=1 |
| F8 | L236 | "the two-term exponential established for capacity fade~\cite{he2011}" | Form not written | NONE (cited only) | **Y** | Exact equation and parameter count |
| F9 | L236 | "a rollover form whose parameters are the initial rate, the transition position, the transition width, and the terminal rate~\cite{saxena2022}" | Parameter names given, equation not | NONE | **Y** | Exact equation. Whether an intercept or initial-capacity parameter is added to the four named ones |
| F10 | L236 | "a power law, which has fewer parameters but cannot express a transition" | Form not written | NONE | **Y** | Exact equation and parameter count |
| F11 | L236 | "nonlinear least squares" | No | NONE | **Y** | Solver, loss (plain vs robust), initial guesses or multi-start, bounds, iteration limits, what happens to units whose fit fails |
| F12 | L236 | "The family is selected per dataset by cross-validated fit error across units" | **No** | E-list (E2) for the outcome; NONE for the procedure | **Y** | CV scheme (folds; what is held out: positions within a unit or whole units, X26), error metric (RMSE on capacity or on z), aggregation (mean or median), tie-break or parsimony rule |
| F13 | L236 | "the error of every candidate is reported" | Given | given | N | — |
| F14 | L236 | "The empirical distribution of the fitted parameters over units is the profile's distribution of $\theta$" | Representation given (empirical) | E-list (E1) | **Y** | Joint vs marginal. Storage scale (raw vs transformed). Whether $q_1$ is included |
| F15 | L236 step 3 | "the mappings $\varphi_c$ ... are fitted as smooth monotone functions" | No | E-list (E3); NONE for the method | **Y** | Function class (monotone spline, isotonic plus smoothing, other), smoothing parameter, knots |
| F16 | L236 step 3 | "of the fitted degradation state" | **Ambiguous** | NONE | **Y** | z from the step-2 parametric fit vs z from step-1 smoothed capacity (X1) |
| F17 | L236 step 3 | "monotone" | No | NONE | **Y** | Direction per channel (from data or declared). Treatment of channels that are not monotone in z, e.g. temperature statistics (X20) |
| F18 | L236 step 3 | — | No | NONE | **Y** | Pooling of (z, x_c) pairs across units. Per-unit weighting, since long units dominate a pooled fit |
| F19 | L236 step 3 | "the covariance among channels is recorded" | No | E-list (E4); NONE for the definition | **Y** | Covariance of what (residuals $x_c-\varphi_c(z)$, raw channels, or within windows), pooled vs per unit, covariance vs correlation. Whether generation uses it (X7, X32) |
| F20 | L236 step 3 | "for the capacity channel the mapping is affine by construction" | Given (form) | given | **Y** | Slope and intercept depend on $q_1$ per unit (X2) |
| F21 | L236 step 4 | "the residuals of the trajectory fit supply the noise variance and autocorrelation" | No | E-list (E5) | **Y** | Residual definition for **non-capacity** channels, where no "trajectory fit" exists (X6) |
| F22 | L236 step 4 | "computed with the positions occupied by detected patterns excluded" | Rule given | given | **Y** | Autocorrelation lag(s) and estimator with gaps. Per-unit then averaged vs pooled. Whether capacity pattern positions are also excluded on other channels |
| F23 | L236 steps 4-5 | "Fourth ... detected patterns excluded ... Fifth, the same residuals supply the inserted patterns" | Order as written is circular | NONE | **Y** | Order of operations or iteration: detect, then estimate noise? Is the residual scale in step 5 computed before patterns are excluded? (X5) |
| F24 | L243 | "exceeds a declared multiple of the residual scale" | **No** | D-list (D4) | **Y** | The multiple k |
| F25 | L243, L245 | "the residual scale" ("alongside the residual scale itself") | No | NONE | **Y** | Estimator (SD, MAD, other), per unit vs pooled per dataset, with or without pattern positions |
| F26 | L243 | "whose length reaches a declared minimum" | **No** | D-list (D4) | **Y** | Minimum run length in positions. One value across profiles? L241: "the same rule has to apply to every profile" |
| F27 | L243 | "a run of consecutive positions"; "the sign of the run gives the type" | Partly | given | **Y** | Absolute vs one-sided comparison, strict vs non-strict, gap tolerance inside a run, whether a run may change sign |
| F28 | L243 | "its signed amplitude" | No | NONE | **Y** | Amplitude = residual at the extremum? In raw capacity units or relative to $q_1$ or the trend? (X29) |
| F29 | L243 | "its duration in positions" | Given (run length) | given | **Y** | — |
| F30 | L243 | "we estimate the distribution of amplitude and of duration" | No | E-list (E6); NONE for the form | **Y** | Empirical vs parametric. Joint vs independent. Separate per type (sign) |
| F31 | L243 | "the per-unit rate of occurrence over the dataset" | No | E-list (E6); NONE for the definition | **Y** | Count per unit vs per position (per cycle). Per type. Interaction with varying $T$ and the sequence-length sweep (X28) |
| F32 | L245 | "report the detected rate and the amplitude distribution over a declared range of the multiple" | **No** | D-inline ("declared range") | **Y-sens** | Grid of k values |
| F33 | L245 | "both are declared before fitting" | Procedural | given | — | Must be fixed and recorded before any fit is run |
| F34 | L236 step 6 | "the empirical distribution of unit lengths is recorded" | No | E-list (E7) | **Y** | Which $T$ (from smoothed-capacity EOL). What the recorded distribution is **used for** in generation, since generated $T$ follows from θ (X16) |
| F35 | L248 | "all splits are performed at the level of units ... on both generated and measured data" | No fractions | NONE | N | Train, validation and test fractions for generated units (LSTM on y, TSTR on R) |
| F36 | L248 | "Normalization statistics are computed on training units alone" | No | NONE | N | Type (z-score, min-max), per channel. For TSTR: statistics from generated or measured training units (X31) |
| F37 | L248 | "the normalized position $t/T$ is excluded while the elapsed position $t$ is not" | Allowed, not mandated | NONE | N | Whether elapsed t is actually an input (LSTM on y, TSTR model) |
| F38 | L158, L255 | exclusion rules beyond never reaching ρ | No | NONE | **Y** | Units with missing channels, failed fits, anomalous cycles |

### 3.4 Profiles and the S2 audit (L250-255)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| P1 | L253 | "temperature statistics per cycle" | No | NONE | **Y** | Which statistics (min, max, mean, other) |
| P2 | L253, L255 | HUST and NASA PCoE channel sets are not named; "which channels are available across all units" | No | NONE (D5 covers the number) | **Y** | Channel availability criterion (e.g. no missing cycles, or a tolerated missing fraction). Common vs per-profile channel set |
| P3 | L253 | MATR "supplies the largest number of units" | No | NONE | **Y** | Which MATR batches or units, and which HUST and NASA cells, are included |
| P4 | L255 | "the fraction of units whose smoothed capacity channel is monotone within tolerance" | **No** | NONE | **Y** (S2 audit output); N for θ unless failing units are excluded, which the paper does not state | Monotonicity statistic and tolerance |
| P5 | L255 | "the detected rate and amplitude of capacity regeneration" | depends on D4 | via D4 | **Y** (S2) | Same thresholds as F24-F27 |
| P6 | L255 | "the fraction of units reaching the declared EOL threshold" | via D1 | D-inline ("declared EOL threshold") | **Y** (S2) | — |
| P7 | L255 | "the distribution of unit lengths" | — | E7 | **Y** (S2) | — |
| P8 | L255 | "A dataset that does not exhibit the property it was selected for has its role reassigned or is dropped" | **No** | NONE | **Ind** (which profiles exist and in what role) | Pass/fail criteria per role: MATR "largest number of units" and primary fidelity read; HUST "protocol varies"; NASA "documented capacity regeneration" (a minimum detected rate?) |
| P9 | L253 | NASA "fidelity measurements are reported with the number of units it contains" | Given | given | N | — |

### 3.5.1 Profile fidelity (L260-266, T1, T2, F5)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| FI1 | L262 | "the classification error of a discriminator trained to separate generated from measured windows~\cite{yoon2019}" | No | NONE | N | Discriminator architecture, training setup, train/test split, class balance, repeats |
| FI2 | L262, T1 L308 "Discriminative err." | same | No | NONE | N | Raw classification error vs \|accuracy−0.5\| |
| FI3 | L262 | "a Fr\'{e}chet-style distance computed in a learned representation space~\cite{psagan2022}" | No | NONE | N | **Representation encoder** (which model, trained on what, embedding size). Whether it is fitted per profile |
| FI4 | L262 | "the agreement of the cross-channel covariance structure" | No | NONE | N | Agreement metric (matrix norm of the difference, correlation of entries, other) |
| FI5 | L262, L301 | "All three are computed on windows, with the window length ... stated alongside" | No | NONE | N | **Fidelity window length** (same as L or not), stride, number of windows |
| FI6 | L262, T1 "Units (eff.)" | "the effective number of independent units" | No | NONE | N | Definition, especially for the generated side, whose unit count is arbitrary (G21) |
| FI7 | L117, L262 | "The profile is separately compared against the held-out split" | Partly (F1 caption) | given (caption) | N | Confirm that all fidelity measures, including the T2 "meas." column, use the held-out split (X24) |
| FI8 | L264, T2 | "each reported for the generated and the measured side" | No | NONE | N | Re-running the fitting pipeline on generated units. The summary statistic per T2 cell (mean, median, distribution distance) |
| FI9 | T2 L328-329 | rows "Drift rate", "Transition position" | No | NONE | N | Mapping to θ components. "Drift rate" matches no named family parameter; "Transition position" exists only in the rollover form (X17) |
| FI10 | L266 | "A model is trained on a profile using the transfer target"; "The same architecture trained on the measured units of the fitting split" | No | NONE | N | TSTR architecture. The text does not say it is the L287 LSTM. Hyperparameters, early stopping |
| FI11 | L266 | — | No | NONE | N | **TSTR input**: channels, **window length**, normalisation (F36), whether t is an input |
| FI12 | L266, L304 | "We report the ratio of the two errors" | No | NONE | N | **TSTR error metric** (RMSE, MAE, other). Direction is given: TSTR/reference (T1 caption L304; `fig_tstr.pdf` text "TSTR / reference") |
| FI13 | L266 | — | No | NONE | N | Number of generated units and windows for TSTR training; generation seeds |
| FI14 | L266, L296 | "with a bootstrap interval"; "bootstrap over units" | No | NONE | N | **Resample count B**, CI level, method (percentile or other), resampling over held-out units |
| FI15 | L266 | "A ratio near one" | No | NONE | N | Tolerance for "near one", if used as a criterion |
| FI16 | L266 | "evaluated on units of the paired dataset that took no part in fitting" | — | — | N | Which t per held-out unit (all t≤T?), handling of t>T |

### 3.5.2 Usability (L275-277, T3)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| U1 | L277, T3 L363 | "A model must reach a predetermined accuracy on each profile"; row "Model error on $y$ & $\le$ --" | **No** | D-inline ("predetermined") | N | **The accuracy/error metric** (RMSE, normalised RMSE, R², other) |
| U2 | same | same | **No** | D-inline | N | **The threshold value** |
| U3 | L277, L205 | — | No | NONE | N | Which model must pass (trained LSTM; per weighting? per seed?) and on which generated split |
| U4 | L277, T3 L364 | "The correlation between the graded and the sparse contribution fields across the dataset must remain below a declared bound" | **No** | D-inline ("declared bound") | N | Correlation type, over which cells (all, or cells with patterns), absolute value or not, and **the bound** |
| U5 | L277, T3 L365-366 | "Retraining with each of the two terms of Equation~\ref{eq:target} removed in turn must change model behaviour in the direction the construction predicts"; bound "sign" | Sign only | NONE | N | Meaning of "removed" (from y only, or from x and y). The metric compared and on which target. The predicted sign. Tolerance or significance |
| U6 | L277, T3 L367 | "permutation importance must show that models do not rely on the channels whose target weights are zero"; "$\approx 0$" | No tolerance | NONE | N | Permutation scheme, repeats, metric, tolerance for ≈0. Whether "zero target weights" means a=b=0 or only a=0 |
| U7 | L277 | "the profile is corrected before use" | **No** | NONE | **Ind** (may change profile channels or parameters) | The correction procedure (X12) |
| U8 | L352, L355 | "Each threshold or declared bound is stated in the row it governs" | — | — | N | All T3 bounds must be fixed before running |

### 3.5.3 Responsiveness (L279-283, T4, T5, F7, F8)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| R1 | L281 | "adding noise of increasing variance" | No | NONE | N | Variance grid, scale relative to the field, distribution |
| R2 | L281 | "shifting a known fraction of the mass toward the start or the end of the sequence" | No | NONE | N | Fraction grid, shift mechanism. "Sequence" vs window (X40) |
| R3 | L281 | "smoothing across neighbouring positions" | No | NONE | N | Kernel and width grid. Across positions only |
| R4 | L281 | "randomly permuting a known fraction of the values" | No | NONE | N | Fraction grid, permutation scope (within channel, within window) |
| R5 | L281, T4 L386 | "the smallest degradation that a score resolves reliably is reported as its resolution"; T4 caption: "with the criterion for reliability stated in Section~\ref{sec:protocol}" | **No**. The criterion is **not** stated in Section 3.5 | NONE (dangling reference) | N | **Reliability criterion** (e.g. CI separation from the undegraded score) |
| R6 | L281 | "A score that does not decrease as the map is degraded" | No | NONE | N | Monotonicity test and tolerance |
| R7 | L281 | — | No | NONE | N | Repetitions per magnitude. Units, windows and profiles used |
| R8 | L83, L262, T6 L428 | "rank agreement against the graded field and precision-recall retrieval metrics standard in the literature~\cite{crabbe2021,queen2023} against the sparse set" | No | NONE | N | **Rank-agreement statistic** (Spearman, Kendall). Cells included (all L×C or target channels). Per-window then aggregated. **Retrieval metrics** (which PR-based quantities), set membership (support of p vs extremum position), sign handling. UNVERIFIED: the metric names used by crabbe2021/queen2023 were not checked in those papers |
| R9 | L283, T5 L411 "Range examined" | "varies the generator settings that control task difficulty" | No | D-list (D9) | N | Grids for noise variance, transition sharpness, sequence length, pattern amplitude. Multiplicative around fitted values? |
| R10 | L283 | "the sharpness of the transition in the degradation state" | No | D-list (D9) | N | Parameter mapping. Defined only if the rollover family is selected (X17) |
| R11 | L283 | "sequence length" | No | D-list (D9) | N | Unit length T or window L, and how it is imposed given that T follows from θ (X16) |
| R12 | L283, F8 L401 | "Scores that saturate near their maximum" | **No** | NONE | N | **Saturation threshold** |
| R13 | L283, F8 L401 | "scores near chance" | **No** | NONE | N | **Chance level definition** (e.g. score of a random map, computed empirically) and the "near" threshold |
| R14 | L283, T5 L411 | "Responsive range", "Failure mode outside it" | No | NONE | N | Responsiveness criterion (a slope or separation test distinct from R12/R13) |
| R15 | L283 | — | No | NONE | N | Base profile for the sweeps. One factor at a time? Which model(s) and methods are scored at each setting? Retraining per setting? Interaction with the usability gate |

### 3.6 Models and baselines (L285-291)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| M1 | L287 | "a recurrent network with long short-term memory units" | No hyperparameters | NONE | N | Layers, hidden size, dropout, head, loss, optimiser, learning rate, batch size, epochs, early stopping |
| M2 | L205, L287 | — | No | NONE | N | Models per profile × weighting × seed (X14) |
| M3 | L289 | "TimeSHAP~\cite{bento2021} ... at their default configurations" | "default" | DEFAULT | N | Implementation and version. **Background/baseline** (UNVERIFIED whether the library has a default or requires one). Sample count, pruning, output level (event, feature, cell). Conversion to an L×C map (UNVERIFIED whether a full cell map is produced by default) |
| M4 | L289 | "Integrated Gradients (IG)~\cite{sundararajan2017}" at defaults | "default" | DEFAULT | N | Implementation and version, **baseline**, number of steps, integration rule. Input space (normalised) vs φ* in raw units (X10) |
| M5 | L289 | "feature occlusion~\cite{suresh2017}" at defaults | "default" | DEFAULT | N | Occlusion unit (cell, channel over window, sliding window), replacement value, implementation |
| M6 | L289, T6 | — | No | NONE | N | Which windows are explained and how many. "reported in aggregate": mean over windows, units, seeds |
| M7 | L291, L296 | "controlled by separate random seeds" | No count | NONE | N (the generation seed changes generated units, not fitted parameters) | Number of seeds per source. Design (one-at-a-time vs factorial). Variance-decomposition method |

### 4. Results placeholders (L293-443)

| ID | Lines | Verbatim | Val? | Paper class | AFFECTS-FIT | What must be decided |
|---|---|---|---|---|---|---|
| RS1 | L296 | "Every reported quantity is accompanied by an interval obtained by bootstrap over units" | No | NONE | N | B, CI level (same as FI14) |
| RS2 | L304 | "a ratio near one" | No | NONE | N | Same as FI15 |
| RS3 | L319 | "The detection thresholds behind the regeneration rows, and the sensitivity of those rows to them, are reported with the counts of Section~\ref{sec:calibration}" | — | D4, F32 | **Y** / **Y-sens** | — |
| RS4 | T2 L327-336 | 10 rows; only "Regeneration" pattern rows | — | — | N | Whether the negative pattern type gets rows. The summary statistic per cell |
| RS5 | F6 L344 | "units generated from the fitted parameter distribution overlaid, with the state axis of Equation~\ref{eq:state} marked" | — | — | N | Which units (illustration only) |
| RS6 | L352 | "A profile that fails the accuracy threshold has its attribution scores reported as void ...; the same convention is used in every table that follows" | — | — | N | See X21 |
| RS7 | T6 L428 | "averaged over profiles that pass the usability checks"; "mass on zero-weight channels is error by construction" | No | NONE | N | Averaging scheme (over profiles, weightings, seeds, windows). **Zero-weight mass** definition (fraction of \|attribution\| on channels with a=0? and b=0?). Which weighting |
| RS8 | L87 | RQ1 "which properties resist calibration" | No | NONE | N | Criterion for "resists calibration" |

---

## 4. Internal tensions and ambiguities an implementer must resolve

Each item is checked against the text. "Fit" marks whether the resolution affects fitted parameters.

**X1. Which capacity defines z and T. (Fit: Y)**
- **Smoothed capacity.** L148: "Let $q_t$ denote the capacity channel, smoothed by a declared filter". Eq.3 at L150 is defined on that $q_t$, and L236 step 1 locates EOL on it.
- **Parametric curve.** L161: "The trajectory $q_t$, and hence $z_t$, follows a parametric curve with ... $\theta$". L236 step 3 fits φ_c "of the **fitted** degradation state".
- **Consequences.** For measured units, $T$ (and hence $R$ and the step-6 length distribution) comes from smoothed capacity. For generated units, $T$ comes from the parametric curve of a sampled θ. A θ fitted to 1..T_smoothed need not reach z=1 exactly at T_smoothed, so generated and measured length distributions differ systematically (T2 "Unit length"). The z used to fit φ_c is ambiguous.
- **Must declare:** (a) z_meas for step 3: smoothed or parametric; (b) z_gen: parametric; (c) whether the parametric fit is constrained to cross z=1 at T_smoothed.

**X2. Per-unit $q_1$ versus a shared φ_c. (Fit: Y)**
- From Eq.3, $q_t = q_1[1-(1-\rho)z_t]$. The capacity mapping is affine with intercept $q_1$ and slope $-(1-\rho)q_1$, and both are **unit-specific**.
- L145 says φ_c "are shared across all units of a profile". It adds that "two units that have reached the same degradation state show the same expected values in every channel". L236 step 3: "for the capacity channel the mapping is affine by construction".
- These agree only if (i) capacity is normalised as $q/q_1$, making φ_cap(z)=1−(1−ρ)z with no free parameter, or (ii) $q_1$ is fixed across units.
- The alternative, $q_1$ in θ with φ_cap per unit, contradicts L145.
- The same "same expected values" clause removes per-unit offsets on other channels (e.g. cell-to-cell initial resistance). That variation then ends up in residual "noise" or disappears, which inflates E5 or reduces fidelity.
- **Must declare** the normalisation and where unit-to-unit level variation goes.

**X3. $q_1$ and θ. (Fit: Y)** For generated units, $q_1$ would be the parametric curve at t=1 (L148 "its value at the first position"). If θ is fitted to raw Ah, it carries the scale; if fitted to $q/q_1$, it carries a constraint. The four rollover parameters named in L236 include no intercept or initial capacity. Must declare whether one is added.

**X4. The trajectory fit uses raw or smoothed capacity. (Fit: Y)**
- L236 step 2 says only "each unit's capacity trajectory".
- Step 4 takes noise variance and autocorrelation from "the residuals of the trajectory fit", and step 5 detects patterns on "the same residuals".
- If the fit target were smoothed capacity, residuals would be the small SG-vs-curve difference. Noise would be underestimated, which L178 warns against: "a generator cleaner than the measured data would report every attribution method as more accurate than it is". Regeneration runs would also be attenuated.
- The coherent reading is to fit raw capacity (1..T), with smoothing used only for EOL/z. The paper does not state it.

**X5. Steps 4 and 5 are circular. (Fit: Y)** Step 4 (noise) excludes "the positions occupied by detected patterns", but detection is step 5. Step 5 thresholds on "the residual scale", which must be computed before patterns are known. The order (or an iteration) and the residual-scale estimator must be declared.

**X6. Residuals for non-capacity channels. (Fit: Y)** Only capacity has a "trajectory fit" (step 2). L178 adds noise "per channel", and step 4 has to supply per-channel variance and autocorrelation. For c≠capacity the residual must be defined, presumably $x_c-\varphi_c(z)$, with z per X1. It must also be declared whether capacity pattern positions are excluded on those channels.

**X7. Noise per channel versus recorded cross-channel covariance. (Fit: Y, for the definition of E4)**
- L178 describes noise as per-channel variance and autocorrelation only. L236 step 3 records "the covariance among channels" (E4). L262 and T2 compare cross-channel covariance between generated and measured data.
- With independent per-channel noise, generated covariance comes only from the shared z. Measured residual covariance would then be unreproducible by design.
- **Must declare** whether E4 is the covariance of residuals, and whether it drives correlated noise in generation.

**X8. Which channels carry patterns. (Fit: Y if detection extends beyond capacity)**
- Eq.1 indexes $p_{k,t,c}$ by channel. L200 states that $b$ is "zero on channels that carry no inserted pattern and takes a single constant value on those that do", which **implies some channels carry patterns and others do not**.
- Detection (L236 step 5, L243) is defined only on the capacity trajectory-fit residual. L173 motivates negative patterns with ambient temperature, which could also appear in a temperature channel. T2 has only "Regeneration" rows.
- The default consistent reading is patterns on capacity only, so $b\ne0$ only on capacity and the sparse field lives entirely on the capacity channel. This is not stated.
- Consequence: if capacity is not among the target channels for $a$, it still enters $y$ through $b$. D6 ("which of them enter the target") only covers $a$.

**X9. The reference model cannot reproduce y exactly when a and b share a channel. (Fit: N)**
- L218: "the linear map that applies the weights $a$ and $b$ to the observed values of the window. It reproduces the target exactly when noise is absent".
- A linear map on observed $x=m+\sum p$ (no noise) has one weight per cell, $w_{u,c}$. For $f(x)=y$ for all m and p, we need $w=a$ wherever $m\ne0$ and $w=b$ wherever $p\ne0$. Since $m=\varphi_c(z)\ne0$ on every channel, a pattern channel requires $a_{u,c}=b$ at every position.
- **Constant $b$ with recency $a$ contradicts this** unless the pattern channel has $a$ uniform and equal to $b$. The same holds if the pattern channel has $a=0$: then $f=\ldots+b\sum m$, which is not $y$.
- Options:
  1. On pattern channels, set $a_{u,c}\equiv b$ (uniform). This conflicts with the default recency weighting on that channel.
  2. Define the "reference model" on generator components $(m,p)$, not observed $x$. This contradicts "observed values".
  3. Accept a non-exact reference model and report the gap.
- Separately, with noise, $f(x)-y=\sum w\varepsilon$. It is zero-mean but has non-zero variance, and the reference model's attributions (e.g. $w\odot x$ at a zero baseline) differ from $\phi^\star=a m+b\sum p$ by $w\odot\varepsilon$. "any remaining error is attributable to the attribution method alone" (L218) is therefore not exact. Declare what reference-model attributions are scored against: $\phi^\star$, or the analytic $w\odot(x-\text{baseline})$.

**X10. Attribution baseline and input normalisation versus $\phi^\star=a\,m$. (Fit: N)**
- Eq.5 uses raw $m$, which implicitly means a zero reference. Models receive normalised inputs (L248), and IG, occlusion and TimeSHAP attribute relative to a baseline.
- For a linear model on $\tilde x=(x-\mu)/\sigma$, zero-baseline IG gives $a\odot(x-\mu)$, not $a\odot m$.
- Because $m$ sits near its level (e.g. capacity ≈ $q_1$), the graded field $a\,m$ within a window is dominated by the position profile of $a$, not by degradation.
- The illustrative `fig_generator.py` L39 draws the graded field as $a\cdot(m_0-m)$, which differs from Eq.5 (non-normative, but shows the ambiguity).
- **Must declare** the origin of $m$ in $\phi^\star$ and y, and the attribution baselines.

**X11. Channel scales in Eq.4. (Fit: N)** Raw channels mix units (capacity, resistance, time, temperature per L253). Unless $a$ is scaled per channel or $m$ is normalised, $\sum a\,m$ is dominated by the largest-scale channel. This also drives the T3 variance-ratio band. It is not stated.

**X12. Redundant z information versus the zero-weight-channel checks. (Fit: Ind)**
- Every channel is $\varphi_c(z)+\ldots$ (Eq.1-2), so zero-weight channels carry the same degradation information as target channels. A trained LSTM can legitimately use them, especially if they are less noisy.
- L277 nevertheless requires permutation importance ≈0 on those channels and treats reliance as leakage ("the profile is corrected before use"). T6 L428 treats "mass on zero-weight channels" as "error by construction" for the trained model.
- For the trained model this conflates model dependence with ground truth. The correction procedure is undefined and could alter the channel set or parameters, which is why it is flagged Ind.

**X13. Noise excluded from y. (Fit: N)** Eq.4 is built from $m$ and $p$ only, while the model receives $x$ with $\varepsilon$. The trained model has an irreducible error set by noise and pattern/noise separability. The reference model's error variance is $\mathrm{Var}(\sum w\varepsilon)>0$. The predetermined accuracy threshold (U2) must be set relative to this floor, and the RQ3 noise sweep (L283) will drive models below it (void scores).

**X14. Three weightings mean three targets. (Fit: N)** L205: "The attribution methods under evaluation are scored against $\phi^\star$ under all three weightings". Since $a$ defines $y$, each weighting is a different target. It is not stated whether the LSTM is retrained per weighting. Scoring a model trained on recency-weighted y against uniform-weighting $\phi^\star$ would score the wrong ground truth. Declare models per weighting, and the accuracy gate per weighting.

**X15. Declared per profile versus comparability. (Fit: N)**
- L203 argues fitted weights "would also vary between profiles, making scores incomparable for the same reason $\rho$ is standardized".
- Yet L205 gives recency "a decay rate declared per profile", and T3 row 1 imposes a variance-ratio "band", which in practice would mean tuning $b$ per profile.
- L200 "a single constant value" does not say whether it is one value across profiles.
- Declare whether the decay rate and $b$ are global or per profile, and whether $b$ is set to satisfy the band.

**X16. "Sequence length" as a generator setting versus T as a consequence of θ; role of the length distribution. (Fit: Y for the E7 role; N for the sweep)**
- L155: "$T$ is a consequence of the trajectory rather than an input to it". Step 6 (L236) records "the empirical distribution of unit lengths", but nothing says how generation uses it.
- L283, T5 L415 and F8 vary "sequence length" as a setting.
- Varying T without changing θ requires rescaling the time axis (which changes pace and RUL), truncation, or reading "sequence length" as window $L$. The text does not choose.

**X17. Transition sharpness and T2 rows are family-specific. (Fit: N for the sweep, but coupled to E2)**
- "the sharpness of the transition in the degradation state" (L283) maps to the rollover "transition width" (L236).
- The power law "cannot express a transition" (L236). The two-term exponential has no explicit transition parameter.
- T2 rows "Drift rate" (matches no named parameter) and "Transition position" (rollover only) presume a family.
- If CV (F12) selects a non-rollover family for any profile, these are undefined.

**X18. Dangling or incorrect cross-references.**
- (a) T4 caption L386: "with the criterion for reliability stated in Section~\ref{sec:protocol}". Section 3.5 (L281) only says "resolves reliably" and gives no criterion.
- (b) L218 "which is what the two properties above report" and L277 "the two properties of the target declared in Section~\ref{sec:target}". Section 3.2 never names two properties; only T3 rows L361-362 do (variance ratio; association of y with RUL).
- (c) L296 "reference values of Section~\ref{sec:protocol}" and L425 "the three methods of Section~\ref{sec:protocol}". The methods are in 3.6 (L285-291, no `\label`); the PDF renders both as "Section 3.5".
- (d) The F1 caption (L117) lists "the degradation state $z$" among profile parameters, whereas L238 lists the distribution of θ.

**X19. Causality claim versus centred smoothing; patterns versus measured z. (Fit: Y, via SG edge handling and z_meas)**
- L155 says $z_t$ "is therefore computable from data available up to $t$". A centred Savitzky–Golay filter uses up to (window−1)/2 future positions, and $q_1$ uses positions 1..window. This is harmless because z is not an input and L248 lets fitting use full units, but the claim is not literal.
- L175 says patterns "do not alter $z_t$, the position of EOL". That holds for generated units, but for measured units, regeneration longer than the SG window survives smoothing and shifts measured z and T. The measured "fitted degradation state" is then non-monotone in t.

**X20. Monotone φ_c for non-monotone channels. (Fit: Y)** Step 3 requires "smooth monotone functions". L253 includes "temperature statistics", which the paper gives no reason to expect monotone in z. Declare the direction rule and the fallback.

**X21. Void convention versus averaging in T6; gate scope. (Fit: N)**
- L352: a failing profile "has its attribution scores reported as void ...; the same convention is used in every table that follows". T6 L428 is instead "averaged over profiles that pass the usability checks", which drops void profiles.
- Averaging across profiles is also the pooling that L266 rejects for TSTR ("a pooled evaluation would allow a close match on one dataset to compensate for a poor match on another").
- Gate scope: L277 defines "void" only for the accuracy check. The permutation check leads to "corrected before use". No consequence is stated for failing the correlation bound or the ablation sign, yet T6 requires passing "the usability checks" (plural).
- T6 has no weighting dimension, which implies the recency default (X39).

**X22. The "sparse set of positions" versus the continuous sparse term. (Fit: N)** L83, L134 and T6 describe a "sparse set of positions". Eq.5 gives the continuous, signed term $b\sum_k p_{k,u,c}$, whose support depends on the unspecified pattern shape (G12). Negative patterns give negative contributions. Declare set membership (support, extremum position only, or a threshold), sign handling, and patterns clipped by window edges. If a profile has no enabled pattern type (L245), then $b\equiv0$ and retrieval, the U4 correlation and the U5 pattern-term ablation are undefined for that profile.

**X23. TSTR details and labels. (Fit: N, except that exclusions follow ρ)**
- "The same architecture" (L266) is not explicitly the LSTM of L287. Input window, features and normalisation source (X31) are unspecified.
- Testing a profile-trained model on measured units requires generated channels in the measured units' scale (ties to X2).
- L227 calls R "the same quantity that measured datasets provide as a RUL label", but T is defined by the declared ρ relative to $q_1$ (L148), not the dataset conventions (L158). Held-out labels must be recomputed by Eq.3 to be consistent.
- Units that never reach ρ are excluded (L158) and cannot appear in the held-out split either.

**X24. Which measured split the fidelity measures use. (Fit: N)** The F1 caption (L117) says "The profile is separately compared against the held-out split". L262 and L264 do not repeat this. The T2 "meas." column could be read as the fitted (fitting-split) values, which would make the comparison in-sample. Declare it.

**X25. ρ relative to $q_1$ versus conventions relative to nominal capacity. (Fit: Y)** L148 defines EOL as a fraction of $q_1$ (smoothed first-position capacity). L158 describes conventions relative to "nominal capacity" and derives the sensitivity range from them. The two references differ whenever $q_1\ne$ nominal, which changes which units "never reach" ρ and are excluded. Whether $q_1$ exceeds or falls below nominal in MATR, HUST or NASA was UNVERIFIED here, since datasets were not read per instructions.

**X26. "Cross-validated fit error across units" is not well-defined for per-unit fits. (Fit: Y)** Each unit's curve is fitted separately (L236), so it is unclear what is held out. Possible readings: (a) held-out positions within each unit (interpolation or extrapolation CV), aggregated across units; (b) unit-level folds where the θ distribution from training folds predicts held-out units' curves; (c) k-fold over units of per-unit in-sample error (then CV adds nothing). This decides E2.

**X27. b is keyed to pattern-carrying channels, not target channels. (Fit: N)** L200 ties $b\ne0$ to "channels that carry inserted patterns", independently of D6 (target channels for $a$). A pattern-carrying channel enters $y$ even if it is not a target channel for $a$. The U6 "channels whose target weights are zero" must say whether that means $a=b=0$.

**X28. Per-unit rate versus variable T. (Fit: Y)** L243 estimates "the per-unit rate of occurrence". If rate means count per unit, generated units of different $T$ (and the sequence-length sweep, X16) get the same expected count regardless of length. If it means per position, the count scales with $T$. Declare which.

**X29. Amplitude definition and selection bias. (Fit: Y)** The recorded amplitude is the signed residual at the extremum of an above-threshold run (L243). It includes noise at that position and is selected by exceeding k×scale, which biases it upward in magnitude. L245 discusses the effect of the threshold on the distribution but not this bias. Mapping it to the inserted shape's amplitude (G12) must be declared.

**X30. Validation data for measured-trained models. (Fit: N)** The TSTR reference is "trained on the measured units of the fitting split" (L266). Any early-stopping or validation set must come from the fitting split, and its fraction is undeclared (F2).

**X31. Normalisation source in TSTR. (Fit: N)** L248: "Normalization statistics are computed on training units alone". For the TSTR model the training units are generated, so measured held-out units would be normalised with generated statistics. That is itself a source of TSTR error, and the alternative is not stated.

**X32. Covariance quantities differ. (Fit: Y, for the E4 definition)** Step 3 records "covariance among channels" (cycle-level, implicitly). L262 computes "agreement of the cross-channel covariance structure" "on windows", and T2 compares "Cross-channel covariance". These may be different statistics (residual vs raw, cycle vs window). Declare one definition used on both sides.

**X33. Noise variance is both estimated and a declared sweep setting. (Fit: N)** E5 is "Estimated", and D9 ("generator settings varied in the protocol") includes "noise variance" (L283). The same applies to pattern amplitude (E6 vs D9) and the transition parameter (E1 vs D9). Declare that base values are estimated and the sweep grid is declared, and the sweep's parameterisation (e.g. multipliers).

**X34. "Number of channels" is declared but bounded by data. (Fit: Y)** D5 declares the number, while L255 reports "which channels are available across all units". The declared set must be a subset of available channels. Declare what happens if a dataset lacks a reference channel.

**X35. An illustrative script uses the rejected $t/T$ form (non-normative).** `paper/img/scripts/fig_mean_component.py` L17-20 draws $z=((t-1)/(T-1))^{3.2}$, the lifetime-normalised form L156 rejects as leakage. The figure is captioned "Curves are illustrative" (L166). An implementer must not reuse it.

**X36. Illustrative constants in the figure scripts are not paper values.** Examples: `fig_weights.py` L13-18 (L=40, τ=8, exponential recency normalised to sum 1); `fig_generator.py` L18 (two-term exponential coefficients), L23-26 (Gaussian-bump patterns, amplitudes 0.04/−0.03/0.055, durations 11-14), L32 (noise SD 0.017), L37 (graded weight decay 260). None appears in `paper.tex`. Any declarations file that attributes them to the paper is wrong.

**X37. Effective number of units on the generated side. (Fit: N)** T1 "Units (eff.)" and L262 "effective number of independent units" have no definition. On the generated side the unit count is a free choice (G21), so the definition must not reward generating more units.

**X38. Measured data after EOL. (Fit: Y)** L124 defines the sequence as ending at T. Whether cycles after T in measured units are discarded before fitting (F7) and before TSTR evaluation (FI16, where $R_t<0$) is not stated.

**X39. Default weighting in tables. (Fit: N)** L205 requires scores under all three weightings and a check of whether orderings agree. T3, T6 and F7/F8 have no weighting dimension, and only the F4 caption (L210) names recency as the default. Declare that tables use recency and where the three-weighting comparison is reported.

**X40. "Toward the start or the end of the sequence". (Fit: N)** L281 and F7 L380 speak of shifting mass along the "sequence", but $\phi^\star$ is defined over a window $W$ (L187, L196). T4 has a single "Shifted mass" column for both directions. Declare window vs unit scope and how the two directions are reported.

**X41. The variance-ratio band is a declared property of generated data. (Fit: N)** T3 row 1 imposes a "band" (declared) on a quantity computed from generated data. No consequence is stated for falling outside it (re-choose b? void?).

**X42. "Default configurations" for arguments without defaults. (Fit: N)** L289 runs the methods "at their default configurations". Baselines and backgrounds for TimeSHAP, IG and occlusion, and the occlusion window, may be arguments with no library default. Whether each library has defaults is UNVERIFIED here and must be checked against the installed implementations and versions.

**X43. Attribution sampling seed. (Fit: N)** L291 gives a seed for "any sampling performed by an attribution method". Whether IG and occlusion are deterministic in the chosen implementations is UNVERIFIED, so it is unclear which of the three methods this seed affects.

---

## 5. Summary: the declarations that block fitting

These items have AFFECTS-FIT = Y and no value in the paper. They must be confirmed before fitting runs and before the S2 audit.
- **Declared quantities:** D1 ρ; D2 and D3 SG window and order; D4 multiple k and minimum run length; D5 channel count and identity (G1, P1, P2, P3, F3).
- **Filter and exclusion details:** SG edge mode (G5, F4); first-cycle handling for $q_1$ (G2, G6); truncation at T (G3, X38); exclusion rules (F38).
- **Split:** fraction, stratification and seed (F1).
- **Trajectory fit:** target and range (F6, F7, X4); family equations (F8-F10); NLS settings (F11); CV scheme and metric (F12, X26); θ representation and $q_1$ (F14, X2, X3).
- **φ_c:** method, z source, monotone direction and pooling (F15-F18, X1, X20); capacity normalisation (F20, X2).
- **Covariance:** definition (F19, X7, X32).
- **Noise:** residuals for non-capacity channels (F21, X6); noise model and autocorrelation estimator (G16-G18, F22).
- **Pattern detection:** step order (F23, X5); residual-scale estimator (F25); run rules (F27); amplitude definition (F28, X29); amplitude/duration distribution form (F30); rate definition (F31, X28); enabling criterion (G14); pattern channels (G15, X8).
- **Length distribution:** which T and its role (F34, X16).
- **S2 audit:** monotonicity statistic and tolerance (P4); channel availability rule (P2); role and drop criteria (P8, Ind).
- **Sensitivity grids (Y-sens):** ρ grid (G8), k grid (F32).
