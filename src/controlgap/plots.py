"""The paper's five figures, generated from the model code.

    python -m controlgap.plots paper/figures

File names match the ``::fig`` directives in the paper source. Requires the
``plots`` extra (matplotlib).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError as err:
    raise ModuleNotFoundError('controlgap.plots needs matplotlib: pip install "controlgap[plots]"') from err

from .cgi import control_gap_index
from .hazard import Gate, Scenario, residual_vulnerability
from .mc import MCConfig, simulate

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"

STYLE = {
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "font.size": 11, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "lines.linewidth": 2,
    "legend.frameon": False,
}  # fmt: skip

# The worked example of Section 12.
EXAMPLE = Scenario("illustrative", C=0.20, A=0.70, O=0.50, X=0.60, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)


def fig_lambda0_identifiability(scenario: Scenario = EXAMPLE, T: float = 10.0):
    """Paper Figure 5: the same inputs give 0.04% to 33% as lambda0 varies."""
    lam0 = np.logspace(-3, 2, 400)
    marks = np.array([0.01, 0.1, 1.0, 10.0])
    p_marks = scenario.probability(marks, T)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(lam0, scenario.probability(lam0, T) * 100, color=S1)
    for l, p in zip(marks, p_marks):
        ax.plot(l, p * 100, "o", ms=8, color=S1, mec=SURF, mew=2)
        ax.annotate(f"λ₀={l:g}\n{p * 100:.2g}%", (l, p * 100), textcoords="offset points",
                    xytext=(-12, 10), ha="right", color=INK, fontsize=10)  # fmt: skip
    ax.axvline(1 / T, color=INK2, ls="--", lw=1)
    ax.text(1 / T * 1.1, 60, "λ₀T = 1: only here does\n'product = probability' hold", color=INK2, fontsize=9.5)
    ax.set_xscale("log")
    ax.set_ylim(0, 100)
    ax.set_xlabel("Baseline rate λ₀ (events / yr at max indices, no defences, certain escalation)")
    ax.set_ylabel(f"P(catastrophe within {T:g} yr), %")
    ax.set_title(f"Same inputs (factor {scenario.factor:.4f}), answers from {p_marks[0] * 100:.2g}% to {p_marks[-1] * 100:.2g}%")
    return fig


def fig_common_mode_floor(n_layers: int = 3):
    """Paper Figure 1: residual vulnerability bottoms out at rho."""
    e = np.linspace(0, 0.99, 300)
    layers = np.repeat(e[:, None], n_layers, axis=1)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for rho, c, lab in [(0.0, S1, "ρ = 0 (independent layers)"), (0.10, S2, "ρ = 0.10"), (0.02, S3, "ρ = 0.02")]:
        ax.plot(e, residual_vulnerability(layers, rho), color=c, label=lab)
        if rho > 0:
            ax.axhline(rho, color=c, lw=1, ls=":")
            ax.text(0.005, rho * 0.62, f"floor = {rho:g}", color=INK2, fontsize=9.5)
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 1.2)
    ax.set_xlabel(f"Effectiveness of each of {n_layers} defensive layers, e")
    ax.set_ylabel("Residual vulnerability V (log)")
    ax.set_title("Better layers stop helping once common-mode bypass dominates")
    ax.legend(loc="lower left")
    return fig


def fig_spec1_vs_spec2(gate: Gate = Gate(z0=0.5, k=15.0)):
    """Paper Figure 2: power laws versus the normalised threshold gate."""
    C = np.linspace(0, 1, 400)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(C, C, color=S1, label="Spec I, θ = 1 (power law)")
    ax.plot(C, gate(C), color=S2, label=f"Spec II, threshold gate at C₀ = {gate.z0:g}")
    ax.plot(C, C**3, color=S3, label="Spec I, θ = 3")
    ax.axvline(gate.z0, color=INK2, ls="--", lw=1)
    ax.annotate("", xy=(gate.z0 + 0.05, 0.62), xytext=(gate.z0 - 0.05, 0.62), arrowprops=dict(arrowstyle="<->", color=INK2))
    ax.text(gate.z0 - 0.07, 0.62, "small ΔC,\nlarge Δλ", ha="right", va="center", color=INK2, fontsize=9.5)
    ax.set_xlabel("Capability index C (others held fixed)")
    ax.set_ylabel("Relative hazard λ / λ_max")
    ax.set_title("Power law vs threshold: same endpoints, different policy lessons")
    ax.legend(loc="upper left")
    return fig


def fig_monte_carlo(correlation: float = 0.6, n: int = 200_000, seed: int = 7):
    """Paper Figure 4: independent versus correlated indices."""
    runs = [
        ("indices independent", S1, simulate(MCConfig(correlation=0.0), n, seed)),
        (f"indices correlated (copula r = {correlation:g})", S2, simulate(MCConfig(correlation=correlation), n, seed)),
    ]
    bins = np.linspace(-6, 0, 72)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for lab, c, res in runs:
        ax.hist(np.log10(res.probabilities), bins=bins, color=c, alpha=0.45, label=lab, density=True, edgecolor=SURF, lw=0.5)
        ax.axvline(np.log10(res.probabilities.mean()), color=c, lw=2)
    span = runs[0][2].summary()["orders_of_magnitude_90"]
    ax.set_xticks(range(-6, 1))
    ax.set_xticklabels([f"10$^{{{k}}}$" for k in range(-6, 1)])
    ax.set_xlabel("P(catastrophe within 10 yr), Monte Carlo draws (log scale)")
    ax.set_ylabel("Density")
    ax.set_title(f"90% range spans ~{span:.1f} orders; correlation fattens the upper tail")
    ax.legend(loc="upper left")
    ax.text(0.99, 0.95, "vertical lines = mean P\n(average probabilities, not hazards)",
            transform=ax.transAxes, ha="right", va="top", color=INK2, fontsize=9.5)  # fmt: skip
    return fig


def fig_control_gap_index():
    """Paper Figure 3: illustrative CGI trajectories. Not data."""
    years = np.arange(2026, 2037)
    t = years - years[0]
    # (name, colour, growth of ln K per yr, growth of ln Gamma per yr)
    scenarios = [
        ("Autonomous cyber ops", S1, 0.35, 0.18),
        ("AI-enabled bio misuse", S2, 0.25, 0.28),
        ("Cascading infra failure", S3, 0.20, 0.12),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for name, c, g_K, g_Gamma in scenarios:
        K = np.exp(g_K * t + 0.05 * np.sin(t))
        cgi = control_gap_index(K, np.exp(g_Gamma * t))
        ax.plot(years, cgi, color=c, label=name)
        ax.text(years[-1] + 0.15, cgi[-1], name, color=INK, va="center", fontsize=10)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xlim(years[0], years[-1] + 4)
    ax.set_xticks(years[::2])
    ax.set_ylabel(f"CGI = Δln K − Δln Γ  (vs {years[0]})")
    ax.set_title("Control Gap Index: the slope is the signal (illustrative)")
    ax.text(years[-1], 0.03, "reference-year balance (not 'safe')", color=INK2, fontsize=9, va="bottom", ha="right")
    return fig


FIGURES = {
    "fig1_lambda0_identifiability.png": fig_lambda0_identifiability,
    "fig2_common_mode_floor.png": fig_common_mode_floor,
    "fig3_spec1_vs_spec2.png": fig_spec1_vs_spec2,
    "fig4_monte_carlo.png": fig_monte_carlo,
    "fig5_control_gap_index.png": fig_control_gap_index,
}


def make_all(outdir: str | Path, dpi: int = 180) -> list[Path]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    with plt.rc_context(STYLE):
        for name, make in FIGURES.items():
            fig = make()
            fig.tight_layout()
            fig.savefig(outdir / name, dpi=dpi)
            plt.close(fig)
            paths.append(outdir / name)
    return paths


if __name__ == "__main__":
    plt.switch_backend("Agg")
    for path in make_all(sys.argv[1] if len(sys.argv) > 1 else "figures"):
        print(path)
