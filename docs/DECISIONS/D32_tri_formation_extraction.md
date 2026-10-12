# D32 — Third profile from the TRI/Stanford formation dataset: documented cells only, regular aging cycles as positions, CC-CV charge time from the per-cycle charge samples, and an offset pre-screen on fitted mean components — declared before download

**Stage / claim affected:**
- W0 (brief "DegradX v2.1");
- declarations r4 `declared_by_design.v2_1` (all keys), the 2026-10-11 entries of `meta.supersession_log`,
  `configs/profiles/tri_formation.yaml`;
- the third column of every v2.1 table; §3.4 Profiles; the Notes box of the review build.

**Timing.** Taken 2026-10-11 from documentation only, **before any byte of either archive was downloaded** (HTTP HEAD
requests returned the archive sizes, dates and ETags). The documentation consulted:
- Cui et al., Joule 8(11):3072-3087 (2024), main text and SI (Elsevier CDN mmc1/mmc2);
- Rhyu et al., arXiv:2410.07458 v1 and its SI, and the published version (Joule 9:101884, 2025, SI only);
- the data page https://data.matr.io/8/ (and its Wayback captures);
- the authors' code: github.com/cx26/formation-analysis @ 2bc2313 (parameter sheet, loader, cycle-life code) and
  cx26/degradation-mode @ 2bba77a; Rhyu's repository @ 9530854;
- BEEP (github.com/TRI-AMDD/beep) at v2022.10.3.16 and main @ f2b984e, with the history in between;
- BatteryLife (arXiv:2502.18807 and its code and processed copies) as a non-binding third-party cross-check.

**Process.** Four documentation readers, a synthesis of 72 claims, and two adversarial verifiers per topic group
(source fidelity; contradiction search). The verified sheet is kept at
`artifacts/v2.1/w0_declarations/documentation_research.md`. This record was then reviewed by three lenses and a judge
before commit (§ Review), and every ruling was applied.

**Decision.** The authors chose the dataset (brief v2.1 §0, decision 2) and fixed most rules (brief §2, W0). What the
documentation leaves open, and this record settles before data:
1. the nominal capacity and its source;
2. which aging files form the cell universe;
3. what a position is, and on which cycle axis T is counted;
4. how charge time is defined, from which source, and how it is validated against BEEP's `charge_duration`;
5. which cycles are rest events, and where charge time is masked;
6. how the authors' EOL definition is reported;
7. how the offset pre-screen is estimated and read;
8. how the two archive versions are handled;
9. the aging-protocol tolerance, and what counts as a second protocol.

## Facts (documentation, verified)

- **Cell.** Single-crystal NMC532 / artificial-graphite pouch cells. They were bought dry and sealed from Li-FUN and filled
  by the authors. Every cell is of this one build (Cui p.3073, p.3082, Table 1).
- **Nominal capacity.** Cui p.3082: "The cells are nominally 240 mAh (in this paper, 1C is defined as 0.24 A) when cycled
  between 3 and 4.4 V". SI Fig. S2 repeats 1C = 0.24 A. Rhyu et al. state no nominal capacity.
- **Aging.** CC 1C to 4.4 V, CV to C/20; CC 3C/4 to 3.0 V with no hold; 30 °C; identical for all cells (Cui p.3074,
  p.3083, Table S4). The parameter sheet's `regular_*` columns are identical in every row.
- **Diagnostics.** HPPC, an RPT at C/20 and an RPT at C/5, in the Table S4 sequence. The documented and inferred layout
  is HPPC 0, 8, 24, 127 + 103k; C/20 RPT 1, 25, 128 + 103k; C/5 RPT 2, 26, 129 + 103k. BEEP's `cycle_index` counts the
  diagnostic cycles: the authors' "after 120 aging cycles" is `cycle_index` 127.
- **EOL.** The paper says "80 % of its initial value" and does not define "initial". The authors' code uses 80 % of the
  cell's maximum regular-cycle capacity and takes the last `cycle_index` at or above it.
- **Cells.** 186 were designed (62 protocols × 3). The parameter sheet has 183 rows: 180 design rows plus the baseline
  protocol, seq 324-326. Failed cells were not shared (SI S1.1). Rhyu et al. used 178.
- **Third-party evidence.** BatteryLife reports 41 processed cells from the 2024 archive and 181 from both releases.
  It also reports `Nova_Regular_Ref_100/101/102` files, whose identity no source documents.
- **Mapping.** The cell → formation-protocol mapping is the authors' `data/Formation_2022-Parameter.csv`
  (cx26/formation-analysis @ 2bc2313, sha256 3a9696ec…), keyed by seq. That repository has no licence file.
- **BEEP semantics** (verified in source):
  - `summary.discharge_capacity` is the maximum of the cycle-cumulative discharge capacity.
  - `summary.charge_duration` runs from the cycle's first record to the first record with charged capacity
    ≥ `nominal_capacity × full_fast_charge`. It is therefore not the CC-CV duration, and it is NaN once a cycle no
    longer charges that much.
  - `charge_duration` is assigned positionally: the value at label l belongs to raw cycle S[l] of the sorted
    `cycle_index` values of summary ∪ diagnostic_summary (G5.6). It is right only for a `cycle_index` contiguous from 0.
  - Without a diagnostic config, or with v2022's positional labels, diagnostic cycles can sit in `summary` as ordinary
    rows (G5.9, G5.13).
  - `paused` is the largest inter-record gap within a cycle when that gap exceeds 3 600 s.
  - `date_time_iso` is the cycle's first timestamp, read as US/Pacific and converted to UTC. The repeated fall-back hour
    is mapped as PDT (G5.10).
  - `cycles_interpolated` puts charge on a capacity axis over the file-wide range, with 1 000 points by default.
  - Post-2023 BEEP labels rest steps "charge". Upper tails are NaN before 2025-02-13 and clamped after.
  - Which BEEP version wrote the files is not documented.
- **Archives.** What changed between `data.tar.gz` (2024-07-31) and `data_03032025.tgz` (2025-03-03) is documented
  nowhere. Raw (non-interpolated) aging records are not stated to be included. Licence: CC BY-NC 4.0 (page footer).

## Options and choices

### 1. Nominal capacity

- (a) 0.24 Ah from Cui et al.'s text. (b) BEEP's `structuring_parameters.nominal_capacity`. (c) A measured initial capacity.
- The brief: "If the primary documentation states it, use that value." It does: "nominally 240 mAh … 1C is defined as 0.24 A".
- (b) is a structuring argument whose only effect is the `charge_duration` threshold, and it is undocumented per file.
  (c) is not documentation (C3).
- **Chosen: (a).** No D-record of the BEEP value is needed. The per-file value is read at W1 and any value other than 0.24
  is reported.

### 2. Cell universe

- **(a) Literal brief.** Every aging file whose regular cycles follow the modal protocol.
- **(b) (a) restricted to files whose seq has a row in the authors' parameter sheet.** The baseline seq 324-326 is
  included.
- **(c) (b) restricted further:**
  - to the 62 designed protocols (baseline excluded), or
  - excluding cells flagged in the lab notes ("shorted" 274/276/278 and others).
- Real: all three. Works:
  - (a) admits files of undocumented identity. The `Ref_100-102` names reported by a third party collide with seq
    100-102, and nothing says they are the same cell build. E1 (one cell type) cannot be verified for them.
  - (b) keeps every cell the authors document.
  - (c) excludes on grounds the brief does not give:
    - The baseline cells have the same build and the same aging. Their formation differs, which is the manufacturing
      variation the profile is meant to carry.
    - The lab notes are unattributed. The SI says failed cells were not shared, yet the flagged cells are in both sheets
      and in Rhyu's 178.
- Clear, in one sentence for (b): "A cell enters the profile if the authors document it and its aging cycles follow the
  common protocol."
- **Chosen: (b).**
  - A seq is read only from base names matching `^Nova_Regular_(\d{3})(\.\d+)?\.json(\.gz)?$`; any other name (e.g.
    `Nova_Regular_Ref_100.034.json.gz`) is an undocumented file: excluded, counted and listed, never merged with any seq.
  - A file must carry at least 10 finite charge and 10 finite discharge samples of the profile-wide charge-time source
    for at least 50 % of its regular summary rows (over the joined rows when a seq has several files). A cell without them is excluded before its protocol tuple is computed and counted as "no per-cycle samples";
    that is not an E5 failure.
  - Notes are attached as tags and never exclude a cell.
  - Several files per seq are joined in date order if their date ranges are disjoint. Each later file's `cycle_index`
    is re-based; diagnostics, the contiguity check and the charge-time validation run per file. The cell is excluded if
    the date ranges overlap.
  - Excluded files are counted by reason. Files excluded by the name pattern, the sheet row or overlapping date ranges
    that parse as BEEP JSON are converted and reported in a side table outside the profile (D28 precedent); they never
    enter E3, the split or any fit.
  - **Flag.** The sheet-row condition (option (b); `cell_scope.rule` (ii)) narrows the brief's literal scope (every cell with an aging file whose regular cycles follow the
    modal protocol) to the cells the authors document, because E1 cannot be verified for a file of undocumented
    identity. It is listed in the paper's Notes box as an open author decision on the cell universe, with the
    side-table count.
  - If no copy of the sheet with its declared SHA-256 can be obtained at W1, the third profile stops before conversion.
    The scope is never formed from another source.

### 3. Positions and the cycle axis

- (a) Positions are BEEP `cycle_index` values, with diagnostic cycles as gaps. (b) Positions are the ordinals of regular
  cycles, with `cycle_number = cycle_index` kept.
- (a) makes T depend on the diagnostic schedule, and the window of L = 24 positions would span gaps. That conflicts with
  the brief: "Diagnostic cycles are never positions."
- (b) is how MATR, HUST and ISU-ILCC are built: positions are aging cycles. The authors' cycle lives are in
  `cycle_index` units, so both are reported where compared.
- **Chosen: (b).**

### 4. Charge time

- **Definitions considered:**
  - (a) `summary.charge_duration`. It is 74 % NaN in the inspected cell, measures time to the per-file
    nominal_capacity × full_fast_charge charged rather than the charge, and is assigned to cycles by position.
  - (b) The CC-CV charge duration: from the first kept charge sample with current > C/50 to the charge end.
  - (c) The CC duration only, up to the CV voltage.
- (a) fails as a channel. (c) drops the CV phase, whose lengthening is part of the degradation signature. In the inspected
  cell, (b) moves from 76.7 to 71.8 min by EOL.
- The brief's example is (b), "CC + CV charge duration from the first to the last charge-step sample".
- **Current threshold C/50.** It removes the zero-current rest rows that post-2023 BEEP labels "charge" and keeps the CV
  phase, which ends at C/20.
- **Source.**
  - One source for the whole profile: raw records only if every documented aging file (`cell_scope` (i)-(ii)) carries
    them, decided from the W1 inventory before the sample and protocol conditions are evaluated, as the brief prefers;
    otherwise `cycles_interpolated` for every file. Raw records, where present, give a reported per-file cross-check.
  - A per-file switch would give per-cell level differences, which the X2 backfit absorbs into δ and the pre-screen
    counts. The BEEP writer (tails, charge pooling, axis) is recorded per file.
- **Trim and end extrapolation.**
  - On interpolated data, charge rows are kept only up to the cycle's own charged capacity Q_chg. This drops "slinear"
    NaN tails and "index" clamped tails alike.
  - The end of the CV phase is extrapolated from the last kept row: t_last + 3600 (Q_chg − Q_last) / I_last.
  - Both writers then give the same value, and the residual error is a small fraction of one grid step.
- **Validation** (per file, a W1 converter check).
  - Agreement with `summary.charge_duration` cannot be the test, because the two quantities differ by construction.
  - The test reproduces BEEP's own definition under its positional assignment (G5.6). For each comparable label,
    d_l = the time from the first kept charge sample of S[l] to the first with cumulative charge ≥ the file's
    nominal_capacity × full_fast_charge, and o_l = charge_duration[l]/60 − d_l.
  - On interpolated data a file passes iff median o_l ≥ −1 min, IQR(o_l) ≤ 1 min, and the first kept charge sample lies
    at ≤ 0.001 Ah in at least 95 % of comparable cycles. The constant o_l is the pre-charge segment that BEEP counts and
    interpolated data do not carry: that is the documented reason for the level difference.
  - On raw data a file passes iff median |o_l| ≤ 1 min.
  - The finiteness agreement (charge_duration finite iff the reproduction reaches the threshold) is reported.
  - A file with fewer than 20 comparable labels is not evaluable (counted, accepted). If no file is evaluable, this is
    stated and the channel is used. The threshold is the file's nominal_capacity × full_fast_charge, with BEEP's default
    0.8 if full_fast_charge is absent; both are recorded.
  - Rejected: a lag search of ±1 cycle. A gap in `cycle_index` shifts every later value by a different amount, and a
    lag chosen from the data would be a post-data choice.
- **Failure.** A failing file's cell is excluded and counted. If more than 10 % of the evaluable in-scope files fail, the
  third profile stops. No other charge-time definition or source is substituted after the data are seen.
- **Chosen: (b),** with that source, trim and validation. A failed weight guard is not repaired by another definition
  (CC-only, `CV_time`, `charge_duration`, or a sample-integrated mean voltage); the cross-checks are reported only (E5).

### 5. Rest events and the charge-time mask

- **Rest-event sources.** The brief names three: diagnostic positions, paused cycles, and gaps longer than a declared
  threshold.
  - **Diagnostic.** The first aging cycle after one or more diagnostic or non_aging cycles. Non-aging cycles count as
    interruptions, because unlabelled diagnostic cycles land there when labels are missing or shifted (G5.9, G5.13).
    A labelled diagnostic cycle with an aging-level discharge current is counted and listed, never relabelled.
  - **Paused.** BEEP's `paused` > 0, meaning a gap of more than 1 h inside the cycle. The rest event is the cycle itself.
    Whether the gap is visible inside the sampled charge or discharge steps is recorded, so the placement can be checked.
  - **Gap.** The excess e_c = (start_c − start_prev) − paused_prev − M_c exceeds 30 min (D28's pause margin). M_c is the
    median of the unit's 21 nearest start-to-start intervals that span no diagnostic cycle, no non_aging cycle and no
    file boundary. Subtracting the preceding row's `paused` keeps a pause from being counted twice.
  - **Gap threshold options:**
    - (a) the unit-wide median start-to-start interval + 30 min. Rejected: start-to-start intervals contain the charge
      and discharge, which shorten with fade by about an hour over life;
    - (b) a rolling 21-interval median + 30 min with the preceding pause removed. Chosen;
    - (c) stop-to-start idle time on `test_time`, as D28 measured. Rejected: Maccor `test_time`'s behaviour across a
      suspension is undocumented, and `summary` carries only the cycle's first timestamp.
  - **File.** The first aging cycle of a later file of the same seq.
  - **One source per event:** diagnostic > file > paused > gap. An event whose cycle is not a kept position moves to the
    next kept position, as `scripts/v2/v2_audit_isu.py` `rest_positions` does.
  - **Daylight saving.** Transitions are computed from the US rules (fall-back: first Sunday of November, 09:00 UTC;
    spring-forward: second Sunday of March, 10:00 UTC), not listed by hand. A fall-back puts a +1 h step into
    `date_time_iso`. Within ±6 h of it, a paused event with 3 600 s < paused ≤ 4 500 s, and a gap event with e_c within
    60 ± 10 min, are clock artefacts, not rest events (counted). Spring-forward events are flagged and kept. The
    mechanism diagnostic and the separability count are also reported with the artefacts included.
  - Position 1 is not a rest event.
- **Charge-time mask.**
  - The first aging cycle after a diagnostic charges from a diagnostic discharge (C/20 or C/5 to 3.0 V, or HPPC's
    3 V hold to C/20), not from a 3C/4 discharge. Its charge is therefore longer by the extra charge removed.
  - ISU-ILCC's D28 masked charge time at the corresponding event for the same reason.
  - Options: (a) mask by protocol; (b) leave it to D17/D27. A 3-5 % departure, about 4 min of about 75 min, would often
    escape D17/D27's 5 % rule and become a periodic excursion in a weighted channel.
- **Chosen: (a),** defined from `cycle_index` order, independently of where rest events are placed. Charge time is
  missing at:
  - the first aging cycle after any diagnostic or non_aging cycle, position 1 included (`cycle_index` 3 charges from the
    C/5 RPT discharge of `cycle_index` 2);
  - the first aging cycle of every later file of a seq (its prior discharge is unknown);
  - any cycle whose kept charge samples contain a time step longer than 10 min: a pause inside the charge, the case
    that needed D27 on MATR_b1c2. The largest legitimate step is about 1.4 min.
  - The mask stays on its cycle and lapses if that cycle is not a kept position. About one position in 100 is masked
    after diagnostics; every count is reported.
  - Capacity and mean discharge voltage are kept there. The capacity reading after the rest is the signal the mechanism
    diagnostic reads.

### 6. The authors' EOL definition

- The brief asks for attainment "under the authors' 80 %-of-initial definition". "Initial" is undefined, and the code
  differs from the wording.
- **Options for "initial":**
  - (a) the first regular cycle;
  - (b) q₁, the profile's robust early-life reference (the maximum of the SG(11,2)-smoothed capacity over the first
    20 positions);
  - (c) the code's maximum over the whole record.
- (a) is noise-sensitive: C3 rejected a first-position anchor for exactly this reason. It also reads a post-diagnostic
  cycle: position 1 (`cycle_index` 3) follows the C/5 RPT at `cycle_index` 2. (b) applies the profile's own estimator
  to the wording. (c) reproduces the code but reads the whole record.
- **Chosen: (c) as the authors' implemented definition, with (b) as DegradX's reading of the wording.**
  - (c) is labelled "the authors' code rule". It is computed on the file's summary rows as stored (no DegradX
    predicates, no D12), in `cycle_index` units, and its count is compared with Rhyu et al.'s 178. In the paper it is
    named the authors' definition as implemented in their code.
  - (b) is labelled as DegradX's operationalisation wherever it is reported.
  - Neither enters the profile; E3 and E4 read the primary definition (ρ q_nom = 0.192 Ah).

### 7. The offset pre-screen

- The brief: "on measured windows under recency and uniform weighting: Var(y_offset) / Var(y) using the profile's κ_c.
  This is the measured counterpart of the V4 stop rule."
- **Options:**
  - (a) Observed values. y is computed from x − x0, and y_offset from per-unit means of x − φ(z). Noise inflates Var(y).
  - (b) Fitted mean components at each unit's measured z, with V4's `offset_terms`: δ for the non-capacity channels and
    (q₁ᵢ − q̄₁)(1 − z) for capacity, z clipped at 0 as the generator clips it, and mappings held at their end values
    outside [0, 1]. q₁ᵢ is the unit's S3 q₁.
- (b) is the same estimator as the V4 rule, applied to measured units in place of generated ones. That is what
  "counterpart" asks for. (a) would understate the share by the noise variance and so make the pre-screen more lenient
  than the rule it anticipates. Var(y) has no pattern term, so the share is at or above V4's when patterns are enabled.
- **Population.** Fitting-split units reaching EOL, all windows ending at L..T (T the primary T), as V4 draws its units.
  All guard-passing units are reported as a sensitivity.
- **κ.** β = 1/3 per weighted channel. If the weight guard demotes a weighted channel, E5 fails and the profile stops;
  the share with β renormalised goes in the stop report only, never read.
- **Formation-protocol share.**
  - Under no effect, E[R²] = (g − 1)/(n − 1) for g protocols over n units: about 0.5 on the fitting split.
  - Headline: the one-way R² of the unit-mean y_offset (recency) on protocol_id, against a permutation null (10 000
    permutations). Read "formation protocol explains part of the offsets" iff p < 0.05. The calibrated share
    (R² − mean null R²) / (1 − mean null R²) is reported with it.
- **Reported, never gating:** Var_true(δ) beside Var(δ̂) (offset sampling noise); the share and the E3 count without the
  tagged cells (274, 276, 278, 140, 155); the largest leave-one-unit-out change (as D26's influence row); the share
  without cells taken from the 2024 archive.
- **Chosen: (b).**

### 8. Archive versions

- The brief: "The current archive (2025-03-03) is primary. Use the 2024 archive only if the current one is corrupt or lacks
  aging files that the 2024 one has."
- **Options:**
  - (a) Current archive only, the 2024 archive consulted only if the current one fails integrity. Rejected: the brief's
    second condition (aging files the 2024 archive has) can be decided only from its member list.
  - (b) Both downloaded, member lists and SHA-256 committed before any member is opened, the 2024 archive used per cell
    under the brief's two conditions. Chosen.
  - (c) Both merged with a version comparison. Rejected: what changed is documented nowhere, so no rule could arbitrate
    a difference.
- **Chosen: (b).** A cell taken from the 2024 archive is flagged in every cell table.
- **Integrity.** Each downloaded object must match its recorded HEAD values (bytes, Last-Modified, ETag). A size
  mismatch is re-downloaded once. A remaining mismatch means the object is not the declared version: no member is
  opened, and the third profile stops for an authors' decision. A matching object that fails gzip or tar integrity is
  corrupt, and the 2024 archive serves under condition (a).
- **Extraction.** Members whose base name matches `^Nova_Regular_.*\.json(\.gz)?$` or that sit under a `maccor`
  directory, plus text metadata; never `Nova_Formation*`. Members matched by only one of the two criteria are listed.

### 9. Protocol tolerance and a second protocol

- **Per-cell tuple.** CC charge current (90th percentile of positive current), CV voltage, discharge current and
  discharge cutoff, on the kept charge rows and discharge samples, tail rows excluded. The modal value is taken per
  element: a tuple with a missing cutoff could never equal a complete one.
- **Options:**
  - (a) Documented values ± tolerance as the scope rule. Rejected as the scope rule: the brief names the modal protocol.
    Kept as the E2 check on the files against the documented values.
  - (b) ISU-ILCC's 10 % margin per cell. Rejected: it also separates programmed rates 25 % apart, but leaves twice the
    room for a mis-set current.
  - (c) 5 % / 0.03 V around the per-element modal tuple. Chosen.
- **Tolerance.** ±5 % on currents and ±0.03 V on the CV voltage. Programmed C-rates on this rig differ by at least 25 %,
  so 5 % separates any other programmed rate. 0.03 V is ten grid steps.
- **Discharge cutoff.** An early stop (more than 0.03 V above the reference) is checked wherever the source's lowest
  discharge voltage reaches the reference. A lower cutoff is checked only where the grid extends 0.05 V below 3.0 V. The
  reference is the modal cutoff, or the documented 3.0 V if no cell allows the lower check.
- **E2 on the files.** E2 fails (stop) if a modal element departs from its documented value (0.24 A, 4.4 V, 0.18 A,
  3.0 V) beyond the tolerance, or if incomplete cycles exceed 5 % of the regular cycles (pooled). Otherwise incomplete
  cycles are masked.
- **Incomplete cycles** (masked, counted by clause):
  - (a) V_cv more than 0.05 V below the modal value;
  - (b) the last kept charge current above 2 × C/20 = 0.024 A (the charge ended before its cutoff; D28's predicate);
  - (c) the cutoff more than 0.05 V above the reference (discharge stopped early), where the source can show it;
  - (c′) otherwise, discharge capacity below 0.95 × charge capacity, except after a diagnostic or non_aging cycle.
- **Second protocol.** A source is a cell (meeting the sheet, name and sample conditions) that is out of tolerance or
  carries runs of more than 11 non-aging cycles; a cell's runs are pooled into one tuple, so one cell is one source. Two
  tuples agree iff their currents differ by at most 5 % of the modal value and their voltages by at most 0.03 V
  (V_end only where both are lower-cutoff evaluable). Two or more agreeing sources → stop and report. A single source
  is excluded and counted. Every source's tuple is listed in the W2 record.
  - Side-table files are not sources. They never enter the profile, so a protocol of theirs cannot become offset
    variance of the profile, which is the ISU-ILCC failure the rule guards against. Their tuples are reported.
- **Per-cycle departures beyond 10 %** (in a cell whose per-cell tuple is within tolerance). Such a cycle is non-aging and is excluded from positions (ISU-ILCC's margin).
  A contiguous run of more than W = 11 non-aging cycles cannot be a diagnostic block of at most 3 cycles: it is a
  within-cell protocol change. The cell is out of tolerance, and the run's tuple enters the second-protocol test.

### Chosen by (all sub-decisions)

1. **Logical.** Every rule is read from the documentation or from BEEP's source, not from data. Where the documentation
   is silent, the rule that cannot move with the outcome is taken (documented cells, positional validation, per-element
   modal tuple, rolling gap reference).
2. **Consistent.** Positions, masks, cleaning and the pre-screen estimator are those of MATR, HUST and ISU-ILCC (D28),
   with the precedent named in each section.
3. **Clear.** Each rule is one or two sentences in `v2_1`.
4. **Measured.** Nothing is measured before download; the counts each rule produces are reported at W1 and W2.

Each sub-decision's cost is in § Cost.

## Stop cases declared with this record

- `v2_1.stop_rules` supersedes `v2.stop_rules` for v2.1 stages and sorts cases by scope (brief §5, §6.4).
- **Third profile only** (park the profile, finish W9-W10 with MATR and HUST):
  - the brief's cases (fewer than 66 cells reaching EOL, a second protocol, E1-E6 including E2 on the files, the
    pre-screen and the generated offset share above 0.5, a failed gate);
  - on a failed gate, the agent neither corrects the profile nor voids the scores;
  - an archive object that does not match its HEAD values; the pinned sheet unobtainable;
  - charge-time validation failing on more than 10 % of the evaluable files;
  - a methodological change confined to the third profile (none is made; it is stated in the stop report);
  - disk or memory limits after the declared memory rule;
  - a W8 TimeSHAP projection above 36 h (2 880 explanations; 4 680 with paired maps).
- **Wait for the authors:** a change touching MATR, HUST, `tstr_without_x3` or the shared method.

## Readings declared with this record

- **X6(ii) for the new profile.**
  - Regeneration is present at scale iff D05 enables the positive type on the fitting split at the declared k, m and
    maximum duration (v2.readings.X6_ii_regeneration_at_scale).
  - It is called rest-induced iff the pooled mechanism ratio (window 0..10) has an interval above 1 and the placebo
    (−11..−1) includes 1 or lies below it. Otherwise: "regeneration not localised after rest events".
  - **Separability** counts rests from pauses, gaps and file starts (one source per event, DST artefacts excluded) in the
    fit ranges of the guard-passing fitting units. Fewer than 10: not separable in this dataset. At least 10 with an
    interval above 1: separable. At least 10 otherwise: rest alone is not followed by recovery, and clustering after
    diagnostic blocks is attributed to the block, not to rest alone.
  - If enabled, patterns are inserted at the fitted rate and amplitude (no inflation, D21).
- **D05 governance.** The W2 outcome on the fitting split decides whether the profile carries patterns. W3 must
  reproduce it; a mismatch is an implementation error fixed before W4.
- **Sparse set on trained models.** Scored for a weighting iff the pattern-term ablation on its primary model has a 95 %
  CI of the NMSE increase above 0; otherwise void (D21). The variance ratio against [0.05, 0.50] is reported, not gated.
- **Transfer.** The new profile's interval is read for containing 1. Its point estimate is placed against HUST's
  [0.936, 1.342], and whether the intervals overlap is reported. HUST stays the anchor (D29), on the TSTR ratio,
  covariance agreement and the property table, not the void discriminator.
- **`tstr_without_x3`.** The one MATR/HUST computation, declared now before it runs. It uses V5's estimator on the
  existing `seed0_x3off` sets with V5's TRTR. X3's share is a paired log-difference against v2 seed 0.
  - X2's share is compared with v1's `full_D27` errors over generation seeds 0-2: the brief's three-seed v1 row, with
    the measured side matched to V5's TRTR. The D17-side full set and v1 seed 0 alone are reported, not read.
  - Table 1 prints the v1 row as the brief states (3.42 / 1.46), with a note giving the `full_D27` values (3.51 / 1.46).

## Cost

- **Pre-registration is partial.**
  - r4 was written after the v1 and v2 results and the ISU-ILCC stop were known.
  - The documentation research exposed outcome-adjacent numbers: initial capacities, the 400-1 300 cycle-life range,
    the list of 178 seq numbers with an authors' cycle life, and the brief's one-cell trajectory.
  - It also exposed BatteryLife's statistics and file listings, the papers' capacity and cycle-life figures, and the
    published finding that formation conditions drive cycle life (a prior for the formation share). The review read
    per-seed v1 TSTR ratios.
  - `v2_1.exposure` lists them. The Limitations list of post-data rules says so.
- **The cell universe depends on the parameter sheet.**
  - Files of undocumented identity are excluded even if they follow the protocol. Their number is reported. Files
    excluded by the name pattern, the sheet row or overlapping date ranges that parse as BEEP JSON are converted and
    reported in a side table outside the profile; they never enter E3, the split or any fit.
  - The sheet comes from a repository without a licence. It is fetched, never committed. If it cannot be obtained with
    its checksum, the third profile stops.
- **Charge time on interpolated data ends on a capacity grid.** The end of the CV phase is read by extrapolating from
  the last grid point inside the cycle's charged capacity, so slinear and index writers give the same value, and the
  residual error is a fraction of one grid step (about 1.4 min at C/20). Without that rule, a uniform cut of up to
  1.4 min would act as noise of SD about 0.4 min (1.4/√12), against a fade to EOL of about 5 min in the brief's cell.
- **Rest after a diagnostic always comes with a rate change.**
  - Unless the files hold enough pauses, recovery after rest cannot be separated from the effect of a lower-rate
    discharge before the next aging cycle.
  - The mechanism diagnostic is reported with that statement, not as evidence of regeneration.
- **The authors' EOL wording is reproduced only approximately.** "Initial" is read as q₁ (DegradX's reading, labelled
  so), and the authors' code rule is reported beside it.
- **Licence.** CC BY-NC 4.0 makes the derived parameters non-commercial. This is flagged for the authors.

## Review (before commit)

See `artifacts/v2.1/w0_declarations/REVIEW.md`: three lenses (brief compliance; measurement science and BEEP semantics;
pre-registration hygiene with an advocate for the rejected options) and a judge. 57 objections (1 blocker, 27 major,
29 minor) were all accepted, 45 of them with modifications, and applied before commit. The rulings are listed there.

**Paper impact:** AMENDMENTS round 8: §3.4 Profiles (the dataset, its role and the licence sentence; the
selection-criteria sentence at paper.tex l.264: 67 → 66, and E2 read strictly for the new profile); the Notes box
(nominal-capacity source, licence, the cell universe with the side-table count, the E3 correction and Tongji, the
post-data rules); the Limitations list.
