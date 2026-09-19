import pytest

from controlgap.mc import MCConfig, simulate


def test_section_10_summary():
    ind = simulate(MCConfig(correlation=0.0)).summary()
    cor = simulate(MCConfig(correlation=0.6)).summary()
    assert ind["median"] == pytest.approx(0.002, rel=0.2)
    assert ind["mean"] == pytest.approx(0.0094, rel=0.05)
    assert cor["mean"] == pytest.approx(0.0121, rel=0.05)
    assert ind["orders_of_magnitude_90"] == pytest.approx(2.5, abs=0.15)
    # Correlation barely moves the median but fattens the upper tail.
    assert cor["median"] == pytest.approx(ind["median"], rel=0.1)
    assert cor["q95"] > ind["q95"]


def test_jensen_mean_probability_below_probability_at_mean_hazard():
    import numpy as np

    p = simulate(MCConfig(lambda0_median=5.0, lambda0_log_sd=0.5), n=50_000).probabilities
    lam_T = -np.log1p(-p)
    assert p.mean() < 1 - np.exp(-lam_T.mean())


def test_most_of_the_spread_is_the_lambda0_assumption():
    from controlgap.mc import spread_decomposition

    d = spread_decomposition(n=100_000)
    assert d["lambda0_only"] == pytest.approx(2 * 1.645 * 1.5 / 2.302585, abs=0.05)
    assert d["without_lambda0"] < d["lambda0_only"] < d["all"]


def test_uncertain_propensity_lowers_the_probability():
    means = dict(C=0.2, A=0.7, O=0.5, X=0.6, M=0.3)
    assert simulate(MCConfig(index_means=means), n=20_000).summary()["median"] < simulate(MCConfig(), n=20_000).summary()["median"]
