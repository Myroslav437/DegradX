# D33 — The aging-protocol check reads the charge current on the constant-current samples of the charge; a cycle with no constant-current phase is not tested

**Stage / claim affected:**
- W1 (brief "DegradX v2.1");
- declarations r4 `declared_by_design.v2_1.aging_protocol.per_cycle_tuple` (I_chg) and `.per_cycle_departure`;
- the cell scope of the TRI formation profile (FORM), and the brief §5 stop case "more than one aging protocol".

**Timing.** Taken 2026-10-13 at W1, **after** the per-cycle statistics of all 182 aging files had been computed. This is a
post-data decision, and it is listed with the other post-data rules (Limitations; the paper's Notes box).

## State

r4 declared the per-cycle charge current as I_chg = the 90th percentile of the positive current over the cycle's kept
charge samples, described as "the CC level". Under the declared rules:
- a regular cycle whose I_chg departs from the modal 0.24 A by more than 10 % is not an aging cycle;
- a contiguous run of more than 11 such cycles makes the cell out of tolerance, as a within-cell change of protocol;
- two or more such sources that agree within the tolerance are a second aging protocol, which is a stop case.

Applied as declared, the W1 run gives:
- **40 cells** carry a run of more than 11 departing cycles;
- the 40 sources agree pairwise in 114 pairs;
- so the rule reports a second aging protocol and would stop the third profile.

The departures are not a protocol (`artifacts/v2.1/w1_ingest/tables/ingest_summary.json`):
- **Discharge and voltages are unchanged.** In every departing run the discharge current is exactly the modal 0.18 A,
  V_cv is 4.400 V and V_end is 3.000 V.
- **Only I_chg moves, and it is spread continuously.** It runs from 0.06 to 0.20 A across the runs, which matches no
  programmed rate. The rig's rates are C/20, C/5, C/3, C/2, 3C/4 and 1C.
- **Every departing cycle is long after EOL.** Capacity has collapsed to 0.006–0.046 Ah, 3–19 % of nominal. Examples:
  - seq 116: 0.192 Ah is crossed at cycle_index 482, and the departures start at 736;
  - seq 100: 489 and 775;
  - seq 140: 630 and 788;
  - seq 139: 661 and 1 177.
- **The charge in those cycles has no constant-current phase.** The cell reaches 4.4 V almost at once, so the time-uniform
  samples are nearly all CV. In seq 116:
  - cycle 736: 8.3 % of the charge samples lie below 4.39 V; the maximum current is 0.2401 A and the 90th percentile 0.2151 A;
  - cycle 916: 0 % lie below 4.39 V; maximum 0.2400 A, 90th percentile 0.082 A;
  - cycle 1 079: 0 % lie below 4.39 V; maximum 0.175 A.
- **The 90th percentile measures the CC level only while the CC phase covers more than a tenth of the charge.** The
  statistic was declared on that assumption, and it does not hold once capacity collapses after EOL.

**Decision.** How is the programmed charge current read in a cycle whose charge has (almost) no constant-current phase?

## Options

| | option | 40 run cells | second-protocol stop | departs from r4 |
|---|---|---|---|---|
| a | keep r4 (p90 over all charge samples) | excluded | **triggered** (false) | no |
| b | I_chg = the maximum (p99) charge current | most kept; fully-CV cycles (max < 0.24) still depart | likely still triggered | percentile only |
| c | **I_chg = median current over the constant-current samples (voltage below the cycle's own V_cv − 10 mV, current > C/50), at least 10 such samples; a cycle with fewer is not tested for a charge-current departure** | kept | not triggered unless a real CC current differs | estimator and its domain |
| d | test departures only on positions up to EOL | kept | not triggered | introduces EOL (a W2 quantity) into W1 |
| e | stop and report (brief §5) for the authors' decision | — | — | none |

Real: all five are possible.

Works:
- **(a)** parks the profile on a reading the data contradict. The documented protocol is one, and the
  discharge, V_cv and V_end of the "second protocol" equal the modal values. It is not what the stop case is for: a second
  programmed protocol, whose offsets would encode protocol identity (the ISU-ILCC lesson).
- **(b)** still fails on cycles that are CV from the first sample, where the current never reaches 0.24 A.
- **(c)** reads the quantity the tolerance is about, the programmed constant current, where it exists. Where it does not,
  the cycle cannot show a different programmed current, so it is not tested. The other three tuple elements (I_dis,
  V_cv, V_end) still test every cycle.
- **(d)** would make W1 depend on the W2 EOL computation.
- **(e)** is the default for "a methodological change the brief does not list". This is not one:
  - The brief specifies the check: a tolerance on the charge and discharge current and on the voltage limits.
  - r4 chose the estimator, and (c) corrects that estimator to measure what it was declared to measure ("the CC level").
  - The method of the paper (generator, target, scores) is untouched.
  - Stopping would discard the profile for an artefact of the agent's own estimator. The authors are told instead (Notes
    box), and can reverse it.

Clear: (c) in one sentence: "The charge current of a cycle is the median current of its constant-current samples; a cycle
without a constant-current phase is not tested for it."

**Chosen: (c).**
1. *Logical:* the tolerance is on the programmed charge current, which exists only during the CC phase.
2. *Consistent:*
   - The per-cell tuple and the modal value use the same estimator.
   - The 10-sample minimum is r4's degenerate-cycle count.
   - The 10 mV margin below V_cv is a third of the declared 0.03 V voltage tolerance.
3. *Clear:* one sentence.
4. *Measured:* with (c), the W1 re-run reports the remaining departures, runs and sources. The literal (a) outcome
   is kept in the W1 tables beside it (`ingest_summary_r4_literal.json`).

## Cost

- **A declared estimator changed after the per-cycle data were seen.**
  - The change is confined to the I_chg element of the protocol check. It touches no profile quantity: capacity, charge
    time and mean discharge voltage are unchanged.
  - The literal outcome is kept and reported, and the Notes box lists the decision for the authors.
- **Collapsed post-EOL cycles are not tested on the charge current.** A real change of programmed charge current after
  EOL would be missed if it came with no CC phase. Such a change could not affect the profile, which uses positions up to
  EOL for every unit reaching it.

**Paper impact:** AMENDMENTS round 8: Limitations, list of post-data rules (D33); Notes box (post-data rules).
