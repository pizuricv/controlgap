"""Smoke-check a deployed ControlGap app.

    python scripts/check_live.py https://<your-app>.streamlit.app

Streamlit Cloud serves the app inside an iframe at /~/+/, so a naive check of
the top-level page finds an empty wrapper and reports nothing at all. This
walks the frames and asserts against the one that actually holds the app.

Needs playwright:  pip install playwright && playwright install chromium
"""

from __future__ import annotations

import sys

CHAPTERS = ["", "chain", "missing-number", "layers", "race", "levers", "what-if", "control-gap", "uncertainty", "challenge"]


def app_frame(page):
    """The frame holding the Streamlit app, which is not the top-level page on Streamlit Cloud."""
    for frame in page.frames:
        try:
            if frame.evaluate("() => !!document.querySelector('.cg-h, [data-testid=\"stAppViewContainer\"]')"):
                return frame
        except Exception:  # a cross-origin frame, e.g. the status-page embed
            continue
    return page.main_frame


def main(base: str) -> int:
    from playwright.sync_api import sync_playwright

    base = base.rstrip("/")
    failures = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 950})
        for path in CHAPTERS:
            page.goto(f"{base}/{path}", wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(15_000 if path == "" else 6_000)
            frame = app_frame(page)
            heading = frame.evaluate("() => document.querySelector('.cg-h')?.textContent?.trim() || ''")
            crashed = frame.evaluate("() => document.body.innerText.includes('Traceback (most recent call last)')")
            if crashed or not heading:
                failures.append(f"/{path}: {'exception on page' if crashed else 'no chapter heading rendered'}")
            print(f"  /{path or '(home)'}: {heading or 'NOTHING RENDERED'}")
        page.goto(base, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(15_000)
        page.mouse.wheel(0, 520)
        page.wait_for_timeout(2_000)
        frame = app_frame(page)
        cards = frame.evaluate("() => [...document.querySelectorAll('[class*=\"st-key-card_\"]')].map(e => Math.round(e.getBoundingClientRect().height))")
        buttons = frame.evaluate("() => [...document.querySelectorAll('[class*=\"st-key-card_\"] button')].map(e => Math.round(e.getBoundingClientRect().y))")
        if cards and (max(cards) - min(cards) > 1 or max(buttons) - min(buttons) > 1):
            failures.append(f"scenario cards are not aligned: heights {cards}, buttons {buttons}")
        print(f"  cards: heights {cards}, buttons {buttons}")
        browser.close()

    print("\nFAILURES:" if failures else "\nall good")
    for line in failures:
        print(f"  {line}")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
