"""The scenario-specific hazard model (paper Sections 4-6 and 8).

Every function broadcasts over NumPy arrays, so the same code serves a single
point estimate, a time series, or a batch of Monte Carlo draws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike

# Capability, access, agency, exposure, and propensity (motive): whether the
# acting agent, human or AI, would attempt the harmful action.
INDEX_NAMES = ("C", "A", "O", "X", "M")


def residual_vulnerability(effectiveness: ArrayLike, rho: ArrayLike = 0.0, axis: int = -1):
    """Common-cause shock mixture, V = rho + (1 - rho) * prod(1 - e_l)  (Section 6.2).

    ``effectiveness`` holds the layer effectivenesses e_l along ``axis``.
    V has a floor at ``rho`` whatever the quality of the individual layers.
    The floor is a modelling hypothesis, not a derived result.
    """
    e = np.asarray(effectiveness, dtype=float)
    rho = np.asarray(rho, dtype=float)
    _check_unit(e, "effectiveness")
    _check_unit(rho, "rho")
    return rho + (1.0 - rho) * np.prod(1.0 - e, axis=axis)


def irreversibility(r_esc: ArrayLike, r_rec: ArrayLike | None = None, *, tau_rec: ArrayLike | None = None):
    """Race between escalation and recovery, p_I = r_esc / (r_esc + r_rec)  (Section 6.3).

    Give the recovery clock either as a rate ``r_rec`` or as a mean time
    ``tau_rec`` (r_rec = 1 / tau_rec). Both clocks are memoryless, which an
    adversary that times its escalation would violate.
    """
    if (r_rec is None) == (tau_rec is None):
        raise ValueError("give exactly one of r_rec or tau_rec")
    r_esc = np.asarray(r_esc, dtype=float)
    r_rec = np.asarray(r_rec, dtype=float) if r_rec is not None else 1.0 / np.asarray(tau_rec, dtype=float)
    if np.any(r_esc < 0) or np.any(r_rec < 0):
        raise ValueError("rates must be non-negative")
    if np.any(r_esc + r_rec == 0):
        raise ValueError("r_esc and r_rec cannot both be zero")
    return r_esc / (r_esc + r_rec)


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def threshold_gate(z: ArrayLike, z0: float, k: float):
    """Normalised sigmoid gate with g(0) = 0 and g(1) = 1  (Specification II, Section 6.5)."""
    z = np.asarray(z, dtype=float)
    lo = _sigmoid(-k * z0)
    return (_sigmoid(k * (z - z0)) - lo) / (_sigmoid(k * (1.0 - z0)) - lo)


@dataclass(frozen=True)
class Gate:
    """Threshold location ``z0`` and steepness ``k`` for one index."""

    z0: float
    k: float

    def __call__(self, z: ArrayLike):
        return threshold_gate(z, self.z0, self.k)


@dataclass(frozen=True)
class Elasticities:
    """Exponents theta of Specification I. The default of 1 is the paper's prior."""

    C: float = 1.0
    A: float = 1.0
    O: float = 1.0
    X: float = 1.0
    M: float = 1.0


@dataclass(frozen=True)
class Coupling:
    """How strongly capability erodes the other terms (Section 6.7).

    A capable system can acquire access, agency and exposure for itself, and
    can evade or defeat its own oversight. Each coefficient g in [0, 1] sets
    how far full capability (C = 1) pushes that term towards its worst value:

        A_eff = 1 - (1 - A)(1 - g_A C)      likewise O, X and rho
        e_eff = e (1 - g_e C)

    All zeros recovers the separable model. The functional form is a
    hypothesis; the coefficients have to come from evaluations.
    """

    A: float = 0.0
    O: float = 0.0
    X: float = 0.0
    e: float = 0.0
    rho: float = 0.0

    def __post_init__(self):
        for name in ("A", "O", "X", "e", "rho"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"coupling {name} must lie in [0, 1]")


def lifted(value: ArrayLike, C: ArrayLike, g: float):
    """Push ``value`` towards 1 as capability rises: 1 - (1 - value)(1 - g C)."""
    return 1.0 - (1.0 - np.asarray(value, dtype=float)) * (1.0 - g * np.asarray(C, dtype=float))


def eroded(value: ArrayLike, C: ArrayLike, g: float):
    """Push ``value`` towards 0 as capability rises: value (1 - g C)."""
    return np.asarray(value, dtype=float) * (1.0 - g * np.asarray(C, dtype=float))


def index_factor(name: str, value: ArrayLike, theta: Elasticities = Elasticities(), gates: Mapping[str, Gate] | None = None):
    """One index's contribution to the hazard: its gate if it has one, else value^theta."""
    value = np.asarray(value, dtype=float)
    _check_unit(value, name)
    if gates and name in gates:
        return gates[name](value)
    return value ** getattr(theta, name)


def index_term(C, A, O, X, M=1.0, theta: Elasticities = Elasticities(), gates: Mapping[str, Gate] | None = None):
    """C^theta_C * A^theta_A * O^theta_O * X^theta_X * M^theta_M, with optional threshold gates.

    Any index named in ``gates`` uses its gate instead of its power term, which
    turns Specification I into Specification II. Gating C and A gives the
    paper's product of gates. ``M = 1`` is the worst case: the agent always tries.
    """
    unknown = set(gates or {}) - set(INDEX_NAMES)
    if unknown:
        raise ValueError(f"unknown index in gates: {sorted(unknown)}")
    out = 1.0
    for name, value in zip(INDEX_NAMES, (C, A, O, X, M)):
        out = out * index_factor(name, value, theta, gates)
    return out


def bilinear_exposure(c: ArrayLike, W: ArrayLike, x: ArrayLike):
    """Vector form of the capability-exposure term, c^T W x  (Section 8).

    ``W`` must be non-negative and sum to 1, which keeps the term in [0, 1] and
    recovers the scalar model as a special case. Use the result in place of the
    product C * X (pass it as ``C`` with ``X = 1``).
    """
    c, W, x = (np.asarray(v, dtype=float) for v in (c, W, x))
    if np.any(W < 0) or not np.isclose(W.sum(), 1.0):
        raise ValueError("W must be non-negative and sum to 1")
    _check_unit(c, "c")
    _check_unit(x, "x")
    return c @ W @ x


def hazard(lambda0, C, A, O, X, V, p_I, M=1.0, theta: Elasticities = Elasticities(), gates: Mapping[str, Gate] | None = None):
    """lambda_s = lambda0 * index term * V * p_I  (Sections 6.4 and 6.5).

    ``lambda0 = nu * kappa`` is the baseline rate: events per year at maximal
    indices, with no defences and certain escalation.
    """
    return np.asarray(lambda0, dtype=float) * index_term(C, A, O, X, M, theta, gates) * V * p_I


def catastrophe_probability(lam: ArrayLike, T: float | None = None, *, t: ArrayLike | None = None, scenario_axis: int | None = None):
    """P(D_T) = 1 - exp(-integral of the total hazard)  (Section 4).

    For a constant hazard, give the horizon ``T``. For a hazard path sampled at
    times ``t`` (last axis), the integral uses the trapezoid rule. If
    ``scenario_axis`` is given, cause-specific hazards are summed along it
    first, which relies on the paper's partition rule.
    """
    if (T is None) == (t is None):
        raise ValueError("give exactly one of T (constant hazard) or t (hazard path)")
    lam = np.asarray(lam, dtype=float)
    if np.any(lam < 0):
        raise ValueError("hazard must be non-negative")
    if scenario_axis is not None:
        lam = lam.sum(axis=scenario_axis)
    cumulative = lam * T if t is None else np.trapezoid(lam, np.asarray(t, dtype=float), axis=-1)
    return -np.expm1(-cumulative)


@dataclass(repr=False)
class Scenario:
    """One catastrophe scenario. Fields may be scalars or arrays over time."""

    name: str
    C: ArrayLike
    A: ArrayLike
    O: ArrayLike
    X: ArrayLike
    effectiveness: ArrayLike  # one entry per layer, each a scalar or a time series
    rho: ArrayLike = 0.0
    p_I: ArrayLike = 1.0
    M: ArrayLike = 1.0
    nu: ArrayLike = 1.0
    theta: Elasticities = field(default_factory=Elasticities)
    gates: Mapping[str, Gate] | None = None
    coupling: Coupling = field(default_factory=Coupling)

    @property
    def effective(self) -> dict[str, np.ndarray]:
        """The five indices after capability coupling (identical to the inputs when coupling is zero)."""
        g = self.coupling
        return {
            "C": np.asarray(self.C, dtype=float),
            "A": lifted(self.A, self.C, g.A),
            "O": lifted(self.O, self.C, g.O),
            "X": lifted(self.X, self.C, g.X),
            "M": np.asarray(self.M, dtype=float),
        }

    @property
    def effective_layers(self) -> list[np.ndarray]:
        """Layer effectivenesses after capability coupling."""
        return [eroded(e, self.C, self.coupling.e) for e in self.effectiveness]

    @property
    def effective_rho(self):
        """Common-mode rate after capability coupling."""
        return lifted(self.rho, self.C, self.coupling.rho)

    @property
    def V(self):
        return residual_vulnerability(np.stack(np.broadcast_arrays(*self.effective_layers)), self.effective_rho, axis=0)

    @property
    def indices(self):
        return index_term(**self.effective, theta=self.theta, gates=self.gates)

    @property
    def factor(self):
        """Index term * V * p_I. This is *not* a probability (Section 12)."""
        return self.indices * self.V * self.p_I

    def hazard(self, lambda0: ArrayLike):
        return np.asarray(lambda0, dtype=float) * self.factor

    def probability(self, lambda0: ArrayLike, T: float):
        return catastrophe_probability(self.hazard(lambda0), T)

    def __repr__(self) -> str:
        factor = np.atleast_1d(self.factor)
        if factor.size == 1:
            return f"Scenario({self.name!r}, V={float(np.atleast_1d(self.V)[0]):.3g}, factor={factor[0]:.3g})"
        return f"Scenario({self.name!r}, {factor.size} time steps, factor {factor[0]:.3g} -> {factor[-1]:.3g})"


def _check_unit(value: np.ndarray, name: str) -> None:
    if np.any(value < 0) or np.any(value > 1):
        raise ValueError(f"{name} must lie in [0, 1]")
