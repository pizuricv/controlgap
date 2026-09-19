"""Walk through the paper's worked examples. Run: python examples/quickstart.py"""

import numpy as np

import controlgap as cg
from controlgap import precursors
from controlgap.mc import MCConfig, simulate

# Section 12: the same inputs, four baseline rates.
s = cg.Scenario("illustrative", C=0.20, A=0.70, O=0.50, X=0.60, effectiveness=(0.6, 0.5, 0.5), rho=0.1, p_I=0.5)
print(f"V = {s.V:.2f}, combined factor = {s.factor:.4f} (not a probability)")
for lam0 in (0.01, 0.1, 1, 10):
    print(f"  lambda0 = {lam0:>5}: P(D_10) = {s.probability(lam0, T=10):.2%}")

# Section 11: once layers are strong, only reducing rho helps.
strong = [0.95, 0.95, 0.95]
print(f"\nV with strong layers, rho=0.10: {cg.residual_vulnerability(strong, 0.10):.4f}")
print(f"V with perfect layers, rho=0.10: {cg.residual_vulnerability([1, 1, 1], 0.10):.4f}")
print(f"V with strong layers, rho=0.02: {cg.residual_vulnerability(strong, 0.02):.4f}")

# Section 15: the dashboard.
t = np.arange(6)
cgi = cg.control_gap_index(K=(1.10 * 1.05 * 1.02 * 1.04 * 1.03) ** t, Gamma=1.06**t)
slope = cg.cgi_slope(t, cgi)
print(f"\nCGI slope = {slope:+.2f}/yr, hazard growing {cg.hazard_growth(slope):.0%}/yr")

# Section 10: correlation mainly moves the tail.
for r in (0.0, 0.6):
    m = simulate(MCConfig(correlation=r)).summary()
    print(f"copula r = {r}: median {m['median']:.2%}, mean {m['mean']:.2%}, 90% interval {m['q05']:.1e} to {m['q95']:.1e}")

# Section 9: score a near-miss that was stopped only by the last layer.
score = precursors.conditional_catastrophe_probability(passed=[0.6, 0.5], remaining=[0.5], rho=0.1, p_I=0.5)
print(f"\nNear-miss past two layers: conditional catastrophe probability {score:.2f}")
