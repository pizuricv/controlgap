"""Calibration from precursor data (paper Section 9).

No irreversible AI catastrophe has occurred, so the control-side parameters
have to come from lower-severity events on the same causal chain: red-team
results, incidents and near-misses. These estimators cover the quantities
Section 9.2 says can already be tracked.

All of this assumes that precursors share the catastrophe's elasticities
(Section 9.1). That assumption is the known weak point of precursor analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
from scipy import stats

from .hazard import residual_vulnerability


@dataclass(frozen=True)
class BetaEstimate:
    """Beta posterior for a probability."""

    a: float
    b: float

    def __iter__(self):
        """Unpack as (a, b), so an estimate can be used wherever MCConfig takes Beta parameters."""
        return iter((self.a, self.b))

    @property
    def mean(self) -> float:
        return self.a / (self.a + self.b)

    def interval(self, level: float = 0.9) -> tuple[float, float]:
        lo, hi = stats.beta.ppf([(1 - level) / 2, (1 + level) / 2], self.a, self.b)
        return float(lo), float(hi)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.beta(self.a, self.b, size=n)


def _beta_posterior(successes: int, trials: int, prior: tuple[float, float]) -> BetaEstimate:
    if not 0 <= successes <= trials:
        raise ValueError("need 0 <= successes <= trials")
    return BetaEstimate(prior[0] + successes, prior[1] + trials - successes)


def layer_effectiveness(stopped: int, challenges: int, prior: tuple[float, float] = (1.0, 1.0)) -> BetaEstimate:
    """e_l from red-team or incident counts: events the layer stopped, of those that reached it."""
    return _beta_posterior(stopped, challenges, prior)


def common_mode_rate(full_bypasses: int, challenges: int, prior: tuple[float, float] = (1.0, 1.0)) -> BetaEstimate:
    """rho from the share of challenges that defeated every layer at once.

    Count only bypasses with a shared cause (one blind spot, one credential).
    Coincident independent failures belong to the layer effectivenesses.
    """
    return _beta_posterior(full_bypasses, challenges, prior)


@dataclass(frozen=True)
class RaceEstimate:
    r_esc: float
    r_rec: float

    @property
    def p_I(self) -> float:
        return self.r_esc / (self.r_esc + self.r_rec)

    @property
    def tau_rec(self) -> float:
        return 1.0 / self.r_rec


def race_rates(durations: ArrayLike, escalated: ArrayLike) -> RaceEstimate:
    """Maximum-likelihood escalation and recovery rates from incident records.

    Each incident contributes its duration until it either escalated or was
    recovered, and a flag for which happened first. With competing exponential
    clocks the estimate of each rate is its event count over total time at risk.
    """
    durations = np.asarray(durations, dtype=float)
    escalated = np.asarray(escalated, dtype=bool)
    if durations.shape != escalated.shape or durations.size == 0:
        raise ValueError("durations and escalated must be non-empty and the same shape")
    if np.any(durations <= 0):
        raise ValueError("durations must be positive")
    exposure = durations.sum()
    return RaceEstimate(r_esc=escalated.sum() / exposure, r_rec=(~escalated).sum() / exposure)


def conditional_catastrophe_probability(passed: ArrayLike, remaining: ArrayLike, rho: float, p_I: float) -> float:
    """Score a precursor, in the manner of the NRC's conditional core-damage probability.

    Given an event that already got past the layers with effectivenesses
    ``passed``, return the probability that it would also have defeated the
    ``remaining`` layers and then escalated beyond recovery.

    Passing layers is evidence of a common-cause bypass, so the answer is
    V(all layers) / V(passed layers) * p_I, not simply prod(1 - e_remaining) * p_I.

    The identity is exact under the shock mixture, but it carries four
    assumptions worth stating:

    1. the common cause is all-or-nothing across every layer. If the bypass is
       known to be specific to one layer -- the usual diagnostic situation --
       the update goes the other way, and this returns too high a number;
    2. ``p_I`` does not depend on how the layers were defeated. A shock that
       takes all of them at once plausibly escalates faster, so this is
       conservative by an unstated amount;
    3. the event genuinely challenged every layer counted as passed;
    4. the score ignores that a near-miss is, by construction, an event
       something later caught. That is the intended counterfactual, but it is
       a modelling choice rather than an identity.

    It is also not what the NRC computes. An ASP score re-runs the plant model
    with the observed component states fixed; this installs a generic
    shared-cause prior instead.
    """
    passed = np.asarray(passed, dtype=float)
    everything = np.concatenate([passed, np.asarray(remaining, dtype=float)])
    return float(residual_vulnerability(everything, rho) / residual_vulnerability(passed, rho) * p_I)


@dataclass(frozen=True)
class ElasticityFit:
    theta: dict[str, float]
    se: dict[str, float]
    log_scale: float  # ln of the per-episode precursor probability at indices of 1

    def interval(self, name: str, z: float = 1.645) -> tuple[float, float]:
        return self.theta[name] - z * self.se[name], self.theta[name] + z * self.se[name]


def fit_elasticities(counts: ArrayLike, nu: ArrayLike, indices: dict[str, ArrayLike], iterations: int = 50) -> ElasticityFit:
    """Estimate the elasticities theta from precursor counts (paper Sections 9.1 and 11).

    Poisson regression with a log link and ln(nu) as offset:

        E[count] = nu * exp(log_scale) * prod(index ** theta)

    Each observation is one period or deployment, with its precursor count,
    its episode count ``nu`` and its index values. The indices must vary across
    observations, and not in lockstep, or theta is not identified. The result
    describes precursors. Carrying it over to catastrophes is the
    shared-elasticities assumption of Section 9.1.
    """
    y = np.asarray(counts, dtype=float)
    offset = np.log(np.asarray(nu, dtype=float) * np.ones_like(y))
    names = list(indices)
    logs = [np.log(np.asarray(indices[k], dtype=float) * np.ones_like(y)) for k in names]
    X = np.column_stack([np.ones_like(y), *logs])
    if np.linalg.matrix_rank(X) < X.shape[1]:
        raise ValueError("indices are constant or collinear across observations, so theta is not identified")
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(max(y.sum(), 0.5) / np.exp(offset).sum())
    for _ in range(iterations):  # Newton's method on the Poisson log-likelihood
        mu = np.exp(offset + X @ beta)
        step = np.linalg.solve(X.T @ (mu[:, None] * X), X.T @ (y - mu))
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    mu = np.exp(offset + X @ beta)
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ (mu[:, None] * X))))
    return ElasticityFit(dict(zip(names, beta[1:].tolist())), dict(zip(names, se[1:].tolist())), float(beta[0]))
