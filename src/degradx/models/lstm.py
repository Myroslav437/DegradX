"""LSTM regressor on windows (paper §3.6: one trained architecture; configs/models/lstm.yaml).

Inputs are windows (N, L, C) of channel values, standardised per channel with statistics of the training units only
(paper l.248); targets are standardised with training-unit statistics. Validation units are a unit-level split of the
training units (declarations statistics.splits.model_validation_from_training_units). Early stopping on validation MSE.
Deterministic under a fixed model-initialisation seed (cuDNN deterministic; S0 env.md).
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn

from degradx.utils.seeding import seed_everything


class LSTMRegressor(nn.Module):
    def __init__(self, n_inputs: int, hidden: int = 64, layers: int = 2, dropout: float = 0.0):
        super().__init__()
        self.lstm = nn.LSTM(n_inputs, hidden, num_layers=layers, batch_first=True, dropout=dropout if layers > 1 else 0.0)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)


@dataclass
class Standardiser:
    mean: np.ndarray
    std: np.ndarray
    y_mean: float
    y_std: float

    @classmethod
    def fit(cls, X: np.ndarray, y: np.ndarray) -> "Standardiser":
        flat = X.reshape(-1, X.shape[-1])
        mu = np.nanmean(flat, axis=0)
        sd = np.nanstd(flat, axis=0)
        sd = np.where(sd > 0, sd, 1.0)
        return cls(mu, sd, float(np.mean(y)), float(np.std(y)) if np.std(y) > 0 else 1.0)

    def x(self, X: np.ndarray) -> np.ndarray:
        return ((X - self.mean) / self.std).astype(np.float32)

    def y(self, y: np.ndarray) -> np.ndarray:
        return ((y - self.y_mean) / self.y_std).astype(np.float32)

    def y_inv(self, y: np.ndarray) -> np.ndarray:
        return y * self.y_std + self.y_mean


@dataclass
class TrainedModel:
    model: LSTMRegressor
    scaler: Standardiser
    history: dict = field(default_factory=dict)
    device: str = "cpu"

    def predict(self, X: np.ndarray, batch: int = 4096) -> np.ndarray:
        batch = min(batch, max(256, 100000 // X.shape[1]))
        self.model.eval()
        out = []
        with torch.no_grad():
            for i in range(0, len(X), batch):
                xb = torch.from_numpy(self.scaler.x(X[i:i + batch])).to(self.device)
                out.append(self.model(xb).float().cpu().numpy())
        return self.scaler.y_inv(np.concatenate(out)) if out else np.array([])


def train_regressor(X: np.ndarray, y: np.ndarray, unit_ids: np.ndarray, *, seed: int, device: str, cfg: dict,
                    val_fraction: float = 0.2, val_units=None, verbose: bool = False) -> TrainedModel:
    """Train with a unit-level validation split: ``val_units`` if given (e.g. the declared generated validation split),
    otherwise ``val_fraction`` of the training units drawn with the model seed."""
    seed_everything(seed)
    arch, tr = cfg["architecture"], cfg["training"]
    units = np.unique(unit_ids)
    if val_units is None:
        g = np.random.default_rng(seed)
        n_val = max(1, int(round(val_fraction * len(units)))) if len(units) > 1 else 0
        val_units = set(g.choice(units, size=n_val, replace=False)) if n_val else set()
    else:
        val_units = set(val_units)
    is_val = np.isin(unit_ids, list(val_units))
    Xtr, ytr, Xva, yva = X[~is_val], y[~is_val], X[is_val], y[is_val]
    scaler = Standardiser.fit(Xtr, ytr)
    model = LSTMRegressor(X.shape[-1], arch["hidden_size"], arch["num_layers"], arch.get("dropout", 0.0)).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=float(tr["learning_rate"]))
    lossf = nn.MSELoss()
    xt = torch.from_numpy(scaler.x(Xtr)).to(device)
    yt = torch.from_numpy(scaler.y(ytr)).to(device)
    xv = torch.from_numpy(scaler.x(Xva)).to(device) if len(Xva) else None
    yv = torch.from_numpy(scaler.y(yva)).to(device) if len(yva) else None
    bs, best, best_state, bad = int(tr["batch_size"]), np.inf, None, 0
    patience, max_epochs = int(tr["early_stopping"]["patience"]), int(tr["max_epochs"])
    hist = {"train": [], "val": [], "epochs": 0, "seconds": 0.0, "val_units": sorted(val_units)}
    gen = torch.Generator(device="cpu").manual_seed(seed)
    t0 = time.perf_counter()
    for epoch in range(max_epochs):
        model.train()
        perm = torch.randperm(len(xt), generator=gen).to(device)
        tot = 0.0
        for i in range(0, len(xt), bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            loss = lossf(model(xt[idx]), yt[idx])
            loss.backward()
            opt.step()
            tot += float(loss) * len(idx)
        hist["train"].append(tot / len(xt))
        if xv is not None:
            model.eval()
            with torch.no_grad():
                ch = max(256, 50000 // X.shape[1])  # windows per validation chunk, bounded for long windows (S7 L = 96 ran out of GPU memory at 8192)
                sse = sum(float(lossf(model(xv[i:i + ch]), yv[i:i + ch])) * len(yv[i:i + ch]) for i in range(0, len(xv), ch))
                vl = sse / len(xv)
            hist["val"].append(vl)
            if vl < best - 1e-6:
                best, best_state, bad = vl, copy.deepcopy(model.state_dict()), 0
            else:
                bad += 1
                if bad >= patience:
                    break
        if verbose:
            print(epoch, hist["train"][-1], hist["val"][-1] if hist["val"] else None)
    if best_state is not None:
        model.load_state_dict(best_state)
    hist["epochs"] = len(hist["train"])
    hist["seconds"] = time.perf_counter() - t0
    hist["best_val_mse_standardised"] = best
    return TrainedModel(model, scaler, hist, device)
