"""Shared state, styling and widgets for the ControlGap app.

The parameter store is a plain dict in session state, not the widget keys
themselves. Streamlit drops widget state for widgets that were not rendered in
the last run, and each chapter renders only the controls it teaches, so the
dict is what survives moving between chapters.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from urllib.parse import quote

import controlgap as cg
from incidents import INCIDENTS

REPO = "https://github.com/pizuricv/controlgap"
PAPER = f"{REPO}/blob/main/paper/ai-drake-equation-v4.md"

# Validated for colour-blind safety; do not add new series hues.
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
FIT = {"type": "fit", "contains": "padding"}
LAYERS = ("Detection", "Intervention", "Containment")
NAMES = {
    "nu": "Episodes ν", "C": "Capability C", "A": "Access A", "O": "Agency O", "X": "Exposure X", "M": "Propensity M",
    "V": "Residual vulnerability V", "p_I": "Irreversibility p_I", "e0": "Detection", "e1": "Intervention",
    "e2": "Containment", "rho": "Common-mode ρ", "r_esc": "Escalation rate", "tau": "Recovery time",
}  # fmt: skip
KEYS = ("C", "A", "O", "X", "M", "e0", "e1", "e2", "rho", "r_esc", "tau", "g")
GROWTH_KEYS = ("gnu", "gC", "gA", "gO", "gX", "gM", "de0", "de1", "de2", "drho", "dtau", "horizon")

# Every preset is illustrative. None of these values is a measurement.
PRESETS = {
    "The paper's example": dict(
        icon="📄", short="The paper's example", tagline="The numbers used throughout the paper.",
        about="Propensity is at its worst case and capability is not coupled to anything else. Start here if you want the figures in §12 to match.",
        C=0.20, A=0.70, O=0.50, X=0.60, M=1.00, e0=0.60, e1=0.50, e2=0.50, rho=0.10, r_esc=1.0, tau=1.0, g=0.0,
        gnu=10, gC=5, gA=2, gO=4, gX=3, gM=0, de0=1.5, de1=1.0, de2=0.0, drho=0.5, dtau=-3, horizon=10),
    "Autonomous cyber operations": dict(
        icon="💻", short="Autonomous cyber ops", tagline="The system is the one acting.",
        about="Events move in hours. Capability helps the system get its own access and evade its own oversight, so coupling is on.",
        C=0.45, A=0.60, O=0.70, X=0.70, M=0.15, e0=0.70, e1=0.50, e2=0.40, rho=0.15, r_esc=2.0, tau=0.5, g=0.40,
        gnu=18, gC=8, gA=3, gO=7, gX=5, gM=2, de0=2.0, de1=1.0, de2=0.5, drho=0.5, dtau=-5, horizon=10),
    "AI-enabled biological misuse": dict(
        icon="🧬", short="AI-enabled bio misuse", tagline="A human is the one acting.",
        about="Very few people would try, and agency barely matters. But a release cannot be recalled, so recovery is slow and the damage is hard to undo.",
        C=0.30, A=0.50, O=0.20, X=0.30, M=0.05, e0=0.80, e1=0.60, e2=0.50, rho=0.05, r_esc=0.2, tau=10.0, g=0.0,
        gnu=8, gC=6, gA=4, gO=1, gX=2, gM=0, de0=1.0, de1=1.0, de2=0.5, drho=0.0, dtau=-2, horizon=10),
    "Cascading infrastructure failure": dict(
        icon="⚡", short="Cascading infra failure", tagline="Nobody has to intend it.",
        about="An accident, so propensity sits at 1. Tightly coupled systems share their weaknesses, so the common-mode rate is high and escalation is fast.",
        C=0.60, A=0.90, O=0.80, X=0.50, M=1.00, e0=0.50, e1=0.40, e2=0.60, rho=0.25, r_esc=4.0, tau=2.0, g=0.0,
        gnu=14, gC=5, gA=2, gO=6, gX=4, gM=0, de0=1.0, de1=0.5, de2=0.0, drho=1.0, dtau=-2, horizon=10),
}  # fmt: skip

# Every precursor event is also a scenario, so the tour can be started from a real one.
FROM_INCIDENTS = {
    incident.scenario_name: dict(
        icon=incident.scenario_icon, short=incident.scenario_short,
        tagline="From a real event.", about=incident.scenario_why, incident=incident.key, **incident.preset,
    )
    for incident in INCIDENTS
}
BASE_PRESETS = dict(PRESETS)  # the four written for this app, without the ones derived from real events
PRESETS |= FROM_INCIDENTS
FIRST = next(iter(BASE_PRESETS))

CSS = """
<style>
/* Page frame */
[data-testid="stMainBlockContainer"] {padding-top: 2.4rem; max-width: 72rem;}
[data-testid="stMarkdownContainer"] > p, [data-testid="stMarkdownContainer"] > ul, [data-testid="stMarkdownContainer"] > ol {max-width: 44rem;}
[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
[data-testid="stMetricLabel"] p {white-space: normal; overflow: visible;}
[data-testid="stSliderThumbValue"] {color: inherit; font-weight: 600; font-variant-numeric: tabular-nums;}
[data-testid="stSidebarHeader"] {height: 2.75rem; min-height: 0; margin-bottom: 0;}
[data-testid="stButton"] button p {white-space: normal; line-height: 1.25;}
.katex-display {overflow-x: auto; overflow-y: hidden; padding-bottom: .35rem; scrollbar-width: thin; text-align: left;}
.katex-display > .katex {text-align: left; margin: 0;}

/* Chapter opener */
.cg-kicker {font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; opacity: .78;}
.cg-h {font-size: 2rem; font-weight: 700; line-height: 1.15; margin: .1rem 0 .35rem;}
.cg-lede {font-size: 1.08rem; line-height: 1.6; opacity: .92; max-width: 44rem;}

/* The takeaway of a chapter */
.cg-take {border-left: 5px solid #2a78d6; background: rgba(42,120,214,.07); border-radius: .5rem;
          padding: .8rem 1.1rem; margin: .4rem 0 .2rem; font-size: .97rem; line-height: 1.55;}
.cg-take b {font-weight: 700;}
.cg-warn {border-left-color: #eb6834; background: rgba(235,104,52,.09);}

/* The one number to watch */
.cg-hero {border: 1px solid rgba(128,128,128,.25); border-left: 6px solid #2a78d6; border-radius: 10px;
          padding: .8rem 1.3rem; margin: .2rem 0 .8rem; display: flex; flex-wrap: wrap; gap: .8rem 2.5rem;
          align-items: center; background: rgba(42,120,214,.06);}
.cg-hero .cg-big {font-size: 2.6rem; font-weight: 700; line-height: 1.05; font-variant-numeric: tabular-nums;}
.cg-hero .cg-big small {font-size: 1rem; font-weight: 600; opacity: .8;}
.cg-hero .cg-verdict {font-size: 1.05rem; font-weight: 600;}
.cg-hero .cg-pace {font-size: .92rem; opacity: .85;}
.cg-hero .cg-side {flex: 1 1 320px; font-size: .9rem; line-height: 1.5;}
.cg-hero .cg-note {opacity: .75; font-size: .84rem; margin-top: .3rem;}

/* Sidebar readout */
.cg-read {font-size: .85rem; line-height: 1.7;}
.cg-read .r {display: flex; justify-content: space-between; gap: 1rem;}
.cg-read b {font-variant-numeric: tabular-nums;}

/* Sticky result strip */
[data-testid="stLayoutWrapper"]:has(> .st-key-sticky) {position: sticky; top: 3.6rem; z-index: 90;}
.st-key-sticky {background: __BG__; border: 1px solid rgba(128,128,128,.28); border-left: 4px solid #2a78d6;
                border-radius: .5rem; padding: .55rem 1rem .6rem; box-shadow: 0 6px 16px -10px rgba(0,0,0,.5);}
.cg-strip {display: flex; flex-wrap: wrap; align-items: center; gap: .25rem 1.5rem;}
.cg-strip-num {font-size: 2rem; font-weight: 700; font-variant-numeric: tabular-nums;}
.cg-chip {font-size: .85rem; font-weight: 600; padding: .1rem .6rem; border-radius: 1rem; background: rgba(128,128,128,.16);}
.cg-strip-note {font-size: .85rem; opacity: .8;}

/* Scenario cards: equal height, and the button pinned to the bottom of each */
[class*="st-key-card_"] {border: 1px solid rgba(128,128,128,.28); border-radius: .6rem; padding: .9rem 1rem .9rem;
                         height: 100%; display: flex; flex-direction: column;}
/* the column stretches, but its wrappers need telling to pass that height down to the card */
[data-testid="stColumn"]:has([class*="st-key-card_"]) > [data-testid="stVerticalBlock"] {height: 100%;}
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-card_"]) {height: 100%;}
[class*="st-key-card_"] > [data-testid="stElementContainer"]:first-child {flex: 1 1 auto;}
[class*="st-key-card_"] .cg-card-icon {font-size: 1.7rem; line-height: 1;}
[class*="st-key-card_"] .cg-card-name {font-weight: 700; font-size: 1.02rem; margin-top: .3rem; line-height: 1.3; min-height: 2.7em;}
[class*="st-key-card_"] .cg-card-body {font-size: .87rem; opacity: .82; line-height: 1.45; margin: .2rem 0 .6rem;}
.st-key-card_active {border-color: #2a78d6; border-width: 2px; background: rgba(42,120,214,.06);}
/* four abreast gets cramped below ~1150px, so wrap to 2x2 and keep the titles on two lines */
@media (max-width: 1150px) {
  [data-testid="stHorizontalBlock"]:has([class*="st-key-card_"]) {flex-wrap: wrap;}
  [data-testid="stColumn"]:has([class*="st-key-card_"]) {flex: 1 1 42%; min-width: 260px;}
}

/* Quiet "try this" callout */
[class*="st-key-try_"] {background: rgba(128,128,128,.09); border-radius: .5rem; padding: .8rem 1rem .6rem;}
[class*="st-key-try_"] [data-testid="stMarkdownContainer"] {font-size: .9rem; line-height: 1.5;}

/* Focus metric */
[class*="st-key-focus_"] {border-left: 4px solid #2a78d6; padding: .1rem 0 .1rem 1rem;}
[class*="st-key-focus_"] [data-testid="stMetricValue"] {font-size: 2.1rem; font-weight: 700;}

/* Captions bound to their own slider */
.st-key-levers [data-testid="stCaptionContainer"] {margin-top: -.85rem; margin-bottom: .55rem;}

@media (max-width: 640px) {
  .cg-h {font-size: 1.6rem;}
  .cg-hero .cg-big {font-size: 2.1rem;}
  .cg-hero .cg-note {display: none;}
  [data-testid="stLayoutWrapper"]:has(> .st-key-sticky) {position: static;}
}
</style>
"""

SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def num(x, decimals: int = 3) -> str:
    """Fixed decimals for ordinary values, scientific notation once they would round to zero."""
    x = float(x)
    if x == 0 or abs(x) >= 10.0 ** -(decimals - 2):
        return f"{x:.{decimals}f}"
    mantissa, exponent = f"{x:.1e}".split("e")
    return f"{mantissa} × 10{str(int(exponent)).translate(SUPERSCRIPT)}"


def tex(x, decimals: int = 2) -> str:
    x = float(x)
    if x == 0 or abs(x) >= 10.0**-decimals:
        return f"{x:.{decimals}f}"
    mantissa, exponent = f"{x:.1e}".split("e")
    return rf"{mantissa}\!\times\!10^{{{int(exponent)}}}"


def ratio_words(ratio: float) -> str:
    if 0.95 <= ratio <= 1.05:
        return "about the same as"
    if ratio >= 1:
        return f"{ratio:,.1f}× higher than" if ratio < 100 else f"{ratio:,.0f}× higher than"
    inverse = 1 / ratio
    return f"{inverse:,.1f}× lower than" if inverse < 100 else (f"{inverse:,.0f}× lower than" if inverse < 1e6 else f"{num(ratio, 3)} of")


# ---------------------------------------------------------------- state
def defaults(name: str) -> dict:
    return {k: v for k, v in PRESETS[name].items() if k in KEYS + GROWTH_KEYS}


CHAPTER_COUNT = 11
MINUTES_EACH = 1.4


def share_link() -> str:
    """The current scenario, packed into a URL, so a configured tour can be sent to someone."""
    import base64
    import json

    preset = PRESETS[st.session_state.preset]
    changed = {k: v for k, v in P().items() if k in preset and v != preset[k]}
    token = base64.urlsafe_b64encode(json.dumps(changed, separators=(",", ":")).encode()).decode().rstrip("=")
    base = (getattr(st.context, "url", None) or "https://controlgap.streamlit.app").split("?")[0]
    return f"{base}?scenario={quote(st.session_state.preset)}" + (f"&tweak={token}" if changed else "")


def _restore_from_link():
    """A ?scenario=...&tweak=... link sets the tour up the way it was sent."""
    import base64
    import json

    params = st.query_params
    name = params.get("scenario")
    stamp = f"{name}{params.get('tweak', '')}"
    if not name or name not in PRESETS or st.session_state.get("link_loaded") == stamp:
        return
    load_preset(name)
    token = params.get("tweak")
    if token:
        try:
            padded = token + "=" * (-len(token) % 4)
            for key, value in json.loads(base64.urlsafe_b64decode(padded)).items():
                if key in KEYS + GROWTH_KEYS:
                    st.session_state.P[key] = value
        except Exception:  # a mangled link should never break the app
            pass
    st.session_state["link_loaded"] = stamp


def init():
    st.session_state.setdefault("preset", FIRST)
    if st.session_state.preset not in PRESETS:  # a link or an older session
        st.session_state.preset = FIRST
    base = defaults(st.session_state.preset)
    store = st.session_state.setdefault("P", dict(base))
    for key, value in base.items():  # top up anything a stale session is missing
        store.setdefault(key, value)
    _restore_from_link()
    st.session_state.setdefault("seen_intro", False)
    st.session_state.setdefault("gated", False)
    st.session_state.setdefault("C0", 0.5)
    st.session_state.setdefault("k", 15.0)


def load_preset(name: str):
    st.session_state.preset = name
    st.session_state.P = defaults(name)
    for key in list(st.session_state):  # let every slider re-seed from the store
        if key.startswith("w_"):
            del st.session_state[key]


def P() -> dict:
    return st.session_state.P


def slider(key: str, label: str, lo, hi, step, where=None, **kw):
    """A slider backed by the parameter store rather than by its own widget key."""
    store = P()
    value = where.slider(label, lo, hi, store[key], step, key=f"w_{key}", **kw) if where else st.slider(label, lo, hi, store[key], step, key=f"w_{key}", **kw)
    store[key] = value
    return value


def scenario(**override) -> cg.Scenario:
    """The current scenario. Any field can be overridden, by a number or a time series."""
    v = {**P(), **override}
    g = v.get("g", 0.0)
    return cg.Scenario(
        "current", C=v["C"], A=v["A"], O=v["O"], X=v["X"], M=v["M"], effectiveness=(v["e0"], v["e1"], v["e2"]),
        rho=v["rho"], p_I=cg.irreversibility(v["r_esc"], tau_rec=v["tau"]), nu=v.get("nu", 1.0),
        coupling=cg.Coupling(A=g, O=g, X=g, e=g, rho=g),
        gates={"C": cg.Gate(st.session_state.C0, st.session_state.k)} if st.session_state.gated else None,
    )  # fmt: skip


def rate(sc: cg.Scenario) -> float:
    """Hazard up to the unknown constant: episode volume times the combined factor."""
    return float(sc.nu * sc.factor)


def flat() -> dict:
    """The level parameters as a plain dict, for controlgap.levers."""
    return {k: P()[k] for k in KEYS if k != "g"} | {"g": P()["g"], "nu": 1.0}


def trend(horizon: int | None = None):
    """The scenario's path over the horizon, its CGI, the slope and the growth of K and Γ."""
    store = P()
    horizon = int(horizon if horizon is not None else store["horizon"])
    t = np.arange(horizon + 1)
    series = {k: np.minimum(store[k] * (1 + store[f"g{k}"] / 100) ** t, 1.0) for k in "CAOXM"}
    series["nu"] = (1 + store["gnu"] / 100) ** t
    series |= {f"e{i}": np.clip(store[f"e{i}"] + store[f"de{i}"] / 100 * t, 0.0, 0.99) for i in range(3)}
    series["rho"] = np.clip(store["rho"] + store["drho"] / 100 * t, 0.0, 1.0)
    series["tau"] = store["tau"] * (1 + store["dtau"] / 100) ** t
    parts = cg.cgi_contributions(scenario(**series))
    total = sum(parts.values())
    K = sum(parts[k] for k in ("nu", "C", "A", "O", "X", "M"))
    gamma = -(parts["V"] + parts["p_I"])
    slope = cg.cgi_slope(t, total)
    return t, parts, total, slope, float(np.expm1(K[-1] / horizon)), float(np.expm1(gamma[-1] / horizon))


# ---------------------------------------------------------------- pieces
def opener(kicker: str, heading: str, lede: str, section: str = ""):
    st.session_state["current_chapter"] = f"{kicker} — {heading}"
    number = kicker.split(" of ")[0].replace("Chapter", "").strip()
    st.session_state["chapter_number"] = int(number) if number.isdigit() else 0
    if number.isdigit():
        st.session_state.setdefault("visited", set()).add(int(number))
    st.markdown(
        f'<div class="cg-kicker">{kicker}</div><div class="cg-h">{heading}</div><div class="cg-lede">{lede}</div>',
        unsafe_allow_html=True,
    )
    if section:
        st.caption(f"Paper: {section}")
    st.write("")


def takeaway(text: str, warn: bool = False):
    st.markdown(f'<div class="cg-take{" cg-warn" if warn else ""}">{text}</div>', unsafe_allow_html=True)


def try_this(section: str, items: list[str], where=None):
    box = (where or st).container(key=f"try_{abs(hash(section)) % 10**8}")
    box.markdown("**Try this**\n" + "\n".join(f"- {t}" for t in items))


def focus(name: str, where=None):
    box = (where or st).container(key=f"focus_{name}")
    box.markdown('<div class="cg-kicker">Number to watch</div>', unsafe_allow_html=True)
    return box


def verdict_of(slope: float) -> tuple[str, str]:
    if slope > 0.005:
        return "▲ Consequential capability is outrunning control", f"At this pace the hazard doubles about every {np.log(2) / slope:.0f} years."
    if slope < -0.005:
        return "▼ Control is catching up", f"At this pace the hazard halves about every {np.log(2) / -slope:.0f} years."
    return "■ Capability and control are in balance", ""


def hero(slope: float, k_growth: float, gamma_growth: float, horizon: int):
    growth = cg.hazard_growth(slope)
    verdict, pace = verdict_of(slope)
    level = rate(scenario()) / rate(shipped())
    if level < 0.01 and slope > 0.005:
        verdict += ", from a very low base"
    st.markdown(
        f"""<div class="cg-hero">
<div><div class="cg-kicker">The number to watch · hazard trend</div>
<div class="cg-big">{growth:+.0%} <small>a year · growth in relative hazard</small></div>
<div class="cg-verdict">{verdict}</div><div class="cg-pace">{pace}</div></div>
<div class="cg-side"><b>Trend.</b> Consequence side <b>K {k_growth:+.0%}</b> / yr versus control side <b>Γ {gamma_growth:+.0%}</b> / yr, over {horizon} years from 2026.<br>
<b>Level.</b> Your settings put the hazard today <b>{ratio_words(level)}</b> this scenario as it ships.
<div class="cg-note">A rate of change since 2026, not a probability and not a forecast. The sliders on this page set the trend;
the scenario sets the level. A tiny hazard can grow fast, and a large one can shrink. Neither number needs the unknown λ₀.</div></div>
</div>""",
        unsafe_allow_html=True,
    )


def shipped() -> cg.Scenario:
    """The current preset at its shipped values, as a reference point for the level."""
    preset = PRESETS[st.session_state.preset]
    return scenario(**{k: preset[k] for k in KEYS})


def strip(number: str, label: str, chip: str, note: str, where=None):
    (where or st).markdown(
        f'<div class="cg-strip"><div><div class="cg-kicker">Number to watch</div><div>{label}</div></div>'
        f'<div class="cg-strip-num">{number}</div><div class="cg-chip">{chip}</div><div class="cg-strip-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def next_chapter(label: str, page):
    st.write("")
    st.divider()
    left, right = st.columns([5, 3])
    left.caption("Keep going")
    if right.button(f"{label}  →", type="primary", width="stretch"):
        st.switch_page(page)


def legend(domain, range_):
    return alt.Color("k:N", scale=alt.Scale(domain=domain, range=range_), legend=alt.Legend(orient="top", title=None, labelLimit=0))


def label_colour() -> str:
    return "#e7e5e0" if getattr(getattr(st.context, "theme", None), "type", "light") == "dark" else "#1f2328"


def bars(df: pd.DataFrame, x: str, y: str, colour: str, domain, range_, fmt: str = "+.1f", step: int = 28):
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, height=16)
        .encode(
            x=alt.X(f"{x}:Q"),
            y=alt.Y(f"{y}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280)),
            color=alt.Color(f"{colour}:N", scale=alt.Scale(domain=domain, range=range_), legend=alt.Legend(orient="top", title=None, labelLimit=0)),
            tooltip=[y, colour, alt.Tooltip(f"{x}:Q", format=fmt)],
        )
        .properties(height=alt.Step(step))
    )


# ---------------------------------------------------------------- feedback
def issue_url(title: str, body: str, labels: str = "feedback") -> str:
    """A pre-filled 'new issue' link.

    Deliberately not an API call: a public app must never carry a write token,
    and a link means the visitor files under their own account, with their own
    rate limits and their own name on it.
    """
    from urllib.parse import quote

    return f"{REPO}/issues/new?title={quote(title)}&body={quote(body)}&labels={quote(labels)}"


INCIDENT_BODY = """**The event**

<!-- one paragraph, in your own words -->

**Source** (required: a published report, not a social-media post)

<!-- URL -->

**Where it sits on the precursor ladder (paper 9.1)**

- [ ] 1 - a dangerous capability shown in the lab
- [ ] 2 - a safeguard bypassed in testing
- [ ] 3 - an incident in deployment
- [ ] 4 - a near-miss stopped by a late layer

**Which layers did it get past, and what stopped it?**

<!-- detection / intervention / containment -->

**Which part of the model is it evidence about?**

<!-- e.g. the common-mode rate, propensity, the recovery clock -->
"""


def state_block() -> str:
    """The current settings, as a fenced block, so a report is reproducible."""
    store = P()
    values = "\n".join(f"{k} = {store[k]}" for k in KEYS + GROWTH_KEYS if k in store)
    return f"Scenario: {st.session_state.preset}\n\n```\n{values}\n```"


INCIDENT_ISSUE = ""  # set below, once issue_url is defined


def feedback_links(where=None) -> None:
    w = where or st
    page = getattr(st.context, "url", "") or ""
    body = (
        "**What I was looking at**\n\n"
        f"Chapter: {st.session_state.get('current_chapter', 'unknown')}\n\n"
        f"{state_block()}\n\n"
        "**What I think is wrong, missing or unclear**\n\n<!-- over to you -->\n"
    )
    w.link_button("Report a problem", issue_url("[app] ", body, "feedback,app"), width="stretch", icon=":material/bug_report:")
    w.link_button("Argue with the model", issue_url("[model] ", f"**Which assumption, and why it is wrong**\n\n<!-- over to you -->\n\n{state_block()}", "feedback,model"), width="stretch", icon=":material/forum:")


# ---------------------------------------------------------------- sidebar
def sidebar_readout() -> None:
    sb = st.sidebar
    sb.divider()
    preset = PRESETS[st.session_state.preset]
    sb.markdown(f"**{preset['icon']} {st.session_state.preset}**")
    if st.session_state.get("chapter_number") == 1:  # not a prefix test: "Chapter 11" starts with "Chapter 1"
        sb.caption(preset["about"])
        sb.caption("Your running numbers appear here from chapter 2 onwards, and follow you through the tour.")
    else:
        s = scenario()
        level = rate(s) / rate(shipped())
        _, _, _, slope, _, _ = trend()
        verdict, _ = verdict_of(slope)
        sb.markdown(
            f'<div class="cg-read">'
            f'<div class="r"><span>Chain \u00d7 defences</span><b>{num(s.factor, 5)}</b></div>'
            f'<div class="r"><span>Versus as shipped</span><b>{ratio_words(level).replace(" than", "").replace("about the same as", "same")}</b></div>'
            f'<div class="r"><span>Hazard trend</span><b>{cg.hazard_growth(slope):+.0%}/yr</b></div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        sb.caption(verdict)

    changed = [NAMES.get(k, k) for k in KEYS + GROWTH_KEYS if k in preset and P().get(k) != preset[k]]
    if changed:
        sb.caption("Changed from the scenario: " + ", ".join(changed) + ". These follow you into every chapter.")
    label = f"Reset {len(changed)} change{'' if len(changed) == 1 else 's'}" if changed else "Reset this scenario"
    # a stable key: without one the changing label changes the widget id, and clicks are lost
    if sb.button(label, key="reset_scenario", width="stretch", icon=":material/restart_alt:"):
        load_preset(st.session_state.preset)
        st.rerun()
    with sb.expander("Switch scenario"):
        for name, item in PRESETS.items():
            st.button(
                f"{item['icon']}  {name}",
                key=f"sw_{name}",
                width="stretch",
                disabled=name == st.session_state.preset,
                on_click=load_preset,
                args=(name,),
            )
    read = len(st.session_state.get("visited", set()))
    sb.divider()
    sb.markdown(f"**{read} of {CHAPTER_COUNT} chapters read**")
    sb.progress(read / CHAPTER_COUNT)
    if read < CHAPTER_COUNT:
        sb.caption(f"About {max(1, round((CHAPTER_COUNT - read) * MINUTES_EACH))} minutes left.")
    with sb.popover("Share this scenario", width="stretch", icon=":material/link:"):
        st.caption("Opens with your scenario, and any changes you have made already applied.")
        st.code(share_link(), language=None, wrap_lines=True)

    sb.divider()
    with sb.expander("Tell us we're wrong"):
        st.caption("Opens a pre-filled issue on GitHub under your own account. Your current settings travel with it.")
        feedback_links()
    sb.caption(f"[Paper]({PAPER}) · [Code]({REPO}) · Code MIT, paper CC BY 4.0. All values illustrative.")


INCIDENT_ISSUE = issue_url("[precursor] ", INCIDENT_BODY, "precursor,data")
