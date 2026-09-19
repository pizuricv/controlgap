"""The chapters of the ControlGap app. Each one teaches a single idea and carries its own controls."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import controlgap as cg
from controlgap import precursors as cg_precursors
from controlgap.levers import GROUPS, LEVERS, apply_levers
from controlgap.mc import MCConfig, beta_params, simulate, spread_decomposition
from incidents import BY_KEY, INCIDENTS, RUNGS
from ui import (
    BASE_PRESETS,
    FIT,
    INCIDENT_ISSUE,
    KEYS,
    LAYERS,
    NAMES,
    PAPER,
    PRESETS,
    REPO,
    S1,
    S2,
    S3,
    bars,
    flat,
    focus,
    hero,
    label_colour,
    load_preset,
    next_chapter,
    num,
    opener,
    P,
    rate,
    ratio_words,
    scenario,
    slider,
    strip,
    takeaway,
    tex,
    trend,
    try_this,
)

# What a unit of effort costs on each lever. App framing, not part of the model.
COST = {
    "Frontier capability jump": 0, "Agentic deployment boom": 0, "Alignment progress": 45, "AI-powered defence": 25,
    "Compute governance and export controls": 40, "Mandatory evaluations and incident reporting": 20,
    "Critical-infrastructure integration rules": 30, "Know-your-customer and liability": 20, "Incident response capacity": 15,
    "Open weights: proliferation": 0, "Open weights: defensive ecosystem": 15,
}  # fmt: skip
BUDGET = 100


def go(name: str):
    return st.session_state["pages"][name]



def _pick_incident(key: str):
    st.session_state["incident"] = key


def _start_from_incident(key: str):
    """Selecting an event sets it as your scenario, exactly like the scenario cards."""
    _pick_incident(key)
    load_preset(BY_KEY[key].scenario_name)


def incident_cards(on_start: bool = False):
    """The precursor events as cards, in the same language as the scenario cards."""
    selected = st.session_state.get("incident", INCIDENTS[0].key)
    for col, incident in zip(st.columns(len(INCIDENTS), gap="medium"), INCIDENTS):
        active = incident.key == selected and not on_start
        with col.container(key=f"card_{'active' if active else incident.key}"):
            icon = "\u26a0\ufe0f" if incident.rung >= 3 else "\U0001f9ea"
            teaser = incident.summary.split(". ")[0] + "."
            links = " \u00b7 ".join(f'<a href="{url}" target="_blank">{name}</a>' for name, url in incident.sources)  # kept out of the f-string: 3.10 forbids backslashes there
            st.markdown(
                f'<div class="cg-card-icon">{icon}</div>'
                f'<div class="cg-card-name">{RUNGS[incident.rung]}</div>'
                f'<div class="cg-card-body"><b>{incident.title}</b><br>'
                f'<span style="opacity:.75">{incident.when}</span><br><br>{teaser}<br><br>{links}</div>',
                unsafe_allow_html=True,
            )
            if on_start:
                chosen = st.session_state.preset == incident.scenario_name
                st.button(
                    "Selected" if chosen else "Choose",
                    key=f"start_{incident.key}",
                    width="stretch",
                    type="primary" if chosen else "secondary",
                    disabled=chosen,
                    on_click=_start_from_incident,
                    args=(incident.key,),
                )
            else:
                st.button(
                    "Showing" if active else "Examine",
                    key=f"pick_inc_{incident.key}",
                    width="stretch",
                    type="primary" if active else "secondary",
                    disabled=active,
                    on_click=_pick_incident,
                    args=(incident.key,),
                )


# ================================================================ 1. Start here
def start():
    opener(
        "Chapter 1 of 11",
        "How close is AI capability to consequential power?",
        "Frank Drake never knew how many alien civilisations existed. His equation mattered because it broke one "
        "unanswerable question into several that could be answered separately. This is the same move, for catastrophic AI risk.",
    )
    left, right = st.columns([3, 2], gap="large")
    left.markdown(
        """
**A capable system is not a dangerous one.** It becomes dangerous when capability turns into *consequential power*:
something that can be reached, can act, can touch things that matter, and that someone or something would actually
attempt — faster than we can detect, stop, contain and recover.

For a catastrophe, **every one of these has to line up at once**:
"""
    )
    left.markdown(
        """
| The consequence side | The control side |
|---|---|
| Is it **capable** enough? | Do we **detect** it? |
| Who can **access** it? | Can we **intervene**? |
| Can it **act**? | Can we **contain** it? |
| What can it **reach**? | Do the defences share a **blind spot**? |
| Would anyone **try**? | How fast do we **recover**? |
"""
    )
    with right.container(border=True):
        st.markdown("**What you will not find here**")
        st.markdown(
            "A probability of doom. The honest result in the paper is that **no such number is identifiable yet** — "
            "the same inputs give anything from 0.04% to 33%.\n\nWhat *is* measurable is the **trend**: whether "
            "consequential capability is pulling ahead of control. Eleven short chapters get you there."
        )
        st.caption("About fifteen minutes. Nothing you click can break it.")

    st.write("")
    st.markdown("#### Pick a scenario to carry with you")
    st.caption("It sets every starting value. You can change it any time, and switch scenarios from the sidebar. All values are illustrative.")
    for col, (name, preset) in zip(st.columns(len(BASE_PRESETS), gap="medium"), BASE_PRESETS.items()):
        active = name == st.session_state.preset
        with col.container(key=f"card_active" if active else f"card_{abs(hash(name)) % 10**6}"):
            st.markdown(
                f'<div class="cg-card-icon">{preset["icon"]}</div><div class="cg-card-name">{preset["short"]}</div>'
                f'<div class="cg-card-body"><b>{preset["tagline"]}</b><br>{preset["about"]}</div>',
                unsafe_allow_html=True,
            )
            st.button(
                "Selected" if active else "Choose",
                key=f"pick_{name}",
                width="stretch",
                type="primary" if active else "secondary",
                disabled=active,
                on_click=load_preset,
                args=(name,),
            )
    st.write("")
    st.markdown("#### Or start from something that actually happened")
    st.caption(
        "Three real, cited events. Choosing one sets your scenario from that event and you carry it through the tour, just like the "
        "four above. Chapter 6 comes back to them and scores how close each one came."
    )
    incident_cards(on_start=True)
    chosen = next((i for i in INCIDENTS if i.scenario_name == st.session_state.preset), None)
    if chosen:
        st.write("")
        with st.container(border=True):
            st.markdown(f"##### You are carrying: {chosen.title}")
            st.caption(f"{chosen.when} · rung {chosen.rung} of the precursor ladder: {RUNGS[chosen.rung]}")
            left, right = st.columns([3, 2], gap="large")
            left.markdown(chosen.summary)
            left.markdown("Sources: " + " · ".join(f"[{name}]({url})" for name, url in chosen.sources))
            right.markdown(f"**Why these starting values**\n\n{chosen.scenario_why}")
            right.markdown(" ".join(f"`{t}`" for t in chosen.tags))
            if right.button("See how close it came \u2192", width="stretch"):
                st.switch_page(go("precursors"))
    next_chapter("Chapter 2 · The chain", go("chain"))


# ================================================================ 2. The chain
def chain():
    opener(
        "Chapter 2 of 11 · Understand",
        "Everything has to line up",
        "Five things decide how much consequential power a system has. They multiply, so the hazard is only as large as "
        "the chain allows — and any one of them at zero ends it. Move them and watch the chain.",
        "§5 The causal chain, §6.1 Two kinds of quantity",
    )
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("**The consequence side**")
        slider("C", "Capability C", 0.01, 1.0, 0.01, help="What share of the capabilities this scenario needs has the system demonstrated?")
        slider("A", "Access A", 0.01, 1.0, 0.01, help="How many actors can get hold of that capability? Open weights push this up; API gating pushes it down.")
        slider("O", "Agency O", 0.01, 1.0, 0.01, help="Can it act? Tools, permissions, persistence, long unsupervised runs.")
        slider("X", "Exposure X", 0.01, 1.0, 0.01, help="What can it reach? Finance, cloud, industrial control, labs.")
        slider("M", "Propensity M", 0.01, 1.0, 0.01, help="Would the acting agent, human or AI, actually try? 1 is the worst case. This is where alignment work shows up.")
        with st.expander("Advanced: coupling, and thresholds (§6.5, §6.7)"):
            slider("g", "Coupling g", 0.0, 1.0, 0.05, help="A capable system can obtain access, agency and exposure for itself, and evade oversight. 0 means the five levers move independently.")
            st.session_state.gated = st.checkbox(
                "Treat capability as a threshold, not a power law", value=st.session_state.gated,
                help="Specification II: some dangerous tasks may be infeasible below a capability level and routine above it.")  # fmt: skip
            if st.session_state.gated:
                st.session_state.C0 = st.slider("Threshold C₀", 0.05, 0.95, st.session_state.C0, 0.05)
                st.session_state.k = st.slider("Steepness k", 1.0, 40.0, st.session_state.k, 1.0)

    s = scenario()
    eff = s.effective
    with right:
        st.markdown("**The chain, as you have set it**")
        stages = [("Every episode", 1.0)] + [(NAMES[k], float(cg.index_factor(k, eff[k], s.theta, s.gates))) for k in "CAOXM"]
        df = pd.DataFrame(stages, columns=["Stage", "Factor"])
        df["Remaining"] = df["Factor"].cumprod()
        base = alt.Chart(df).encode(
            y=alt.Y("Stage:N", sort=list(df["Stage"]), title=None, axis=alt.Axis(labelLimit=200)),
            x=alt.X("Remaining:Q", scale=alt.Scale(type="log"), title="Share of episodes still on the path",
                    axis=alt.Axis(values=[10.0**-k for k in range(0, 13)], format="~%", orient="top")),
            tooltip=["Stage", alt.Tooltip("Factor:Q", format=".3f"), alt.Tooltip("Remaining:Q", format=".2e")])  # fmt: skip
        text = base.mark_text(align="right", dx=-10, color=label_colour()).encode(text=alt.Text("Remaining:Q", format=".2~%"))
        st.altair_chart((base.mark_line(color=S1, strokeWidth=2) + base.mark_point(color=S1, filled=True, size=90, opacity=1) + text).properties(autosize=FIT, height=alt.Step(30)), width="stretch")

    st.latex(r"\text{consequence} \;=\; " + r" \times ".join(rf"\underbrace{{{tex(eff[k])}}}_{{{k}}}" for k in "CAOXM") + rf" \;=\; {tex(s.indices, 4)}")
    takeaway(
        "<b>This is a conjunction, and that cuts both ways.</b> It is why catastrophe is rare: five things must coincide. "
        "It is also why the picture is uncomfortable — every one of the five is trending upwards at once, and they are not independent. "
        "A more capable system gets its own access, its own agency and its own reach."
    )
    try_this("chain", [
        "Drag **Propensity M** to 0.01. The hazard nearly vanishes: this is what alignment work buys.",
        "Put **Capability C** at 0.9, then open the advanced expander and set coupling to 0.5. Watch the other four indices move on their own.",
        "Set any single slider to its minimum. One zero ends the chain — that is the Drake structure.",
    ])  # fmt: skip
    next_chapter("Chapter 3 · The number nobody has", go("lambda0"))


# ================================================================ 3. The missing number
def lambda0():
    opener(
        "Chapter 3 of 11 · Understand",
        "The number nobody has",
        "You now have a chain. Turning it into a probability needs one more thing: how often a catastrophe would happen "
        "if everything were at maximum and nothing stopped it. Nobody knows that number, because it has never happened.",
        "§12 An illustrative calibration",
    )
    s = scenario()
    T = st.slider("Horizon T (years)", 1, 50, 10)
    st.markdown("**Your chain, three defensible priors, one horizon.**")
    priors = [
        (0.1, "An attempt worth worrying about arises about once a decade."),
        (1.0, "About once a year."),
        (10.0, "Ten a year. The world is full of attempts."),
    ]
    for col, (lam, gloss) in zip(st.columns(3, gap="large"), priors):
        with col:
            st.caption(gloss)
            st.metric(f"λ₀ = {lam:g}", f"{float(s.probability(lam, T)):.2%}", label_visibility="visible")
    takeaway(
        "<b>Nothing about the world changed between those three columns.</b> The chain is identical, the defences are identical. "
        "The only thing that moved is a rate nobody has ever measured, because the event has never happened. "
        "Pick whichever column you prefer — that is exactly what a published p(doom) does, silently."
    )

    st.write("")
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown("**Or set your own**")
        lam0 = st.select_slider("Baseline rate λ₀ (events / yr)", options=[0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100], value=0.1)
        focus("p").metric(f"P(catastrophe within {T} yr)", f"{float(s.probability(lam0, T)):.2%}",
                          help="Only as good as your guess of λ₀, which nothing pins down.")  # fmt: skip
        halve = st.radio("Now halve one thing", ["Access", "Propensity", "Recovery time", "Nothing"], index=0)

    key = {"Access": "A", "Propensity": "M", "Recovery time": "tau"}.get(halve)
    grid = np.logspace(-3, 2, 200)
    frames = [pd.DataFrame({"lambda0": grid, "P": s.probability(grid, T), "Chain": "as you set it"})]
    if key:
        halved = scenario(**{key: P()[key] / 2})
        frames.append(pd.DataFrame({"lambda0": grid, "P": halved.probability(grid, T), "Chain": f"{halve.lower()} halved"}))
    df = pd.concat(frames)
    x = alt.X("lambda0:Q", scale=alt.Scale(type="log"), axis=alt.Axis(values=[0.001, 0.01, 0.1, 1, 10, 100], format="~g"),
              title="Baseline rate λ₀ (events / yr)")  # fmt: skip
    y = alt.Y("P:Q", scale=alt.Scale(type="log", domain=[1e-6, 1], clamp=True),
              axis=alt.Axis(values=[1, 0.1, 0.01, 0.001, 1e-4, 1e-5, 1e-6], format="~%"), title=f"P(catastrophe), {T} yr (log)")  # fmt: skip
    colour = alt.Color("Chain:N", scale=alt.Scale(range=[S1, S2]), legend=alt.Legend(orient="top", title=None, labelLimit=0))
    lines = alt.Chart(df).mark_line(strokeWidth=2).encode(x=x, y=y, color=colour,
                                                          tooltip=["Chain", alt.Tooltip("lambda0:Q", title="λ₀", format=".3g"), alt.Tooltip("P:Q", format=".2%")])  # fmt: skip
    point = pd.DataFrame({"lambda0": [lam0], "P": [float(s.probability(lam0, T))], "Chain": ["as you set it"]})
    mark = alt.Chart(point).mark_point(size=150, filled=True, color=S3, opacity=1).encode(x=x, y=y)
    right.altair_chart((lines + mark).properties(autosize=FIT, height=340), width="stretch")
    right.caption("λ₀ is the rate at maximum indices, with no defences and certain escalation. The dot is your setting.")

    if key:
        takeaway(
            "<b>Two parallel lines, and they stay parallel.</b> Halving that one thing divides the <i>hazard</i> by exactly the same "
            "factor at every λ₀ — all five orders of magnitude of it. The lines close up only at the top right, where both chains are "
            "near certainty and there is no room left. <b>The level is unknowable; the ratio is fixed.</b> That ratio is the only thing "
            "here you can measure, and the rest of the tour is about measuring it."
        )
    if abs(lam0 * T - 1) < 0.05:
        takeaway(
            f"<b>Notice the coincidence.</b> Your chain × defences is <b>{num(s.factor, 5)}</b>, and your {T}-year probability is "
            f"<b>{float(s.probability(lam0, T)):.2%}</b>. They are the same number, because λ₀ × T = 1 here. Anyone who reads a chain of "
            "factors straight off as a probability has picked λ₀T = 1 without knowing they picked anything — the paper's own first draft did.",
            warn=True,
        )
    else:
        st.caption(f"Set λ₀ = {1 / T:g} with T = {T} and watch the probability meet the chain × defences figure in the sidebar.")
    next_chapter("Chapter 4 · The layers", go("layers"))


# ================================================================ 4. The layers
def _cheese_svg(e_values, rho: float, ink: str) -> str:
    """Three barriers with holes. The hole sizes follow (1 - e); a shared channel opens as rho rises."""
    w, h, slab_w, gap = 520, 210, 66, 150
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Three defensive layers with holes that can line up">']
    offsets = ((-46, 34), (28, -30), (-18, 44))  # fixed hole positions, so only the sizes move
    for i, e in enumerate(e_values):
        x = 40 + i * gap
        parts.append(f'<rect x="{x}" y="18" width="{slab_w}" height="{h - 60}" rx="9" fill="{S1}" opacity="0.18" stroke="{S1}" stroke-opacity="0.5"/>')
        r = 6 + 26 * (1 - e)  # a weak layer has a big hole
        for dy in offsets[i]:
            parts.append(f'<ellipse cx="{x + slab_w / 2}" cy="{h / 2 - 12 + dy}" rx="{slab_w / 2 - 9}" ry="{r}" fill="#ffffff" fill-opacity="0.0" stroke="{S1}" stroke-opacity="0.45" stroke-dasharray="3 3"/>')
        parts.append(f'<ellipse cx="{x + slab_w / 2}" cy="{h / 2 - 12}" rx="{slab_w / 2 - 9}" ry="{r}" fill="{S2}" opacity="{0.22 + 0.5 * (1 - e):.2f}"/>')
        parts.append(f'<text x="{x + slab_w / 2}" y="{h - 26}" text-anchor="middle" font-size="11" fill="{ink}" opacity=".75">{LAYERS[i]}</text>')
        parts.append(f'<text x="{x + slab_w / 2}" y="{h - 12}" text-anchor="middle" font-size="11" fill="{ink}" opacity=".55">e = {e:.2f}</text>')
    y = h / 2 - 12
    parts.append(f'<line x1="6" y1="{y}" x2="{40 + 2 * gap + slab_w + 26}" y2="{y}" stroke="{S2}" stroke-width="{1 + 4 * min(rho / 0.3, 1):.1f}" opacity="{0.25 + 0.7 * min(rho / 0.3, 1):.2f}" stroke-dasharray="7 5"/>')
    parts.append(f'<text x="{40 + 2 * gap + slab_w + 30}" y="{y + 4}" font-size="11" fill="{S2}">ρ = {rho:.2f}</text>')
    parts.append("</svg>")
    return "".join(parts)


def layers():
    opener(
        "Chapter 4 of 11 · Control",
        "Three good layers, one shared blind spot",
        "Detection, intervention, containment. If they failed independently, three layers that each stop 90% would let "
        "one event in a thousand through. Real barriers are not independent — and that changes what is worth buying.",
        "§6.2 Residual vulnerability with correlated failures",
    )
    left, right = st.columns([1, 1], gap="large")
    with left:
        for i, name in enumerate(LAYERS):
            slider(f"e{i}", f"{name} effectiveness", 0.0, 0.99, 0.01, help="Probability that this layer stops an event that reaches it.")
        slider("rho", "Common-mode bypass ρ", 0.0, 0.5, 0.01, help="The chance that one weakness defeats every layer at once: a shared blind spot, one stolen credential, the same monitoring gap.")
        s = scenario()
        rho_now, layers_now = float(s.effective_rho), [float(v) for v in s.effective_layers]
        st.markdown(_cheese_svg(layers_now, rho_now, label_colour()), unsafe_allow_html=True)
        st.caption("Hole size follows each layer's miss rate. The dashed line is the shared channel: as ρ rises it cuts straight through all three.")

    with right:
        grid = np.linspace(0, 0.99, 200)
        same = np.repeat(grid[:, None], 3, axis=1)
        names = ["if the layers were independent", f"with a shared blind spot (ρ = {rho_now:.2f})"]
        df = pd.concat([pd.DataFrame({"e": grid, "V": cg.residual_vulnerability(same, r), "Layers": n}) for n, r in zip(names, (0.0, rho_now))])
        x = alt.X("e:Q", title="Effectiveness of each of the three layers")
        y = alt.Y("V:Q", scale=alt.Scale(type="log", domain=[1e-4, 1], clamp=True), axis=alt.Axis(values=[1, 0.1, 0.01, 0.001, 0.0001], format="~g", labelOverlap=False), title="Residual vulnerability V (log)")
        colour = alt.Color("Layers:N", scale=alt.Scale(domain=names, range=[S1, S2]), legend=alt.Legend(orient="top", title=None, labelLimit=0))
        curves = alt.Chart(df).mark_line(strokeWidth=2).encode(x=x, y=y, color=colour, tooltip=["Layers", alt.Tooltip("e:Q", format=".2f"), alt.Tooltip("V:Q", format=".4f")])
        you = pd.DataFrame({"e": [float(np.mean(layers_now))], "V": [float(s.V)]})
        here = alt.Chart(you).mark_point(size=160, filled=True, color=S3, opacity=1).encode(x=x, y=y) + alt.Chart(you).mark_text(text="your V", dx=12, align="left", color=label_colour()).encode(x=x, y=y)
        st.altair_chart((curves + here).properties(autosize=FIT), width="stretch")
        focus("v").metric("V — what gets through everything", num(s.V, 3), f"it can never go below ρ = {rho_now:.2f}", delta_color="off", delta_arrow="off")

    takeaway(
        f"<b>Perfect layers would still leave ρ.</b> Right now the shared blind spot is <b>{rho_now / float(s.V):.0%}</b> of everything that gets "
        "through. Past that point, making any single layer stronger buys almost nothing; making the layers <i>independent</i> is the "
        "only thing that moves V. Separate the monitoring from the monitored system, and diversify.",
        warn=rho_now / float(s.V) > 0.5,
    )
    st.markdown("#### Score a near-miss, the way nuclear safety does")
    if True:  # kept indented: this is the most surprising number in the app, so it is not hidden
        a, b = st.columns([2, 3])
        passed_n = a.radio("How many layers did the event get past before something stopped it?", [0, 1, 2], index=2, horizontal=True)
        score = cg_precursors.conditional_catastrophe_probability(layers_now[:passed_n], layers_now[passed_n:], rho_now, float(s.p_I))
        naive = float(np.prod([1 - v for v in layers_now[passed_n:]]) * s.p_I)
        c, d = a.columns(2)
        c.metric("Would have completed", f"{score:.1%}")
        d.metric("Naive estimate", f"{naive:.1%}", help="Multiplying the miss rates of the layers still standing, as if they were independent.")
        b.markdown(
            "The US Nuclear Regulatory Commission has scored reactor near-misses since 1979 by asking how likely each one was "
            "to have gone all the way. It is how you calibrate an event that has never happened.\n\n"
            "**Getting past layers is evidence that a shared weakness is in play**, so the real score is higher than the naive one. "
            "That is the same ρ, read backwards from an incident."
        )
    next_chapter("Chapter 5 · The race", go("race"))


# ================================================================ 5. The race
def race():
    opener(
        "Chapter 5 of 11 · Control",
        "The race you do not get to re-run",
        "Something got through. Now two clocks start: the event spreading, and you detecting, isolating and restoring. "
        "Whichever finishes first decides whether this is an incident you talk about afterwards, or one you cannot undo.",
        "§6.3 Irreversibility as a race",
    )
    left, right = st.columns([1, 1], gap="large")
    with left:
        slider("r_esc", "Escalation rate (per day)", 0.01, 5.0, 0.01, help="How fast an event that got through grows beyond repair.")
        slider("tau", "Mean time to recover (days)", 0.05, 20.0, 0.05, help="Time to detect, isolate and restore.")
        s = scenario()
        p_I = float(s.p_I)
        focus("race").metric("Of 100 events that get through…", f"{p_I * 100:.0f} become irreversible", f"recovery wins the other {100 - p_I * 100:.0f}", delta_color="off", delta_arrow="off")
        st.latex(r"p_I = \frac{r_{\text{esc}}}{r_{\text{esc}} + r_{\text{rec}}} = " + f"{p_I:.2f}")
        st.caption(f"Escalation runs at {P()['r_esc']:.2f}/day; recovery at {1 / P()['tau']:.2f}/day (τ = {P()['tau']:.2f} days).")

    with right:
        rng = np.random.default_rng(11)
        n = 100
        escalated = np.sort(rng.random(n) < p_I)[::-1]  # sorted, so the proportion is legible at a glance
        grid_df = pd.DataFrame({
            "col": np.arange(n) % 10, "row": np.arange(n) // 10,
            "Outcome": np.where(escalated, "irreversible", "recovered in time"),
        })  # fmt: skip
        chart = alt.Chart(grid_df).mark_point(filled=True, size=210, opacity=1).encode(
            x=alt.X("col:O", axis=None), y=alt.Y("row:O", axis=None),
            color=alt.Color("Outcome:N", scale=alt.Scale(domain=["recovered in time", "irreversible"], range=[S1, S2]), legend=alt.Legend(orient="top", title=None, labelLimit=0)),
            shape=alt.Shape("Outcome:N", scale=alt.Scale(domain=["recovered in time", "irreversible"], range=["circle", "cross"]), legend=None),
            tooltip=["Outcome"])  # fmt: skip
        st.altair_chart(chart.properties(height=230, autosize=FIT), width="stretch")
        st.caption("One hundred events that already defeated every layer. The crosses are the ones nobody gets to take back.")

    takeaway(
        "<b>This term is where reversibility lives.</b> Almost every other number in this model is about making bad things rarer. "
        "This one is about what happens when rarity fails anyway — and it is the only place where <i>speed</i> is the whole story. "
        "Backups, drills, kill switches, blast-radius limits and circuit breakers all show up here, nowhere else."
    )
    takeaway(
        "One caveat worth saying out loud: both clocks here are memoryless, which suits accidents. An adversary that waits for "
        "your recovery capacity to be at its lowest before it escalates breaks that assumption, and then <b>p<sub>I</sub> is an underestimate</b>.",
        warn=True,
    )
    try_this("race", [
        "Cut **recovery time** in half. The count of crosses falls: that is the whole return on incident response.",
        "Set escalation to 5/day and recovery to 10 days — the bio-misuse shape. Almost nothing is recoverable.",
        "Try to reach zero crosses. You cannot; you can only make them rare.",
    ])  # fmt: skip
    next_chapter("Chapter 6 · What nearly happened", go("precursors"))


# ================================================================ 6. Precursors
def precursors_chapter():
    opener(
        "Chapter 6 of 11 · Evidence",
        "Nothing has happened yet. Calibrate on what nearly did",
        "No irreversible AI catastrophe has occurred, so none of these numbers can be fitted to outcomes. Nuclear safety hit the same "
        "wall and answered it with precursors: score the near-misses by how close they came. The US NRC has done exactly that since 1979. "
        "Here are three real events, scored against the scenario you are carrying.",
        "§9.1 Identifiability and precursors",
    )
    st.caption(
        "Each summary follows its cited source. **Placing an event on this model's layers is our judgement, not the source's** — "
        "it is there to show the method. Disagree loudly; there is a button at the bottom."
    )
    incident_cards()
    st.write("")
    incident = BY_KEY[st.session_state.get("incident", INCIDENTS[0].key)]

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"##### {incident.title}")
        st.caption(f"{incident.when} · rung {incident.rung} of the ladder: {RUNGS[incident.rung]}")
        st.markdown(incident.summary)
        st.markdown(" ".join(f"`{t}`" for t in incident.tags))
        st.markdown("Sources: " + " · ".join(f"[{name}]({url})" for name, url in incident.sources))

    s = scenario()
    rho_now, layers_now = float(s.effective_rho), [float(v) for v in s.effective_layers]
    with right:
        if incident.layers_passed is None:
            focus("precursor").metric("What this one measures", "Propensity M", f"you have it at {float(s.effective['M']):.2f}", delta_color="off", delta_arrow="off")
        else:
            n = incident.layers_passed
            score = cg_precursors.conditional_catastrophe_probability(layers_now[:n], layers_now[n:], rho_now, float(s.p_I))
            naive = float(np.prod([1 - v for v in layers_now[n:]]) * s.p_I)
            focus("precursor").metric(
                "Chance it would have completed", f"{score:.1%}",
                f"naive estimate {naive:.1%}", delta_color="off", delta_arrow="off",
                help="Scored against your current layer effectivenesses, ρ and p_I. Getting past layers is evidence that a shared weakness is in play, so the honest score beats the naive one.")  # fmt: skip
            st.caption(f"Passed **{n}** of 3 layers before something stopped it.")
        st.info(incident.mapping_note, icon=":material/rule:")
        if st.session_state.preset == incident.scenario_name:
            st.success("Your scenario is set from this event.", icon=":material/check:")
        elif st.button("Use this event as my scenario", width="stretch", icon=":material/tune:"):
            _start_from_incident(incident.key)
            st.rerun()

    takeaway(incident.teaches)
    if incident.caveat:
        takeaway(incident.caveat, warn=True)

    st.divider()
    a, b = st.columns([3, 2], gap="large")
    a.markdown(
        "**Why this is the only route.** Everything else in this model is a hypothesis about a thing that has never happened. Precursors are "
        "the one place real numbers can enter: layer effectivenesses from how often each one catches something, ρ from how often a single "
        "weakness defeats several at once, the recovery clock from how long incidents actually take to close.\n\n"
        "It rests on one assumption worth saying out loud: **precursors must share the catastrophe's elasticities**. Calibrating on near-misses "
        "assumes whatever drives a near-miss drives a catastrophe in the same proportion. Probabilistic risk assessment is criticised for exactly "
        "this extrapolation, and the criticism lands here too."
    )
    with b.container(border=True):
        st.markdown("**Know a better example?**")
        st.caption("Real, cited events only. Opens a pre-filled issue under your own GitHub account.")
        st.link_button("Propose an event", INCIDENT_ISSUE, width="stretch", icon=":material/add_link:")

    st.divider()
    with st.expander("Advanced: estimate the exponents from precursor counts (§11)"):
        _fit_panel()
    next_chapter("Chapter 7 · Where effort pays", go("levers"))


def _fit_panel():
    """Estimate the elasticities from precursor counts, which is what §11 calls the scientific target."""
    st.markdown("#### Then you can stop guessing the exponents")
    st.markdown(
        "Everywhere else in this app the elasticities θ are set to 1, because that is the paper's prior and nothing better exists yet. "
        "They are not supposed to stay that way. Given enough precursor counts across periods where the indices differed, they can be "
        "**estimated**: a Poisson regression of counts on the log indices, with episode volume as the exposure."
    )
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.caption("One row per period or deployment. Edit the numbers, add rows, or paste your own.")
        seed = pd.DataFrame({
            "Episodes ν": [50_000, 80_000, 120_000, 200_000, 260_000, 340_000],
            "Access A": [0.30, 0.38, 0.50, 0.62, 0.70, 0.80],
            "Agency O": [0.20, 0.35, 0.30, 0.55, 0.50, 0.75],
            "Precursors seen": [3, 9, 17, 48, 61, 132],
        })  # fmt: skip
        table = st.data_editor(seed, width="stretch", num_rows="dynamic", key="fit_rows",
                               column_config={c: st.column_config.NumberColumn(format="%.2f" if "0." in str(seed[c][0]) else "%d") for c in seed.columns})  # fmt: skip
    with right:
        rows = table.dropna()
        if len(rows) < 3:
            st.info("Needs at least three complete rows.", icon=":material/info:")
            return
        try:
            fit = cg_precursors.fit_elasticities(
                rows["Precursors seen"].to_numpy(),
                rows["Episodes ν"].to_numpy(),
                {"A": rows["Access A"].to_numpy(), "O": rows["Agency O"].to_numpy()},
            )
        except Exception as err:  # collinear or constant indices, mostly
            st.warning(f"No fit: {err}", icon=":material/warning:")
            return
        for name, label in (("A", "θ for access"), ("O", "θ for agency")):
            lo, hi = fit.interval(name)
            st.metric(label, f"{fit.theta[name]:.2f}", f"90% interval {lo:.2f} to {hi:.2f}", delta_color="off", delta_arrow="off")
            if lo < 0 < hi:
                st.caption("The interval spans zero: with this much data the fit cannot tell you the sign, let alone the size. That is the honest state of the field.")
        st.caption(f"Per-episode precursor rate at indices of 1: {np.exp(fit.log_scale):.2e}")
    takeaway(
        "<b>This is the scientific target (§11).</b> “Access matters more than capability” is not an opinion, it is the claim "
        "θ<sub>A</sub> &gt; θ<sub>C</sub> — something precursor data can settle. Note what the fit does <i>not</i> give you: "
        "λ₀ is still missing, so this buys you the shape of the hazard, never its level."
    )
    takeaway(
        "And it inherits the assumption from above. These θ describe <i>precursors</i>. Carrying them over to catastrophes assumes the two "
        "share elasticities — the step every precursor programme has to make, and the one it can never fully justify.",
        warn=True,
    )


# ================================================================ 7. The levers
def levers():
    opener(
        "Chapter 7 of 11 · Act",
        "Where would effort actually pay?",
        "You have all the pieces now. Each bar shows how far the hazard falls if that one thing improves by 10%. "
        "These are ratios, so they hold whatever λ₀ turns out to be.",
        "§11 Sensitivity, §14 What levers act on which variables",
    )
    s = scenario()
    p = P()
    changes = {f"{NAMES[key]} −10%": {key: p[key] * 0.9} for key in "CAOXM"}
    changes |= {f"{name}: 10% fewer misses": {f"e{i}": 1 - 0.9 * (1 - p[f"e{i}"])} for i, name in enumerate(LAYERS)}
    changes |= {"Shared blind spot ρ −10%": {"rho": p["rho"] * 0.9}, "Recovery time −10%": {"tau": p["tau"] * 0.9}, "Escalation rate −10%": {"r_esc": p["r_esc"] * 0.9}}
    rows = [{"Lever": k, "Hazard reduction, %": (1 - rate(scenario(**v)) / rate(s)) * 100, "Side": "consequence" if i < 5 else "control"} for i, (k, v) in enumerate(changes.items())]
    best = max(rows, key=lambda r: r["Hazard reduction, %"])

    left, right = st.columns([3, 2], gap="large")
    left.altair_chart(bars(pd.DataFrame(rows), "Hazard reduction, %", "Lever", "Side", ["consequence", "control"], [S2, S1], ".2f"), width="stretch")
    with right:
        focus("lever").metric("Best value for 10% of effort", f"−{best['Hazard reduction, %']:.1f}% hazard", best["Lever"], delta_color="off", delta_arrow="off")
        st.write("")
        try_this("levers", [
            "With the paper's example, every consequence-side bar is exactly 10%. That is what a multiplicative model means: no favourites.",
            "Raise **ρ** in chapter 4 to 0.3 and come back. The three layer bars collapse and only ρ is worth touching.",
            "Turn on **coupling** in chapter 2. Capability's bar overtakes everything, because capability now moves the others too.",
        ])  # fmt: skip

    if p["g"] == 0 and p["rho"] / float(s.V) > 0.5:
        takeaway(f"The shared blind spot is {p['rho'] / float(s.V):.0%} of V, which is why the three layer bars are so short. Independence, not strength.", warn=True)
    if p["g"] > 0:
        takeaway("Coupling is on, so capability's bar includes everything it drags with it. That is why it beats the separable levers.")
    takeaway(
        "<b>Nothing here says you have to stop capability.</b> Every factor is a lever, and several are cheaper to move than "
        "capability is. That claim holds as long as the levers are independent — which is exactly what coupling attacks."
    )
    next_chapter("Chapter 8 · Who moves what", go("whatif"))


# ================================================================ 7. What if
def whatif():
    opener(
        "Chapter 8 of 11 · Act",
        "Model advances, governments, open weights",
        "None of these acts on *risk* in general. Each one acts on particular terms, and some of them pull in both directions "
        "at once. Dial in a mix and watch the hazard move.",
        "§13 The open-weight question, §14 What levers act on which variables",
    )
    st.caption("The mapping from driver to term follows the paper. **The effect sizes are placeholders**, there to show direction and structure.")
    head = st.container(key="sticky")
    support = st.container()
    strengths = {}
    for col, group in zip(st.container(key="levers").columns(len(GROUPS), gap="large"), GROUPS):
        col.markdown(f"**{group}**")
        for lever in (lv for lv in LEVERS if lv.group == group):
            acts = ", ".join(f"{NAMES[k]} {'↑' if u > 0 else '↓'}" for k, u in lever.effects.items())
            strengths[lever.name] = col.slider(lever.name, 0, 100, 0, 10, format="%d%%", help=lever.description) / 100
            col.caption(f"Acts on: {acts}")

    s, base = scenario(), None
    active = {k: v for k, v in strengths.items() if v > 0}
    ratio = rate(scenario(**apply_levers(flat(), active))) / rate(s)
    solo = pd.DataFrame([{"Driver": k, "Change in hazard, %": (rate(scenario(**apply_levers(flat(), {k: v}))) / rate(s) - 1) * 100} for k, v in active.items()])
    moved = abs(ratio - 1) >= 0.005
    chip = f"{'▲' if ratio > 1 else '▼'} {ratio - 1:+.0%} · {'raises' if ratio > 1 else 'lowers'} hazard" if moved else "no change yet"
    top = solo.loc[solo["Change in hazard, %"].abs().idxmax()] if active else None
    note = f"Strongest driver: <b>{top['Driver']}</b> ({top['Change in hazard, %']:+.0f}%)" if active else "Move a slider below. This line stays in view while you scroll."
    strip(f"×{ratio:.2f}", "Hazard changes by", chip, note, where=head)

    open_only = {k: v for k, v in active.items() if k.startswith("Open weights")}
    if not active:
        st.caption("Move a driver above. The index shift, the open-weights effect and the term-by-term table appear here.")
    else:
        h = support.columns(3)
        h[0].metric("Shift in the Control Gap Index", f"{np.log(ratio):+.2f}", help="The log of the hazard ratio. It needs no λ₀.")
        if open_only:
            net = rate(scenario(**apply_levers(flat(), open_only))) / rate(s)
            h[1].metric("Open weights, on net", f"{net - 1:+.0%}", help="Proliferation and the defensive ecosystem, together.")
        else:
            h[1].metric("Open weights, on net", "not applied")
        h[2].metric("Drivers applied", f"{len(active)} of {len(LEVERS)}")

        st.divider()
        b, c = st.columns(2, gap="large")
        solo["Effect"] = np.where(solo["Change in hazard, %"] >= 0, "raises hazard", "lowers hazard")
        b.markdown("**Each driver on its own**")
        b.altair_chart(bars(solo, "Change in hazard, %", "Driver", "Effect", ["raises hazard", "lowers hazard"], [S2, S1], "+.1f", 30), width="stretch")
        b.caption("Drivers multiply, so the bars do not add up to the total.")
        after = scenario(**apply_levers(flat(), active))
        rows = {"Episodes ν": (1.0, float(after.nu))} | {NAMES[k]: (float(s.effective[k]), float(after.effective[k])) for k in "CAOXM"}
        rows |= {NAMES["V"]: (float(s.V), float(after.V)), NAMES["p_I"]: (float(s.p_I), float(after.p_I))}
        c.markdown("**Which terms moved**")
        c.dataframe(
            pd.DataFrame([{"Term": k, "Before": f"{u:.3f}", "After": f"{v:.3f}", "Change": "" if np.isclose(u, v) else f"{v / u - 1:+.0%}"} for k, (u, v) in rows.items()]),
            hide_index=True,
            width="stretch",
        )
    takeaway(
        "<b>Open weights is the one to sit with.</b> The paper refuses to answer it, on purpose: release raises access and strips "
        "safeguards, and it also builds the defensive ecosystem that lowers the shared blind spot. The sign depends on the scenario "
        "and on how strong that second effect really is. The framework does not settle the argument — it says which measurement would."
    )
    next_chapter("Chapter 9 · The number to watch", go("gap"))


# ================================================================ 8. The control gap
def gap():
    opener(
        "Chapter 9 of 11 · Measure",
        "The one number that survives",
        "Levels need a λ₀ nobody has. Ratios do not. Compare this year's hazard with a reference year and the unknown scale "
        "cancels exactly — which leaves a question you can actually answer: is consequential capability pulling ahead of control?",
        "§7 The Control Gap Index, §15 A dashboard",
    )
    p = P()
    t, parts, total, slope, k_growth, gamma_growth = trend()
    hero(slope, k_growth, gamma_growth, int(p["horizon"]))

    a, b, c = st.columns([1, 1, 1], gap="large")
    a.markdown("**Consequence side**, growth % / yr")
    for key, label in [("gnu", "Episodes ν"), ("gC", "Capability"), ("gA", "Access"), ("gO", "Agency"), ("gX", "Exposure"), ("gM", "Propensity")]:
        slider(key, label, -10, 50, 1, where=a)
    b.markdown("**Control side**, change per yr")
    for i, name in enumerate(LAYERS):
        slider(f"de{i}", f"{name} (points)", -3.0, 3.0, 0.5, where=b)
    slider("drho", "Shared blind spot ρ (points)", -2.0, 2.0, 0.1, where=b)
    slider("dtau", "Recovery time (%)", -20, 20, 1, where=b)
    slider("horizon", "Horizon (years)", 3, 30, 1, where=b)

    t, parts, total, slope, k_growth, gamma_growth = trend()
    with c:
        focus("cgi").metric("Implied hazard growth", f"{cg.hazard_growth(slope):+.0%} / yr", f"CGI slope {slope:+.3f}", delta_color="off", delta_arrow="off")
        st.write("")
        if slope > 0.005:
            st.error("Consequential capability is outrunning control.", icon=":material/trending_up:")
        elif slope < -0.005:
            st.success("Control is catching up.", icon=":material/trending_down:")
        else:
            st.info("The two sides are in balance.", icon=":material/trending_flat:")
        capped = [k for k in "CAOXM" if min(p[k] * (1 + p[f'g{k}'] / 100) ** t[-1], 1.0) >= 1.0 and p[f"g{k}"] > 0]
        if capped:
            st.warning(f"{', '.join(capped)} hit the ceiling of 1 inside the horizon. After that only episode volume ν can still grow.", icon=":material/warning:")

    K = sum(parts[k] for k in ("nu", "C", "A", "O", "X", "M"))
    gamma = -(parts["V"] + parts["p_I"])
    wide = pd.DataFrame({"Year": 2026 + t, "Control Gap Index": total, "Δln K (consequence)": K, "−Δln Γ (control)": -gamma})
    long = wide.melt("Year", var_name="Series", value_name="Value")
    colour = alt.Color("Series:N", scale=alt.Scale(domain=list(wide.columns[1:]), range=[S1, S2, S3]), legend=alt.Legend(orient="top", title=None, labelLimit=0))
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#898781").encode(y="y:Q")
    lines = alt.Chart(long).mark_line(strokeWidth=2).encode(
        x=alt.X("Year:Q", axis=alt.Axis(format="d")), y=alt.Y("Value:Q", title="Log change since 2026"), color=colour,
        tooltip=["Year", "Series", alt.Tooltip("Value:Q", format="+.3f")])  # fmt: skip
    left, right = st.columns([3, 2], gap="large")
    left.altair_chart((zero + lines).properties(autosize=FIT), width="stretch")
    contrib = pd.DataFrame({"Term": [NAMES[k] for k in parts], "Contribution": [float(v[-1]) for v in parts.values()]})
    contrib["Side"] = np.where(contrib["Contribution"] >= 0, "raises hazard", "lowers hazard")
    right.markdown(f"**What drives it after {int(p['horizon'])} years**")
    right.altair_chart(bars(contrib, "Contribution", "Term", "Side", ["raises hazard", "lowers hazard"], [S2, S1], "+.3f", 26), width="stretch")

    takeaway(
        "<b>Zero does not mean safe.</b> It means the balance of the reference year. There is no universal threshold here, and the "
        "level is still unknown — only the direction is honest. <b>The slope is the signal.</b>"
    )
    takeaway(
        "Watch which bar is longest. Episode volume ν is usually the winner, and it is the only term with no ceiling: the indices "
        "stop at 1, deployments do not. That makes <i>what counts as one episode</i> the most consequential measurement choice in the whole framework."
    )
    next_chapter("Chapter 10 · How much we don't know", go("uncertainty"))


# ================================================================ 9. Uncertainty
@st.cache_data(show_spinner="Sampling…")
def _mc(means: tuple, e_mean: float, rho_mean: float, pI_mean: float, conc: float, r: float, median: float, log_sd: float, T: float, n: int):
    clip = lambda m: float(np.clip(m, 0.0, 1.0))
    cfg = MCConfig(index_means={k: clip(v) for k, v in means}, index_concentration=conc, correlation=r,
                   effectiveness=beta_params(np.clip(e_mean, 0.01, 0.99), 10), rho=beta_params(np.clip(rho_mean, 0.01, 0.99), 20),
                   p_I=beta_params(np.clip(pI_mean, 0.01, 0.99), 12),
                   lambda0_median=median, lambda0_log_sd=log_sd, T=T)  # fmt: skip
    return simulate(cfg, n).probabilities, spread_decomposition(cfg, n)


def uncertainty():
    opener(
        "Chapter 10 of 11 · Measure",
        "How much of this do we actually know?",
        "Every input so far was a single number, and none of them deserves that confidence. Carry distributions instead and "
        "two things show up that point estimates hide.",
        "§10 Uncertainty, correlation and the multiple-stage fallacy",
    )
    p = P()
    s = scenario()
    a, b = st.columns([1, 3], gap="large")
    r = a.slider("Correlation between the indices", 0.0, 0.9, 0.6, 0.05, help="High capability tends to come with broad access, agency and exposure. Zero pretends they are unrelated.")
    median = a.select_slider("Median λ₀", options=[0.001, 0.01, 0.1, 1, 10], value=0.1)
    log_sd = a.slider("How unsure are you about λ₀?", 0.0, 3.0, 1.5, 0.1, help="Log standard deviation. Set it to 0 to see the uncertainty the model itself produces.")
    conc = a.slider("Confidence in the indices", 4.0, 100.0, 12.0, 1.0, help="Beta concentration. Higher means narrower.")
    T_mc = a.slider("Horizon T (years)", 1, 50, 10)
    means = tuple((k, p[k]) for k in "CAOXM")
    args = (means, float(np.mean([p["e0"], p["e1"], p["e2"]])), p["rho"], float(s.p_I), conc)
    runs = {"if the indices were independent": _mc(*args, 0.0, median, log_sd, T_mc, 50_000), f"correlated (r = {r:g})": _mc(*args, r, median, log_sd, T_mc, 50_000)}

    edges = np.linspace(-7, 0, 71)
    hist = pd.concat([pd.DataFrame({"log10 P": edges[:-1], "Density": np.histogram(np.log10(np.maximum(P_, 1e-7)), edges, density=True)[0], "Indices": name}) for name, (P_, _) in runs.items()])
    chart = alt.Chart(hist).mark_line(interpolate="step-after", strokeWidth=2).encode(
        x=alt.X("log10 P:Q", title=f"log₁₀ P(catastrophe within {T_mc} yr)"), y=alt.Y("Density:Q"),
        color=alt.Color("Indices:N", scale=alt.Scale(domain=list(runs), range=[S1, S2]), legend=alt.Legend(orient="top", title=None, labelLimit=0)),
        tooltip=["Indices", alt.Tooltip("log10 P:Q", format=".2f"), alt.Tooltip("Density:Q", format=".3f")])  # fmt: skip
    b.altair_chart(chart.properties(autosize=FIT, height=300), width="stretch")
    P_corr = runs[f"correlated (r = {r:g})"][0]
    cols = b.columns(3)
    with cols[0]:
        focus("mc").metric("Mean probability", f"{P_corr.mean():.2%}", f"median {np.median(P_corr):.2%}", delta_color="off", delta_arrow="off",
                           help="Decide on the mean, not the median: the distribution is skewed, so the typical draw understates the expected risk.")  # fmt: skip
    cols[1].metric("90% interval", f"{np.quantile(P_corr, 0.05):.1e} – {np.quantile(P_corr, 0.95):.1e}")
    spread = runs["if the indices were independent"][1]
    cols[2].metric("Orders of magnitude", f"{spread['all']:.1f}", f"λ₀ alone gives {spread['lambda0_only']:.1f}", delta_color="off", delta_arrow="off")

    takeaway(
        "<b>One: assuming independence hides the tail.</b> Correlating the indices barely moves the median and clearly fattens the "
        "upper end. A chain of factors each shaded down separately is the classic way to talk yourself into a comfortable number."
    )
    takeaway(
        f"<b>Two: most of this width is assumed, not discovered.</b> Of the {spread['all']:.1f} orders of magnitude in the 90% interval, "
        f"about {spread['lambda0_only']:.1f} come from your uncertainty about λ₀ alone and {spread['without_lambda0']:.1f} from everything else. "
        "Set the λ₀ slider to 0 to see what the model itself actually claims."
    )
    next_chapter("Chapter 11 · Your turn", go("challenge"))


# ================================================================ 10. Challenge
def _best_allocation(base_rate: float, budget: int, step: int = 5) -> tuple[dict, float]:
    """Greedy search: spend the budget where each step buys the most reduction."""
    alloc, spent = {}, 0
    payable = [lv.name for lv in LEVERS if COST[lv.name] > 0]
    while spent + step <= budget:
        best, best_ratio = None, None
        for name in payable:
            trial = dict(alloc)
            trial[name] = min(trial.get(name, 0) + step / 100, 1.0)
            if sum(v * COST[k] for k, v in trial.items()) > budget:
                continue
            value = rate(scenario(**apply_levers(flat(), trial))) / base_rate
            if best_ratio is None or value < best_ratio:
                best, best_ratio = name, value
        if best is None:
            break
        alloc[best] = min(alloc.get(best, 0) + step / 100, 1.0)
        spent = sum(v * COST[k] for k, v in alloc.items())
    return alloc, rate(scenario(**apply_levers(flat(), alloc))) / base_rate


def challenge():
    opener(
        "Chapter 11 of 11 · Play",
        "Your turn: buy down the hazard",
        f"You have <b>{BUDGET} points</b> of effort and a menu of interventions with different prices. Spend them however you like. "
        "The goal is simple: cut the hazard as far as you can.",
        "§11 Sensitivity, §14 What levers act on which variables",
    )
    s = scenario()
    base = rate(s)
    head = st.container(key="sticky")
    st.write("")

    picks, spent = {}, 0
    cols = st.columns(3, gap="large")
    payable = [lv for lv in LEVERS if COST[lv.name] > 0]
    for i, lever in enumerate(payable):
        col = cols[i % 3]
        share = col.slider(f"{lever.name} · {COST[lever.name]} pts", 0, 100, 0, 10, format="%d%%", key=f"ch_{lever.name}", help=lever.description)
        picks[lever.name] = share / 100
        spent += share / 100 * COST[lever.name]
        col.caption(f"{share / 100 * COST[lever.name]:.0f} of {COST[lever.name]} pts")

    over = spent > BUDGET
    applied = {} if over else {k: v for k, v in picks.items() if v > 0}
    ratio = rate(scenario(**apply_levers(flat(), applied))) / base
    cut = 1 - ratio
    chip = f"{spent:.0f} / {BUDGET} pts spent" if not over else f"over budget by {spent - BUDGET:.0f} pts"
    note = "Over budget — nothing is applied until you trim it." if over else ("Nothing spent yet." if not applied else f"Hazard is now ×{ratio:.2f} of where it started.")
    strip(f"−{cut:.0%}" if not over else "—", "Hazard cut by", chip, note, where=head)

    st.divider()
    left, right = st.columns([2, 3], gap="large")
    with left:
        if over:
            st.error(f"You are {spent - BUDGET:.0f} points over. Trim something.", icon=":material/error:")
        elif cut >= 0.9:
            st.success("Over 90% cut. That is about as far as this scenario goes.", icon=":material/military_tech:")
            if not st.session_state.get("cheered"):
                st.session_state.cheered = True
                st.balloons()
        elif cut >= 0.6:
            st.info("A serious dent. Can you find the last stretch?", icon=":material/trending_down:")
        st.metric("Points left", f"{max(BUDGET - spent, 0):.0f}")
        if st.button("Show me the best mix I can find", type="primary"):
            st.session_state.show_best = True
        if st.button("Clear my picks"):
            for lever in payable:
                st.session_state[f"ch_{lever.name}"] = 0
            st.session_state.show_best = False
            st.rerun()

    with right:
        if st.session_state.get("show_best"):
            alloc, best_ratio = _best_allocation(base, BUDGET)
            st.markdown(f"**A greedy search gets to −{1 - best_ratio:.0%}**, against your −{cut:.0%}, with this mix:")
            st.dataframe(
                pd.DataFrame([{"Intervention": k, "Strength": f"{v:.0%}", "Cost": f"{v * COST[k]:.0f} pts"} for k, v in sorted(alloc.items(), key=lambda kv: -kv[1] * COST[kv[0]])]),
                hide_index=True,
                width="stretch",
            )
            st.caption("Greedy, not optimal — but notice how it concentrates on a few levers rather than spreading thin.")
        else:
            st.markdown(
                "**Three things this tends to teach.**\n\n"
                "- Spreading the budget evenly is almost always worse than concentrating it.\n"
                "- The cheap control-side buys — incident response, reporting — often beat the expensive consequence-side ones.\n"
                "- If the shared blind spot ρ is large, defence spending stalls early. Go back to chapter 4, raise ρ, and try again."
            )
    takeaway(
        "<b>The prices here are invented.</b> The structure is not: each intervention acts on particular terms, and the returns "
        "genuinely do interact and saturate. If you want this to mean something, replace the costs with your own and the effect "
        "sizes with evidence — that is what the package is for."
    )
    st.divider()
    st.markdown(
        f"#### That's the tour\n\nThe model, the package and the paper are open, and free for anyone to use.\n\n"
        f"- **Paper** — [The AI Drake Equation]({PAPER}), CC BY 4.0\n"
        f"- **Code** — [{REPO.split('//')[1]}]({REPO}), MIT, `pip install -e .`\n"
        f"- **Send it to someone** — [controlgap.streamlit.app](https://controlgap.streamlit.app)\n"
        f"- **Argue with it** — the functional forms are hypotheses and the framework is weakest exactly where it matters most, "
        f"on autonomous loss of control. Issues and pull requests welcome, especially real data for any of these terms."
    )
