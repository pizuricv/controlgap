import numpy as np
import pytest

import controlgap as cg

# The worked example of paper Section 12.
EXAMPLE = cg.Scenario("illustrative", C=0.20, A=0.70, O=0.50, X=0.60, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)


def test_section_12_numbers():
    assert EXAMPLE.indices == pytest.approx(0.042)
    assert EXAMPLE.V == pytest.approx(0.19)
    assert EXAMPLE.factor == pytest.approx(0.00399)
    p = EXAMPLE.probability([0.01, 0.1, 1, 10], T=10)
    assert np.round(p * 100, 2) == pytest.approx([0.04, 0.40, 3.91, 32.90])


def test_vulnerability_floor():
    assert cg.residual_vulnerability([0.999, 0.999, 0.999], rho=0.02) == pytest.approx(0.02, abs=1e-8)
    assert cg.residual_vulnerability([0.5, 0.5], rho=0.0) == pytest.approx(0.25)


def test_irreversibility_race():
    assert cg.irreversibility(2.0, 2.0) == pytest.approx(0.5)
    assert cg.irreversibility(1.0, tau_rec=0.25) == pytest.approx(0.2)
    with pytest.raises(ValueError):
        cg.irreversibility(1.0)


def test_gate_keeps_conjunction_property():
    assert cg.threshold_gate(0.0, 0.5, 15) == pytest.approx(0.0)
    assert cg.threshold_gate(1.0, 0.5, 15) == pytest.approx(1.0)
    assert cg.threshold_gate(0.5, 0.5, 15) == pytest.approx(0.5)


def test_product_of_gates_is_low_when_both_below_threshold():
    gates = {"C": cg.Gate(0.5, 15), "A": cg.Gate(0.5, 15)}
    assert cg.index_term(0.1, 0.1, 1, 1, gates=gates) < 1e-4
    assert cg.index_term(0.9, 0.9, 1, 1, gates=gates) > 0.99


def test_zero_factor_gives_zero_hazard():
    assert cg.hazard(10.0, 0.0, 1, 1, 1, V=1, p_I=1) == 0.0


def test_hazard_path_and_competing_risks():
    t = np.linspace(0, 10, 101)
    lam = np.full((2, t.size), 0.01)  # two scenarios
    p = cg.catastrophe_probability(lam, t=t, scenario_axis=0)
    assert p == pytest.approx(1 - np.exp(-0.2))


def test_bilinear_exposure_recovers_scalar_model():
    assert cg.bilinear_exposure([0.2], [[1.0]], [0.6]) == pytest.approx(0.12)
    with pytest.raises(ValueError):
        cg.bilinear_exposure([0.2, 0.1], [[1.0, 1.0]], [0.6])


def test_indices_are_validated():
    with pytest.raises(ValueError):
        cg.index_term(1.2, 1, 1, 1)


def test_scenario_layers_can_be_time_series():
    t = np.arange(4)
    s = cg.Scenario("s", C=0.2, A=0.7, O=0.5, X=0.6, effectiveness=(0.6 + 0.05 * t, 0.5, 0.5), rho=0.1 + 0.01 * t, p_I=0.5)
    assert s.V.shape == (4,)
    assert s.V[0] == pytest.approx(0.19)
    assert cg.scenario_cgi(s).shape == (4,)


def test_degenerate_inputs_raise():
    with pytest.raises(ValueError):
        cg.irreversibility(0.0, 0.0)
    with pytest.raises(ValueError):
        cg.control_resilience(0.19, 0.0)


def test_propensity_defaults_to_worst_case_and_scales_hazard():
    base = dict(C=0.2, A=0.7, O=0.5, X=0.6, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)
    assert cg.Scenario("s", **base, M=0.25).factor == pytest.approx(EXAMPLE.factor / 4)


def test_coupling_makes_capability_matter_more_than_its_elasticity():
    def factor(C, coupling):
        return cg.Scenario("s", C=C, A=0.7, O=0.5, X=0.6, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5, coupling=coupling).factor

    def elasticity(coupling):
        return np.log(factor(0.202, coupling) / factor(0.2, coupling)) / np.log(1.01)

    assert elasticity(cg.Coupling()) == pytest.approx(1.0)
    assert elasticity(cg.Coupling(A=0.5, O=0.5, X=0.5, e=0.5, rho=0.5)) > 1.3
    assert factor(0.2, cg.Coupling()) == pytest.approx(EXAMPLE.factor)


def test_repr_is_short():
    assert repr(EXAMPLE) == "Scenario('illustrative', V=0.19, factor=0.00399)"
