"""Real-world drivers as levers on the model (paper Sections 13 and 14).

Model advances, government action and open-weight release do not act on
"risk" in general. Each acts on particular terms of the hazard. This module
records which terms, and lets you apply any mix of drivers to a set of
parameters.

The mapping from driver to term follows the paper. The effect *sizes* are
illustrative placeholders, not estimates: replace them with your own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

BOUNDED = ("C", "A", "O", "X", "M", "e0", "e1", "e2", "rho")  # live in [0, 1]
RATES = ("nu", "r_esc", "tau")  # positive, scaled multiplicatively


@dataclass(frozen=True)
class Lever:
    """One driver, and its effect on each parameter at full strength.

    For a bounded parameter, a positive effect u closes that share of the gap
    to 1 (v -> 1 - (1 - v)(1 - u)) and a negative effect removes that share of
    the value (v -> v (1 - |u|)). For a rate, the effect is a relative change
    (v -> v (1 + u)).
    """

    name: str
    group: str
    description: str
    effects: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key, u in self.effects.items():
            if key not in BOUNDED + RATES:
                raise ValueError(f"unknown parameter {key!r}")
            if key in BOUNDED and not -1 <= u <= 1:
                raise ValueError(f"effect on {key} must lie in [-1, 1]")
            if key in RATES and u <= -1:
                raise ValueError(f"effect on {key} must exceed -1")


LEVERS = [
    # ---- model advances
    Lever("Frontier capability jump", "Model advances",
          "A new generation demonstrates more of the capabilities the scenario needs.", {"C": 0.40}),
    Lever("Agentic deployment boom", "Model advances",
          "Agents get more tools, longer runs and more integrations, and there are many more of them.", {"O": 0.40, "X": 0.30, "nu": 1.00}),
    Lever("Alignment progress", "Model advances",
          "Systems become less inclined to attempt harmful actions, and evaluations can show it.", {"M": -0.50}),
    Lever("AI-powered defence", "Model advances",
          "The same advances improve monitoring, triage and incident response.", {"e0": 0.20, "e1": 0.10, "tau": -0.30}),
    # ---- governments
    Lever("Compute governance and export controls", "Governments",
          "Thresholds on training runs and controls on hardware slow capability and narrow access.", {"C": -0.15, "A": -0.10}),
    Lever("Mandatory evaluations and incident reporting", "Governments",
          "Adversarial testing and reporting duties, as in Article 55 of the EU AI Act, improve detection.", {"e0": 0.25, "e1": 0.10}),
    Lever("Critical-infrastructure integration rules", "Governments",
          "Limits on connecting capable agents to energy, finance, health and industrial control.", {"X": -0.30}),
    Lever("Know-your-customer and liability", "Governments",
          "Identity checks narrow access, and attribution deters misuse.", {"A": -0.20, "M": -0.20}),
    Lever("Incident response capacity", "Governments",
          "Drills, isolation powers, backups and circuit breakers speed recovery and slow escalation.", {"tau": -0.40, "r_esc": -0.20}),
    # ---- open source: the paper's Section 13 splits the effect in two
    Lever("Open weights: proliferation", "Open source",
          "More actors obtain the capability. Safeguards can be stripped, use is harder to monitor, and weights cannot be recalled.",
          {"A": 0.60, "e0": -0.20, "e1": -0.30, "nu": 0.30}),
    Lever("Open weights: defensive ecosystem", "Open source",
          "Broader red-teaming and tooling improve the layers, and more diverse defences share fewer weaknesses.",
          {"e0": 0.15, "e2": 0.10, "rho": -0.30}),
]  # fmt: skip

GROUPS = tuple(dict.fromkeys(lever.group for lever in LEVERS))


def apply_levers(params: dict[str, float], strengths: dict[str, float], levers: list[Lever] = LEVERS) -> dict[str, float]:
    """Return a copy of ``params`` after applying each named lever at its strength in [0, 1].

    ``params`` maps the names in ``BOUNDED`` and ``RATES`` to values. Parameters
    that are absent are left alone. Levers apply in catalogue order.
    """
    catalogue = {lever.name: lever for lever in levers}
    unknown = set(strengths) - set(catalogue)
    if unknown:
        raise ValueError(f"unknown levers: {sorted(unknown)}")
    out = dict(params)
    for lever in levers:
        s = float(strengths.get(lever.name, 0.0))
        if not 0 <= s <= 1:
            raise ValueError("strength must lie in [0, 1]")
        for key, u in lever.effects.items():
            if key not in out or s == 0:
                continue
            v, u = out[key], u * s
            if key in RATES:
                out[key] = v * (1 + u)
            else:
                out[key] = float(np.clip(1 - (1 - v) * (1 - u) if u > 0 else v * (1 + u), 0.0, 1.0))
    return out
