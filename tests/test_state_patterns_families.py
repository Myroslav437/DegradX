import numpy as np

from degradx.fitting.families import FAMILIES, fit_family
from degradx.fitting.patterns import detect, pattern_mask
from degradx.generator.state import StateSpec, unit_state

SPEC = StateSpec(rho=0.8, q_nom=1.1, k=20, margin=0.05, sg_window=11, sg_polyorder=2)


def test_state_r2_endpoints_and_T():
    n = np.arange(1, 801)
    q = 1.08 - 0.25 * (n / 800) ** 2  # crosses 0.88 Ah once
    st = unit_state(q, SPEC)
    thr = 0.8 * 1.1
    assert st.T == int(np.flatnonzero(st.q_smooth <= thr)[0]) + 1
    assert abs(st.z[st.T - 1] - 1) < 0.01 and st.z[st.T - 2] < 1
    assert st.q1 == st.q_smooth[:20].max()
    assert not st.excluded_by_guard


def test_state_T_independent_of_k():
    n = np.arange(1, 801)
    q = 1.05 + 0.02 * np.minimum(n, 50) / 50 - 0.3 * (n / 800) ** 2  # early rise
    t_values = {unit_state(q, StateSpec(**{**SPEC.__dict__, "k": k})).T for k in (1, 10, 20, 50)}
    assert len(t_values) == 1


def test_guard_excludes_unit_starting_near_threshold():
    q = np.full(300, 0.9)  # 0.9 - 0.88 = 0.02 < 0.05 * 1.1
    st = unit_state(q, SPEC)
    assert st.excluded_by_guard and st.T is None


def test_detect_runs_sign_and_min_length():
    r = 1e-3 * (-1.0) ** np.arange(400)  # bounded noise: never exceeds 2.5 * MAD scale
    r[100:104] += 0.02   # positive run of 4
    r[250] -= 0.02       # single outlier: below min run length
    r[300:303] -= 0.02   # negative run of 3
    pats, s = detect(r, k=2.5, m=2)
    signs = [(p.sign, p.start, p.duration) for p in pats if p.duration >= 3]
    assert (1, 101, 4) in signs and (-1, 301, 3) in signs
    assert not any(p.start == 251 and p.duration == 1 for p in pats)
    assert pattern_mask(400, pats)[100:104].all()


def test_families_recover_their_own_curves():
    pos = np.arange(1, 1001, dtype=float)
    truth = {"power_law": [1.0, 0.15, 2.0], "rollover": [1.0, -0.02, 0.7, 0.05, -0.8], "two_term_exponential": [1.0, -0.05, -0.002, 6.0]}
    for name, p in truth.items():
        y = FAMILIES[name](p, pos)
        fit = fit_family(name, pos, y)
        assert fit.rmse < 2e-3, (name, fit.rmse)


def test_record_end_rule_only_for_records_ending_at_threshold():
    n = np.arange(1, 1001)
    q = 1.08 - 0.1995 * (n / 1000) ** 3  # ends at 0.8805 Ah, never <= 0.88
    strict = unit_state(q, SPEC)
    assert strict.T is None
    tol = unit_state(q, StateSpec(**{**SPEC.__dict__, "record_end_tau": 0.01}))
    assert tol.T == 1000 and tol.T_from_record_end
    far = unit_state(q + 0.05, StateSpec(**{**SPEC.__dict__, "record_end_tau": 0.01}))
    assert far.T is None


def test_eol_search_starts_at_q1_position():
    q = np.concatenate([np.full(5, 0.85), np.linspace(1.08, 1.07, 30), np.linspace(1.07, 0.85, 400)])
    st = unit_state(q, SPEC)
    assert st.T is not None and st.T > st.t1 > 5
