"""Monte Carlo propagation of uncertainty (paper Section 10).

The four indices are sampled jointly through a Gaussian copula with Beta
marginals, so that assuming independence is a choice rather than a default.
Results are per-draw *probabilities*: average those, never the hazards.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from scipy import stats

from .hazard import INDEX_NAMES, Elasticities, catastrophe_probability, index_term, residual_vulnerability


def beta_params(mean: float, concentration: float) -> tuple[float, float]:
    """Beta(a, b) with the given mean and concentration a + b."""
    if not 0 < mean < 1:
        raise ValueError("mean must lie strictly between 0 and 1")
    return mean * concentration, (1.0 - mean) * concentration


def sample_indices(means, concentration: float, correlation: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Draw (n, len(means)) index values with a common Gaussian-copula correlation."""
    d = len(means)
    cov = np.full((d, d), correlation, dtype=float)
    np.fill_diagonal(cov, 1.0)
    u = stats.norm.cdf(rng.multivariate_normal(np.zeros(d), cov, size=n))
    return np.column_stack([stats.beta.ppf(u[:, i], *beta_params(m, concentration)) for i, m in enumerate(means)])


@dataclass
class MCConfig:
    """Illustrative inputs of Section 10. Every value is an assumption, not data.

    Add an ``M`` entry to ``index_means`` to make propensity uncertain; without
    one it is fixed at its worst case, M = 1.
    """

    index_means: dict[str, float] = field(default_factory=lambda: dict(C=0.2, A=0.7, O=0.5, X=0.6))
    index_concentration: float = 12.0
    correlation: float = 0.0  # Gaussian-copula correlation between the four indices
    n_layers: int = 3
    effectiveness: tuple[float, float] = (6.0, 4.0)  # Beta(a, b), mean 0.6
    rho: tuple[float, float] = (2.0, 18.0)  # Beta(a, b), mean 0.1
    p_I: tuple[float, float] = (6.0, 6.0)  # Beta(a, b), mean 0.5
    lambda0_median: float = 0.1  # events / yr
    lambda0_log_sd: float = 1.5
    T: float = 10.0
    theta: Elasticities = field(default_factory=Elasticities)


@dataclass
class MCResult:
    probabilities: np.ndarray

    def summary(self) -> dict[str, float]:
        p = self.probabilities
        q05, q50, q95 = np.quantile(p, [0.05, 0.5, 0.95])
        return {
            "mean": float(p.mean()),
            "median": float(q50),
            "q05": float(q05),
            "q95": float(q95),
            "orders_of_magnitude_90": float(np.log10(q95 / q05)),
        }


def simulate(config: MCConfig = MCConfig(), n: int = 200_000, seed: int | None = 7) -> MCResult:
    """Sample the T-year catastrophe probability for one scenario."""
    names = tuple(config.index_means)
    if not set(INDEX_NAMES[:4]) <= set(names) <= set(INDEX_NAMES):
        raise ValueError(f"index_means needs C, A, O and X, and may add M; got {names}")
    rng = np.random.default_rng(seed)
    idx = sample_indices(list(config.index_means.values()), config.index_concentration, config.correlation, n, rng)
    e = rng.beta(*config.effectiveness, size=(n, config.n_layers))
    rho = rng.beta(*config.rho, size=n)
    lambda0 = np.exp(rng.normal(np.log(config.lambda0_median), config.lambda0_log_sd, n))
    p_I = rng.beta(*config.p_I, size=n)
    lam = lambda0 * index_term(**dict(zip(names, idx.T)), theta=config.theta) * residual_vulnerability(e, rho) * p_I
    return MCResult(catastrophe_probability(lam, config.T))


_PIN = 1e4  # scales Beta parameters to collapse a distribution onto its mean


def spread_decomposition(config: MCConfig = MCConfig(), n: int = 200_000, seed: int | None = 7) -> dict[str, float]:
    """How much of the 90% spread (in orders of magnitude) is assumed rather than derived.

    ``lambda0_only`` fixes everything except the baseline rate, so its spread is
    an input: about 2 * 1.645 * log_sd / ln 10. ``without_lambda0`` fixes the
    baseline rate and keeps the rest. Spreads add roughly in quadrature.
    """
    pinned = dict(
        index_concentration=config.index_concentration * _PIN,
        effectiveness=tuple(v * _PIN for v in config.effectiveness),
        rho=tuple(v * _PIN for v in config.rho),
        p_I=tuple(v * _PIN for v in config.p_I),
    )
    runs = {"all": config, "lambda0_only": replace(config, **pinned), "without_lambda0": replace(config, lambda0_log_sd=0.0)}
    return {name: simulate(cfg, n, seed).summary()["orders_of_magnitude_90"] for name, cfg in runs.items()}
