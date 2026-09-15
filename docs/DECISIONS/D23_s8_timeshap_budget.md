# D23 — S8 compute budget: TimeSHAP explains 40 of the 120 scored windows per profile, with sampling seeds 0–1 on trained models and seed 0 on the reference model

**Stage / claim affected:** S8 (Table 6 TimeSHAP rows); the interval width of TimeSHAP reference values.

**Decision.** At the declared settings (120 windows × 2 models × 3 weightings × 3 attribution seeds, doubled on NASA for paired maps), TimeSHAP needs about 8 640 window explanations. At the measured 5–7 s per window (D22) that is 12–17 GPU-hours for TimeSHAP alone. The plan was about 4 hours for the whole stage, so it exceeds twice the planned compute. Which declared lever reduces it (brief v2 §6)?

**Options considered**
- **a. No change** (about 14 h).
- **b. Fewer TimeSHAP windows:** a stratified random 40 of the 120 scored windows (same windows for every model, weighting and seed).
- **c. Fewer TimeSHAP sampling seeds:** seeds 0–1 on trained models; seed 0 on the reference model, where seed-to-seed differences are 3e-7 (D22).
- **d. Reduced coalition budget** (nsamples 32 000 → 8 000). Not chosen: it changes the method's default configuration, which §3.6 fixes.

**Evidence**
- D22: TimeSHAP costs 5.3–6.6 s per NASA window. Seed spread on the reference model is 3.0e-7 against a field scale of 0.115, and 2.4e-3 on the trained model.
- Projected counts:
  - (a) 8 640 explanations ≈ 14 h.
  - (b) + (c): trained 40 × 3 weightings × 2 seeds, plus reference 40 × 3 × 1, plus the recency secondary background 40. This is doubled on NASA. Total = 1 400 explanations ≈ 2.3 h.
- IG and occlusion stay at all 120 windows, with every model including the ten ensemble members.

Real: yes. Works: (b)+(c) fits the budget. The intervals over units widen by about √3 for TimeSHAP rows, and the convergence readout keeps two seeds on trained models, where sampling variance is non-negligible.

Clear: "TimeSHAP, the only sampling-based and most expensive method, is scored on a stratified third of the windows, with two sampling seeds on trained models and one on the reference model, where it is exact."

**Chosen: b + c.**
1. *Logical:* only replicates are reduced. Profiles, weightings, ground-truth checks, the method configuration and the separation of generation, model-initialisation and attribution-sampling seeds are unchanged.
2. *Consistent:* the brief lists "fewer explained windows under stratified sampling" and "fewer seeds above the declared minimum" as the levers.
3. *Clear.*
4. *Measured:* 2.3 h instead of 14 h.

**Cost.**
- TimeSHAP's reference values rest on 40 windows per profile instead of 120, and their unit-bootstrap intervals are wider than IG's and occlusion's. The TimeSHAP row is therefore not directly comparable in precision.
- The identifiability floor for TimeSHAP is not measured (IG and occlusion only).
- A reviewer may note that TimeSHAP's seed-0 values on the reference model are unreplicated; D22 shows why that is harmless there.

**Paper impact:** none; Table 6's note states the window counts per method.
