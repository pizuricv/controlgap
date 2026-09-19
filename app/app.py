"""ControlGap: an explorable version of The AI Drake Equation. Run: streamlit run app/app.py"""

from __future__ import annotations

import streamlit as st

import chapters
import ui

st.set_page_config(page_title="ControlGap", page_icon="🎛️", layout="wide")
ui.init()

dark = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
st.markdown(ui.CSS.replace("__BG__", "#15171b" if dark else "#ffffff"), unsafe_allow_html=True)

read = st.session_state.get("visited", set())
ORDER = {"start": 1, "chain": 2, "lambda0": 3, "layers": 4, "race": 5, "precursors": 6,
         "levers": 7, "whatif": 8, "gap": 9, "uncertainty": 10, "challenge": 11}


def title(key: str, text: str) -> str:
    """A tick on chapters already read, so progress is visible in the nav itself."""
    return f"{text}  ✓" if ORDER[key] in read else text


PAGES = {
    "start": st.Page(chapters.start, title=title("start", "Start here"), icon=":material/play_circle:", default=True),  # the default page is always served at "/"
    "chain": st.Page(chapters.chain, title=title("chain", "The chain"), icon=":material/link:", url_path="chain"),
    "lambda0": st.Page(chapters.lambda0, title=title("lambda0", "The missing number"), icon=":material/help:", url_path="missing-number"),
    "layers": st.Page(chapters.layers, title=title("layers", "The layers"), icon=":material/shield:", url_path="layers"),
    "race": st.Page(chapters.race, title=title("race", "The race"), icon=":material/timer:", url_path="race"),
    "precursors": st.Page(chapters.precursors_chapter, title=title("precursors", "What nearly happened"), icon=":material/history:", url_path="precursors"),
    "levers": st.Page(chapters.levers, title=title("levers", "Where effort pays"), icon=":material/tune:", url_path="levers"),
    "whatif": st.Page(chapters.whatif, title=title("whatif", "What if"), icon=":material/alt_route:", url_path="what-if"),
    "gap": st.Page(chapters.gap, title=title("gap", "The control gap"), icon=":material/monitoring:", url_path="control-gap"),
    "uncertainty": st.Page(chapters.uncertainty, title=title("uncertainty", "How much we know"), icon=":material/blur_on:", url_path="uncertainty"),
    "challenge": st.Page(chapters.challenge, title=title("challenge", "Your turn"), icon=":material/sports_esports:", url_path="challenge"),
}
st.session_state["pages"] = PAGES

nav = st.navigation(
    {
        "Understand": [PAGES["start"], PAGES["chain"], PAGES["lambda0"], PAGES["layers"], PAGES["race"]],
        "Evidence": [PAGES["precursors"]],
        "Act": [PAGES["levers"], PAGES["whatif"]],
        "Measure": [PAGES["gap"], PAGES["uncertainty"]],
        "Play": [PAGES["challenge"]],
    },
    position="sidebar",
    expanded=True,
)

nav.run()
ui.sidebar_readout()  # after the chapter, so it reflects this run's slider values
