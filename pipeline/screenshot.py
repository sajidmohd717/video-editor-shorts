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


# Locate a phrase in the rendered page and hand back its box in page coordinates.
#
# This is how the highlight box gets positioned. The alternative was OCR, which is
# the wrong tool when we own the browser: the DOM already knows exactly where every
# word was painted, to the pixel, with no recognition step to be wrong about.
#
# Matching is on whitespace-collapsed, case-folded text with the node offsets kept
# alongside, so a phrase that straddles a <b> or a line break still resolves.
FIND_JS = """
(phrases) => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let flat = "";
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const p = n.parentElement;
    if (!p) continue;
    const st = getComputedStyle(p);
    if (st.display === "none" || st.visibility === "hidden") continue;
    const t = n.nodeValue.replace(/\\s+/g, " ");
    if (!t.trim()) continue;
    nodes.push({ node: n, start: flat.length, text: t });
    flat += t;
  }
  const hay = flat.toLowerCase();

  const locate = (offset) => {
    for (const e of nodes) {
      if (offset >= e.start && offset <= e.start + e.text.length) {
        return { node: e.node, offset: Math.min(offset - e.start, e.node.nodeValue.length) };
      }
    }
    return null;
  };

  return phrases.map((phrase) => {
    const needle = phrase.replace(/\\s+/g, " ").trim().toLowerCase();
    const i = hay.indexOf(needle);
    if (i < 0) return { phrase, found: false };
    const a = locate(i), b = locate(i + needle.length);
    if (!a || !b) return { phrase, found: false };
    const r = document.createRange();
    try { r.setStart(a.node, a.offset); r.setEnd(b.node, b.offset); }
    catch (e) { return { phrase, found: false }; }
    const box = r.getBoundingClientRect();
    // Per-line rects: a phrase wrapping across two lines is two boxes, and one
    // box around both would highlight the empty gutter between them.
    const lines = Array.from(r.getClientRects()).map((c) => ({
      x: c.x + scrollX, y: c.y + scrollY, w: c.width, h: c.height,
    }));
    return {
      phrase, found: true,
      x: box.x + scrollX, y: box.y + scrollY, w: box.width, h: box.height,
      lines,
    };
  });
}
"""


def capture(
    url: str,
    dest: Path,
    selector: str | None,
    full: bool,
    find: list[str] | None = None,
    crop_pad: int | None = None,
) -> dict:
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

        hits: list[dict] = []
        if find:
            page.evaluate("() => window.scrollTo(0, 0)")
            hits = page.evaluate(FIND_JS, find)
            meta["find"] = hits
            for h in hits:
                if not h.get("found"):
                    print(f"   ! phrase not found: {h['phrase'][:60]!r}")

        # Cropping to a located phrase is the point of --find: a 39,000px-tall
        # press release is not an asset, but the 900px around the sentence that
        # matters is.
        found = [h for h in hits if h.get("found")]
        if crop_pad is not None and found:
            top = min(h["y"] for h in found) - crop_pad
            bottom = max(h["y"] + h["h"] for h in found) + crop_pad
            full_h = page.evaluate("() => document.documentElement.scrollHeight")
            clip = {
                "x": 0, "y": max(0, top),
                "width": VIEWPORT["width"],
                "height": min(bottom, full_h) - max(0, top),
            }
            page.screenshot(path=str(dest), clip=clip, full_page=True)
            meta["mode"] = "phrase-crop"
            meta["clip"] = clip
            # Re-express every hit relative to the CROP, normalised — that's the
            # coordinate space the overlay actually draws in.
            for h in found:
                h["rel"] = {
                    "x": h["x"] / clip["width"],
                    "y": (h["y"] - clip["y"]) / clip["height"],
                    "w": h["w"] / clip["width"],
                    "h": h["h"] / clip["height"],
                }
                h["relLines"] = [{
                    "x": l["x"] / clip["width"],
                    "y": (l["y"] - clip["y"]) / clip["height"],
                    "w": l["w"] / clip["width"],
                    "h": l["h"] / clip["height"],
                } for l in h.get("lines", [])]
        elif full:
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
    ap.add_argument("--find", action="append", default=None,
                    help="locate a phrase and record its box; repeatable")
    ap.add_argument("--width", type=int, default=None,
                    help="viewport width; narrow it to reflow sidebars away and "
                         "let the article column fill the frame")
    ap.add_argument("--crop-pad", type=int, default=None,
                    help="with --find, crop to the phrases plus N px of context")
    args = ap.parse_args()

    if args.width:
        VIEWPORT["width"] = args.width

    project = Project(args.slug).ensure()
    shots = project.assets / "articles"
    shots.mkdir(parents=True, exist_ok=True)

    dest = shots / f"{args.name or slugify(args.url)}.png"
    meta = capture(args.url, dest, args.selector, args.full,
                   find=args.find, crop_pad=args.crop_pad)
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
    for h in meta.get("find", []):
        if h.get("found"):
            r = h.get("rel")
            where = (f"rel x={r['x']:.3f} y={r['y']:.3f} w={r['w']:.3f} h={r['h']:.3f}"
                     if r else f"page y={h['y']:.0f}")
            print(f"   found {h['phrase'][:44]!r} -> {where}")
    print(f"   manifest: {manifest}")


if __name__ == "__main__":
    sys.exit(main())
