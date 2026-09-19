"""ControlGap: the AI Drake Equation, as code."""

from .cgi import (
    cgi_contributions,
    cgi_slope,
    consequential_capability,
    control_gap_index,
    control_resilience,
    hazard_growth,
    scenario_cgi,
)
from .hazard import (
    Coupling,
    Elasticities,
    Gate,
    Scenario,
    bilinear_exposure,
    catastrophe_probability,
    hazard,
    index_factor,
    index_term,
    irreversibility,
    residual_vulnerability,
    threshold_gate,
)

__version__ = "0.1.0"

__all__ = [
    "Coupling",
    "Elasticities",
    "Gate",
    "Scenario",
    "bilinear_exposure",
    "catastrophe_probability",
    "cgi_contributions",
    "cgi_slope",
    "consequential_capability",
    "control_gap_index",
    "control_resilience",
    "hazard",
    "hazard_growth",
    "index_factor",
    "index_term",
    "irreversibility",
    "residual_vulnerability",
    "scenario_cgi",
    "threshold_gate",
]
