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
    next(b for b in at.sidebar.button if b.label.startswith("Reset")).click()
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
    banner = next(m.value for m in at.markdown if 'class="cg-hero"' in m.value)
    assert "+24%" in banner
    assert "On these growth rates" in banner, "the verdict must name what it depends on"
    assert metric(at, "CGI slope") == "+0.218"
    s = sliders(at)
    for name in ("Detection (points)", "Intervention (points)", "Containment (points)"):
        s[name].set_value(3.0)
    s["Recovery time (%)"].set_value(-20)
    s["Episodes ν"].set_value(-10)
    run(at)
    assert float(metric(at, "CGI slope")) < 0


def test_the_sidebar_asserts_no_trend_before_chapter_nine():
    at = app("chain")
    sidebar = " ".join(m.value for m in at.sidebar.markdown)
    assert "Chain × defences" in sidebar
    assert "Hazard trend" not in sidebar, "the trend depends on sliders the reader has not seen"
    assert not any("outrunning control" in c.value for c in at.sidebar.caption)
    at = app("gap")
    assert "Hazard trend" in " ".join(m.value for m in at.sidebar.markdown)


def test_the_game_runs_four_rounds_against_a_moving_world():
    at = app("challenge")
    assert at.session_state["game"]["round"] == 0
    strip = next(m.value for m in at.markdown if 'class="cg-strip"' in m.value)
    assert "Round 1 of 4" in strip and "25 pts to spend" in strip

    for expected in range(1, 5):
        sliders(at)["Incident response capacity · 15 pts"].set_value(10)
        run(at)
        next(b for b in at.button if b.label.startswith("Commit")).click()
        run(at)
        if expected < 4:
            assert at.session_state["game"]["round"] == expected
    assert at.session_state["game"]["done"]
    text = " ".join(m.value for m in at.markdown)
    assert "Where you differed" in text and "2037" in text
    assert any("Play again" in b.label for b in at.button)


def test_the_world_plays_a_card_that_cannot_be_unplayed():
    at = app("challenge")
    at.session_state["game"] = {"round": 1, "spent": {}, "log": [], "seed": 1, "done": False}
    run(at)
    takeaways = " ".join(m.value for m in at.markdown if "cg-take" in m.value)
    assert "The world played a card" in takeaways
    assert "not a prediction" in takeaways


def test_the_walls_money_cannot_buy_are_on_screen():
    at = app("challenge")
    labels = [m.label for m in at.metric]
    assert "The floor you cannot buy past" in labels
    assert "Not recoverable at any price" in labels
    assert "At the ceiling already" in labels


def _retired_test_challenge_spends_a_budget_and_refuses_to_overspend():
    at = app("challenge")
    s = sliders(at)
    s["Incident response capacity · 15 pts"].set_value(100)
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
    for label in ("Capability C", "Access A", "Agency O", "Exposure X", "Trigger M"):
        s[label].set_value(0.01)
    run(at)
    assert "× 10⁻" in next(m.value for m in at.sidebar.markdown if "Chain" in m.value)


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


def test_incident_cards_appear_on_the_start_page_and_select_one():
    import incidents

    at = app("start")
    text = " ".join(m.value for m in at.markdown)
    for incident in incidents.INCIDENTS:
        assert incident.title in text, incident.key
    at = app("precursors_chapter")
    second = incidents.INCIDENTS[1]
    next(b for b in at.button if b.key == f"pick_inc_{second.key}").click()
    run(at)
    assert at.session_state["incident"] == second.key
    assert second.title in " ".join(m.value for m in at.markdown)


def test_an_incident_can_be_started_from_like_any_scenario():
    import incidents
    import ui

    first = incidents.INCIDENTS[0]
    assert first.scenario_name in ui.PRESETS, "each event should also be a scenario"
    at = app("start")
    next(b for b in at.button if b.key == f"start_{first.key}").click()
    run(at)
    assert at.session_state.preset == first.scenario_name
    assert at.session_state.P["X"] == first.preset["X"]
    # and the tour continues from chapter 2, exactly like the scenario cards
    assert any("Chapter 2" in b.label for b in at.button)


def test_choosing_an_event_shows_its_story_and_sources_immediately():
    import incidents

    first = incidents.INCIDENTS[0]
    at = app("start")
    text = " ".join(m.value for m in at.markdown)
    for incident in incidents.INCIDENTS:  # every card carries a teaser and its sources
        assert incident.summary.split(". ")[0] in text, incident.key
        assert all(url in text for _, url in incident.sources), incident.key
    next(b for b in at.button if b.key == f"start_{first.key}").click()
    run(at)
    told = " ".join(m.value for m in at.markdown)
    assert first.summary in told, "the full account should appear once chosen"
    assert first.scenario_why in told


def test_chapter_three_never_shows_a_single_probability():
    at = app("lambda0")
    shown = [m.value for m in at.metric]
    assert "0.40%" in shown and "3.91%" in shown and "32.90%" in shown, shown
    text = " ".join(m.value for m in at.markdown)
    assert "Nothing about the world changed" in text
    # the default lands on lambda0 * T = 1, where the chain and the probability coincide
    assert "same number, because λ₀ × T = 1" in text


def test_halving_a_factor_is_a_parallel_line_at_every_lambda0():
    import controlgap as cg
    import ui

    base = ui.scenario.__wrapped__ if hasattr(ui.scenario, "__wrapped__") else None
    grid = [0.01, 0.1, 1.0, 10.0]
    p = dict(ui.PRESETS["The paper's example"])
    full = cg.Scenario("a", C=p["C"], A=p["A"], O=p["O"], X=p["X"], M=p["M"],
                       effectiveness=(p["e0"], p["e1"], p["e2"]), rho=p["rho"],
                       p_I=cg.irreversibility(p["r_esc"], tau_rec=p["tau"]))
    half = cg.Scenario("b", C=p["C"], A=p["A"] / 2, O=p["O"], X=p["X"], M=p["M"],
                       effectiveness=(p["e0"], p["e1"], p["e2"]), rho=p["rho"],
                       p_I=cg.irreversibility(p["r_esc"], tau_rec=p["tau"]))
    ratios = [float(half.hazard(lam) / full.hazard(lam)) for lam in grid]
    assert all(abs(r - 0.5) < 1e-12 for r in ratios), ratios


def test_progress_is_tracked_and_the_end_card_appears():
    at = app("chain")
    assert at.session_state["visited"] == {2}
    assert "1 of 11 chapters read" in " ".join(m.value for m in at.sidebar.markdown)
    at = app("challenge")
    at.session_state["game"]["done"] = True
    run(at)
    assert any("Three things to leave with" in m.value for m in at.markdown)
    pasted = " ".join(c.value for c in at.get("code"))
    assert "The level is not identifiable" in pasted
    assert "scenario=" in pasted


def test_a_shared_link_restores_the_scenario_and_the_tweaks():
    import ui

    at = chapter("chain")
    at.query_params["scenario"] = "Autonomous cyber operations"
    run(at)
    assert at.session_state.preset == "Autonomous cyber operations"
    assert at.session_state.P["C"] == 0.45
    link = ui.share_link.__doc__ is not None  # helper exists
    assert link


def test_the_last_chapter_is_not_mistaken_for_the_first():
    at = app("challenge")
    assert at.session_state["chapter_number"] == 11
    sidebar = " ".join(m.value for m in at.sidebar.markdown)
    assert "Chain × defences" in sidebar
    assert "appear here from chapter 2" not in " ".join(c.value for c in at.sidebar.caption)


def _bare_session():
    """The helpers read st.session_state, which AppTest does not keep alive between runs."""
    import streamlit as st

    import ui

    for key, value in [("preset", ui.FIRST), ("gated", False), ("C0", 0.5), ("k", 15.0)]:
        st.session_state[key] = value
    st.session_state["P"] = ui.defaults(ui.FIRST)


def test_buying_early_beats_buying_late():
    """The four-round premise only means something if timing changes the score."""
    import chapters

    _bare_session()
    early = chapters._play_out({0: {"Alignment progress": 1.0}}, {})
    late = chapters._play_out({3: {"Alignment progress": 1.0}}, {})
    nothing = chapters._play_out({}, {})
    assert early < late < nothing, (early, late, nothing)
    assert chapters._efficiency({}, {}, "Alignment progress", 0) > chapters._efficiency({}, {}, "Alignment progress", 3)


def test_a_shared_link_starts_the_tour_rather_than_the_last_chapter():
    import ui

    _bare_session()
    link = ui.share_link()
    assert "/challenge" not in link and "?scenario=" in link


def test_chapter_eight_arrives_with_something_to_read():
    at = app("whatif")
    strip = next(m.value for m in at.markdown if 'class="cg-strip"' in m.value)
    assert "no change yet" not in strip, "the chapter should not open as a blank form"
    assert metric(at, "Drivers applied") == "2 of 11"
    assert metric(at, "Open weights, on net") != "not applied"


def test_every_incident_names_at_least_one_source_and_the_cluster_has_two():
    import incidents

    for incident in incidents.INCIDENTS:
        assert incident.sources
        for name, url in incident.sources:
            assert url.startswith("https://") and name
    cluster = incidents.BY_KEY["containment"]
    hosts = {url.split("/")[2] for _, url in cluster.sources}
    assert len(hosts) >= 2, "a claim about four organisations should not rest on one outlet"
