"""D02b harness: minimum number of held-out measured units per fidelity measure (D02 left it provisional at 5).

MATR (38 held-out units reaching EOL, 40 held-out in total). For n in {3, 5, 8, 12, 20} held-out units, draws without
replacement (seed stream 'bootstrap'):
  TSTR ratio        per-unit SSE from one TSTR (generation seed 0, model seed 0) and one TRTR model; ratio on the drawn units
  discriminator     retrained (2000 iterations) on the drawn held-out units vs generated seed 0; discriminative error
  Frechet (TS2Vec)  encoder trained once on fitting windows; generated vs drawn held-out representations
  covariance        relative Frobenius distance of channel correlation, generated vs drawn held-out
Spread = (p97.5 - p2.5) / 2 over draws, relative to the full held-out value. The declared readability criterion (D02):
relative half-width <= 0.5. Draws: 40 for the cheap measures, 8 for the discriminator.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from degradx.data.audit import CleaningRule
from degradx.fitting.profile import ChannelRule, prepare_units
from degradx.generator.state import spec_from_declarations
from degradx.metrics import fidelity as F
from degradx.models.lstm import train_regressor
from degradx.utils.config import load_declarations
from degradx.utils.seeding import rng

ROOT = Path(__file__).resolve().parents[3]
decl = load_declarations()
ds, qn, L = "MATR", 1.1, 24
prof = json.loads((ROOT / f"artifacts/s3_fit_profiles/profiles/{ds}.json").read_text())
chans = prof["declared_used"]["channels_available"]
split = pd.read_csv(ROOT / f"artifacts/s3_fit_profiles/tables/split_{ds}.csv")
df = pd.read_csv(ROOT / f"data/processed/cycle_tables/{ds}.csv.gz", low_memory=False)
spec = spec_from_declarations(decl, qn)
rule, cr = CleaningRule("D12", isolated_excursion_frac=0.05, drop_recovered_collapse=True), ChannelRule(0.05)
fit_u = prepare_units(df, split[split.split == "fitting"].cell_id, qn, spec, rule, chans, cr)
ho_u = prepare_units(df, split[split.split == "held_out"].cell_id, qn, spec, rule, chans, cr)
ms_fit, ms_ho = F.measured_series(fit_u, chans), F.measured_series(ho_u, chans)
gen = pickle.loads((ROOT / f"data/generated/{ds}/seed0.pkl").read_bytes())[0]
cfg = yaml.safe_load((ROOT / "configs/models/lstm.yaml").read_text())
n_tr = sum(s.T is not None for s in ms_fit)
# TSTR per-unit errors
Xm, Um, Rm = F.windows(ms_fit, L, with_rul=True, with_elapsed=True)
Xg, Ug, Rg = F.windows(F.generated_series(gen[:n_tr], len(chans)), L, with_rul=True, with_elapsed=True)
Xh, Uh, Rh = F.windows(ms_ho, L, with_rul=True, with_elapsed=True)
trtr = train_regressor(Xm, Rm, Um, seed=0, device="cuda", cfg=cfg)
tstr = train_regressor(Xg, Rg, Ug, seed=0, device="cuda", cfg=cfg)
units, sa, n = F.per_unit_sse(tstr.predict(Xh), Rh, Uh)
_, sb, _ = F.per_unit_sse(trtr.predict(Xh), Rh, Uh)
# representations
Wf, Uf, _ = F.windows(ms_fit, L, max_per_unit=100, seed=0)
Wh, Uhw, _ = F.windows(ms_ho, L, max_per_unit=100, seed=0)
Wg, Ugw, _ = F.windows(F.generated_series(gen, len(chans)), L, max_per_unit=100, seed=0)
flat = Wf.reshape(-1, Wf.shape[-1]); mu, sd = flat.mean(0), np.where(flat.std(0) > 0, flat.std(0), 1)
enc, _ = F.train_encoder(Wf, mu, sd, seed=0, device="cuda")
rep_h, rep_g = F.encode(enc, Wh, mu, sd), F.encode(enc, Wg, mu, sd)
C_g = F.channel_correlation(Wg, mu, sd)
full = {"tstr_ratio": float(np.sqrt(sa.sum() / n.sum()) / np.sqrt(sb.sum() / n.sum())),
        "frechet": F.frechet_distance(rep_g[: len(rep_h)], rep_h),
        "cov_rel_frob": F.covariance_agreement(F.channel_correlation(Wh, mu, sd), C_g)["relative_frobenius"]}
full["disc_error"] = F.discriminative_score(Wh, Uhw, Wg, Ugw, mu, sd, seed=0, device="cuda")["discriminative_error"]
g = rng(11, "bootstrap", "D02b")
ho_ids = np.unique(Uhw)
out = {"full": full, "held_out_units": int(len(ho_ids)), "curves": {}}
for m in (3, 5, 8, 12, 20):
    vals = {"tstr_ratio": [], "frechet": [], "cov_rel_frob": [], "disc_error": []}
    for d in range(40):
        pick_t = g.choice(len(units), size=min(m, len(units)), replace=False)
        vals["tstr_ratio"].append(float(np.sqrt(sa[pick_t].sum() / n[pick_t].sum()) / np.sqrt(sb[pick_t].sum() / n[pick_t].sum())))
        pick = g.choice(ho_ids, size=min(m, len(ho_ids)), replace=False)
        sel = np.isin(Uhw, pick)
        vals["frechet"].append(F.frechet_distance(rep_g[g.choice(len(rep_g), sel.sum(), replace=False)], rep_h[sel]))
        vals["cov_rel_frob"].append(F.covariance_agreement(F.channel_correlation(Wh[sel], mu, sd), C_g)["relative_frobenius"])
        if d < 8:
            vals["disc_error"].append(F.discriminative_score(Wh[sel], Uhw[sel], Wg, Ugw, mu, sd, seed=100 + d, device="cuda")["discriminative_error"])
    out["curves"][m] = {k: {"relative_half_width_95": float((np.quantile(v, 0.975) - np.quantile(v, 0.025)) / 2 / abs(full[k])) if full[k] else None,
                            "median": float(np.median(v)), "draws": len(v)} for k, v in vals.items()}
    print(m, {k: round(v["relative_half_width_95"], 3) for k, v in out["curves"][m].items()}, flush=True)
Path(__file__).with_name("result.json").write_text(json.dumps(out, indent=1))
print("full", full)
