"""Generator, paper Eq. 1-3 (own code: benchmark-specific, brief R2).

A generated unit draws a fitting unit j of the profile (declarations theta_distribution: empirical resampling of unit
vectors; the family parameters, q1, and the unit's noise and pattern rates are taken jointly) and builds:

  trajectory   y(n) = family(theta_j, n) for n = 1, 2, ...  (capacity over q1_j, as fitted from t1 to EOL)
  state        z_n = max(0, (Q_ref - Q(n)) / (Q_ref - rho q_nom)), Q(n) = q1_j y(n), Q_ref = max of Q over the first 20
               positions (D18: Eq. 3 read on the generated trajectory; clipped at the
               pristine level before the early-life reference);  T = min{n : z_n >= 1}  (no record-end rule: not truncated)
  mean         m_{n,c} = phi_c(z_n)  (capacity: the shared affine mapping; others: isotonic + PCHIP)          (Eq. 2)
  patterns     enabled types only, capacity channel only: Poisson count with the unit's per-position rate over T
               positions; (amplitude, duration) resampled jointly from the profile's detected events of that type;
               start uniform; raised-cosine shape A sin^2(pi (j+1)/(D+1)), j = 0..D-1; truncated at T
  noise        per channel stationary AR(1) with the unit's (variance, lag-1) estimate, pooled estimate if missing
  null         null_flat: AR(1), unit variance, lag-1 = the profile's pooled capacity-noise lag-1; null_permuted: i.i.d.
               draws from the pooled measured charge-time readings of the fitting split
  observation  x = m + sum_k p + eps   (Eq. 1); null channels are their own values

Everything a unit needs for the targets is returned separately (m, p, eps, z, T), so the attribution ground truth, the
pattern-free counterpart window (x - p) and the transfer target are exact by construction. All randomness comes from
one generator seeded per (profile, generation seed, unit index); a unit regenerated with patterns disabled shares every
other draw (patterns use their own child stream).

v2 (brief "DegradX v2", declarations r3 declared_by_design.v2; active only for a profile fitted with offsets, so v1
profiles generate exactly as before):
  X2 mean      capacity m = Q_ref - z (Q_ref - rho q_nom) with the unit's own early-life reference Q_ref (D18: max of its
               generated trajectory over the first k positions; so m equals the trajectory exactly); other measured
               channels m = phi_c(z) + delta_{c,j} with the resampled unit's offsets; the state part phi_c(z) (capacity:
               the profile-level affine mapping at q1_bar) is kept as ``m_state`` so the offset contribution is exact
  X3 noise     measured channels drawn jointly (one child stream 'noise_joint'): AR(1) per channel with the unit's own
               (variance, lag-1); ONE innovation correlation per profile, r_eps = r (1 - phi_i phi_j) / sqrt(...) from the
               within-unit residual correlation r (after X2) and the pooled lag-1 coefficients, repaired to the nearest
               correlation matrix when not positive definite (declarations v2.correlated_noise)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from degradx.fitting.families import FAMILIES
from degradx.fitting.noise_mappings import Mapping, ar1_joint_sample, ar1_sample, innovation_correlation, is_positive_definite, nearest_correlation
from degradx.utils.seeding import derive_seed

NULL_CHANNELS = ("null_flat", "null_permuted")


@dataclass
class Profile:
    name: str
    q_nom: float
    rho: float
    family: str
    theta_units: list[dict]
    channels: list[str]                  # measured channels, capacity first
    mappings: dict[str, Mapping]
    noise_pooled: dict[str, dict]
    pattern_types: dict[str, dict]       # E6 with 'enabled', amplitude_Ah, duration, rate_per_position_by_unit
    weighted: list[str]
    x0: dict[str, float]
    null_pool: np.ndarray                # measured charge-time readings for null_permuted
    max_length_factor: float = 3.0
    # v2 (X2/X3); None on v1 profiles
    offsets_by_unit: dict | None = None  # cell_id -> {channel: delta}
    capacity_per_unit: bool = False      # capacity mapping affine with the unit's own q1 (X2)
    noise_corr: np.ndarray | None = None # fitted within-unit residual correlation over measured channels (X3)

    def __post_init__(self):
        self.innov_corr, self.innov_repair = None, None
        if self.noise_corr is not None:  # X3: one profile-level innovation correlation at the pooled lag-1 coefficients
            phis = np.array([self.noise_pooled[c]["phi"] for c in self.channels], float)
            r_eps = innovation_correlation(self.noise_corr, phis)
            repaired = not is_positive_definite(r_eps)
            self.innov_corr = nearest_correlation(r_eps) if repaired else r_eps
            phi_c = np.clip(phis, -0.999, 0.999)
            B = np.sqrt(np.outer(1 - phi_c ** 2, 1 - phi_c ** 2)) / (1 - np.outer(phi_c, phi_c))
            self.innov_repair = {"repaired": bool(repaired), "max_abs_entry_change": float(np.max(np.abs(self.innov_corr - r_eps))),
                                 "max_abs_stationary_change": float(np.max(np.abs(self.innov_corr - r_eps) * B)),
                                 "innovation_correlation_unrepaired": r_eps.tolist(), "innovation_correlation": self.innov_corr.tolist()}

    @property
    def all_channels(self) -> list[str]:
        return list(self.channels) + list(NULL_CHANNELS)

    @classmethod
    def from_json(cls, prof: dict, null_pool: np.ndarray) -> "Profile":
        e = prof["estimated_from_data"]
        maps = {}
        for c, d in e["E3_channel_mappings"].items():
            maps[c] = Mapping(c, np.asarray(d["grid"]), np.asarray(d["values"]), bool(d["increasing"]), d["kind"])
        x0 = {c: float(v) for c, v in prof["derived"]["reference_point_x0"].items()}
        x0["null_flat"] = 0.0
        x0["null_permuted"] = float(np.median(null_pool))
        v2 = prof.get("v2") or {}
        offsets = {u["cell_id"]: u["offsets"] for u in e["E1_theta_distribution"]["per_unit"]} if v2.get("per_unit_offsets") else None
        corr = np.asarray(v2["within_unit_correlation"], float) if v2.get("correlated_noise") else None
        return cls(prof["dataset"], float(prof["declared_used"]["q_nom_Ah"]), float(prof["declared_used"]["rho"]),
                   e["E1_theta_distribution"]["family"], e["E1_theta_distribution"]["per_unit"], list(prof["declared_used"]["channels_available"]),
                   maps, e["E5_noise"], e["E6_patterns"], list(prof["derived"]["channel_roles"]["weighted"]), x0, np.asarray(null_pool, float),
                   offsets_by_unit=offsets, capacity_per_unit=bool(v2.get("per_unit_offsets")), noise_corr=corr)


@dataclass
class GeneratedUnit:
    profile: str
    index: int
    source_unit: str
    T: int
    z: np.ndarray            # (T,)
    m: np.ndarray            # (T, C) mean component, null channels zero
    p: np.ndarray            # (T,) summed inserted patterns on the capacity channel
    eps: np.ndarray          # (T, C) noise (null channels: their whole value)
    patterns: list[dict]
    channels: list[str]
    m_state: np.ndarray | None = None   # v2: phi_c(z) without offsets (capacity: profile-level affine); None on v1 units
    q1: float | None = None             # v2: the unit's capacity early-life reference Q_ref used by its mapping (D18)

    @property
    def x(self) -> np.ndarray:
        x = self.m + self.eps
        x[:, 0] = x[:, 0] + self.p
        return x

    @property
    def x_pattern_free(self) -> np.ndarray:
        return self.m + self.eps

    @property
    def R(self) -> np.ndarray:
        return self.T - np.arange(1, self.T + 1)


def _state_from_theta(prof: Profile, u: dict, n_max: int, with_ref: bool = False):
    pos = np.arange(1, n_max + 1, dtype=float)
    Q = float(u["q1"]) * FAMILIES[prof.family](np.asarray(u["family_params"], float), pos)  # capacity trajectory [Ah]
    # D18: Eq. 3's early-life reference taken on the generated trajectory itself (max over the first k = 20 positions);
    # z = 1 still falls where Q = rho q_nom, so T is unchanged, and z starts at the pristine level
    q_ref = float(Q[:20].max())
    z = (q_ref - Q) / (q_ref - prof.rho * prof.q_nom)
    z = np.maximum(z, 0.0)
    hit = np.flatnonzero(z >= 1.0)
    T = int(hit[0]) + 1 if hit.size else None
    return (z, T, q_ref) if with_ref else (z, T)


def generate_unit(prof: Profile, gen_seed: int, index: int, patterns_on: bool = True, noise_on: bool = True,
                  overrides: dict | None = None) -> GeneratedUnit | None:
    """One unit. ``overrides`` (S7 difficulty settings): noise_variance_multiplier, pattern_amplitude_multiplier,
    transition_sharpness_multiplier (exponent s on the state, z -> z^s), theta_unit (force a source unit)."""
    ov = overrides or {}
    g = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index))
    j = int(ov.get("theta_unit", g.integers(len(prof.theta_units))))
    u = prof.theta_units[j]
    n_max = int(prof.max_length_factor * float(u["T"]))
    z, T, q_ref = _state_from_theta(prof, u, n_max, with_ref=True)
    s = float(ov.get("transition_sharpness_multiplier", 1.0))
    if s != 1.0:  # sharpness of the transition: z -> z^s keeps z(1st) = 0, z(T) = 1 and T; s > 1 concentrates the fall late
        z = np.clip(z, 0.0, None) ** s
    if T is None or T < 2:
        return None
    z = z[:T]
    C = len(prof.channels) + len(NULL_CHANNELS)
    m = np.zeros((T, C))
    for ci, c in enumerate(prof.channels):
        m[:, ci] = prof.mappings[c](z)
    m_state, q1_unit = None, None
    if prof.capacity_per_unit or prof.offsets_by_unit is not None:  # v2 X2
        m_state = m.copy()
        q1_unit = float(q_ref)  # the unit's own early-life reference (D18), so m_cap equals its generated trajectory
        if prof.capacity_per_unit:
            m[:, 0] = q1_unit - z * (q1_unit - prof.rho * prof.q_nom)
        if prof.offsets_by_unit is not None:
            off = prof.offsets_by_unit[u["cell_id"]]
            for ci, c in enumerate(prof.channels):
                if c != "capacity":
                    m[:, ci] += float(off[c])
    # noise: independent child streams per channel so enabling/disabling patterns never changes the noise draws
    eps = np.zeros((T, C))
    vm = float(ov.get("noise_variance_multiplier", 1.0))
    nvar, nphi = [], []
    for ci, c in enumerate(prof.channels):
        nz = (u.get("noise") or {}).get(c) or {}
        var = nz.get("variance") if nz.get("variance") is not None and np.isfinite(nz.get("variance", np.nan)) else prof.noise_pooled[c]["variance"]
        phi = nz.get("phi") if nz.get("phi") is not None and np.isfinite(nz.get("phi", np.nan)) else prof.noise_pooled[c]["phi"]
        nvar.append(var * vm)
        nphi.append(phi)
    if prof.innov_corr is not None:  # v2 X3: measured channels drawn jointly with the profile's innovation correlation
        if noise_on:
            gj = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index, "noise_joint"))
            eps[:, :len(prof.channels)] = ar1_joint_sample(gj, T, np.asarray(nvar), np.asarray(nphi), prof.innov_corr)
    else:
        for ci, c in enumerate(prof.channels):
            gc = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index, "noise", c))
            eps[:, ci] = ar1_sample(gc, T, nvar[ci], nphi[ci]) if noise_on else 0.0
    gnf = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index, "null_flat"))
    eps[:, len(prof.channels)] = ar1_sample(gnf, T, 1.0, prof.noise_pooled["capacity"]["phi"])
    gnp = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index, "null_permuted"))
    eps[:, len(prof.channels) + 1] = gnp.choice(prof.null_pool, size=T, replace=True)
    # patterns
    p = np.zeros(T)
    pats = []
    if patterns_on:
        gp = np.random.default_rng(derive_seed(gen_seed, "generation", prof.name, index, "patterns"))
        am = float(ov.get("pattern_amplitude_multiplier", 1.0))
        for t, spec in prof.pattern_types.items():
            if not spec["enabled"] or not spec["amplitude_Ah"]:
                continue
            rate = float(spec["rate_per_position_by_unit"].get(u["cell_id"], np.nan))
            if not np.isfinite(rate):
                rate = float(spec["measured_rate_per_100"]) / 100.0
            n_events = gp.poisson(rate * T)
            for _ in range(n_events):
                e = int(gp.integers(len(spec["amplitude_Ah"])))
                A, D = float(spec["amplitude_Ah"][e]) * am, int(spec["duration"][e])
                start = int(gp.integers(1, T + 1))
                jj = np.arange(D)
                shape = A * np.sin(np.pi * (jj + 1) / (D + 1)) ** 2
                idx = start - 1 + jj
                keep = idx < T
                p[idx[keep]] += shape[keep]
                pats.append({"type": t, "start": start, "duration": D, "amplitude_Ah": A, "truncated": bool((~keep).any())})
    return GeneratedUnit(prof.name, index, u["cell_id"], T, z, m, p, eps, pats, prof.all_channels, m_state=m_state, q1=q1_unit)
