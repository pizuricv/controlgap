# ControlGap

[![tests](https://github.com/pizuricv/controlgap/actions/workflows/tests.yml/badge.svg)](https://github.com/pizuricv/controlgap/actions/workflows/tests.yml)

**The AI Drake Equation, as code.**

ControlGap implements the measurement architecture from the paper
[*The AI Drake Equation: when does AI capability become consequential power?*](paper/ai-drake-equation-v4.md).

The thesis is that capability alone does not determine catastrophic AI risk.
Risk emerges when capability becomes *consequential power*: capability that is
accessible, able to act and connected to systems that matter, faster than we
can detect, stop, contain and recover from its failures.

One scenario-specific hazard model carries this, read in two ways:

- **As a probability.** `P(D_T) = 1 − exp(−∫ Σ_s λ_s dt)`, with
  `λ_s = λ₀ · C^θ · A^θ · O^θ · X^θ · M^θ · V · p_I`. Absolute probabilities are not
  currently identifiable: for fixed, plausible inputs they range from 0.04% to 33%.
- **As a trend.** The **Control Gap Index**, `CGI_s(t) = ln[λ_s(t) / λ_s(t₀)]`, in
  which the unknown scale cancels. It measures whether consequential capability
  is growing faster than control, and it can be tracked today.

This is a research programme and a monitoring architecture, not a prediction engine.

## Install

```bash
git clone https://github.com/pizuricv/controlgap && cd controlgap
pip install -e ".[dev]"     # not yet on PyPI
```

## Quickstart

```python
import numpy as np
import controlgap as cg

# Section 12: one scenario, illustrative values
s = cg.Scenario("illustrative", C=0.20, A=0.70, O=0.50, X=0.60,
                effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)
s.V                                  # 0.19, residual vulnerability
s.factor                             # 0.0040, which is NOT a probability
s.probability([0.01, 0.1, 1, 10], T=10)   # 0.04%, 0.40%, 3.9%, 33%

# Section 15: the dashboard. K grows 26%/yr, Γ grows 6%/yr
t = np.arange(0, 6)
cgi = cg.control_gap_index(K=1.262 ** t, Gamma=1.06 ** t)
cg.cgi_slope(t, cgi)                 # +0.17 per year
cg.hazard_growth(0.174)              # hazard growing ~19% per year
```

Monte Carlo with correlated indices (Section 10):

```python
from controlgap.mc import MCConfig, simulate

simulate(MCConfig(correlation=0.0)).summary()   # median 0.22%, mean 0.94%
simulate(MCConfig(correlation=0.6)).summary()   # median 0.23%, mean 1.22%
```

## Try it

**[Open the app](https://pizuricv-controlgap-appapp-deploy-ns3yua.streamlit.app/)** — ten short chapters that walk through the
paper, with every number live. Pick a scenario, move the sliders, and each chapter ends with what just happened and what to try next.

| | |
|---|---|
| 1 · Start here | The question, and a scenario to carry with you |
| 2 · The chain | Five things must line up. Watch the hazard shrink through them |
| 3 · The missing number | Why there is no headline p(doom): it all rides on λ₀ |
| 4 · The layers | Three good layers, one shared blind spot, and the floor it puts under V |
| 5 · The race | Escalation against recovery — where reversibility is won or lost |
| 6 · Where effort pays | What a 10% improvement buys, lever by lever |
| 7 · What if | Model advances, governments and open weights, and the terms each one moves |
| 8 · The control gap | The one number that survives: is capability outrunning control? |
| 9 · How much we know | Correlated uncertainty, and how much of the spread is assumed |
| 10 · Your turn | Spend a budget of effort and buy the hazard down |

Run it yourself:

```bash
pip install -e ".[app]"
streamlit run app/app.py
```

There is also a notebook tour, [`notebooks/controlgap_tour.ipynb`](notebooks/controlgap_tour.ipynb), which walks through
the paper section by section. Rebuild it with `python notebooks/build_notebook.py`.

## Modules

| Module | Paper | Contents |
|---|---|---|
| `controlgap.hazard` | §4–6, §8 | Five indices including propensity `M`, residual vulnerability with a common-mode floor, the escalation–recovery race, Specifications I and II, capability coupling, the vector form `cᵀWx`, `P(D_T)` |
| `controlgap.cgi` | §7 | `K`, `Γ`, the Control Gap Index, its split into per-term contributions, its slope and the implied hazard growth |
| `controlgap.mc` | §10 | Gaussian-copula sampling of the indices; averages probabilities, not hazards; splits the spread into the part assumed through λ₀ and the rest |
| `controlgap.precursors` | §9 | Estimators for `e_ℓ`, `ρ` and the race rates from red-team and incident counts; Poisson fit of the elasticities `θ`; ASP-style conditional scoring of a near-miss |
| `controlgap.levers` | §13–14 | A catalogue of real-world drivers (model advances, governments, open weights) and the terms each acts on. Effect sizes are placeholders |
| `controlgap.plots` | Figures 1–5 | Regenerates every figure in the paper from the model code |

## Reproduce the paper's figures

```bash
python -m controlgap.plots paper/figures
```

## Tests

```bash
pytest
```

The tests pin the numbers quoted in the paper: `V = 0.19`, the 0.04%–33% table,
the dashboard's +0.17 slope, the Monte Carlo summary and the spread decomposition.
They also run the app headlessly.

## Tell us we're wrong

The app has a feedback panel in its sidebar that opens a pre-filled GitHub issue with your current settings attached, so a
report is reproducible. It is a link, not an API call: a public app should never carry a write token, and this way the issue
is filed under your own account.

## Status

A research programme and a monitoring architecture, not a prediction engine. The functional forms are hypotheses,
the example values are illustrative, and the framework is more mature for misuse scenarios than for loss of control.
Issues and pull requests are welcome, especially real indicator data for any of the terms.

## Free for everyone

Anyone can use ControlGap, for any purpose, including commercial use, teaching, policy work and building products on top of it.
You do not need to ask.

- **Code**: [MIT](LICENSE). Use it, change it, ship it. Keep the copyright notice.
- **Paper and figures**: [CC BY 4.0](paper/LICENSE.md). Copy, translate, adapt and republish them. Credit the author.

If you use the framework in your own work, please cite it. [`CITATION.cff`](CITATION.cff) has the details, and GitHub's
"Cite this repository" button will format it for you.
