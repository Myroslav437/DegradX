# W9 — methodology diagrams redrawn from scripts (brief "DegradX v2.1", 2026-10-13)

## What ran

- **The five methodology diagrams were redrawn** from scripts in `paper/img/scripts/`, in the reconstructed paper style
  (`degradx.viz.style`):
  - `fig_loop.py`
  - `fig_generator.py`
  - `fig_mean_component.py`
  - `fig_weights.py`
  - `fig_tstr.py` (new; Fig. 5 had no script)
- **Shared loader.** `diagram_inputs.py` is a read-only loader of the declarations and profile JSONs, shared by the five
  scripts.
- **Every number and label is read from the declarations or the fitted / generated FORM profile**, never typed by hand:
  profiles, split fractions, input sets, ensemble size, L, h, the correlation, the illustrated unit and its window.
- **`fig_weights_r3.py` was removed.** It would overwrite `fig_weights.pdf` with the old L = 40 drawing, and git keeps it.
- **Print check.** Every figure keeps its `\includegraphics` width. Printed scale is 0.97–1.04, and the smallest text
  prints at about 6.8 pt or larger. Previews are in `figures/`.

## What each diagram shows now

| figure | content (brief W9) |
|---|---|
| Fig. 1 `fig_loop` | Three measured datasets (MATR, HUST, FORM); the fitting (0.7) and held-out (0.3) splits; a profile with $z$, $\varphi_c$, $\delta_{c,i}$, $\varepsilon$, $p$; the fidelity box (TSTR with 5 input sets, covariance agreement, property table, discriminator); the reference model $g$ as the correctness check; trained LSTMs with the primary model and the 10-member ensemble (floor). |
| Fig. 2 `fig_generator` | One generated FORM unit (index 173, source TRI_169), capacity and charge time: (a) mean component and its shared part ($\delta_{c,i}$ visible on charge time); (b) inserted patterns, FORM only (zero in MATR and HUST); (c) noise correlated across channels, $r = -0.89$ (fitted within-unit); (d) $x$; (e) $\phi^{\star}$ of a 24-position window under recency (graded field and sparse stems). |
| Fig. 3 `fig_mean_component` | FORM: two fitting units at the 10th / 90th percentile of the charge-time offset. (a) pace in $z$; (b) the shared mappings (scaled); (c) charge time = shared mapping at the unit's state, shifted by $\delta_{c,i}$. |
| Fig. 4 `fig_weights` | $L = 24$, $h = 6$: recency (primary), uniform (sensitivity), final position (defined, not scored). |
| Fig. 5 `fig_tstr` | TSTR and its reference, both evaluated on the held-out units; the ratio is taken once per input set (full, capacity only, capacity relative, capacity state, full centred). |

**Input-set names.** Table 3 (W10) now uses the same declared names, so the paper uses one vocabulary.

## Captions for W10

These are applied to `paper/paper.tex` at W10 and adapted to the final text.

- **Fig. 1.** Structure of the benchmark. The units of each measured dataset (MATR, HUST, FORM) are divided into a
  fitting split (0.7) and a held-out split (0.3).
  - Generator parameters are estimated from the fitting split, giving a profile: the degradation state $z$; the channel
    mappings $\varphi_c$ shared by all units, with a per-unit offset $\delta_{c,i}$; the noise $\varepsilon$, correlated
    across channels; and the inserted patterns $p$.
  - Drawing $\theta$ per unit generates units, each carrying $x$, $\phi^{\star}$, $y$ and $R$.
  - The profile is compared against the held-out split by the transfer ratio for each of five input sets, the covariance
    agreement, the property table and a discriminator.
  - Attribution maps are scored on generated units only:
    - on the reference model $g$, whose exact attribution is known, as a correctness check of each method;
    - on trained LSTMs, for the primary model and an ensemble of ten equally accurate models, whose spread is the
      identifiability floor.
- **Fig. 2.** Decomposition of one generated FORM unit, for capacity (left) and charge time (right).
  - (a) The mean component $m_{t,c}$ (solid) and its shared part $\varphi_c(z_t)$ (dashed). On charge time they differ by
    the unit's offset $\delta_{c,i}$.
  - (b) The inserted patterns: recoveries of capacity after a diagnostic block, the one type FORM enables. The term is
    zero in MATR and HUST.
  - (c) The noise, standardised per channel. The noise of mean discharge voltage (grey) is drawn with that of charge time,
    with the fitted within-unit correlation $r = -0.89$.
  - (d) The observation $x_{t,c}$.
  - (e) The attribution ground truth of the shaded window of $L = 24$ positions, under recency weighting: a graded field
    from the mean component and a sparse set from the inserted pattern.
- **Fig. 3.** Construction of the mean component, on FORM.
  - (a) Two units advance through the degradation state at different paces.
  - (b) The same fitted mappings, scaled to their change from the pristine level to EOL, apply to both.
  - (c) In charge time, each unit's mean component is the shared mapping at its own state, shifted by its offset
    $\delta_{c,i}$.
- **Fig. 4.** Position profiles $\pi_u$ within a window of $L = 24$ positions.
  - Recency, $\pi_u \propto 2^{-(t-u)/h}$ with $h = 6$, is primary.
  - Uniform weighting is a sensitivity.
  - Final-position weighting is defined but not scored.
- **Fig. 5.** The transfer measurement. Models trained on generated units and on the measured fitting split are
  evaluated on the held-out measured units. The ratio of their errors is reported for each of the five input sets: full,
  capacity only, capacity relative, capacity state and full centred.

## Provenance

`scripts/v2_1/w10_write_paper.py` (`diagrams()`) writes one row per diagram to `results/v2.1/provenance.json` and
`docs/RESULTS_PROVENANCE.md`.
