import pytest

pytest.importorskip("streamlit")
from pathlib import Path  # noqa: E402

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).parents[1] / "app" / "app.py")


def run(at):
    at.run(timeout=120)
    assert not at.exception, [e.value for e in at.exception]
    return at


def metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_defaults_reproduce_section_12():
    at = run(AppTest.from_file(APP))
    assert metric(at, "Residual vulnerability V") == "0.190"
    assert metric(at, "Combined factor") == "0.00399"
    assert metric(at, "P(catastrophe within 10 yr)") == "0.40%"


def test_sliders_coupling_and_gate():
    at = run(AppTest.from_file(APP))
    by_label = {w.label: w for w in at.slider}
    by_label["Coupling g"].set_value(0.5)
    by_label["Common-mode bypass ρ"].set_value(0.3)
    by_label["Capability C"].set_value(0.95)
    at.toggle[0].set_value(True)
    run(at)
    assert float(metric(at, "Combined factor")) > 0.00399


def test_what_if_and_presets():
    at = run(AppTest.from_file(APP))
    sliders = {w.label: w for w in at.slider}
    sliders["Open weights: proliferation"].set_value(100)
    run(at)
    assert metric(at, "Hazard changes by").startswith("×") and float(metric(at, "Hazard changes by")[1:]) > 1
    {w.label: w for w in at.slider}["Open weights: defensive ecosystem"].set_value(100)
    at.selectbox[0].set_value("Autonomous cyber operations")
    run(at)
    assert metric(at, "Residual vulnerability V") != "0.190"


def test_intro_shows_once_and_can_be_reopened():
    at = run(AppTest.from_file(APP))
    assert at.session_state.intro_open and at.session_state.intro_step == 0
    next(b for b in at.button if b.label == "Next").click()
    run(at)
    assert at.session_state.intro_step == 1
    next(b for b in at.button if b.label == "Skip").click()
    run(at)
    assert not at.session_state.intro_open
    assert not [b for b in at.button if b.label == "Next"]
    next(b for b in at.button if b.label == "Show intro").click()
    run(at)
    assert at.session_state.intro_open and at.session_state.intro_step == 0


def test_tiny_hazard_is_never_shown_as_zero_and_banner_gives_the_level():
    at = run(AppTest.from_file(APP))
    sliders = {w.label: w for w in at.slider}
    for label in ("Capability C", "Access A", "Agency O", "Exposure X", "Propensity M"):
        sliders[label].set_value(0.01)
    run(at)
    assert "× 10⁻" in metric(at, "Combined factor")
    banner = next(m.value for m in at.markdown if 'class="cg-hero"' in m.value)
    assert "from a very low base" in banner
    assert "× 10⁻" in banner or "lower than" in banner
