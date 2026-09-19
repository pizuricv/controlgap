from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).parents[1] / "app" / "app.py")
CHAPTERS = ["start", "chain", "lambda0", "layers", "race", "precursors_chapter", "levers", "whatif", "gap", "uncertainty", "challenge"]


def _chapter_script(name, app_path, chapters_list):
    """Run one chapter the way app.py would, without the navigation wrapper.

    AppTest runs this as its own script, so it takes everything it needs as
    arguments rather than closing over the test module.
    """
    import streamlit as st

    import chapters
    import ui

    ui.init()
    st.markdown(ui.CSS.replace("__BG__", "#ffffff"), unsafe_allow_html=True)
    st.session_state["pages"] = dict.fromkeys([*chapters_list, "precursors"], app_path)  # only read when a "next" button is clicked
    getattr(chapters, name)()
    ui.sidebar_readout()


def run(at):
    at.run(timeout=180)
    assert not at.exception, [f"{e.value}\n{e.stack_trace}" for e in at.exception]
    return at


def chapter(page: str = "start") -> AppTest:
    return AppTest.from_function(_chapter_script, args=(page, APP, CHAPTERS), default_timeout=180)


def app(page: str = "start"):
    return run(chapter(page))


def metric(at, label):
    return next(m.value for m in at.metric if m.label.endswith(label))


def sliders(at):
    return {w.label: w for w in at.slider}


def test_the_app_itself_starts():
    at = run(AppTest.from_file(APP))
    assert at.session_state.preset in ("The paper's example",)
    assert at.markdown


@pytest.mark.parametrize("page", CHAPTERS)
def test_every_chapter_renders(page):
    at = app(page)
    assert at.markdown, f"{page} rendered nothing"


def test_defaults_reproduce_section_12():
    assert app("chain").session_state.P["C"] == 0.20
    assert metric(app("lambda0"), "P(catastrophe within 10 yr)") == "0.40%"


def test_parameters_survive_moving_between_chapters():
    at = app("chain")
    sliders(at)["Capability C"].set_value(0.9)
    run(at)
    assert at.session_state.P["C"] == 0.9

    # a different chapter, carrying the store over, then back again
    other = chapter("layers")
    other.session_state["P"] = at.session_state["P"]
    other.session_state["preset"] = at.session_state["preset"]
    run(other)
    back = chapter("chain")
    back.session_state["P"] = other.session_state["P"]
    back.session_state["preset"] = other.session_state["preset"]
    run(back)
    assert back.session_state.P["C"] == 0.9
    assert sliders(back)["Capability C"].value == 0.9


def test_scenario_cards_load_a_preset_and_reset_restores_it():
    at = app("start")
    next(b for b in at.button if b.key == "pick_Autonomous cyber operations").click()
    run(at)
    assert at.session_state.preset == "Autonomous cyber operations"
    assert at.session_state.P["C"] == 0.45
    at.session_state.P["C"] = 0.11
    next(b for b in at.sidebar.button if "Reset" in b.label).click()
    run(at)
    assert at.session_state.P["C"] == 0.45


def test_layers_show_the_common_mode_floor():
    at = app("layers")
    s = sliders(at)
    for name in ("Detection effectiveness", "Intervention effectiveness", "Containment effectiveness"):
        s[name].set_value(0.99)
    s["Common-mode bypass ρ"].set_value(0.2)
    run(at)
    assert metric(at, "V — what gets through everything").startswith("0.20")


def test_race_reports_the_split():
    at = app("race")
    s = sliders(at)
    s["Escalation rate (per day)"].set_value(3.0)
    s["Mean time to recover (days)"].set_value(1.0)
    run(at)
    assert metric(at, "Of 100 events that get through…") == "75 become irreversible"


def test_whatif_strip_and_open_weights():
    at = app("whatif")
    sliders(at)["Open weights: proliferation"].set_value(100)
    run(at)
    strip = next(m.value for m in at.markdown if 'class="cg-strip"' in m.value)
    assert float(strip.split('cg-strip-num">×')[1].split("<")[0]) > 1
    assert "raises hazard" in strip
    assert metric(at, "Open weights, on net") != "not applied"


def test_control_gap_slope_matches_the_paper_dashboard():
    at = app("gap")
    assert metric(at, "Implied hazard growth") == "+24% / yr"
    s = sliders(at)
    for name in ("Detection (points)", "Intervention (points)", "Containment (points)"):
        s[name].set_value(3.0)
    s["Recovery time (%)"].set_value(-20)
    s["Episodes ν"].set_value(-10)
    run(at)
    assert float(metric(at, "Implied hazard growth").rstrip("% / yr")) < 0
    assert at.success


def test_challenge_spends_a_budget_and_refuses_to_overspend():
    at = app("challenge")
    s = sliders(at)
    s["Incident response capacity"].set_value(100)
    run(at)
    strip = next(m.value for m in at.markdown if 'class="cg-strip"' in m.value)
    assert "15 / 100 pts spent" in strip
    for label in list(sliders(at)):
        sliders(at)[label].set_value(100)
    run(at)
    assert "over budget" in next(m.value for m in at.markdown if 'class="cg-strip"' in m.value)


def test_tiny_values_never_display_as_zero():
    at = app("chain")
    s = sliders(at)
    for label in ("Capability C", "Access A", "Agency O", "Exposure X", "Propensity M"):
        s[label].set_value(0.01)
    run(at)
    assert "× 10⁻" in next(m.value for m in at.sidebar.markdown if "Combined factor" in m.value)


def test_feedback_links_are_prefilled_and_carry_no_token():
    at = app("start")
    urls = [b.proto.url for b in at.sidebar.get("link_button")]
    assert urls, "no feedback links rendered"
    for url in urls:
        assert url.startswith("https://github.com/pizuricv/controlgap/issues/new?")
        assert "title=" in url and "body=" in url and "labels=" in url
        assert "token" not in url.lower()


def test_precursor_chapter_cites_every_event_and_scores_them():
    import incidents

    at = app("precursors_chapter")
    text = " ".join(m.value for m in at.markdown)
    for incident in incidents.INCIDENTS:
        assert incident.sources, f"{incident.key} has no source"
        for _, url in incident.sources:
            assert url.startswith("https://"), url
    shown = incidents.INCIDENTS[0]
    assert shown.title in text
    assert all(url in text for _, url in shown.sources)
    assert "our judgement, not the source" in " ".join(c.value for c in at.caption)
    assert metric(at, "Chance it would have completed")


def test_proposing_an_event_asks_for_a_source():
    at = app("precursors_chapter")
    urls = [b.proto.url for b in at.get("link_button")]
    proposal = next(u for u in urls if "precursor" in u)
    assert proposal.startswith("https://github.com/pizuricv/controlgap/issues/new?")
    assert "Source" in __import__("urllib.parse", fromlist=["unquote"]).unquote(proposal)


def test_fitting_elasticities_from_precursor_counts():
    at = app("precursors_chapter")
    theta_a = metric(at, "θ for access")
    assert 0.5 < float(theta_a) < 3.0, theta_a
    assert "90% interval" in next(m.delta for m in at.metric if m.label.endswith("θ for access"))
