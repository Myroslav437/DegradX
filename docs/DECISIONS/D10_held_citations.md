# D10 — Held citations: pan2022 verified and re-described; the temperature-input claim attributed to olivares2013 removed

**Stage / claim affected:** §3.1.2 (inserted patterns) and §3.3 (the two detection families).

**Decision.** Two citations were held at S0. What does each source support, and what does the paper say?

**Options considered**
- **pan2022**
  - **a.** Keep the sentence as written (the source cited for residual decomposition that assigns uncorrelated components to regeneration).
  - **b.** If the full text is available, describe what it does. Otherwise distinguish the detection families by trigger and note the overlap.
- **olivares2013 ("ambient temperature … entering prognostic models as an explicit input")**
  - **c.** Keep.
  - **d.** Substitute a different reference. Excluded by the brief: never substitute a guessed reference.
  - **e.** Drop the claim, keep the citation where the verified abstract supports it.

**Evidence**
- **pan2022, full text** (S0 download: Energies 15:2498; abstract l.14–27, method l.500–520, flow chart l.655–675).
  - It splits "the health state degradation curve … into the normal degradation trend part, capacity regeneration part, and random fluctuation part".
  - It decomposes by EMD to obtain the trend.
  - It predicts regeneration with GPR on SOH, initial SOC and rest time, applied when "the rest time exceeds the capacity regeneration time threshold".
  - Data: CALCE.
  - The three-part split cited in §3.1.2 is confirmed. The paper's §3.3 description ("assigning the components uncorrelated with the trend to regeneration") is not what the method does: regeneration is triggered by rest time.
- **olivares2013.**
  - Only the abstract is accessible (IEEE TIM 62:364; the full text sits behind an anti-bot challenge, S0 datasets.md §3.5). It confirms particle-filter prognosis "while simultaneously detecting and isolating the effect of self-recharge phenomena".
  - Nothing accessible supports ambient temperature as an explicit model input. S0 notes the claim may originate in a different source (Pola 2016), but that source is not verified either.

**Chosen: b and e.**
1. *Logical:* cite a source only for what it is seen to contain.
2. *Consistent:* the §3.3 argument for adopting residual-based detection (rest time is recoverable in some datasets and not others; the same rule must apply to every profile) is unaffected.
3. *Clear:* the two families are now named by trigger, with one sentence on the overlap.

**Cost.**
- §3.1.2 loses its model-input evidence for temperature and keeps only the dataset-level evidence (Severson 2019's chamber-temperature excursions).
- A reviewer who knows a source for temperature as an input may ask for it, and it can be added once verified.
- `ma2021` (§3.3) was checked at S0 only through secondary listings (particle filter plus Mann-Whitney U test for regeneration points). It is not held by the brief, but it is listed in the final report as secondarily verified.

**Paper impact:** §3.3 detection-families sentences and §3.1.2 negative-fluctuation sentence (round-5 amendment); `.bib` TODO comments on both entries.
