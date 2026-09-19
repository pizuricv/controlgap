import numpy as np
import pytest

import controlgap as cg


def test_section_15_dashboard():
    K_growth = 1.10 * 1.05 * 1.02 * 1.04 * 1.03
    assert K_growth == pytest.approx(1.26, abs=0.005)
    t = np.arange(6)
    cgi = cg.control_gap_index(K_growth**t, 1.06**t)
    slope = cg.cgi_slope(t, cgi)
    assert cgi[0] == 0.0
    assert slope == pytest.approx(0.17, abs=0.005)
    assert cg.hazard_growth(slope) == pytest.approx(0.19, abs=0.005)


def test_kappa_and_index_scale_cancel():
    t = np.arange(5)
    C = 0.2 * 1.1**t
    s = cg.Scenario("s", C=C, A=0.7, O=0.5, X=0.6, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)
    rescaled = cg.Scenario("s", C=C / 2, A=0.7, O=0.5, X=0.6, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)
    assert cg.scenario_cgi(s) == pytest.approx(cg.scenario_cgi(rescaled))
    # CGI equals the log hazard ratio for any lambda0
    assert cg.scenario_cgi(s) == pytest.approx(np.log(s.hazard(3.0) / s.hazard(3.0)[0]))


def test_reference_must_be_positive():
    with pytest.raises(ValueError):
        cg.control_gap_index([0.0, 1.0], [1.0, 1.0])


def test_contributions_sum_to_cgi_and_nu_dominates():
    t = np.arange(11)
    s = cg.Scenario("cyber", nu=1.10**t, C=np.minimum(0.2 * 1.05**t, 1), A=0.7, O=0.5, X=0.6,
                    effectiveness=(0.6 + 0.02 * t, 0.5, 0.5), rho=0.1, p_I=0.5)  # fmt: skip
    parts = cg.cgi_contributions(s)
    assert sum(parts.values()) == pytest.approx(np.log(s.nu * s.factor / (s.nu * s.factor)[0]))
    assert parts["nu"][-1] > parts["C"][-1] > 0 > parts["V"][-1]
    assert parts["A"][-1] == 0.0
