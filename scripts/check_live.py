"""Smoke-check a deployed ControlGap app.

    python scripts/check_live.py https://<your-app>.streamlit.app

Streamlit Cloud serves the app inside an iframe at /~/+/, so a naive check of
the top-level page finds an empty wrapper and reports nothing at all. This
walks the frames and asserts against the one that actually holds the app.

Needs playwright:  pip install playwright && playwright install chromium
"""

from __future__ import annotations

import sys

CHAPTERS = ["", "chain", "missing-number", "layers", "race", "precursors", "levers", "what-if", "control-gap", "uncertainty", "challenge"]


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
            slow = path in ("", "uncertainty", "challenge")  # these sample or search before they draw
            deadline = 40_000 if slow else 12_000
            waited = 0
            while waited < deadline:
                page.wait_for_timeout(2_000)
                waited += 2_000
                if app_frame(page).evaluate("() => !!document.querySelector('.cg-h')"):
                    break
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
        # the page has more than one row of cards, so compare only within a row
        cards = frame.evaluate("""() => [...document.querySelectorAll('[class*="st-key-card_"]')].map(e => {
            const r = e.getBoundingClientRect();
            const b = e.querySelector('button');
            return {top: Math.round(r.y), height: Math.round(r.height), button: b ? Math.round(b.getBoundingClientRect().y) : null};
        })""")
        rows: dict[int, list[dict]] = {}
        for card in cards:
            rows.setdefault(card["top"] // 40, []).append(card)
        for row in rows.values():
            heights = [c["height"] for c in row]
            buttons = [c["button"] for c in row if c["button"] is not None]
            if max(heights) - min(heights) > 1 or (buttons and max(buttons) - min(buttons) > 1):
                failures.append(f"a row of cards is not aligned: heights {heights}, buttons {buttons}")
        print(f"  cards: {len(rows)} row(s), heights {[[c['height'] for c in r] for r in rows.values()]}")
        browser.close()

    print("\nFAILURES:" if failures else "\nall good")
    for line in failures:
        print(f"  {line}")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
