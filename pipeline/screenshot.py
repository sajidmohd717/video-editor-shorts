"""
Article screenshot capture.

    python -m pipeline.screenshot <slug> --url https://... [--selector "article h1"]
    python -m pipeline.screenshot <slug> --url https://... --full

Captures the headline block of a news article as a PNG for the `article-clip`
overlay — ref 003's evidence device, and the thing that turns an assertion in the
script into a visible citation.

By default it crops to the headline region rather than grabbing the whole page: a
full-page screenshot scaled into a 1080-wide vertical frame renders the text
unreadable, which defeats the purpose.

On consent banners: these are removed from the DOM, never clicked. Clicking
"accept" would be agreeing to terms on your behalf, and we only need the pixels.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from .config import Project

VIEWPORT = {"width": 1400, "height": 1800}

# Headline containers, most specific first.
HEADLINE_SELECTORS = [
    "article header",
    "[data-testid='headline']",
    "article h1",
    "main h1",
    "h1",
]

# Overlays that sit on top of article text. Removed, not dismissed.
CLUTTER = """
[id*='onetrust'], [class*='onetrust'], [id*='cookie'], [class*='cookie-banner'],
[class*='consent'], [id*='consent'], [aria-label*='cookie' i],
[class*='paywall'], [class*='newsletter'], [class*='subscribe-overlay'],
[class*='modal'], [role='dialog'], [class*='sticky'], [class*='pop-up'],
[class*='popup'], [id*='gdpr'], [class*='gdpr'], iframe[src*='doubleclick']
"""


def slugify(url: str) -> str:
    p = urlparse(url)
    stem = f"{p.netloc}{p.path}".strip("/")
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")[:80] or "article"


def capture(url: str, dest: Path, selector: str | None, full: bool) -> dict:
    from playwright.sync_api import sync_playwright

    meta: dict = {"url": url}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,  # retina capture; text stays crisp when scaled
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        ).new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        try:
            page.wait_for_load_state("networkidle", timeout=12_000)
        except Exception:
            pass  # ad-heavy pages never go idle; the DOM is what matters

        # Strip overlays rather than interacting with them.
        page.evaluate(
            """(sel) => {
                document.querySelectorAll(sel).forEach(el => el.remove());
                document.body.style.overflow = 'visible';
            }""",
            CLUTTER.strip(),
        )
        page.wait_for_timeout(600)

        meta["title"] = page.title()

        if full:
            page.screenshot(path=str(dest), full_page=True)
            meta["mode"] = "full"
        else:
            target = None
            for sel in ([selector] if selector else HEADLINE_SELECTORS):
                try:
                    el = page.query_selector(sel)
                    if el and el.bounding_box():
                        target = el
                        meta["selector"] = sel
                        break
                except Exception:
                    continue

            if target is None:
                page.screenshot(path=str(dest))
                meta["mode"] = "viewport-fallback"
            else:
                box = target.bounding_box()
                # Pad generously below the headline so kicker, byline and dateline
                # come along — those are what make it read as a real article.
                page.screenshot(path=str(dest), clip={
                    "x": max(0, box["x"] - 30),
                    "y": max(0, box["y"] - 40),
                    "width": min(VIEWPORT["width"], box["width"] + 60),
                    "height": box["height"] + 260,
                })
                meta["mode"] = "headline"

        # Grab the visible headline text so the timeline can reference the exact
        # phrase to sweep-highlight without re-reading the image.
        try:
            h1 = page.query_selector("h1")
            meta["headline"] = h1.inner_text().strip() if h1 else ""
        except Exception:
            meta["headline"] = ""

        browser.close()

    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--url", required=True)
    ap.add_argument("--selector", default=None, help="CSS selector to crop to")
    ap.add_argument("--full", action="store_true", help="capture the whole page")
    ap.add_argument("--name", default=None)
    args = ap.parse_args()

    project = Project(args.slug).ensure()
    shots = project.assets / "articles"
    shots.mkdir(parents=True, exist_ok=True)

    dest = shots / f"{args.name or slugify(args.url)}.png"
    meta = capture(args.url, dest, args.selector, args.full)
    meta["file"] = project.asset_ref(dest)
    meta["outlet"] = urlparse(args.url).netloc.replace("www.", "")

    manifest = shots / "manifest.json"
    entries = []
    if manifest.exists():
        entries = json.loads(manifest.read_text(encoding="utf-8")).get("articles", [])
    entries = [e for e in entries if e.get("file") != meta["file"]] + [meta]
    manifest.write_text(json.dumps({"articles": entries}, indent=2), encoding="utf-8")

    size = dest.stat().st_size // 1024 if dest.exists() else 0
    print(f"-> {dest}  ({size} KB, mode={meta.get('mode')})")
    if meta.get("headline"):
        print(f"   headline: {meta['headline'][:90]}")
    print(f"   manifest: {manifest}")


if __name__ == "__main__":
    sys.exit(main())
