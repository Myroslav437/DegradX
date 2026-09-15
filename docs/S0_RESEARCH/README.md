# S0 research reports

Seven investigations run at S0, before any data-consuming code, to ground the declarations and
tooling choices: `env.md`, `attribution_apis.md`, `fidelity_metrics.md`, `datasets.md`,
`declarations_text.md`, `declarations_domain.md`, and the figure-style reconstruction (summarised in
`docs/TOOLING.md`; code in `src/degradx/viz/style.py`).

The reports refer to scratch paths (`/tmp/claude-…/scratchpad/...`) that were session-local and are
not preserved. The analysis scripts behind any number quoted in `configs/declarations.yaml` are kept
under `scripts/` here (e.g. `scripts/domain/run_rule_sim.py` for the detection false-run rates,
`scripts/domain/sg_cutoff.py` for the Savitzky–Golay cutoffs). Downloaded papers and cloned
repositories are not redistributed; the reports cite their URLs and commits.

Counts about the datasets in `datasets.md` come from their documentation and remote file probes. They
are context for S1 checks, never results of this programme (R1).
