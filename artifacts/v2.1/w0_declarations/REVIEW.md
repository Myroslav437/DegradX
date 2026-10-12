# W0 — documentation and declarations r4 (brief "DegradX v2.1", 2026-10-11)

## What ran

- **Tag and branch.** `v2-results` tags the v2 HEAD (`855e425`). All v2.1 work is on branch `v2.1`.
- **Output roots.** `artifacts/v2.1/`, `results/v2.1/` and `data/v2.1/` (`data/` is gitignored). Their paths are in
  `degradx.ARTIFACTS_V21`, `RESULTS_V21` and `DATA_V21` (`src/degradx/__init__.py`).
- **Snapshot.** The declarations as they stood at `v2-results` are kept verbatim in
  `configs/declarations_history/declarations_at_v2-results.yaml`.
- **Documentation research.** Four documentation readers, a synthesis of 72 claims in six topic groups (cell and
  nominal capacity; aging protocol and diagnostics; EOL and counts; formation mapping and naming; BEEP semantics;
  archives and licence), and 12 verifiers (a source-fidelity and an adversary lens per group). Output:
  `documentation_research.md` in this folder. Only HTTP HEAD requests touched the archives; no byte of either archive
  was downloaded.
- **Profile config.** `configs/profiles/tri_formation.yaml`: cell, nominal capacity 0.24 Ah with its source (Cui et al.
  p.3082), aging protocol and diagnostic layout, the authors' EOL wording and code rule, the pinned formation mapping,
  licence.
- **Declarations r4.** Added as `declared_by_design.v2_1` in `configs/declarations.yaml`, with dated (2026-10-11)
  supersession entries.
- **Decision record.** D32 (extraction, scope, channels, rest events, pre-screen, archives, tolerance).
- **DEVIATIONS T7.** The v2 ISU-ILCC mechanism diagnostic placed run starts one position late; not recomputed (closed).

## What r4 declares (one line each)

| block | declares |
|---|---|
| `paths` | v2.1 writes only under `artifacts/v2.1`, `results/v2.1`, `data/v2.1`; stage folders W0-W10. |
| `authors_decisions` | ISU-ILCC closed under option A; the TRI/Stanford formation dataset (CC BY-NC 4.0); E3 corrected to 66, Tongji not re-opened. |
| `scope` | Dataset key `TRI_FORMATION`; every r2/r3 rule not superseded applies; only `tstr_without_x3` touches MATR/HUST; HUST stays the anchor, on TSTR, covariance and the property table. |
| `eligibility` | E1-E6 with E3 = 66 and E2 read strictly; `E2_files` (modal tuple vs documented values; incomplete cycles ≤ 5 % pooled); E5 not repaired by re-assigning roles or redefining a channel. |
| `archive` | Current archive primary; both archives downloaded, member lists and SHA-256 committed before any member is opened; the 2024 archive per cell under the brief's two conditions; HEAD mismatch is a stop; anchored extraction pattern. |
| `formation_mapping` | The authors' parameter sheet pinned by commit and SHA-256, fetched not committed; unobtainable → stop; protocol groups; lab notes as tags only. |
| `cell_scope` | (i) anchored name pattern, (ii) a sheet row, (iii) ≥ 10 charge and 10 discharge samples on ≥ 50 % of rows, (iv) modal protocol; undocumented files excluded and side-tabled; date-order join of several files; the narrowing flagged for the authors. |
| `aging_protocol` | Per-cycle tuple on kept rows; per-element modal values; ±5 % / 0.03 V with a one-sided early-stop check; second protocol: two or more out-of-tolerance sources (cells, with a cell's runs of > 11 non-aging cycles pooled) agreeing within the tolerance → stop; a single one is excluded and counted; side-table files are reported, not sources. |
| `positions`, `cycle_predicates` | Regular aging cycles in `cycle_index` order; diagnostic cycles never positions, never relabelled; degenerate (`no_samples` counted), incomplete (a)-(c′), non_aging. |
| `channels` | Capacity and mean discharge voltage from `summary`; CC-CV charge time on one profile-wide source with trim and end extrapolation, validated per file against BEEP's positional `charge_duration`; failing cells excluded, > 10 % → stop; protocol mask (a)-(c). |
| `rest_events` | Diagnostic or non_aging interruptions, paused cycles, gaps on a rolling 21-interval reference with the preceding pause removed, later-file starts; one source per event; placement on kept positions; DST artefacts from computed transitions are not rest events. |
| `eol_reported` | Primary Eq. 3 at 0.192 Ah; the wording with "initial" = q₁ (DegradX's reading, labelled); the authors' code rule on the stored summary rows, compared with Rhyu's 178. |
| `converter_checks` | Summary equality to machine precision; charge-time validation; `cycle_index` disjointness and contiguity; diagnostic labels; tuples; counts; BEEP-writer markers. |
| `audit`, `mechanism_diagnostic` | S2-style audit on the declared split; windows 0..10 and placebo −11..−1 with the corrected start index; three-branch separability reading. |
| `weight_guard`, `offset_prescreen` | E5's guard from the W2 fit; V4's `offset_terms` on measured units (z clipped at 0); stop above 0.5; formation headline by permutation p-value; sensitivity rows never gating. |
| `readings` | X6(ii) (rest-induced only with the placebo), D05 governance, trained sparse-set scores, transfer (contains 1, against and overlapping HUST), covariance, discriminator, gates, generated offset share, y-RUL. |
| `stop_rules` | Supersedes `v2.stop_rules` for v2.1: twelve third-profile-only park cases; MATR/HUST/shared-method cases wait for the authors. |
| `tstr_without_x3` | V5's estimator on `seed0_x3off`; X3's share against v2 seed 0; X2's share against v1 `full_D27` over three seeds; Table 1 rows. |
| `exposure` | Results known, the brief's one cell, documentation, third-party material, figures, the published finding, the review's per-seed values, HEAD requests. |

## Review before commit

Three independent lenses reviewed the draft r4 block, D32 and the profile config:
- **brief compliance** (every W0 requirement, §5 stop classification, supersession entries);
- **measurement science** (BEEP semantics, implementability on interpolated and raw data, the pre-screen against V4's code);
- **pre-registration hygiene** (post-data latitude, exposure, and an advocate for each rejected option).

A judge ruled on every objection and set the order in which rulings that rewrite the same key are applied.

**Counts.** 57 objections: 1 blocker, 27 major, 29 minor. All were accepted: 12 as proposed and 45 with modifications
(the judge ranked the blocker major, since (i)'s name pattern already hinted at the intent). Parts of measurement-03,
-06, -10, brief-tstr-x2-share and hygiene-14 were declined within their rulings. All rulings were applied before this
commit.

The main changes:
- **Seq parsing.** The seq comes from an anchored name pattern, so `Nova_Regular_Ref_100.034.json.gz` cannot read as
  seq 100. Undocumented and overlapping files go to a side table; the sheet gate is flagged for the authors.
- **Charge-time source.** One source for the whole profile, with tail trim and end extrapolation, so `slinear` and
  `index` writers give the same value.
- **Charge-time validation.** Per file, under BEEP's documented positional assignment, with a constant-offset criterion
  on interpolated data. The ±1 lag search is gone. Failing cells are excluded; above 10 % of files the profile stops.
- **Non-aging cycles.** They count as interruptions (unlabelled diagnostics land there). A run of more than 11 is a
  within-cell protocol change and enters the second-protocol test.
- **Charge-time mask.** Defined from `cycle_index`, covering position 1, later-file starts and pauses inside the charge.
- **Gap events.** A rolling 21-interval reference with the preceding pause subtracted, replacing a whole-record median
  that drifted with fade.
- **DST.** Transitions computed from the US rules; fall-back artefacts are not rest events.
- **Incomplete cycles and E2.** The last-current predicate (D28) was added and V_end checks made one-sided where the
  grid allows. A CE fallback covers the rest. E2 now has a failure condition on the files.
- **Readings.** Separability has three branches. X6(ii) calls recovery rest-induced only with the placebo. D05
  governance, the trained sparse-set rule and the transfer overlap are declared.
- **Offset pre-screen.** V4's estimator applied faithfully (z clipped, S3 q₁, primary T). E5 demotion is a stop. The
  formation share has a headline, a permutation p-value and the correct null (about 0.5).
- **`tstr_without_x3`.** X2's share is compared with v1's `full_D27` errors over three seeds (the measured side matched);
  the alternatives are reported, not read.
- **Stops.** Third-profile-only cases are parked rather than waiting; seven new cases were added; the "neither corrects
  nor voids" clause was restored.
- **Archive integrity.** A HEAD mismatch is a stop. Member lists are committed before any member is opened.
- **Hygiene.** Supersession entries for rest events, ingestion, the TimeSHAP projection, `eligibility.evaluated` and
  Tongji's finding; exposure extended; D32 given the five-step options and a "Chosen by" block; DEVIATIONS T7 notes the
  ratios quoted in the v2 log.

### Rulings

| id | severity | ruling | applied in |
|---|---|---|---|
| brief-seq-parse | blocker | accept, modified | `cell_scope.rule`, `undocumented_files`, `baseline_cells`; D32 §2 |
| brief-scope-sheet-gate | major | accept, modified | `cell_scope.flag`, `side_table`; `formation_mapping.storage`; stop case; D32 §2, Cost |
| brief-charge-time-source | major | accept, modified | via measurement-02; `archive.rule` flag; 2024-archive sensitivity |
| brief-charge-time-validation | major | accept, modified | `charge_time.validation`, `failure`; stop case; D32 §4 |
| brief-non-aging-cycles | major | accept, modified | `rest_events.sources.diagnostic`; `per_cycle_departure` run rule; `second_protocol` |
| brief-separability | major | accept, modified | `mechanism_diagnostic.separability`; D32 Readings |
| brief-e2-files | major | accept, modified | via hygiene-07 |
| brief-tstr-x2-share | major | accept, modified | via hygiene-10 |
| brief-stop-classification | major | accept | `stop_rules` |
| brief-supersession-gaps | minor | accept, modified | three new log entries; decisions 1-2 entry; `scope.fidelity_anchor` |
| brief-tongji-e3 | minor | accept, modified | E3 log entry; D32 Paper impact |
| brief-beta-renorm | minor | accept, modified | `offset_prescreen.terms` (via measurement-10) |
| brief-archive-integrity | minor | accept, modified | `archive.integrity`, `archive.rule`; stop case; D32 §8 |
| brief-extraction-pattern | minor | accept, modified | `archive.extraction` |
| brief-vend-evaluable | minor | accept, modified | via measurement-05 |
| brief-d32-five-step | minor | accept, modified | D32 §5, §8, §9 options; "Chosen by" |
| brief-conditional-readings | minor | accept | `readings.D05_governance`, `sparse_set_trained`, `transfer` |
| brief-meta-status | minor | accept, modified | `meta.status` |
| measurement-01 | major | accept, modified | via brief-charge-time-validation, hygiene-06 |
| measurement-02 | major | accept, modified | `charge_time.value`, `source`, `resolution`; `archive.raw_records`; `per_cycle_tuple` |
| measurement-03 | major | accept, modified | `cell_scope.rule` (iii); `cycle_predicates.degenerate` (`no_samples`) |
| measurement-04 | major | accept | `cycle_predicates.incomplete` (b) |
| measurement-05 | minor | accept, modified | `per_cycle_tuple` V_end; `tolerance`; `incomplete` (a)-(c′) |
| measurement-06 | major | accept, modified | `positions.diagnostic_cycles` |
| measurement-07 | major | accept, modified | `rest_events.dst`; D32 §5 |
| measurement-08 | major | accept, modified | `rest_events.sources.gap`, `precedence`; D32 §5 |
| measurement-09 | minor | accept, modified | `rest_events.sources.paused` |
| measurement-10 | major | accept, modified | `offset_prescreen.terms`, `units_windows`; D32 §7 |
| measurement-11 | major | accept | `charge_time.protocol_mask`; `rest_events.position_1`, `use` |
| measurement-12 | minor | accept, modified | `rest_events.placement` |
| measurement-13 | major | accept | `protocol_mask` (c) |
| measurement-14 | minor | accept | `aging_protocol.modal` |
| measurement-15 | minor | accept | `eol_reported.authors_code` |
| measurement-16 | minor | accept, modified | `cell_scope.several_files_per_seq`; D32 §2 |
| hygiene-01 | major | accept, modified | via brief-separability |
| hygiene-02 | major | accept | `readings.X6_ii_regeneration`; D32 Readings |
| hygiene-03 | major | accept, modified | via measurement-08 |
| hygiene-04 | minor | accept, modified | via measurement-07 |
| hygiene-05 | major | accept, modified | via brief-charge-time-validation |
| hygiene-06 | major | accept, modified | `charge_time.documented_reason`; D32 §4 (a) |
| hygiene-07 | major | accept, modified | `eligibility.E2_files`, `evaluated`; `aging_protocol.modal`; `incomplete` (c′) |
| hygiene-08 | major | accept | `cell_scope.rule` (iii), `no_per_cycle_samples`, `counts_reported` |
| hygiene-09 | major | accept, modified | via measurement-16 |
| hygiene-10 | major | accept, modified | `tstr_without_x3.purpose`, `shares`, `rows`; `exposure.review` |
| hygiene-11 | minor | accept, modified | `offset_prescreen.reported` (formation headline); D32 §7 |
| hygiene-12 | minor | accept, modified | via brief-scope-sheet-gate |
| hygiene-13 | minor | accept | `offset_prescreen.reported` (tagged cells, leave-one-out) |
| hygiene-14 | minor | accept, modified | `eol_reported.authors_wording`, `authors_code`; D32 §6 |
| hygiene-15 | minor | accept, modified | `exposure.third_party`, `figures`, `findings`, `brief_one_cell`; D32 Cost |
| hygiene-16 | minor | accept, modified | via brief-tongji-e3 |
| hygiene-17 | minor | accept, modified | via brief-beta-renorm |
| hygiene-18 | minor | accept, modified | stop case (TimeSHAP > 36 h); log entry |
| hygiene-19 | minor | accept | DEVIATIONS T7 |
| hygiene-20 | minor | accept, modified | via measurement-11, -12, brief-non-aging-cycles |
| hygiene-21 | minor | accept | `eligibility.E5` |
| hygiene-22 | minor | accept, modified | via measurement-02 |
| hygiene-23 | minor | accept, modified | `offset_prescreen.reported` (Var_true(δ)) |

One adaptation beyond the ruling texts: `cycle_predicates.handling` now reads "no halt, except under
eligibility.E2_files", so that it does not contradict the new E2 failure condition.

## Exposure

r4 was written after the v1 and v2 results were known, including the ISU-ILCC offset-share stop. The brief itself
reports one cell's measurements (Nova_Regular_197.034: capacity trajectory, mean discharge voltage, `charge_duration`
NaN from cycle 213, charge-step spans, stored nominal capacity, diagnostic triplets). The documentation research read
design metadata and outcome-adjacent values printed in the papers or saved notebook outputs: initial capacities, the
400-1 300 cycle-life range, the list of 178 seq numbers with an authors' cycle life, the capacity and cycle-life
figures, and the published finding that formation conditions drive cycle life. It also read BatteryLife's text,
statistics, code and Hugging Face file listings (names only). HTTP HEAD requests gave the archive sizes, dates and
ETags. During the review, the reviewers read per-seed v1 TSTR ratios from the stored V1 per-unit errors. The judge read
only already-reported v1/v2 summaries and listed npz keys, and computed no new ratio. No cycle-life table and no
measurement file of the dataset was opened. `v2_1.exposure` lists all of this.

## Checks

- `load_declarations()` parses r4: `meta.revision` r4, 32 supersession entries, every `v2_1` key present.
- The regexes are in single-quoted scalars and load as written: the scope pattern reads `Nova_Regular_197.034.json.gz`
  as seq 197 and rejects `Nova_Regular_Ref_100.034.json.gz`.
- `configs/declarations_history/declarations_at_v2-results.yaml` is byte-identical to `v2-results:configs/declarations.yaml`
  (`git show v2-results:configs/declarations.yaml | cmp - configs/declarations_history/declarations_at_v2-results.yaml`:
  no difference).

## Decisions needed (for the authors)

- **Cell universe.** r4 narrows the brief's literal scope to the cells the authors document (a row in the parameter
  sheet), because E1 cannot be verified for a file of undocumented identity. Excluded files are converted and reported
  in a side table. Confirm, or widen the scope.
- **Licence.** CC BY-NC 4.0 makes the fitted parameters and generated units non-commercial (README licence note).
  Confirm that this is acceptable for the release.
- **E3 correction and Tongji.** E3 = 66 removes r3's only written ground against Tongji (66 NCA cells < 67). Tongji
  stays closed by the authors' decision ("ineligible on other grounds"); please name the grounds for the Notes box.
- **Nominal capacity.** 0.24 Ah from Cui et al.'s text ("nominally 240 mAh"), so no flag is needed beyond confirmation.

## Next: W1

Download both archives into their own empty directories, record and commit their checksums and member lists before
any member is opened, fetch the pinned parameter sheet, then convert one cell per process with the declared converter
checks.

## Consistency check after the rulings (second pass)

A fresh consistency reviewer read the applied text and found eight further problems, all applied before commit:
the source and scope rules defined each other (the source is now decided from the documented files before (iii) and
(iv)); the second-protocol test now defines a source (one cell = one source, its runs pooled), pairwise agreement and
the role of side-table files (reported, not sources); (iii) now counts samples and covers joined files; a dated
supersession entry for E5; three D32 / REVIEW wording mismatches; and short units in the gap rule. The YAML parses with
32 supersession entries.
