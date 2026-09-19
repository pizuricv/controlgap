import pytest

import controlgap as cg
from controlgap.levers import GROUPS, LEVERS, Lever, apply_levers

BASE = dict(C=0.2, A=0.7, O=0.5, X=0.6, M=1.0, e0=0.6, e1=0.5, e2=0.5, rho=0.1, r_esc=1.0, tau=1.0, nu=1.0)


def hazard(v):
    s = cg.Scenario("s", C=v["C"], A=v["A"], O=v["O"], X=v["X"], M=v["M"], effectiveness=(v["e0"], v["e1"], v["e2"]),
                    rho=v["rho"], p_I=cg.irreversibility(v["r_esc"], tau_rec=v["tau"]))  # fmt: skip
    return v["nu"] * s.factor


def test_catalogue_covers_the_three_drivers():
    assert GROUPS == ("Model advances", "Governments", "Open source")
    assert apply_levers(BASE, {}) == BASE


def test_direction_of_each_lever():
    raises = {"Frontier capability jump", "Agentic deployment boom", "Open weights: proliferation"}
    for lever in LEVERS:
        ratio = hazard(apply_levers(BASE, {lever.name: 1.0})) / hazard(BASE)
        assert (ratio > 1) == (lever.name in raises), lever.name


def test_open_weights_net_effect_depends_on_the_defensive_side():
    both = {"Open weights: proliferation": 1.0, "Open weights: defensive ecosystem": 1.0}
    alone = hazard(apply_levers(BASE, {"Open weights: proliferation": 1.0}))
    assert hazard(BASE) < hazard(apply_levers(BASE, both)) < alone


def test_values_stay_in_range_and_strength_scales():
    out = apply_levers(BASE, {lever.name: 1.0 for lever in LEVERS})
    assert all(0 <= out[k] <= 1 for k in ("C", "A", "O", "X", "M", "e0", "e1", "e2", "rho"))
    half = apply_levers(BASE, {"Critical-infrastructure integration rules": 0.5})
    assert half["X"] == pytest.approx(0.6 * 0.85)


def test_validation():
    with pytest.raises(ValueError):
        apply_levers(BASE, {"No such lever": 1.0})
    with pytest.raises(ValueError):
        Lever("bad", "g", "d", {"Z": 0.1})
