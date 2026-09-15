# DegradX: precedent for the constants the paper declares but does not specify (domain research, S0)

Scope: the eight topics assigned. For each one: **Proposal**, **Precedent** (with sources), **Residual uncertainty**.
Evidence rules. Every number below comes from a source I opened: a PDF or web page, installed package source, or a script I ran. If I only saw a claim in a search-engine snippet or a secondary source, it is marked **UNVERIFIED (secondary)**. If I found no precedent, I say so.
I did not read anything under `/home/mmishchuk/projects/DegradX/data/`. Nothing here depends on the raw datasets. Every count that needs the data is flagged as a check to run.

Local evidence directory (downloaded papers, text extracts, cloned code, scripts):
`/tmp/claude-1000/-home-mmishchuk-projects-DegradX/e1767cc0-419f-4700-b388-11290dc5e816/scratchpad/s0_research/domain/`
(`src/` holds the cloned repos and the venv. Commit hashes are listed at the end.)

---

## 0. Headline risks found while researching (read first)

1. **The EOL reference is q1, not nominal capacity, and MATR/HUST may not reach ρ=0.80.** The published conventions are 80% of *nominal* capacity for MATR (Severson 2019) and 70% of *rated* capacity for NASA. The paper instead defines ρ relative to the smoothed first-cycle capacity q1 (paper.tex l.148-152). The MATR cells were cycled to the nominal-based 80% threshold (0.88 Ah). Any MATR/HUST cell whose q1 is below 1.1 Ah therefore needs to fall *below* 0.88 Ah to reach ρ=0.80 relative to q1. Some cells may have stopped before that. For example, a hypothetical q1 = 1.07 Ah gives a threshold of 0.856 Ah (arithmetic only). Saxena 2022 says "Total test cycles … do not equate to the EOL for many cells" and that values below 0.88 Ah were removed. So some cells ran past 0.88 Ah, but not necessarily all. **The exclusion count at ρ=0.80 relative to q1 is the first data check to run.**
2. **Baseline mismatch between φ\* and the methods' baselines.** φ\*_{u,c} = a_{u,c} m_{u,c} (paper l.195-197) is an attribution against a *zero* reference. Captum IG, Occlusion and FeatureAblation default to a zero baseline (captum 0.9.0 source, below). TimeSHAP uses a training-set average or median event as background (TimeSHAP paper Eq. 5; package `calc_avg_event` uses the median). For the linear reference model, the exact Shapley or IG attribution with baseline B is a_{u,c}(x_{u,c} − B_{u,c}), not a_{u,c} m_{u,c}. Under mean-nonstationarity x − B is far from x, so TimeSHAP scored against φ\* is penalised by construction. Also, "zero" means zero *after normalization*, which is not the physical zero. **The ground truth needs a declared reference: either define φ\* relative to the same baseline the methods receive, or give every method a zero baseline in the space where m is defined.**
3. **TimeSHAP has no default cell-level configuration.** `cell_level` raises `ValueError("No threshold condition provided for cell level")` unless you pass `threshold`, `top_x` or `top_x_events`+`top_x_feats`. Cells that are not selected are merged into "Other Events", "Other Features" and "Pruned Events" aggregates (timeshap 1.0.4 `explainer/cell_level.py`, the `cell_level` function). A dense L×C map therefore needs a declared non-default setting: top_x_events=L, top_x_feats=C, and no pruning.
4. **Citation-accuracy flags in Section 3:**
   - **pan2022** is cited (l.241) as a decomposition method that assigns trend-uncorrelated components to regeneration. In the paper I read, EMD extracts only the trend. Regeneration is switched on by a **rest-time threshold**, λ = 1 if t_i ≥ t_G,th = 18 h (Eq. 2, p.4; p.10). The data are **CALCE CS2**, not NASA, and EOL is 76%. It belongs with the rest-time family, or needs rewording.
   - **olivares2013** is cited (l.173) for temperature as an explicit model input. Pola et al. 2016, from the same group, describe the Olivares 2013 model and write "This model was upgraded with inclusion of the average temperature of operation as a model input" (Pola 2016, p.3). That suggests the temperature input is Pola 2016's addition. Olivares' full text was not reachable (it sits behind a proof-of-work wall), so this is **PLAUSIBLE, not confirmed**.
5. **Smoothing and regeneration statistics interact.** A Savitzky-Golay filter with polyorder 2 keeps only 37-71% of the peak of a jump-and-geometric-decay pattern at W=11 (my simulation, §2). If regeneration residuals are taken from the *smoothed* series, the amplitude distribution is biased downward. Detection residuals should be raw capacity minus the parametric fit.
6. **Causality wording.** A centered SG filter uses (W−1)/2 future cycles, so q_t, and therefore z_t, is not "computable from data available up to t" (l.155) unless a one-sided filter is used. This affects only the claim, not the fitting, which may use full units (l.248).
7. **"Decay rate declared per profile"** (l.205) contradicts the paper's own comparability argument for standardising ρ (l.158, l.203). Declare one decay as a fraction of L, shared by all profiles.

---

## 1. EOL fraction ρ

**Proposal.** Declared ρ = **0.80**, relative to q1 as the paper defines it. Sensitivity grid ρ ∈ {**0.70, 0.75, 0.80, 0.85, 0.90**}. The grid spans the NASA 70%-of-rated convention, Pan 2022's 76%, the 80% convention, and BatteryLife's 90% for cells that do not reach 80%. Report exclusions per profile at every grid value.
Also declare a rule before seeing fits: if ρ=0.80 relative to q1 excludes too many MATR or HUST units, the declared value moves to 0.85. The trigger level needs to be set by the team; I found no precedent for one. As an alternative handling rule there is BatteryLife's extrapolation rule (below).

**Precedent.**
- MATR (Severson et al. 2019, Nature Energy, doi:10.1038/s41560-019-0356-8; PDF from https://web.mit.edu/braatzgroup/Severson_NatureEnergy_2019.pdf, local `severson2019.txt`):
  - Quote: "cycle life (or equivalently, end of life) defined as the number of cycles until 80% of nominal capacity"
  - Cells: "A123 Systems, model APR18650M1A, 1.1 Ah nominal capacity", "temperature-controlled environmental chamber (30 °C)"
  - Cycle lives "from approximately 150 to 2,300 cycles (average cycle life of 806 with a standard deviation of 377)"
  - "four cells had unexpectedly high measurement noise and were excluded from analysis"
  - "cell temperatures vary by up to 10 °C within a cycle"
  - Chamber temperature fluctuations cause error increases (Methods and Fig. 2 text)
- Saxena et al. 2022 (J. Power Sources 542:231736; OSTI accepted manuscript https://www.osti.gov/servlets/purl/1910034, local `saxena2022.txt` ~l.245):
  - 178 LFP cells
  - "minimally processed to remove discharge capacity values below 80% of the nominal capacity (0.88 Ah)"
  - "Total test cycles … do not equate to the EOL for many cells"
- NASA PCoE (data.gov catalogue https://catalog.data.gov/dataset/li-ion-battery-aging-datasets): experiments stopped at "end-of-life (EOL) criteria of 30% fade in rated capacity (from 2 Ah to 1.4 Ah)". Qin et al. 2016 repeats this for B0005-B0007 and states "The total charge/discharge cycles are all 168 for these three batteries" (Energies 9:896, p.12, local `qin2016.pdf`).
  - Qin defines SOH = C_i/C_0 with C_0 "the initial capacity value" (Eq. 21). Their Fig. 6 shows final SOH relative to *initial* capacity of roughly 70% (No.5), below 60% (No.6) and about 75% (No.7). These are **approximate figure reads, not tabulated**. If they hold, B0007 would not reach ρ=0.70 relative to q1, while all three reach 0.80.
  - B0005 initial capacity 1.86 Ah: **UNVERIFIED (secondary search snippet)**, so 1.4/1.86 ≈ 0.75 is not verified.
- HUST (Ma et al. 2022, EES 15:4083, doi:10.1039/d2ee01676a): the publisher returned 403.
  - Mendeley page (https://data.mendeley.com/datasets/nsc7hnsg4s/1): "77 LFP/graphite cells", "1.1 Ah nominal capacity", "constant temperature of 30°C". No termination criterion on that page.
  - EOL = 80% of nominal for HUST: **UNVERIFIED (secondary)**. HyBattNet arXiv:2505.16664 states 80% for this dataset.
  - Cycle life 1,100-2,700: **UNVERIFIED (secondary search snippet)**.
- Pan et al. 2022 (Energies 15:2498, p.10, local `pan2022.txt` l.836-840): "When the available capacity decreases by 20–30%, its performance will decline exponentially … the end-of-life threshold of a lithium-ion battery is 76%." This is the source for the paper's "20 to 30%".
- BatteryLife benchmark (arXiv:2502.18807v1, https://arxiv.org/html/2502.18807v1):
  - EOL is "the cycle number at which the SOH becomes no larger than 80%", relative to nominal
  - λ=90% for CALB "since most batteries didn't reach 80%"
  - "batteries whose final SOH greater than λ+2.5%" are excluded
  - "linear extrapolation" is used for final SOH in (λ, λ+2.5%]
  - "excluded batteries whose life labels are no larger than 100"
  - This gives a precedent for both a 90% grid point and an exclusion/extrapolation rule.
- BatteryML code (read-only clone, commit 2861ae3b): `batteryml/label/rul.py` l.14-35.
  - Default `eol_soh=0.8`, applied as `Qd <= nominal_capacity_in_Ah * eol_soh`
  - `pad_eol=True` gives non-reaching cells label = cycles+1
  - `min_rul_limit=100.0`: labels ≤ 100 become NaN
  - `preprocess_MATR.py` l.218 and `preprocess_HUST.py` l.80 set `nominal_capacity_in_Ah=1.1`
- Zhang, Altaf, Wik (arXiv:2304.11671v3, local `kneeonset.txt` l.572, 607-608): EoL "set to 80% of their initial nominal capacity". Warranty convention of "70-80% of their initial nominal capacity" (l.93).

**Residual uncertainty.**
- How many MATR/HUST/NASA units reach each ρ relative to q1 needs the data. The MATR/HUST risk at ρ=0.80 is real (headline 1).
- q1 depends on the SG edge treatment. scipy's default `mode='interp'` fits a degree-`polyorder` polynomial to the first `window_length` points and evaluates the edge outputs from it (scipy 1.18.1 `_savitzky_golay.py` docstring l.297-300). q1 therefore shifts with W.
- If early cycles show capacity *rising* (not verified for these datasets), z_t < 0 at the start. The generator should declare whether z is clamped.

---

## 2. Savitzky-Golay window length and polynomial order

**Proposal.** A **fixed window in cycles**, not a fraction of length.
- **W = 11 cycles, polyorder N = 2**, `mode='interp'`, the same for every profile.
- Sensitivity: W ∈ {7, 11, 21}, N = 2.
- Take regeneration and noise residuals from raw capacity minus the parametric fit, never from the smoothed series.

Rationale:
- (a) W=11 (half-width 5) is wider than the longest regeneration region Qin tabulates for NASA (5 cycles), so a single regeneration cannot trigger or delay the z ≥ 1 crossing on its own.
- (b) Its 3 dB cutoff is 0.197 (normalized to Nyquist), so components with periods shorter than about 10 cycles are attenuated. That is far shorter than the transitions of interest (Saxena fixes the rollover width δ at 50 cycles for MATR-type cells).
- (c) W=11 ≤ the shortest unit length in all three datasets. MATR has at least 150 cycles (Severson); NASA B0005-7 have 168 (Qin). Other NASA cells are **unverified**, and `mode='interp'` requires W ≤ len.
- (d) A fraction-of-length window would make q_t, and so T, depend on how long the experiment ran, which is the stopping time the transfer label encodes. A fixed cycle count gives the same cutoff in cycles⁻¹ in every profile, matching the paper's standardization logic for ρ.

**Precedent.**
- Schafer, "What is a Savitzky-Golay filter?", IEEE SPM 28(4):111-117, 2011, doi:10.1109/MSP.2011.941097 (local `schafer2011.txt` l.395-399):
  - Eq. (12): f_c ≈ (N+1)/(3.2M − 4.6), valid for M ≥ 25 and N < M
  - For 10 ≤ M < 25, "a formula similar to (12) with 4.6 replaced by 2 gives more accurate predictions"
  - Table 1: M=5, N=2 → 0.197; M=6, N=2 → 0.165
  - I reproduced the table with `scipy.signal.savgol_coeffs` and `freqz` (script `src/sg_cutoff.py`). Output, as (W, N): f_c, period at cutoff = 2/f_c:
    - (7, 2): 0.320, 6.3 cycles
    - (11, 2): 0.197, 10.1 cycles
    - (15, 2): 0.143, 14.0 cycles
    - (21, 2): 0.102, 19.6 cycles
    - (31, 2): 0.069, 29.1 cycles
    - N=3 gives the same cutoffs as N=2
- Battery precedents applying SG to capacity or other signals (heterogeneous and weak):
  - Garapati, Huld, Lee, Lamb 2026, *Machine Learning: Engineering* 2(1), doi:10.1088/3049-4761/ae5067 (https://iopscience.iop.org/article/10.1088/3049-4761/ae5067): SG on "capacity loss per cycle data" for MATR/SNL/Oxford/UL-PUR with "a window size of approximately half the total number of data points (N/2) and a polynomial order of 2". A fraction-of-length, very heavy smoother built for knee detection; not suitable for locating EOL.
  - Zhang, Altaf, Wik (arXiv:2304.11671): SG on normalized per-cycle capacity of the Severson/TRI data. The window is **not stated in the text** (local `kneeonset.txt` l.402-406).
  - Zhang 2025, PLOS One (doi:10.1371/journal.pone.0339528): "window size: 21, polynomial order: 2", but applied to *within-cycle* voltage, current and temperature sequences, not per-cycle capacity.
  - HyBattNet (arXiv:2505.16664v1): window length 191 on "voltage, current and capacity signals" of HUST. Within-cycle; polyorder not stated.
- Median-filter precedent on per-cycle capacity (a different filter with a fixed cycle window): BatteryML `preprocess_CALCE.py` l.88-90 uses `medfilt(Qd, 21)` and keeps cycles with |Q − medfilt| < 3·median|Q − medfilt|. BatteryLife "median filtering" on discharge-capacity trajectories, window not stated in the HTML.

My simulation (`src/run_rule_sim.py`): peak retained by SG (N=2) for a unit jump followed by geometric decay with ratio d.

| d | W=7 | W=11 | W=21 |
|---|---|---|---|
| 0.50 | 0.54 | 0.37 | 0.21 |
| 0.70 | 0.69 | 0.52 | 0.32 |
| 0.85 | 0.83 | 0.71 | 0.51 |

**Residual uncertainty.**
- **I found no published precedent for SG applied to per-cycle capacity with a fixed small window across NASA and MATR together.** W=11/N=2 is a reasoned declaration from the filter's frequency response, not a literature convention.
- Shortest NASA unit length is unverified; very short NASA cells would force a smaller W or exclusion.

---

## 3. Regeneration detection: threshold multiple, minimum run length, amplitude/duration statistics, robust scale

**Proposal.**
- Residual r_t = raw capacity − fitted trajectory. Fit with a robust loss, `scipy.optimize.least_squares(loss='soft_l1')`, or refit once with detected positions excluded.
- Scale s = 1.4826·MAD(r), per unit.
- A pattern is a run of ≥ **m = 2** consecutive same-sign residuals with |r| > **k = 2.5**·s.
- Declared sensitivity range: k ∈ {2.0, 2.5, 3.0} × m ∈ {2, 3}.
- Report the lag-1 autocorrelation of r with every count, because the false-run rate depends on it (table below).
- Amplitude = signed residual at the run extremum. Duration = run length. This matches Qin's "regeneration cycle number" only approximately; see below.

Null false-detection rate of this rule, from my Monte Carlo (`src/run_rule_sim.py`: Gaussian AR(1) with unit marginal variance, MAD-normal scale, 200 series × 1000 positions, seed 20260915). Values are false runs per 1000 positions, counting both signs.

| φ | k | m=1 | m=2 | m=3 |
|---|---|---|---|---|
| 0.0 | 2.0 | 45.83 | 1.08 | 0.03 |
| 0.0 | 2.5 | 12.97 | 0.10 | 0.01 |
| 0.0 | 3.0 | 2.92 | 0.00 | 0.00 |
| 0.3 | 2.0 | 41.28 | 3.92 | 0.46 |
| 0.3 | 2.5 | 11.88 | 0.40 | 0.03 |
| 0.3 | 3.0 | 2.60 | 0.07 | 0.00 |
| 0.6 | 2.0 | 34.87 | 7.97 | 2.12 |
| 0.6 | 2.5 | 10.48 | 1.64 | 0.43 |
| 0.6 | 3.0 | 2.40 | 0.28 | 0.03 |

With MATR-scale data (on the order of 10⁵ positions, from 124 cells × a mean of 806 cycles per Severson), k=2.0/m=2 at φ=0.3 would yield hundreds of false runs. k=2.5/m=2 yields tens. That is why the proposal is k=2.5, not 2.

**Precedent.**
- **Qin et al. 2016** (Energies 9:896, doi:10.3390/en9110896; PDF via mdpi-res.com, local `qin2016.pdf` pp.7-13):
  - NASA B0005-B0007, 168 cycles each. Training on cycles 1-100, testing on 101-168.
  - Detection is on the forward SOH difference DH_E(k) = H_E(k+1) − H_E(k) with threshold **Th = 0.2% SOH**, refined by SVM-HS on rest time (hyperplane shift p = −0.5).
  - Amplitude is the SOH increment into the regeneration cycle (Eq. 28).
  - "Regeneration cycle number" counts cycles c+j while H(c+j) − H(c) ≥ 0 (Algorithm 1).
  - Table 2 (predicted regeneration cycle numbers, test portion): No.5: 3,5,4,4,5; No.6: 4,5,4,5,5; No.7: 3,4,3,4,4 cycles. The text says the predicted regeneration cycles "are exactly the real regeneration cycles" (p.14).
  - Table 3 (predicted regeneration amplitude, % SOH relative to C_0): No.5: 1.07, 1.85, 1.23, 1.48, 1.77; No.6: 2.15, 3.73, 2.47, 2.98, 3.56; No.7: 0.87, 1.51, 1.00, 1.21, 1.44.
  - Table 1: cycles before regeneration 102, 119, 132, 149, 166, i.e. 5 events in 68 test cycles. Units of the listed DT' values are not stated in what I read.
  - Converting % SOH to Ah needs C_0 per cell, which is **not tabulated there**.
- **Olivares et al. 2013** (IEEE TIM 62(2):364-376, doi:10.1109/TIM.2012.2215142). Full text not accessible (repositorio.uchile.cl behind an Anubis challenge); abstract read via Semantic Scholar API. The model is described in Pola et al. 2016 (PHM Society Annual Conf.; PDF https://ridda2.utp.ac.pa/server/api/core/bitstreams/fbd80011-87e5-4250-940d-64ae73b5ecfd/content, local `utp_raw.txt` l.315-324, p.3 Eqs. 5-9):
  - Regeneration state x3(k+1) = δ(U)ω31 + δ(1−U)·x3·ω32 + δ(2−U)(x3 + ω31), with U ∈ {0,1,2} an on-line detection module
  - "ω31 is a log-normal noise used to characterize the typical amount of SOH that is added"
  - "ω32 is used to characterize the typical damping ratio of self-recharge phenomena and distributes as a uniform over a range"
  - "Both ω31(k) and ω32(k) were determined statistically in (Olivares et al., 2013) studying the accelerated degradation data provided by NASA Ames"
  - Numerical parameters: **UNVERIFIED (not reached)**.
  - This is precedent for the *shape* of a regeneration pattern: log-normal jump amplitude plus geometric decay, which DegradX's position/amplitude/duration could parameterise.
  - Pola 2016's outlier test uses p_fa = 1% and an offset "K_th (a 12% of the nominal capacity)" (l.445-448).
- **Pan et al. 2022** (Energies 15:2498, local `pan2022.txt`): CALCE CS2_33/34/35/36/38, EOL 76%, rest-time regeneration threshold t_G,th = 18 h. Random fluctuation is modelled as α-stable with sampling limits P{X > Z_α} = 0.975 and P{X < Z_β} = 0.025 (Eq. 14). No NASA amplitudes. See headline 4.
- **Ma et al. 2021** (Energy 234:121233, doi:10.1016/j.energy.2021.121233): publisher 403. Method is particle filter plus Mann-Whitney U test for capacity regeneration points (**UNVERIFIED, secondary**: ScienceDirect/ResearchGate listing via search). Significance level and window: **UNVERIFIED**.
- **Saha & Goebel 2009** regeneration term, as quoted by Deng, Hsu, Li 2017 (PHM Society, doi:10.36001/phmconf.2017.v9i1.2438, local `deng2017.txt` l.111): C_{k+1} = η_C C_k + β1 exp(−β2/Δt_k), with Δt_k the rest time.
- Robust scale and thresholds:
  - `scipy.stats.median_abs_deviation(scale='normal')` divides by Φ⁻¹(0.75) ≈ 0.67449, i.e. multiplies by ≈1.4826 (scipy 1.18.1 docstring).
  - Leys et al. 2013 (J. Exp. Soc. Psych., doi:10.1016/j.jesp.2013.03.013) recommend 2.5 (or 3) as the MAD cut-off with b=1.4826. **UNVERIFIED primary; secondary**: hausekeep docs https://hauselin.github.io/hausekeep/reference/outliersMAD.html state "Leys et al. recommend 2.5 or 3.0" and bConstant=1.4826.
  - Battery code precedent: BatteryML `preprocess_HNEI.py` l.146-150 `hampel_filter(num, ths=3)` (3 × raw MAD); `preprocess_CALCE.py` l.88-90 (3 × raw MAD around a 21-cycle median filter). 3 × raw MAD ≈ 2.02 σ for Gaussian noise (3 × 0.6745).
  - Pairing a σ-multiple with a run length: NIST/SEMATECH e-Handbook §6.3.2 WECO rules (https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm): "Any Point Above +3 Sigma", "2 Out of the Last 3 Points Above +2 Sigma", "4 Out of the Last 5 Points Above +1 Sigma", "8 Consecutive Points on This Side of Control Line".

**Residual uncertainty.**
- **No published amplitude distribution for NASA PCoE in Ah was verified.** Qin's are predicted values in % SOH for 3 cells, test portion only. Olivares' fitted distribution parameters were not accessible.
- Qin's duration (cycles until SOH falls back below the pre-regeneration value) is not the same as "run length above k·s" and will generally be longer. Report both definitions, or state that they differ.
- The false-run table assumes Gaussian AR(1). Real residuals may be heavier-tailed (Pan uses α-stable).
- k=2.5/m=2 is a declaration supported by the table and by WECO/Leys-style conventions. It is not a battery-specific convention; none exists for residual-run detection that I could find.

---

## 4. Candidate trajectory families: exact equations, bounds, initialisation

**Proposal (fit on y_k = q_k/q1, k = cycle index; rescale k by 1000 for conditioning).**
1. **Two-term exponential** (He 2011 form): y = a·e^{b k} + c·e^{d k}.
   - **No sign constraints on a, b, c, d.** Constraining a, c > 0 and b, d < 0 gives a convex curve that cannot bend downward (a knee).
   - Box bounds |a|, |c| ≤ 2; |b|, |d| ≤ 20 per 1000 cycles.
   - Multi-start: a+c = y_1 ≈ 1, initial (b, d) from a grid.
2. **Rollover (Saxena 2022)**, as capacity change from cycle 0: q(n) = m_o·n + (m_f − m_o)·δ·ln[(e^{n/δ} + e^{N_k/δ}) / (1 + e^{N_k/δ})], and y = y_0 + q(n)/q1.
   - Parameters (y_0, m_o, N_k, δ, m_f). Fit δ freely within declared bounds (e.g. [5, 500] cycles), not fixed at 50 as Saxena did, because the paper lists width as a parameter and varies transition sharpness.
   - Implement with `np.logaddexp` to avoid overflow.
   - Saxena's bounds in Ah per cycle (1.1 Ah cells): m_o ∈ (−1e-3, 0), N_k ∈ (0, 3000), m_f ∈ (−2e-2, 0). Divide by q1 when fitting y.
3. **Power law**: y = y_0 − a·k^b, with a > 0 and b ∈ (0, 5]. Monotone, one curvature direction, no inflection, so no transition.
   - Selection by K-fold cross-validated RMSE across units (paper l.236). Report parameter counts: 4 / 5 / 3 including the intercept.

**Precedent.**
- **Two-term exponential form.** Johnen et al. 2019 (arXiv:1907.12961, local `johnen2019.txt` l.144-179) list it as Eq. (1), f(x; β) = β1 e^{β2 x} + β3 e^{β4 x}, with β ∈ R⁴, i.e. no sign constraints. They state "He et al. [8] apply the double exponential model (1) to describe the capacity degradation".
  - Identifiability: "Wang et al. [15] consider the double exponential model as justified in [8], but observe that the parameters cannot be uniquely determined in a nonlinear least squares regression. Therefore, they replace one of the exponential terms by a power function with proposed exponent 2 or 4". [15] is Wang, Miao, Pecht 2013, J. Power Sources 239:253-264, doi:10.1016/j.jpowsour.2013.03.129; title verified via Crossref.
  - Karma (arXiv:2510.02839v1) uses C(k) = a·exp(b·k) + c·exp(d·k) with "a,c>0, b,d<0, and a+c≈y₀", attributed to Zhang et al. 2023, not He.
  - **He et al. 2011's own fitted parameters, initial values, and data set: UNVERIFIED.** Publisher paywalled; Crossref and Semantic Scholar have no abstract. Metadata verified via Crossref: J. Power Sources 196(23):10314-10321.
- **Rollover.** Saxena et al. 2022, accepted manuscript (OSTI 1910034, local `saxena2022.txt` l.289-404), verbatim structure:
  - Eq. (1) γ = 1/(1 + e^{−(n−N_k)/δ})
  - Eq. (2) dq/dn = m_o + (m_f − m_o)·γ
  - Eq. (4) C = −(m_f − m_o)·δ·ln(1 + e^{N_k/δ}) from q(0) = 0
  - Eq. (5) as written above
  - The four parameters are "initial slope (mo), rollover cycle (Nk), rollover width (δ), and failure slope (mf)"
  - Fitted by "differential evolution … with MAE as the objective function", evaluated "at every 10 cycles"
  - "we kept the value of the rollover width, δ, constant as 50"
  - Bounds "(-1e-3, 0), (0, 3000), and (-2e-2, 0) for parameters mo, Nk, mf"
  - Across 108 training cells the parameters "closely match the Cauchy, Rayleigh, and lognormal distributions" (KS test at 0.05). This is a published precedent for parametric forms of the θ distribution, if the empirical distribution is to be smoothed.
- **Power law.** Wang et al. 2011, "Cycle-life model for graphite-LiFePO4 cells", J. Power Sources 196(8):3942-3948, doi:10.1016/j.jpowsour.2010.11.134 (metadata verified via Crossref). Q_loss = B·exp(−E_a/RT)·(Ah)^z with z = 0.55: **UNVERIFIED (secondary search snippet; PDF download timed out)**.
- Other forms Johnen lists: polynomial β1x² + β2x + β3 (Eq. 2); mixture β1e^{β2x} + β3x² + β4 (Eq. 3); a sigmoidal linear-plus-logistic model (Eq. 4) with five positive parameters. The sigmoidal one is another knee-capable candidate.
- Robust fitting API: `scipy.optimize.least_squares(..., loss='linear'|'soft_l1'|'huber'|'cauchy'|'arctan', f_scale=1.0, method='trf', x_scale=None)` (scipy 1.18.1 signature and docstring). 'lm' supports only linear loss.

**Residual uncertainty.**
- The two-term exponential is poorly identifiable (Wang 2013 via Johnen). Its per-unit parameters will have unstable joint distributions, which matters because θ is resampled. Consider reporting fit error only and preferring a reparameterisation.
- A free δ may trade off against N_k; Saxena fixed δ for exactly this alignment reason ("A constant δ helped in better aligning the rollover cycle", l.396).
- None of the bounds above for NASA's 2 Ah cells come from a publication. Saxena's bounds are for MATR-type 1.1 Ah cells.

---

## 5. Window length L, recency decay, and fidelity-metric window lengths

**Proposal.**
- **L = 24 positions (cycles)** for the models, the decomposable target, the discriminator and Context-FID. Sensitivity L ∈ {16, 48}.
- 24 matches the TimeGAN/Diffusion-TS evaluation convention, sits in the range of cycle-level NASA RUL windows (8-16 in Chen 2022, 10 in Zhang 2025), and fits in the shortest units (MATR ≥ 150, NASA B0005-7 = 168). The number of windows per NASA unit after truncation at T is not verified.
- **Recency weights** a_u ∝ 2^{−(t−u)/h} with half-life **h = L/4 = 6**. This equals exponential-smoothing α = 1 − 2^{−1/6} ≈ 0.109; first-to-last weight ratio 2^{−23/6} ≈ 0.070 (computed). Sensitivity h ∈ {L/8, L/2}, i.e. α ≈ 0.206 and 0.056.
- Declare h as a fraction of L, the same for all profiles (headline 7).

**Precedent.**
- TimeGAN (Yoon et al. 2019), official code https://github.com/jsyoon0823/TimeGAN @8f6181cb:
  - `main_timegan.py` CLI defaults: `--seq_len 24`, `--metric_iteration 10`
  - `metrics/discriminative_metrics.py` l.51-53, 126-127: post-hoc GRU with hidden_dim = dim/2, 2000 iterations, batch 128, score = |0.5 − accuracy|
  - `utils.py` l.28: `train_rate = 0.8`
  - `data_loading.py` l.105-112: overlapping windows shuffled "to make it similar to i.i.d", i.e. a window-level split. DegradX must replace this with a unit-level split (paper l.247).
  - Minor bug: l.46 computes `generated_time` from `ori_data`.
- Diffusion-TS (ICLR 2024; code https://github.com/Y-debug-sys/Diffusion-TS @566307e6):
  - Every `Config/*.yaml` has `window: 24`
  - `Utils/context_fid.py`: TS2Vec with output_dims=320, trained on the real data, `encoding_window='full_series'`, then the FID formula
  - `Experiments/metric_pytorch.ipynb`: `iterations = 5`
  - `Utils/metric_utils.py` l.11-16: mean ± t_{0.975, df=4}·SEM
  - `Utils/cross_correlation.py`: correlational score = Σ|lag-0 cross-correlation(fake) − (real)| / 10 over the lower-triangular channel pairs. A ready precedent for "agreement of cross-channel covariance structure".
  - Paper (arXiv:2403.01742 HTML): 24-length main results; longer lengths 64, 128, 256 on ETTh/Energy; "running each method 5 times".
- PSA-GAN (Jeha et al., ICLR 2022; arXiv:2108.00981, local `psagan.txt` l.276-284, 326-344):
  - Context-FID uses "the time series embeddings from Franceschi et al. (2019)", i.e. **not TS2Vec** (TS2Vec is Diffusion-TS's re-implementation)
  - "we train the embedding network for each dataset separately"
  - Lengths 64, 128, 256; "We score 5120 randomly selected windows and report the mean and standard deviation"
- NASA/CALCE cycle-level RUL windows: Chen, Hong, Zhou 2022, IEEE Access 10:19621 (code https://github.com/XiuzeZhou/RUL @26f12968):
  - `Transformer - NASA.ipynb`: `feature_size = 16`, passed as `window_size`, `Rated_Capacity = 2.0`, threshold `Rated_Capacity*0.7`, `for seed in range(5)`
  - `Transformer - CALCE.ipynb`: `feature_size = 64`, `Rated_Capacity = 1.1`
  - Zhang 2025 PLOS One: "a window of 10 consecutive 128-dimensional feature vectors"
  - Karma arXiv:2510.02839: prediction start point SP=60 for NASA
- MATR: BatteryML uses cycles up to index 98-99 as model input (`configs/baselines/sklearn/pcr/matr_2.yaml`: `max_cycle_index: 98`, `cycles_to_keep: 98`; `voltage_capacity_matrix.py` default `max_cycle_index=99`). An early-life, not rolling, window.
- Recency weighting: Hyndman & Athanasopoulos, FPP3 §8.1 (https://otexts.com/fpp3/ses.html): SES weights α(1−α)^j, with the table for α ∈ {0.2, 0.4, 0.6, 0.8} (e.g. α=0.2: 0.2000, 0.1600, 0.1280, 0.1024, 0.0819, 0.0655). Half-life conversions computed: α=0.1 → 6.58 positions; α=0.2 → 3.11.

**Residual uncertainty.**
- **I found no precedent for recency-weighted *ground truth* in time-series XAI benchmarks**; the exponential-smoothing analogy is the closest.
- φ\* = a·m means rank agreement against φ\* depends on m's sign and scale within a window. Standardised channels crossing zero would scramble the ordering. Define m in an offset-free physical space, or rank on a only (headline 2).
- L=24 against actual NASA lengths to EOL needs the data.

---

## 6. Bootstrap intervals and seeds

**Proposal.**
- **Unit-level (cluster) bootstrap.** For the TSTR ratio, resample held-out units *paired* (both models on the same resampled units) and compute ratio = mean err_profile / mean err_measured per resample.
- **B = 10,000**; scipy default n_resamples = 9999 is acceptable.
- **BCa**, which is scipy's default, and report the percentile interval alongside. When held-out units are few (NASA), report the unit count and treat intervals as descriptive. The small-n cut-off is a team declaration; I found no precedent value.
- Seeds: **5** per factor (generation, model init, attribution sampling), crossed only where the factor is stochastic.
  - IG and occlusion are deterministic given the model.
  - Only TimeSHAP's KernelSHAP coalition sampling (`rs`) needs attribution seeds.

**Precedent.**
- DiCiccio & Efron 1996, Statistical Science 11(3):189-228 (JSTOR scan, local `diciccio_efron1996.pdf` p.192): "Two thousand bootstrap replications is 10 times too many for estimating a standard error, but not too many for the more delicate task of setting confidence intervals"; B = 2,000 in their BCa example.
- `scipy.stats.bootstrap` (scipy 1.18.1 signature): `n_resamples=9999`, `paired=False`, `confidence_level=0.95`, `method='BCa'`, choices {'percentile','basic','bca'}; references Efron & Tibshirani 1993.
- Cluster bootstrap: Field & Welsh 2007, JRSS-B 69(3):369-390, doi:10.1111/j.1467-9868.2007.00593.x. Title and venue verified via search result; content **not read**.
- Seeds and runs in the benchmarks read:
  - TimeX: `range(1,6)` splits across experiment scripts (e.g. `experiments/seqcomb_mv/train_lstm.py`)
  - time_interpret: `experiments/hmm/main.sh` `for fold in $(seq 0 4)`, `seed=42`
  - Diffusion-TS: 5 iterations
  - PSA-GAN: "ten runs" / "three runs" in downstream experiments (l.453, 648)
  - Dynamask: `--CV` runs, user-set (README l.114-125)
  - BatteryML NN baselines: `for seed in 0 … 9`; README: "error mean across ten seeds"
  - Chen 2022: `range(5)`
  - TimeGAN: `metric_iteration` 10

**Residual uncertainty.**
- BCa with very few clusters (NASA) is unreliable, and neither source gives a minimum.
- A ratio of means with a near-zero denominator is unstable; a log-ratio interval is an option (declaration, no precedent checked).

---

## 7. Retrieval metrics (sparse set) and rank agreement (graded field)

**Proposal.**
- **Sparse set.** Report **AUPRC** (sklearn `average_precision_score`) as primary, plus **AUP** and **AUR** as defined in TimeX code.
- Per window: min-max normalize |attribution| over (L×C). Take the absolute value first, because negative patterns carry negative φ\*. Ground-truth label = 1 at cells with a nonzero pattern term.
- Average over windows (TimeX convention), not pooled (Dynamask/tint convention). Declare it.
- **Graded field.** Spearman ρ per window between |attribution| and |φ\*| over cells with a_{u,c} ≠ 0 (OpenXAI RC and Adebayo "absolute value" variant). Secondary: Kendall τ-b (`scipy.stats.kendalltau` default variant 'b'). Also report the signed ("diverging") variant.

**Precedent (exact code).**
- **TimeX** (Queen et al., NeurIPS 2023; https://github.com/mims-harvard/TimeX @58ad882e), `txai/utils/evaluation.py`:
  - `normalize_exp` (l.111-115) min-max normalizes per sample
  - `ground_truth_xai_eval` (l.121-163): `gt_exps.astype(int)`; per sample `auprc = average_precision_score(gt, gen)`; `prec, rec, thres = precision_recall_curve(gt, gen)`; `aur = auc(thres, rec[:-1])`; `aup = auc(thres, prec[:-1])`; lists returned per sample
  - No absolute value is taken.
- **Dynamask** (Crabbé & van der Schaar, ICML 2021; https://github.com/JonathanCrabbe/Dynamask @637d8456), `experiments/results/rare_time/get_results.py` l.20-22:
  - `precision_recall_curve(true_saliency.flatten(), pred_saliency.flatten())` pooled over all instances
  - `AUP = auc(thres, prec[1:])`, `AUR = auc(thres, rec[1:])`
  - sklearn ≥ 1.x returns precision/recall "such that element i is the precision of predictions with score >= thresholds[i] and the last element is 1" (sklearn 1.9.1 docstring). So Dynamask's `[1:]` slice is offset by one relative to TimeX/tint's `[:-1]`.
  - Information and entropy metrics follow at l.24-28.
- **time_interpret / tint** (Enguehard 2023; https://github.com/josephenguehard/time_interpret @ebef7361), `tint/metrics/white_box/`:
  - `aup.py`: `auc(pre_rec[2], pre_rec[0][:-1])`
  - `aur.py`: `auc(pre_rec[2], pre_rec[1][:-1])`
  - `auprc.py`: `average_precision_score`
  - `base.py`: per-sample min-max normalization (EPS=1e-5), then *flatten across the batch*, `hard_labels=True` → `true_attr.int()`
  - Also has `roc_auc.py`, `entropy.py`, `information.py`, `mae.py`, `mse.py`, `rmse.py`. This is the packaged implementation.
- **OpenXAI** (Agarwal et al., NeurIPS 2022 D&B; https://github.com/AI4LIFE-GROUP/OpenXAI @a1828862), `openxai/metrics.py`:
  - `rankcorr` (l.44-60): Pearson on `rankdata(-abs(x), method='dense')` per instance, averaged, i.e. Spearman with dense ties
  - `pairwise_comp` (PRA, l.16-41): fraction of feature pairs with the same relative order
  - Top-k FA/RA/SA/SRA in `eval_ground_truth_faithfulness`
  - Ground truth there is the linear model's coefficient vector, the closest analogue to DegradX's reference model.
- **Adebayo et al. 2018** (arXiv:1810.03292, local `adebayo.txt` l.210-212): "Spearman rank correlation with absolute value (absolute value), Spearman rank correlation without absolute value (diverging), the structural similarity index (SSIM), and the Pearson correlation of the histogram of gradients".

**Residual uncertainty.**
- AUP and AUR integrate over the *threshold* axis, so they depend on the score distribution after min-max normalization; AUPRC does not.
- Pooled vs per-sample averaging changes values. The three packages differ (TimeX per sample; Dynamask pooled, raw; tint per-sample normalized then pooled).
- I did not verify the Dynamask or TimeX paper *text* definitions; the downloaded Dynamask PDF had no extractable text. The code is the evidence.

---

## 8. TimeSHAP background instance and "default configuration"

**Proposal.**
- Background = **average event over training-split windows of the same profile**, computed with `timeshap.utils.calc_avg_event` (per-feature median), tiled across the window. This is the TimeSHAP default usage.
- **Also** run a zero background in the same space as φ\*'s reference, and score each attribution against the φ\* that matches its baseline (headline 2).
- Settings: `nsamples = 32000` (package default), `rs` ∈ 5 seeds, **pruning disabled**.
- Cell level with `top_x_events = L`, `top_x_feats = C`, so every (u,c) is its own player: 96 players at L=24, C=4. This is a documented non-default and must be reported as such.

**Precedent.**
- Bento et al. 2021, KDD (arXiv:2012.00073, local `ts_raw.txt`):
  - l.172-174: "b ∈ X^m represents an uninformative input sample, which is often taken to be the zero vector [26], b = 0, or to be composed of the average feature values in the input dataset [10]"
  - l.299-300: "we define the background matrix B ∈ R^{l×d} as containing the average feature values in the training dataset" (Eq. 5, same average event at every position)
  - l.695: "This null contribution might stem from our choice of a background/uninformative event"
  - Pruning tolerance η = 0.025 used, with η ∈ {0.005, 0.0075, 0.01, 0.025, 0.05} studied (layout text l.300, 317, 376)
- timeshap 1.0.4 wheel (PyPI) and repo https://github.com/feedzai/timeshap @218f2ba3:
  - `explainer/kernel/timeshap_kernel.py` l.78-88 docstring: "In TimeSHAP you can use an average event or average sequence … consider using `timeshap.calc_avg_event` … Note that when using the average sequence, all sequences of the dataset need to be the same length"
  - `utils/utils.py` l.317-326: `calc_avg_event` "Calculates the median of numerical features, and the mode for categorical"
  - `explainer/event_level.py` l.170-182 and `feature_level.py` l.174-185: defaults `rs=42`, `nsamples=32000`
  - `explainer/cell_level.py` `cell_level`: needs `threshold`, `top_x` or `top_x_events`+`top_x_feats`, else `ValueError`; unselected cells returned as "Other Events", "Other Features", "Pruned Events"
  - AReM tutorial notebook: `pruning_dict = {'tol': 0.025}`, `event_dict = {'rs': 42, 'nsamples': 32000}`, `cell_dict = {'rs': 42, 'nsamples': 32000, 'top_x_events': 3, 'top_x_feats': 3}`, `average_event = calc_avg_event(d_train_normalized, …)`
- Captum 0.9.0 (PyPI wheel), `attr/_core/integrated_gradients.py` l.84-85, 163-164: `n_steps=50`, `method="gausslegendre"`, "In the cases when `baselines` is not provided, we internally use zero scalar"
  - `occlusion.py` l.130-131 and `feature_ablation.py` l.338-339: same zero default
  - `Occlusion.attribute` requires `sliding_window_shapes` with no default (l.51-58), so "default configuration" for occlusion also needs a declared window, e.g. (1, 1) per cell.

**Residual uncertainty.**
- A single average or median event under mean-nonstationarity is a mid-life state. TimeSHAP's own paper notes the background choice can zero out contributions.
- No publication gives TimeSHAP background guidance for trending sequences; I found none.
- KernelSHAP with 96 players at 32,000 samples is not guaranteed to converge. Check seed variance.

---

## Source inventory (commit hashes and local files)

- BatteryML clone (read-only, given): 2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd
- `src/jsyoon0823_TimeGAN` 8f6181cb9b9d2fa0c930cd902411d9ac8a308e07
- `src/Y-debug-sys_Diffusion-TS` 566307e6cf2d8095e58de4c6e3a6ae965b69b5b5
- `src/JonathanCrabbe_Dynamask` 637d84568a3a3af56fbfd343bd9ecd474fe6f633
- `src/mims-harvard_TimeX` 58ad882e153ddca3440d2bb86e122cad3ad04e80
- `src/time_interpret` ebef73615dda67e4c9bd42d3bac81cce6607280f
- `src/feedzai_timeshap` 218f2ba385cb72f73ad245d249996f8566e65360; `src/pkgs/timeshap-1.0.4-py3-none-any.whl`
- `src/OpenXAI` a18288620464250856b55234266a6d1dabb64656
- `src/XiuzeZhou_RUL` 26f12968ffece1e14873273841889982af8135d5
- `src/pkgs/captum-0.9.0-py3-none-any.whl`
- venv `src/venv`: scipy 1.18.1, scikit-learn 1.9.1
- Scripts I ran: `src/sg_cutoff.py`, `src/run_rule_sim.py`
- Papers and extracts in `domain/`: severson2019, saxena2022, qin2016, pan2022, schafer2011, kneeonset_2304.11671, johnen2019, psagan, timeshap2021, adebayo2018, diciccio_efron1996, utp_pf (Pola 2016), deng2017, iastate_rul, phm_ijphm2703

Not reachable (403 / paywall / challenge): He et al. 2011 full text; Ma et al. 2021 full text; Olivares et al. 2013 full text; Ma et al. 2022 (HUST) full text; Wang et al. 2011 PDF; Leys et al. 2013 full text; Field & Welsh 2007 full text.
