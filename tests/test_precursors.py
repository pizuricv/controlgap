import pytest

from controlgap import precursors as pc
from controlgap import residual_vulnerability


def test_layer_effectiveness_posterior():
    est = pc.layer_effectiveness(stopped=60, challenges=100)
    assert est.mean == pytest.approx(61 / 102)
    lo, hi = est.interval(0.9)
    assert lo < 0.6 < hi


def test_race_rates():
    est = pc.race_rates(durations=[1, 2, 3, 4], escalated=[True, False, False, False])
    assert est.r_esc == pytest.approx(0.1)
    assert est.r_rec == pytest.approx(0.3)
    assert est.p_I == pytest.approx(0.25)


def test_conditional_scoring_accounts_for_common_cause():
    e, rho, p_I = [0.6, 0.5, 0.5], 0.1, 0.5
    # Nothing passed yet: the unconditional V * p_I.
    assert pc.conditional_catastrophe_probability([], e, rho, p_I) == pytest.approx(residual_vulnerability(e, rho) * p_I)
    # Having passed two layers makes a common-cause bypass more likely than the naive (1 - e3).
    scored = pc.conditional_catastrophe_probability(e[:2], e[2:], rho, p_I)
    assert scored > (1 - e[2]) * p_I
    assert scored == pytest.approx(0.19 / 0.28 * 0.5)


def test_estimates_feed_the_monte_carlo():
    from controlgap.mc import MCConfig, simulate

    est = pc.layer_effectiveness(stopped=42, challenges=60)
    weak = simulate(MCConfig(effectiveness=est), n=20_000).summary()
    strong = simulate(MCConfig(effectiveness=pc.layer_effectiveness(57, 60)), n=20_000).summary()
    assert strong["median"] < weak["median"]


def test_fit_elasticities_recovers_theta():
    import numpy as np

    rng = np.random.default_rng(0)
    n = 400
    nu = rng.uniform(1e4, 1e5, n)
    A, O = rng.uniform(0.1, 1, n), rng.uniform(0.1, 1, n)
    counts = rng.poisson(nu * 1e-3 * A**1.5 * O**0.7)
    fit = pc.fit_elasticities(counts, nu, {"A": A, "O": O})
    assert fit.theta["A"] == pytest.approx(1.5, abs=3 * fit.se["A"])
    assert fit.theta["O"] == pytest.approx(0.7, abs=3 * fit.se["O"])
    assert fit.se["A"] < 0.05
    assert fit.log_scale == pytest.approx(np.log(1e-3), abs=0.1)
    with pytest.raises(ValueError):
        pc.fit_elasticities(counts, nu, {"A": np.full(n, 0.5)})
