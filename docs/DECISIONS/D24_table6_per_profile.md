# D24 — Table 6 reports reference values per profile, not averaged over profiles

**Stage / claim affected:** S9 (Table 6), §4.4; how later work quotes the reference values.

**Decision.** The declared Table 6 caption reports each method "averaged over profiles that pass the usability checks". All three profiles pass the accuracy gate, so the average would run over all three. Does averaging preserve what the measurement says?

**Options considered**
- **a. No change:** one row per method, averaged over the three profiles.
- **b. Per profile:** one block per profile, with the exact attribution of the reference model, the ensemble range (C2) and the average-event background as rows.
- **c. Averaged in Table 6, per profile in an appendix table.**

**Evidence** (`experiments/decisions/D24/{run.py,result.json}`), rank agreement on the trained model, all three weightings:

| weighting | averaged order | MATR | HUST | NASA PCoE |
|---|---|---|---|---|
| recency | IG > TimeSHAP > occlusion | IG > TimeSHAP > occlusion | **TimeSHAP > IG > occlusion** | IG > TimeSHAP > occlusion |
| uniform | IG > occlusion > TimeSHAP | IG > occlusion > TimeSHAP | **IG > TimeSHAP > occlusion** | **occlusion > IG > TimeSHAP** |
| final position | TimeSHAP > occlusion > IG | **occlusion > IG > TimeSHAP** | **TimeSHAP > IG > occlusion** | TimeSHAP > occlusion > IG |

The averaged ordering reproduces the profile's own ordering in 4 of the 9 profile × weighting combinations.

Two further properties are per profile, not per average:
- The ensemble range that bounds what a method difference can mean (C2) is 0.111 in MATR, 0.332 in HUST and 0.094 in NASA PCoE for Integrated Gradients under recency weighting, against largest between-method differences of 0.089, 0.035 and 0.034. An averaged range has no such reading, since it is not the spread of any set of models.
- Retrieval exists only in NASA PCoE (D05), so an "average over profiles" in that column is one profile's value presented as an average.

Real: yes, all from the S8 artifacts. Works: (b) and (c) both keep the per-profile values; (a) loses them.

Clear, option (b): "Table 6 reports each method per profile, with the exact attribution of the reference model as the ceiling and the ensemble range beside it."

**Chosen: b.**
1. *Logical:* the three profiles are three different measurements (different fitted dynamics, different channels, one of them with inserted patterns); their mean is not a measurement of anything.
2. *Consistent:* Tables 1–3 are already per profile, and §3.6's "reported in aggregate" concerns positions within a trajectory, which stays aggregated.
3. *Clear:* the reader sees the ceiling, the methods and the ensemble range in the same block.
4. *Measured:* averaging preserves the profile's own ordering of the methods in 4 of 9 combinations.

**Cost.**
- Table 6 is three times longer (18 rows) and set in \scriptsize; it occupies most of a page.
- No aggregate number is given, so later work must quote reference values per profile. This is intended: the profiles measure different things.
- (c) was not chosen only because the paper has no appendix; if one is added, the averaged row could return there at no cost to the argument.

**Paper impact:** Table 6's caption is rewritten in `\rev` and its body is generated per profile; §4.4 reports per profile. Recorded in `docs/AMENDMENTS.md` (round 6).
