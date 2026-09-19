"""The Control Gap Index (paper Section 7).

CGI_s(t) = ln[K_s(t) / K_s(t0)] - ln[Gamma_s(t) / Gamma_s(t0)] is the log
hazard ratio relative to a reference year. The unknown scale kappa_s cancels,
so nothing here needs an absolute probability.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .hazard import Elasticities, Scenario, index_factor, index_term


def consequential_capability(nu, C, A, O, X, M=1.0, theta: Elasticities = Elasticities(), gates=None):
    """K = nu * C^theta_C * A^theta_A * O^theta_O * X^theta_X * M^theta_M."""
    return np.asarray(nu, dtype=float) * index_term(C, A, O, X, M, theta, gates)


def control_resilience(V: ArrayLike, p_I: ArrayLike):
    """Gamma = 1 / (V * p_I): the factor by which defences and recovery cut the hazard."""
    product = np.asarray(V, dtype=float) * np.asarray(p_I, dtype=float)
    if np.any(product <= 0):
        raise ValueError("Gamma is undefined when V * p_I = 0: the hazard is zero and the CGI has no reference")
    return 1.0 / product


def control_gap_index(K: ArrayLike, Gamma: ArrayLike, ref: int = 0):
    """CGI along the last (time) axis, relative to the sample at index ``ref``.

    K and Gamma must be strictly positive at the reference time. Under
    Specification I the index is invariant to rescaling an index but not to
    shifting its zero; with threshold gates it is not invariant to either.
    """
    K, Gamma = np.broadcast_arrays(np.asarray(K, dtype=float), np.asarray(Gamma, dtype=float))
    K0, G0 = K[..., ref], Gamma[..., ref]
    if np.any(K0 <= 0) or np.any(G0 <= 0):
        raise ValueError("K and Gamma must be strictly positive at the reference time")
    return np.log(K / K0[..., None]) - np.log(Gamma / G0[..., None])


def cgi_contributions(scenario: Scenario, ref: int = 0) -> dict[str, np.ndarray]:
    """Split a scenario's CGI into the part due to each term. The parts sum to the CGI.

    Keys are ``nu``, the five indices, ``V`` and ``p_I``. Positive values push
    the hazard up. Because the indices are bounded by 1 and episode counts are
    not, ``nu`` tends to dominate over long horizons.
    """
    terms = {"nu": np.asarray(scenario.nu, dtype=float)}
    for name, value in scenario.effective.items():
        terms[name] = index_factor(name, value, scenario.theta, scenario.gates)
    terms["V"] = scenario.V
    terms["p_I"] = np.asarray(scenario.p_I, dtype=float)
    shape = np.broadcast_shapes(*(np.shape(v) for v in terms.values()))
    if not shape:
        raise ValueError("at least one scenario field must be a time series")
    out = {}
    for name, value in terms.items():
        value = np.broadcast_to(value, shape)
        if np.any(value[..., ref] <= 0):
            raise ValueError(f"{name} must be strictly positive at the reference time")
        out[name] = np.log(value / value[..., ref, None])
    return out


def scenario_cgi(scenario: Scenario, ref: int = 0):
    """CGI for a :class:`Scenario` whose fields are time series."""
    return sum(cgi_contributions(scenario, ref).values())


def cgi_slope(t: ArrayLike, cgi: ArrayLike) -> float:
    """Least-squares slope of the CGI per unit time. The slope is the signal."""
    return float(np.polyfit(np.asarray(t, dtype=float), np.asarray(cgi, dtype=float), 1)[0])


def hazard_growth(slope: float) -> float:
    """Annual hazard growth implied by a CGI slope, exp(slope) - 1."""
    return float(np.expm1(slope))
