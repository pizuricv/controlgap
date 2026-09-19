"""ControlGap playground. Run: streamlit run app/app.py"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import controlgap as cg
from controlgap import precursors
from controlgap.levers import GROUPS, LEVERS, apply_levers
from controlgap.mc import MCConfig, beta_params, simulate, spread_decomposition

S1, S2, S3, INK = "#2a78d6", "#eb6834", "#1baf7a", "#898781"
LAYERS = ("Detection", "Intervention", "Containment")
PAPER = "https://github.com/pizuricv/controlgap/blob/main/paper/ai-drake-equation-v4.md"

# Every preset is illustrative. None of these values is a measurement.
PRESETS = {
    "Paper's worked example (§12)": dict(
        about="The numbers used throughout the paper. Propensity is at its worst case and there is no coupling.",
        C=0.20, A=0.70, O=0.50, X=0.60, M=1.00, e0=0.60, e1=0.50, e2=0.50, rho=0.10, r_esc=1.0, tau=1.0, g=0.0),
    "Autonomous cyber operations": dict(
        about="The AI system is the acting agent. Events move in hours, and capability helps the system get access and evade oversight, so coupling is on.",
        C=0.45, A=0.60, O=0.70, X=0.70, M=0.15, e0=0.70, e1=0.50, e2=0.40, rho=0.15, r_esc=2.0, tau=0.5, g=0.40),
    "AI-enabled biological misuse": dict(
        about="A human is the acting agent. Few people would try and agency matters little, but a release is very hard to recall.",
        C=0.30, A=0.50, O=0.20, X=0.30, M=0.05, e0=0.80, e1=0.60, e2=0.50, rho=0.05, r_esc=0.2, tau=10.0, g=0.0),
    "Cascading infrastructure failure": dict(
        about="An accident, so nobody has to intend it: propensity is 1. Tightly coupled systems share weaknesses, so ρ is high and escalation is fast.",
        C=0.60, A=0.90, O=0.80, X=0.50, M=1.00, e0=0.50, e1=0.40, e2=0.60, rho=0.25, r_esc=4.0, tau=2.0, g=0.0),
}  # fmt: skip
KEYS = ("C", "A", "O", "X", "M", "e0", "e1", "e2", "rho", "r_esc", "tau", "g")
NAMES = {"nu": "Episodes ν", "C": "Capability C", "A": "Access A", "O": "Agency O", "X": "Exposure X", "M": "Propensity M",
         "V": "Residual vulnerability V", "p_I": "Irreversibility p_I", "e0": "Detection", "e1": "Intervention", "e2": "Containment",
         "rho": "Common-mode ρ", "r_esc": "Escalation rate", "tau": "Recovery time"}  # fmt: skip

st.set_page_config(page_title="ControlGap", page_icon="🎛️", layout="wide")


# ---------------------------------------------------------------- first-visit intro
INTRO = [
    ("The question", """
People argue about one number: *the probability of AI catastrophe*. This app takes the question apart instead,
the way Frank Drake did for alien civilisations.

A capable AI system is not dangerous just by being capable. It becomes dangerous when that capability turns into
**consequential power** faster than we can control it. So there are two sides:

| Consequence side | Control side |
|---|---|
| Is it **capable** enough? | Do we **detect** it? |
| Who can **access** it? | Can we **intervene**? |
| Can it **act**? | Can we **contain** it? |
| What can it **reach**? | Do our defences share a **weak spot**? |
| Would anyone, or anything, **try**? | How fast do we **recover**? |
"""),
    ("The sidebar is your scenario", """
Everything on the left describes **one scenario**.

- Start by picking one under **Start from a scenario**, for example *Autonomous cyber operations*.
- The sliders go from 0 to 1. Hover the **?** next to any of them to see what it means.
- The four numbers at the top of the page update as you move them. The last one, the *combined factor*,
  is everything multiplied together.

You cannot break anything. Every value is illustrative, not a measurement.
"""),
    ("Two ways to read the result", """
**1. How likely is it?** The honest answer is that nobody can know yet. To turn the factor into a probability you need a
baseline rate, **λ₀**, and no catastrophe has happened to pin it down. The same inputs give anything from 0.04% to 33%.

**2. Which way is it moving?** This one *can* be answered. Compare the hazard with a reference year and the unknown
λ₀ cancels. What is left is the **Control Gap Index**: is consequential capability growing faster than control?

That second question is the point of the whole framework.
"""),
    ("A route through the tabs", """
Each tab teaches one idea, and each has a **Try this** box with two or three experiments.

1. **Start here**: the equation, with your numbers in it.
2. **Probability**: why there is no headline number.
3. **Defences**: why better layers stop helping, and how to score a near-miss.
4. **Levers**: where a 10% improvement pays off most.
5. **What if**: model advances, governments and open weights as levers.
6. **Control Gap Index**: is capability outrunning control?
7. **Monte Carlo**: what uncertainty does to all of the above.

You can reopen this introduction any time from the bottom of the sidebar.
"""),
]  # fmt: skip


def close_intro():
    st.session_state.intro_open = False


@st.dialog("Welcome to ControlGap", width="large", on_dismiss=close_intro)
def intro():
    step = st.session_state.intro_step
    title, body = INTRO[step]
    st.progress((step + 1) / len(INTRO), text=f"{step + 1} of {len(INTRO)} · {title}")
    st.markdown(body)
    back, skip, _, forward = st.columns([1, 1, 3, 1.4])
    if step > 0 and back.button("Back"):
        st.session_state.intro_step -= 1
        st.rerun()
    if step < len(INTRO) - 1:
        if skip.button("Skip"):
            close_intro()
            st.rerun()
        if forward.button("Next", type="primary"):
            st.session_state.intro_step += 1
            st.rerun()
    elif forward.button("Start exploring", type="primary"):
        close_intro()
        st.rerun()


def open_intro():
    st.session_state.intro_open, st.session_state.intro_step = True, 0


# ---------------------------------------------------------------- sidebar
def apply_preset():
    for key in KEYS:
        st.session_state[key] = PRESETS[st.session_state.preset][key]


def sidebar() -> dict:
    for key in KEYS:
        st.session_state.setdefault(key, next(iter(PRESETS.values()))[key])
    sb = st.sidebar
    sb.selectbox("Start from a scenario", list(PRESETS), key="preset", on_change=apply_preset)
    sb.caption(PRESETS[st.session_state.preset]["about"] + " *Illustrative values.*")

    sb.header("Consequence side")
    sb.caption("How much real-world power the capability has.")
    sb.slider("Capability C", 0.01, 1.0, step=0.01, key="C", help="What share of the capabilities this scenario needs has the system demonstrated?")
    sb.slider("Access A", 0.01, 1.0, step=0.01, key="A", help="How many actors can get hold of that capability? Open weights push this up; API gating pushes it down.")
    sb.slider("Agency O", 0.01, 1.0, step=0.01, key="O", help="Can it act? Tools, permissions, persistence, long unsupervised runs.")
    sb.slider("Exposure X", 0.01, 1.0, step=0.01, key="X", help="What can it reach? Finance, cloud, industrial control, labs.")
    sb.slider("Propensity M", 0.01, 1.0, step=0.01, key="M", help="Would the acting agent, human or AI, actually try? 1 is the worst case. This is where alignment work shows up.")

    sb.header("Control side")
    sb.caption("How well we stop it, and how fast we recover.")
    for i, name in enumerate(LAYERS):
        sb.slider(f"{name} effectiveness", 0.0, 0.99, step=0.01, key=f"e{i}", help="Probability that this layer stops an event that reaches it.")
    sb.slider("Common-mode bypass ρ", 0.0, 0.5, step=0.01, key="rho", help="Chance that one weakness defeats every layer at once: a shared blind spot, one stolen credential. V can never fall below ρ.")
    sb.slider("Escalation rate (per day)", 0.01, 5.0, step=0.01, key="r_esc", help="How fast an event that got through grows beyond repair.")
    sb.slider("Mean time to recover (days)", 0.05, 20.0, step=0.05, key="tau", help="Time to detect, isolate and restore.")
    with sb.expander("Advanced: capability coupling (§6.7)"):
        st.slider("Coupling g", 0.0, 1.0, step=0.05, key="g", help="A capable system can obtain access, agency and exposure for itself, and evade oversight. 0 means the levers are independent.")
    with sb.expander("Advanced: capability threshold (§6.5)"):
        gated = st.toggle("Use a threshold gate for C", help="Some dangerous tasks may be impossible below a capability level and routine above it.")
        C0 = st.slider("Threshold C₀", 0.05, 0.95, 0.50, 0.05)
        k = st.slider("Steepness k", 1.0, 40.0, 15.0, 1.0)
    sb.divider()
    sb.button("Show intro", on_click=open_intro, width="stretch")
    return {**{key: st.session_state[key] for key in KEYS}, "nu": 1.0, "gated": gated, "C0": C0, "k": k}


def scenario(p: dict, **override) -> cg.Scenario:
    """Build a Scenario from the sidebar values. Any field can be overridden, by a number or a time series."""
    v = {**p, **override}
    g = p["g"]
    return cg.Scenario(
        "playground", C=v["C"], A=v["A"], O=v["O"], X=v["X"], M=v["M"], effectiveness=(v["e0"], v["e1"], v["e2"]), rho=v["rho"],
        p_I=cg.irreversibility(v["r_esc"], tau_rec=v["tau"]), nu=v["nu"],
        coupling=cg.Coupling(A=g, O=g, X=g, e=g, rho=g),
        gates={"C": cg.Gate(p["C0"], p["k"])} if p["gated"] else None,
    )  # fmt: skip


def rate(sc: cg.Scenario) -> float:
    """Hazard up to the unknown constant: episode volume times the combined factor."""
    return float(sc.nu * sc.factor)


def line(df: pd.DataFrame, x: alt.X, y: alt.Y, colour=None, tooltip=None, width: float = 2) -> alt.Chart:
    enc = dict(x=x, y=y, tooltip=tooltip or [x, y])
    if colour is not None:
        enc["color"] = colour
    return alt.Chart(df).mark_line(strokeWidth=width, color=S1).encode(**enc)


CSS = """
<style>
/* Compact page header, so the controls of each tab start above the fold */
[data-testid="stMainBlockContainer"] {padding-top: 2.6rem;}
.cg-title {display: flex; flex-wrap: wrap; align-items: baseline; gap: .2rem 1rem; margin-bottom: .2rem;}
.cg-title h1 {font-size: 2.1rem; padding: 0; margin: 0;}
.cg-title span {font-size: 1.02rem; opacity: .8;}
/* What-if results stay in view while the sliders below are dragged */
/* (Streamlit wraps the container in a same-height layout wrapper, so the wrapper is what has to stick.) */
[data-testid="stLayoutWrapper"]:has(> .st-key-whatif_head) {position: sticky; top: 3.75rem; z-index: 90;}
.st-key-whatif_head {background: __BG__; box-shadow: 0 6px 14px -10px rgba(0,0,0,.45);}
/* The one number to watch, at the top of every tab */
.cg-hero {border: 1px solid rgba(128,128,128,.25); border-left: 6px solid #2a78d6; border-radius: 10px; padding: .75rem 1.3rem; margin: .3rem 0 .6rem;
          display: flex; flex-wrap: wrap; gap: 1rem 2.5rem; align-items: center; background: rgba(42,120,214,.06);}
.cg-eyebrow {font-size: .72rem; letter-spacing: .09em; text-transform: uppercase; font-weight: 600; opacity: .7;}
.cg-hero .cg-big {font-size: 2.6rem; font-weight: 700; line-height: 1.05; margin: .15rem 0;}
.cg-hero .cg-big small {font-size: 1.1rem; font-weight: 500; opacity: .75;}
.cg-hero .cg-verdict {font-size: 1.05rem; font-weight: 600;}
.cg-hero .cg-side {flex: 1 1 320px; font-size: .92rem; line-height: 1.5;}
.cg-hero .cg-side b {font-variant-numeric: tabular-nums;}
.cg-hero .cg-note {opacity: .7; font-size: .85rem; margin-top: .35rem;}
/* Supporting numbers are smaller than the focus number */
.st-key-blocks [data-testid="stMetricValue"] {font-size: 1.35rem;}
.st-key-blocks [data-testid="stMetricLabel"] {opacity: .8;}
/* Each tab's own number to watch */
[class*="st-key-focus_"] {border-left: 4px solid #2a78d6; padding: .1rem 0 .1rem 1rem; margin-bottom: .6rem;}
[class*="st-key-focus_"] [data-testid="stMetricValue"] {font-size: 2.3rem; font-weight: 700;}
</style>
"""


def focus(name: str, why: str):
    """A keyed container that marks one metric per tab as the number to watch."""
    box = st.container(key=f"focus_{name}")
    box.markdown(f'<div class="cg-eyebrow">Number to watch · {why}</div>', unsafe_allow_html=True)
    return box


def render_hero(box, slope: float, k_growth: float, gamma_growth: float, horizon: int):
    growth = cg.hazard_growth(slope)
    if slope > 0.005:
        verdict = "▲ Consequential capability is outrunning control"
    elif slope < -0.005:
        verdict = "▼ Control is catching up"
    else:
        verdict = "■ Capability and control are in balance"
    box.markdown(
        f"""<div class="cg-hero">
<div><div class="cg-eyebrow">The number to watch · hazard trend</div>
<div class="cg-big">{growth:+.0%} <small>per year</small></div>
<div class="cg-verdict">{verdict}</div></div>
<div class="cg-side">Consequence side <b>K {k_growth:+.0%}</b> / yr &nbsp;versus&nbsp; control side <b>Γ {gamma_growth:+.0%}</b> / yr, over {horizon} years from 2026.
<div class="cg-note">This is a <i>trend</i>: how fast the hazard is changing relative to 2026. It is not a probability and not a forecast.
It is the one quantity in the model that does not depend on the unknown λ₀. Set the yearly trends in the <i>Control Gap Index</i> tab.</div></div>
</div>""",
        unsafe_allow_html=True,
    )


def lesson(what: str, tries: list[str], section: str):
    """The explainer at the top of each tab."""
    left, right = st.columns([3, 2])
    left.markdown(what)
    left.caption(f"Paper: {section}")
    with right.container(border=True):
        st.markdown("**Try this**\n" + "\n".join(f"- {t}" for t in tries))


if "intro_open" not in st.session_state:
    open_intro()

p = sidebar()
s = scenario(p)
if st.session_state.intro_open:
    intro()

dark = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
st.markdown(CSS.replace("__BG__", "#0e1117" if dark else "#ffffff"), unsafe_allow_html=True)
st.markdown('<div class="cg-title"><h1>ControlGap</h1><span>When does AI capability become <i>consequential power</i>? · The AI Drake Equation, as code</span></div>', unsafe_allow_html=True)
hero = st.container()  # filled once the trend has been computed, further down

blocks = st.container(key="blocks")
blocks.caption("**Building blocks of the hazard.** Watch them move as you change the sidebar. None of them is the answer on its own.")
cols = blocks.columns(4)
cols[0].metric("Consequence: index term", f"{float(s.indices):.4f}", help="C · A · O · X · M after gates and coupling")
cols[1].metric("Residual vulnerability V", f"{float(s.V):.3f}", help=f"Chance an event gets past every layer. Floor: V ≥ ρ = {p['rho']:.2f}")
cols[2].metric("Irreversibility p_I", f"{float(s.p_I):.3f}", help="Chance an event that got through escalates before we recover")
cols[3].metric("Combined factor", f"{float(s.factor):.5f}", help="Not a probability. It becomes one only once you choose λ₀.")

tab_intro, tab_p, tab_def, tab_levers, tab_whatif, tab_cgi, tab_mc = st.tabs(
    ["Start here", "Probability", "Defences", "Levers", "What if", "Control Gap Index", "Monte Carlo"]
)

# ---------------------------------------------------------------- start here
with tab_intro:
    left, right = st.columns([3, 2])
    left.markdown(
        """
Frank Drake's equation never told us how many civilisations exist. It turned one unanswerable question into
several that can be answered one at a time. This app does the same for catastrophic AI risk.

**The idea.** A capable AI system is not dangerous by being capable. It becomes dangerous when that capability
can be **accessed**, can **act**, can **reach** systems that matter, and someone or something would **try**,
faster than we can **detect, stop, contain and recover**. For a catastrophe, everything has to line up:
"""
    )
    eff = s.effective
    left.latex(
        r"\lambda \;=\; \lambda_0 \times "
        + r" \times ".join(rf"\underbrace{{{float(eff[k]):.2f}}}_{{{k}}}" for k in "CAOXM")
        + rf" \times \underbrace{{{float(s.V):.3f}}}_{{V}} \times \underbrace{{{float(s.p_I):.2f}}}_{{p_I}}"
    )
    left.latex(rf"\lambda \;=\; \lambda_0 \times {float(s.factor):.5f}")
    left.markdown(
        """
The first five terms are the **consequence side**, the last two are the **control side**, and **λ₀** is the
baseline rate that nobody knows. Move a slider in the sidebar and watch the equation change.

**Two ways to read it**

1. **As a probability** *(Probability tab)*. The honest answer is that we cannot know it yet: the same inputs give anything from 0.04% to 33%.
2. **As a trend** *(Control Gap Index tab)*. Is consequential capability growing faster than control? Here the unknown λ₀ cancels, so this can be measured today.

Then ask what changes it: *Levers* shows where effort pays off, and *What if* applies model advances, government action and open-weight release.
"""
    )
    with right.container(border=True):
        st.markdown("**How the chain shrinks the hazard**")
        st.caption("Start from the baseline rate. Each factor removes a share of it. Log scale.")
        stages = [("Baseline λ₀", 1.0)] + [(NAMES[k], float(cg.index_factor(k, eff[k], s.theta, s.gates))) for k in "CAOXM"]
        stages += [("Gets past defences (V)", float(s.V)), ("Escalates (p_I)", float(s.p_I))]
        chain = pd.DataFrame(stages, columns=["Stage", "Factor"])
        chain["Remaining"] = chain["Factor"].cumprod()
        base = alt.Chart(chain).encode(
            y=alt.Y("Stage:N", sort=list(chain["Stage"]), title=None, axis=alt.Axis(labelLimit=200)),
            x=alt.X("Remaining:Q", scale=alt.Scale(type="log"), title="Share of baseline hazard remaining"),
            tooltip=["Stage", alt.Tooltip("Factor:Q", format=".3f"), alt.Tooltip("Remaining:Q", format=".2e")])  # fmt: skip
        st.altair_chart((base.mark_line(color=S1, strokeWidth=2) + base.mark_point(color=S1, filled=True, size=90, opacity=1)).properties(height=alt.Step(30)), width="stretch")
    with st.expander("Glossary"):
        st.markdown(
            """
| Term | Plain meaning |
|---|---|
| **Episode** | One deployment that matters for the scenario: an agent run, a model access, an integration exercised |
| **λ₀** | Catastrophes per year if every index were 1, with no defences and certain escalation. The least knowable number in the model |
| **C, A, O, X, M** | Capability, Access, Agency, Exposure, Propensity. Indices from 0 to 1, not probabilities |
| **V** | Residual vulnerability: the chance an event gets past every defensive layer |
| **ρ** | Common-mode bypass: the chance one weakness defeats all layers at once. V can never be lower than ρ |
| **p_I** | Irreversibility: the chance an event escalates before we recover |
| **K and Γ** | Consequential capability (ν · C · A · O · X · M) and control & resilience (1 / (V · p_I)) |
| **CGI** | Control Gap Index: the log of how much the hazard has changed since the reference year. Its slope is the signal |
"""
        )
    st.caption(f"Every value in this app is illustrative. The model cannot give a trustworthy absolute probability, and says so.  ·  [Read the paper]({PAPER})  ·  Free for everyone to use: code MIT, paper CC BY 4.0.")

# ---------------------------------------------------------------- probability
with tab_p:
    lesson(
        "**Why there is no headline number.** The factor above is *not* a probability. To get one you must choose λ₀, "
        "and no catastrophe has happened, so nothing pins it down. Anyone quoting a single p(doom) has chosen a λ₀ without saying so.",
        ["Slide **λ₀** across its range and watch the answer move by orders of magnitude.", "Halve any sidebar term: the probability roughly halves, *whatever* λ₀ is. Relative statements are robust."],
        "§12, An illustrative calibration",
    )  # fmt: skip
    left, right = st.columns([1, 3])
    lam0 = left.select_slider("Baseline rate λ₀ (events / yr)", options=[0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100], value=0.1)
    T = left.slider("Horizon T (years)", 1, 50, 10)
    focus("p", "only as good as your guess of λ₀").metric(f"P(catastrophe within {T} yr)", f"{float(s.probability(lam0, T)):.2%}")
    lo, hi = s.probability([0.01, 10], T)
    left.info(f"The same inputs give **{lo:.2%}** at λ₀ = 0.01 and **{hi:.1%}** at λ₀ = 10.")

    grid = np.logspace(-3, 2, 200)
    curve = pd.DataFrame({"lambda0": grid, "P": s.probability(grid, T) * 100})
    x = alt.X("lambda0:Q", scale=alt.Scale(type="log"), title="Baseline rate λ₀ (events / yr at max indices, no defences, certain escalation)")
    y = alt.Y("P:Q", scale=alt.Scale(domain=[0, 100]), title=f"P(catastrophe within {T} yr), %")
    tip = [alt.Tooltip("lambda0:Q", title="λ₀", format=".3g"), alt.Tooltip("P:Q", title="P, %", format=".3g")]
    point = pd.DataFrame({"lambda0": [lam0], "P": [float(s.probability(lam0, T)) * 100]})
    chart = line(curve, x, y, tooltip=tip) + alt.Chart(point).mark_point(size=140, filled=True, color=S2, opacity=1).encode(x=x, y=y, tooltip=tip)
    right.altair_chart(chart, width="stretch")

# ---------------------------------------------------------------- defences
with tab_def:
    lesson(
        "**Layers, and the hole they share.** Three layers that each stop 90% of events would let through 1 in 1,000, "
        "*if* they failed independently. Real barriers share weaknesses. With probability ρ one flaw defeats them all, so V never falls below ρ. "
        "The floor is a modelling hypothesis; an adaptive adversary is the reason to believe it.",
        ["Set **ρ** to 0 and raise the three layers: V falls towards zero.", "Now set ρ to 0.10 and raise them again: V stalls at 0.10.",
         "In the scorer, see a near-miss come out more alarming than the naive estimate."],
        "§6.2 Residual vulnerability, §9.1 Precursors",
    )  # fmt: skip
    left, right = st.columns([3, 2])
    rho_now, layers_now = float(s.effective_rho), [float(v) for v in s.effective_layers]
    grid = np.linspace(0, 0.99, 200)
    same = np.repeat(grid[:, None], 3, axis=1)
    names = ["independent layers (ρ = 0)", f"with common-mode bypass (ρ = {rho_now:.2f})"]
    floor = pd.concat([pd.DataFrame({"e": grid, "V": cg.residual_vulnerability(same, r), "Layers": n}) for n, r in zip(names, (0.0, rho_now))])
    colour = alt.Color("Layers:N", scale=alt.Scale(domain=names, range=[S1, S2]), legend=alt.Legend(orient="top", title=None))
    x = alt.X("e:Q", title="Effectiveness of each of the three layers")
    y = alt.Y("V:Q", scale=alt.Scale(type="log", domain=[1e-4, 1], clamp=True), title="Residual vulnerability V (log)")
    tip = ["Layers", alt.Tooltip("e:Q", format=".2f"), alt.Tooltip("V:Q", format=".4f")]
    you = pd.DataFrame({"e": [float(np.mean(layers_now))], "V": [float(s.V)]})
    here = alt.Chart(you).mark_point(size=160, filled=True, color=S3, opacity=1).encode(x=x, y=y, tooltip=[alt.Tooltip("V:Q", title="Your V", format=".4f")])
    left.altair_chart(line(floor, x, y, colour, tip) + here, width="stretch")
    left.caption("Green dot: your current V, plotted at the average effectiveness of your three layers.")
    with right:
        focus("v", "how much gets through, and how close it is to its floor").metric(
            "V against its floor ρ", f"{float(s.V):.3f}", f"floor {rho_now:.2f} is {rho_now / float(s.V):.0%} of V", delta_color="off")

    with right.container(border=True):
        st.markdown("**Score a near-miss**")
        st.caption("Nuclear safety scores each precursor by how close it came to core damage. The same idea works here.")
        passed_n = st.radio("How many layers did the event get past before it was stopped?", [0, 1, 2], index=2, horizontal=True)
        score = precursors.conditional_catastrophe_probability(layers_now[:passed_n], layers_now[passed_n:], rho_now, float(s.p_I))
        naive = float(np.prod([1 - v for v in layers_now[passed_n:]]) * s.p_I)
        a, b = st.columns(2)
        a.metric("Chance it would have completed", f"{score:.1%}")
        b.metric("Naive estimate", f"{naive:.1%}", help="Multiplying the miss rates of the remaining layers, as if the layers were independent")
        if passed_n:
            st.markdown("Getting past layers is *evidence* that a shared weakness is in play, so the true score is higher than the naive one.")

# ---------------------------------------------------------------- levers
with tab_levers:
    lesson(
        "**Where would effort pay off?** Every term is a lever. Each bar shows how far the hazard falls if that lever improves by 10%. "
        "These are relative statements, so they hold whatever λ₀ is.",
        ["With the paper's example, every consequence-side lever gives exactly 10%. That is what a multiplicative model means.",
         "Raise **ρ** to 0.3: the layer bars collapse and only ρ is worth improving.",
         "Turn on **coupling**: capability's bar overtakes the others, because capability now moves them too."],
        "§11 Sensitivity, §14 What levers act on which variables",
    )  # fmt: skip
    changes = {f"{NAMES[key]} −10%": {key: p[key] * 0.9} for key in "CAOXM"}
    changes |= {f"{name}: 10% fewer misses": {f"e{i}": 1 - 0.9 * (1 - p[f"e{i}"])} for i, name in enumerate(LAYERS)}
    changes |= {"Common-mode ρ −10%": {"rho": p["rho"] * 0.9}, "Recovery time −10%": {"tau": p["tau"] * 0.9}, "Escalation rate −10%": {"r_esc": p["r_esc"] * 0.9}}
    rows = [{"Lever": k, "Hazard reduction, %": (1 - rate(scenario(p, **v)) / rate(s)) * 100, "Side": "consequence" if i < 5 else "control"}
            for i, (k, v) in enumerate(changes.items())]  # fmt: skip
    best = max(rows, key=lambda r: r["Hazard reduction, %"])
    focus("lever", "the lever where a 10% improvement buys most").metric("Best lever", f"−{best['Hazard reduction, %']:.1f}% hazard", best["Lever"], delta_color="off")
    bars = alt.Chart(pd.DataFrame(rows)).mark_bar(cornerRadiusEnd=4, height=16).encode(
        x=alt.X("Hazard reduction, %:Q"), y=alt.Y("Lever:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
        color=alt.Color("Side:N", scale=alt.Scale(domain=["consequence", "control"], range=[S2, S1]), legend=alt.Legend(orient="top", title=None)),
        tooltip=["Lever", "Side", alt.Tooltip("Hazard reduction, %:Q", format=".2f")]).properties(height=alt.Step(28))  # fmt: skip
    st.altair_chart(bars, width="stretch")
    if p["g"] == 0 and p["rho"] / float(s.V) > 0.5:
        st.warning(f"The common-mode floor is {p['rho'] / float(s.V):.0%} of V. Better individual layers buy little now; only a lower ρ does.")
    if p["g"] > 0:
        st.info("With coupling on, capability also moves access, agency, exposure and the defences, so its bar exceeds the 10% a separable model gives.")

# ---------------------------------------------------------------- what if
with tab_whatif:
    lesson(
        "**Who moves which term?** Model advances, governments and open-weight releases do not act on *risk* in general. Each acts on particular terms. "
        "Dial in a mix and see the net change in hazard, which holds whatever λ₀ is. "
        "The mapping from driver to term follows the paper. **The effect sizes are placeholders**, there to show direction and structure.",
        ["Turn **Frontier capability jump** to 100%, then try to cancel it using only the government column.",
         "Open weights has two sliders because the paper splits it: proliferation raises access and weakens safeguards, the defensive ecosystem improves layers and lowers ρ. Find where they break even.",
         "Switch scenario in the sidebar. The same lever matters more or less depending on the scenario."],
        "§13 The open-weight question, §14 What levers act on which variables",
    )  # fmt: skip
    headline = st.container(border=True, key="whatif_head")  # filled in below, so the result stays in view above the sliders
    strengths = {}
    for col, group in zip(st.columns(len(GROUPS)), GROUPS):
        col.markdown(f"**{group}**")
        for lever in (lv for lv in LEVERS if lv.group == group):
            acts = ", ".join(f"{NAMES[k]} {'↑' if u > 0 else '↓'}" for k, u in lever.effects.items())
            strengths[lever.name] = col.slider(lever.name, 0, 100, 0, 10, format="%d%%", help=f"{lever.description}\n\nActs on: {acts}") / 100
            col.caption(f"Acts on: {acts}")

    active = {k: v for k, v in strengths.items() if v > 0}
    flat = {k: p[k] for k in KEYS[:-1]} | {"nu": 1.0}
    after = scenario(p, **apply_levers(flat, active))
    ratio = rate(after) / rate(s)
    solo = pd.DataFrame([{"Driver": k, "Change in hazard, %": (rate(scenario(p, **apply_levers(flat, {k: v}))) / rate(s) - 1) * 100} for k, v in active.items()])
    open_only = {k: v for k, v in active.items() if k.startswith("Open weights")}
    with headline:
        h = st.columns([1.4, 1, 1, 1])
        with h[0]:
            h0 = focus("whatif", "net effect")
        h0.metric("Hazard changes by", f"×{ratio:.2f}", f"{ratio - 1:+.0%}", delta_color="inverse")
        h[1].metric("Shift in the Control Gap Index", f"{np.log(ratio):+.2f}", help="The log of the hazard ratio. Independent of λ₀.")
        if open_only:
            net = rate(scenario(p, **apply_levers(flat, open_only))) / rate(s)
            h[2].metric("Open weights alone", f"{net - 1:+.0%}", help="The sign depends on the scenario and on how strong the defensive side really is. The framework does not settle the question; it says which measurements would.")
        else:
            h[2].metric("Open weights alone", "not applied")
        if active:
            top = solo.loc[solo["Change in hazard, %"].abs().idxmax()]
            h[3].metric("Strongest driver", f"{top['Change in hazard, %']:+.0f}%", top["Driver"], delta_color="off")
        else:
            h[3].metric("Strongest driver", "none yet", "move a slider below", delta_color="off")

    st.divider()
    b, c = st.columns(2)
    if not active:
        b.info("Move a slider above to apply a driver.")
    else:
        solo["Effect"] = np.where(solo["Change in hazard, %"] >= 0, "raises hazard", "lowers hazard")
        b.markdown("**Each driver on its own**")
        b.altair_chart(alt.Chart(solo).mark_bar(cornerRadiusEnd=4, height=16).encode(
            x=alt.X("Change in hazard, %:Q"), y=alt.Y("Driver:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280)),
            color=alt.Color("Effect:N", scale=alt.Scale(domain=["raises hazard", "lowers hazard"], range=[S2, S1]), legend=alt.Legend(orient="top", title=None)),
            tooltip=["Driver", alt.Tooltip("Change in hazard, %:Q", format="+.1f")]).properties(height=alt.Step(30)), width="stretch")  # fmt: skip
        b.caption("Drivers combine multiplicatively, so the bars do not simply add up to the total.")
    before_after = {"Episodes ν": (1.0, float(after.nu))} | {NAMES[k]: (float(s.effective[k]), float(after.effective[k])) for k in "CAOXM"}
    before_after |= {NAMES["V"]: (float(s.V), float(after.V)), NAMES["p_I"]: (float(s.p_I), float(after.p_I))}
    table = pd.DataFrame([{"Term": k, "Before": f"{u:.3f}", "After": f"{v:.3f}", "Change": "" if np.isclose(u, v) else f"{v / u - 1:+.0%}"} for k, (u, v) in before_after.items()])
    c.markdown("**Which terms moved**")
    c.dataframe(table, hide_index=True, width="stretch")

# ---------------------------------------------------------------- CGI
with tab_cgi:
    lesson(
        "**Which way is it moving?** The Control Gap Index compares today's hazard with a reference year. The unknown λ₀ cancels, "
        "so everything here can be measured now. Zero means *the balance of the reference year*, not *safe*. **The slope is the signal.**",
        ["The defaults are the paper's dashboard: K grows 26% a year, control only a few.", "Make control win: push **Detection** to +3 points and **Recovery time** to −20%.",
         "Stretch the horizon to 30 years. The indices hit their ceiling and only episode volume ν keeps growing."],
        "§7 The Control Gap Index, §15 A dashboard",
    )  # fmt: skip
    a, b, c = st.columns(3)
    a.markdown("**Consequence side**, growth % / yr")
    growth = {k: a.slider(label, -10, 50, d, key=f"g_{k}") / 100 for k, label, d in
              [("nu", "Episodes ν", 10), ("C", "Capability", 5), ("A", "Access", 2), ("O", "Agency", 4), ("X", "Exposure", 3), ("M", "Propensity", 0)]}  # fmt: skip
    b.markdown("**Control side**, change per yr")
    d_e = [b.slider(f"{name} (points)", -3.0, 3.0, d, 0.5, key=f"de_{i}") / 100 for i, (name, d) in enumerate(zip(LAYERS, (1.5, 1.0, 0.0)))]
    d_rho = b.slider("Common-mode ρ (points)", -2.0, 2.0, 0.5, 0.1) / 100
    d_tau = b.slider("Recovery time (%)", -20, 20, -3) / 100
    horizon = b.slider("Horizon (years)", 3, 30, 10)

    t = np.arange(horizon + 1)
    series = {k: np.minimum(p[k] * (1 + growth[k]) ** t, 1.0) for k in "CAOXM"}
    series["nu"] = (1 + growth["nu"]) ** t
    series |= {f"e{i}": np.clip(p[f"e{i}"] + d * t, 0.0, 0.99) for i, d in enumerate(d_e)}
    series["rho"] = np.clip(p["rho"] + d_rho * t, 0.0, 1.0)
    series["tau"] = p["tau"] * (1 + d_tau) ** t
    parts = cg.cgi_contributions(scenario(p, **series))
    total = sum(parts.values())
    slope = cg.cgi_slope(t, total)

    K, Gamma = sum(parts[k] for k in ("nu", "C", "A", "O", "X", "M")), -(parts["V"] + parts["p_I"])
    k_growth, gamma_growth = float(np.expm1(K[-1] / horizon)), float(np.expm1(Gamma[-1] / horizon))
    render_hero(hero, slope, k_growth, gamma_growth, horizon)
    with c:
        focus("cgi", "the same number as the banner above").metric("Implied hazard growth", f"{cg.hazard_growth(slope):+.0%} / yr", f"CGI slope {slope:+.3f}", delta_color="off")
    c.metric("Consequential capability K", f"{k_growth:+.0%} / yr")
    c.metric("Control & resilience Γ", f"{gamma_growth:+.0%} / yr")
    capped = [k for k in "CAOXM" if series[k][-1] >= 1.0 and growth[k] > 0]
    if capped:
        c.warning(f"{', '.join(capped)} hit the ceiling of 1. After that only ν can still grow.")

    wide = pd.DataFrame({"Year": 2026 + t, "CGI": total, "Δln K (consequence)": K, "−Δln Γ (control)": -Gamma})
    long = wide.melt("Year", var_name="Series", value_name="Value")
    colour = alt.Color("Series:N", scale=alt.Scale(domain=["CGI", "Δln K (consequence)", "−Δln Γ (control)"], range=[S1, S2, S3]), legend=alt.Legend(orient="top", title=None))
    tip = ["Year", "Series", alt.Tooltip("Value:Q", format="+.3f")]
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK).encode(y="y:Q")
    st.altair_chart(zero + line(long, alt.X("Year:Q", axis=alt.Axis(format="d")), alt.Y("Value:Q", title="Log change vs 2026"), colour, tip), width="stretch")

    contrib = pd.DataFrame({"Term": [NAMES[k] for k in parts], "Contribution": [float(v[-1]) for v in parts.values()]})
    contrib["Side"] = np.where(contrib["Contribution"] >= 0, "raises hazard", "lowers hazard")
    st.markdown(f"**What drives the index after {horizon} years**")
    st.altair_chart(alt.Chart(contrib).mark_bar(cornerRadiusEnd=4, height=14).encode(
        x=alt.X("Contribution:Q", title="Contribution to CGI"), y=alt.Y("Term:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
        color=alt.Color("Side:N", scale=alt.Scale(domain=["raises hazard", "lowers hazard"], range=[S2, S1]), legend=alt.Legend(orient="top", title=None)),
        tooltip=["Term", alt.Tooltip("Contribution:Q", format="+.3f")]).properties(height=alt.Step(26)), width="stretch")  # fmt: skip


# ---------------------------------------------------------------- Monte Carlo
@st.cache_data(show_spinner="Sampling…")
def run_mc(means: tuple, e_mean: float, rho_mean: float, pI_mean: float, conc: float, r: float, median: float, log_sd: float, T: float, n: int):
    clip = lambda m: float(np.clip(m, 0.01, 0.99))
    cfg = MCConfig(index_means={k: clip(v) for k, v in means}, index_concentration=conc, correlation=r,
                   effectiveness=beta_params(clip(e_mean), 10), rho=beta_params(clip(rho_mean), 20), p_I=beta_params(clip(pI_mean), 12),
                   lambda0_median=median, lambda0_log_sd=log_sd, T=T)  # fmt: skip
    return simulate(cfg, n).probabilities, spread_decomposition(cfg, n)


with tab_mc:
    lesson(
        "**Every input is uncertain, so carry distributions, not point values.** Two lessons. First, shading each factor down independently "
        "*hides the tail*: high capability tends to come with broad access, agency and exposure. Second, most of the width of the result "
        "comes from what you *assumed* about λ₀, not from the model.",
        ["Move **correlation** from 0 to 0.9: the median barely moves, the upper tail fattens and the mean rises.", "Set **log-sd of λ₀** to 0 to see the uncertainty the model itself produces."],
        "§10 Uncertainty, correlation and the multiple-stage fallacy",
    )  # fmt: skip
    a, b = st.columns([1, 3])
    r = a.slider("Correlation between indices", 0.0, 0.9, 0.6, 0.05)
    median = a.select_slider("Median λ₀", options=[0.001, 0.01, 0.1, 1, 10], value=0.1, key="mc_median")
    log_sd = a.slider("Log-sd of λ₀", 0.0, 3.0, 1.5, 0.1)
    conc = a.slider("Confidence in the indices", 4.0, 100.0, 12.0, 1.0, help="Beta concentration. Higher means narrower.")
    T_mc = a.slider("Horizon T (years)", 1, 50, 10, key="mc_T")
    means = tuple((k, p[k]) for k in "CAOXM")
    args = (means, float(np.mean([p["e0"], p["e1"], p["e2"]])), p["rho"], float(s.p_I), conc)
    runs = {"independent": run_mc(*args, 0.0, median, log_sd, T_mc, 50_000), f"correlated (r = {r:g})": run_mc(*args, r, median, log_sd, T_mc, 50_000)}

    edges = np.linspace(-7, 0, 71)
    hist = pd.concat([pd.DataFrame({"log10 P": edges[:-1], "Density": np.histogram(np.log10(np.maximum(P, 1e-7)), edges, density=True)[0], "Indices": name})
                      for name, (P, _) in runs.items()])  # fmt: skip
    colour = alt.Color("Indices:N", scale=alt.Scale(domain=list(runs), range=[S1, S2]), legend=alt.Legend(orient="top", title=None))
    chart = alt.Chart(hist).mark_line(interpolate="step-after", strokeWidth=2).encode(
        x=alt.X("log10 P:Q", title=f"log₁₀ P(catastrophe within {T_mc} yr)"), y="Density:Q", color=colour,
        tooltip=["Indices", alt.Tooltip("log10 P:Q", format=".2f"), alt.Tooltip("Density:Q", format=".3f")])  # fmt: skip
    b.altair_chart(chart, width="stretch")
    P_corr = runs[f"correlated (r = {r:g})"][0]
    with a:
        focus("mc", "the mean, not the median").metric("Mean probability", f"{P_corr.mean():.2%}", f"median {np.median(P_corr):.2%}, {P_corr.mean() / np.median(P_corr):.1f}× lower", delta_color="off")

    table = pd.DataFrame({name: {"Median": f"{np.median(P):.3%}", "Mean": f"{P.mean():.3%}", "5%": f"{np.quantile(P, 0.05):.1e}", "95%": f"{np.quantile(P, 0.95):.1e}"}
                          for name, (P, _) in runs.items()}).T  # fmt: skip
    b.dataframe(table, width="stretch")
    spread = runs["independent"][1]
    a.info(f"90% interval: **{spread['all']:.1f}** orders of magnitude. λ₀ alone gives **{spread['lambda0_only']:.1f}**; everything else gives **{spread['without_lambda0']:.1f}**. "
           "Most of the width is assumed, not derived.")  # fmt: skip
