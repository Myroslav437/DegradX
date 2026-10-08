# V9 — X9 pilot: observation-level target on HUST (exploratory)

## What ran

- **Command.** `python scripts/v2/v9_observation_target.py` (CUDA, 11:37–12:09 on 2026-10-08, 3 CPU threads), then
  `--compare-only` after V8 was scored.
  - It ran on the GPU while V8's TimeSHAP run used the CPU, which the brief allows ("V9 runs last, or whenever the GPU is
    idle").
- **Design.** Declared in r3 `v2.observation_target` (2026-10-07, before V9).
  - **Target.** y_obs = Σ w (x − x⁰) on the observed window, with ϕ*_obs = w (x − x⁰).
  - **Data.** HUST, recency, V4 generation seed 0 with its split.
  - **Ensemble.** Ten LSTM members, A 64 × 2 and B 128 × 1 × seeds 0–4, as in V6.
  - **Measures.**
    - The X4 gate on every member.
    - IG and occlusion on V8's 120 HUST windows for every member.
    - The three scores against ϕ*_obs.
  - TimeSHAP was optional and was not run.
- **Outputs.** `tables/observation_target.json`, `figures/hust_yobs_ensemble_vs_method_gap`, the ten models in `models/`
  (LFS), and D31. Nothing enters the paper tables.

## What came out

- **Accuracy.**
  - NRMSE on y_obs is 0.0012–0.0019 over the ten members.
  - RMSE / SD(Σwε) is 0.011–0.018, so every member reads the cell-level values (declared reading ≤ 0.5).
- **X4.** Every member uses all three weighted channels materially:
  - capacity 0.031 [0.027, 0.038];
  - charge time 0.034 [0.030, 0.041];
  - mean discharge V 0.606 [0.526, 0.708] (A0).
- **Scores against ϕ*_obs, and the declared reading** (ensemble range < largest method gap):

| score | A0: IG / occlusion | gap | range IG / occlusion | restored | standard y, V8: gap / ranges |
|---|---|---|---|---|---|
| rank agreement | 0.961 / 0.958 | 0.003 | 0.077 / 0.072 | no | 0.016 / 0.151, 0.206 |
| channel allocation error | 0.004 / 0.019 | 0.015 | 0.006 / 0.013 | **yes** | 0.018 / 0.093, 0.098 |
| temporal profile error | 0.79 / 0.75 | 0.035 | 0.47 / 0.45 | no | 0.108 / 1.17, 0.73 |

**X9 answer: no.** Position-level identifiability is not restored: rank agreement and the temporal error stay above
the method gap. The channel allocation becomes identifiable. All ranges narrow by 1.6–15 times against the standard y,
and the levels rise: rank agreement goes from 0.73–0.75 to 0.96.

## Checks

2 pass (`logs/checks.md`):
- IG on the reference model equals ϕ*_obs (7.5e-8);
- the primary model passes the accuracy gate (0.002).

## Anomalies

1. **One member (B3) is an outlier on rank agreement** (0.888 against 0.950–0.965 for the other nine). It sets most of
   the rank range, but without it the range is still about 0.013, five times the gap.
2. **The allocation reading has a small margin:** occlusion's range is 0.013 against a gap of 0.015.

## Decisions needed

None. D31 records the result. The benchmark keeps y (option a); nothing from V9 enters the paper tables.
