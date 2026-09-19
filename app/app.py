"""ControlGap: an explorable version of The AI Drake Equation. Run: streamlit run app/app.py"""

from __future__ import annotations

import streamlit as st

import chapters
import ui

st.set_page_config(page_title="ControlGap", page_icon="🎛️", layout="wide")
ui.init()

dark = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
st.markdown(ui.CSS.replace("__BG__", "#15171b" if dark else "#ffffff"), unsafe_allow_html=True)

PAGES = {
    "start": st.Page(chapters.start, title="Start here", icon=":material/play_circle:", default=True),  # the default page is always served at "/"
    "chain": st.Page(chapters.chain, title="The chain", icon=":material/link:", url_path="chain"),
    "lambda0": st.Page(chapters.lambda0, title="The missing number", icon=":material/help:", url_path="missing-number"),
    "layers": st.Page(chapters.layers, title="The layers", icon=":material/shield:", url_path="layers"),
    "race": st.Page(chapters.race, title="The race", icon=":material/timer:", url_path="race"),
    "levers": st.Page(chapters.levers, title="Where effort pays", icon=":material/tune:", url_path="levers"),
    "whatif": st.Page(chapters.whatif, title="What if", icon=":material/alt_route:", url_path="what-if"),
    "gap": st.Page(chapters.gap, title="The control gap", icon=":material/monitoring:", url_path="control-gap"),
    "uncertainty": st.Page(chapters.uncertainty, title="How much we know", icon=":material/blur_on:", url_path="uncertainty"),
    "challenge": st.Page(chapters.challenge, title="Your turn", icon=":material/sports_esports:", url_path="challenge"),
}
st.session_state["pages"] = PAGES

nav = st.navigation(
    {
        "Understand": [PAGES["start"], PAGES["chain"], PAGES["lambda0"], PAGES["layers"], PAGES["race"]],
        "Act": [PAGES["levers"], PAGES["whatif"]],
        "Measure": [PAGES["gap"], PAGES["uncertainty"]],
        "Play": [PAGES["challenge"]],
    },
    position="sidebar",
    expanded=True,
)

nav.run()
ui.sidebar_readout()  # after the chapter, so it reflects this run's slider values
