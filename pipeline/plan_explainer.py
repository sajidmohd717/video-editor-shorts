"""
Explainer planner (ref 003 treatment).

    python -m pipeline.plan_explainer <slug>

Reads projects/<slug>/words.json (word-level timings) plus an authored beat map,
and writes projects/<slug>/timeline.json.

What's automated vs. authored, honestly:
  automated — caption chunking, shot subdivision, framing rotation, punch-in
              direction, strobe placement, pacing metadata
  authored  — WHICH graphic goes on WHICH sentence (the BEATS list below)

Choosing the right visual for a claim is the part that actually needs to
understand the sentence. Everything else is mechanical, and mechanical is what
gets ref 003's 1.5 cuts/sec without a human placing 50 cuts by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Project

FPS = 30
AROLL = "yc-sam-01/aroll.mp4"

# --- Framing rotation -------------------------------------------------------
# One landscape source, cut into distinct "shots" by varying the 9:16 crop focus
# and the punch. The subject sits at ~0.72 across the source frame.
FRAMINGS = [
    {"focusX": 0.72, "focusY": 0.42, "from": 1.00, "to": 1.06},  # medium
    {"focusX": 0.70, "focusY": 0.34, "from": 1.14, "to": 1.20},  # close, high
    {"focusX": 0.74, "focusY": 0.48, "from": 1.08, "to": 1.02},  # pull back
    {"focusX": 0.66, "focusY": 0.40, "from": 1.22, "to": 1.28},  # tight
    {"focusX": 0.72, "focusY": 0.46, "from": 1.00, "to": 1.10},  # medium push
]

# --- B-roll ------------------------------------------------------------------
# Portrait Pexels clips only. The Pixabay results are all landscape (their video
# endpoint has no orientation filter) and would need reframing — fine for texture
# later, but the native-portrait ones are cleaner.
#
# B-roll goes on CONCRETE NOUNS only, never on the reasoning. Altman is making an
# argument and his face carries it; cutting away mid-point weakens the claim.
# Total cutaway here is ~7.9s of 40.6s.
# Every entry here was eyeballed before use. Stock APIs match tags, not meaning:
# "city skyline aerial" returned trees and a parked car, "server data center"
# returned a screen of ping output, and "rocket launch" returned a child with a
# toy rocket. Assume roughly half of any search is unusable and look first.
BROLL = {
    "vintage": "yc-sam-01/stock/pexels-video-12271136.mp4",   # vintage tower PCs
    "skyline": "yc-sam-01/stock/pexels-video-9921286.mp4",    # night skyscrapers
    "robotics": "yc-sam-01/stock/pexels-video-8328143.mp4",   # robotic arm + lab coats
    "datacenter": "yc-sam-01/stock/pexels-video-6755162.mp4",  # circuit board macro
    "typing": "yc-sam-01/stock/pexels-video-12893579.mp4",    # hands typing code
}


def broll_clip(cid: str, start: float, end: float, src: str, offset: float = 0.6,
               scale_from: float = 1.04, scale_to: float = 1.12) -> dict:
    return {
        "id": cid,
        "start": round(start, 3),
        "end": round(end, 3),
        "layout": "full",
        "background": "#000000",
        "sources": [{
            "src": src, "offset": offset,
            "focusX": 0.5, "focusY": 0.5,
            "panX": 0, "panY": 0, "scale": 1, "muted": True,
        }],
        "camera": {
            "kind": "punch-in", "from": scale_from, "to": scale_to,
            "originX": 0.5, "originY": 0.5,
        },
        "filters": [],
        "transitionIn": "cut",
        "transitionDuration": 0,
    }


# --- Authored beats ---------------------------------------------------------
# (start, end, kind, payload). Times in seconds, from the transcript.
BEATS: list[tuple[float, float, str, dict]] = [
    # A plain label, not an annotation: an arrow pointing into someone's hair
    # annotates nothing. Arrows belong on graphics, where there's a thing to point at.
    (1.10, 3.55, "word", {
        "text": "3 MONTHS", "face": "sans-heavy", "size": 128, "color": "#FFFFFF",
    }),
    # Comparison, not chart. The sentence claims a jump, not a trend.
    (10.10, 12.70, "compare", {
        "beforeLabel": "Then", "beforeValue": "3 months",
        "afterLabel": "Now", "afterValue": "7 minutes",
        "afterDelay": 0.85, "accent": "#FF5A3C", "tone": "light",
    }),
    # "only 20 years ago" — vintage machine under the card, not his face.
    (12.85, 15.60, "word", {
        "text": "20 years ago.", "face": "serif-display", "size": 132,
        "color": "#FFFFFF", "broll": "vintage",
    }),
    (26.90, 28.80, "code", {
        "code": "$ codex \"build a marketplace for used telescopes\"\n"
                "  > scaffolding next.js app...\n"
                "  > wiring stripe checkout...\n"
                "  > seeding 400 listings...\n"
                "  > deployed. 6m 41s\n",
    }),
    # "the world's most ambitious, crazy company"
    (30.60, 32.40, "broll", {"asset": "skyline"}),
    # "experts in every field working together"
    (32.90, 34.85, "broll", {"asset": "robotics"}),
    # "these very hard technological things"
    (36.30, 37.70, "broll", {"asset": "datacenter", "scale_from": 1.0, "scale_to": 1.16}),
    (37.85, 39.30, "strobe", {"count": 5}),
    (39.30, 40.60, "word", {
        "text": "impossible.", "face": "sans-heavy", "size": 150,
        "color": "#FF5A3C",
    }),
]

STROBE_FRAME = 1 / FPS


def chunk_words(words: list[dict], max_words: int = 2, max_gap: float = 0.45) -> list[dict]:
    """
    Group words into 1-2 word caption cards (ref 003's rate).

    Breaks early on a long pause or on terminal punctuation so a card never
    straddles a sentence boundary — that reads as a mistake even at this speed.
    """
    cues: list[dict] = []
    buf: list[dict] = []

    def flush() -> None:
        if not buf:
            return
        cues.append({
            "start": round(buf[0]["start"], 3),
            "end": round(buf[-1]["end"], 3),
            "emphasis": "none",
            "words": [dict(w) for w in buf],
        })
        buf.clear()

    for i, w in enumerate(words):
        buf.append(w)
        ends_sentence = w["text"].rstrip("”’\"'").endswith((".", "?", "!", ","))
        gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 0
        if len(buf) >= max_words or ends_sentence or gap > max_gap:
            flush()
    flush()

    # Close gaps so a card stays up until the next one takes over — holes read as
    # dropped captions rather than as deliberate silence.
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else c["end"] + 0.4
        c["end"] = round(min(nxt, c["end"] + 0.5), 3)
    return cues


def emphasise(cues: list[dict], keywords: set[str]) -> None:
    for c in cues:
        joined = " ".join(w["text"] for w in c["words"]).lower().strip(".,“”’")
        if any(k in joined for k in keywords):
            c["emphasis"] = "color"


def aroll_clip(cid: str, start: float, end: float, framing: dict, background: str = "#000000") -> dict:
    return {
        "id": cid,
        "start": round(start, 3),
        "end": round(end, 3),
        "layout": "full",
        "background": background,
        "sources": [{
            "src": AROLL, "offset": round(start, 3),
            "focusX": framing["focusX"], "focusY": framing["focusY"],
            "panX": 0, "panY": 0, "scale": 1, "muted": True,
        }],
        "camera": {
            "kind": "punch-in", "from": framing["from"], "to": framing["to"],
            "originX": 0.5, "originY": 0.38,
        },
        "filters": [],
        "transitionIn": "cut",
        "transitionDuration": 0,
    }


def graphic_clip(cid: str, start: float, end: float, background: str) -> dict:
    return {
        "id": cid, "start": round(start, 3), "end": round(end, 3),
        "layout": "graphic", "background": background, "sources": [],
        "camera": {"kind": "none", "from": 1, "to": 1, "originX": 0.5, "originY": 0.5},
        "filters": [], "transitionIn": "cut", "transitionDuration": 0,
    }


def build(words: list[dict], duration: float) -> dict:
    clips: list[dict] = []
    overlays: list[dict] = []
    n = 0

    # Beats claim their windows first; a-roll fills whatever is left.
    claimed = sorted([(b[0], b[1]) for b in BEATS])
    gaps: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in claimed:
        if s > cursor:
            gaps.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration:
        gaps.append((cursor, duration))

    # Subdivide each a-roll gap into shots. Target ~1.1s, which combined with the
    # beat inserts lands near ref 003's 1.5 cuts/sec overall.
    for gi, (gs, ge) in enumerate(gaps):
        span = ge - gs
        shots = max(1, round(span / 1.1))
        step = span / shots
        for i in range(shots):
            f = FRAMINGS[(gi + i) % len(FRAMINGS)]
            clips.append(aroll_clip(f"a{gi}_{i}", gs + i * step, gs + (i + 1) * step, f))

    for bi, (bs, be, kind, payload) in enumerate(BEATS):
        n += 1
        if kind == "annotate":
            clips.append(aroll_clip(f"b{bi}", bs, be, FRAMINGS[1]))
            overlays.append({
                "type": "annotation", "id": f"anno{bi}", "start": bs + 0.15, "end": be,
                "z": 55, "labelSize": 92, **payload,
            })
        elif kind == "chart":
            clips.append(graphic_clip(f"b{bi}", bs, be, "#E9E9EC"))
            overlays.append({
                "type": "stat-chart", "id": f"chart{bi}", "start": bs, "end": be,
                "z": 40, **payload,
            })
        elif kind == "compare":
            clips.append(graphic_clip(f"b{bi}", bs, be, "#E9E9EC"))
            overlays.append({
                "type": "comparison", "id": f"cmp{bi}", "start": bs, "end": be,
                "z": 40, **payload,
            })
        elif kind == "broll":
            clips.append(broll_clip(
                f"b{bi}", bs, be, BROLL[payload["asset"]],
                offset=payload.get("offset", 0.6),
                scale_from=payload.get("scale_from", 1.04),
                scale_to=payload.get("scale_to", 1.12),
            ))
        elif kind == "word":
            card = {k: v for k, v in payload.items() if k != "broll"}
            if payload.get("broll"):
                clips.append(broll_clip(f"b{bi}", bs, be, BROLL[payload["broll"]]))
            else:
                clips.append(aroll_clip(f"b{bi}", bs, be, FRAMINGS[3]))
            overlays.append({
                "type": "word-card", "id": f"word{bi}", "start": bs, "end": be,
                "z": 65, **card,
            })
        elif kind == "code":
            clips.append(graphic_clip(f"b{bi}", bs, be, "#04120A"))
            overlays.append({
                "type": "code-panel", "id": f"code{bi}", "start": bs, "end": be,
                "z": 40, "language": "bash", "scrollSpeed": 14, **payload,
            })
        elif kind == "montage":
            # Rapid list: 4-frame shots while the VO enumerates.
            shots = payload["shots"]
            step = (be - bs) / shots
            for i in range(shots):
                f = FRAMINGS[i % len(FRAMINGS)]
                c = aroll_clip(f"b{bi}_{i}", bs + i * step, bs + (i + 1) * step, f)
                c["camera"] = {"kind": "none", "from": 1.05 + i * 0.06, "to": 1.05 + i * 0.06,
                               "originX": 0.5, "originY": 0.38}
                clips.append(c)
        elif kind == "strobe":
            # Single-frame percussive inserts. Not editorial cuts — impacts.
            count = payload["count"]
            for i in range(count):
                t = bs + i * (STROBE_FRAME * 2)
                c = aroll_clip(f"b{bi}_{i}", t, t + STROBE_FRAME, FRAMINGS[i % len(FRAMINGS)])
                c["camera"] = {"kind": "none", "from": 1.3 + i * 0.1, "to": 1.3 + i * 0.1,
                               "originX": 0.5, "originY": 0.38}
                if i % 2:
                    c["filters"] = ["desaturate"]
                clips.append(c)
            clips.append(aroll_clip(f"b{bi}_tail", bs + count * STROBE_FRAME * 2, be, FRAMINGS[3]))

    clips.sort(key=lambda c: c["start"])

    cues = chunk_words(words, max_words=2)
    emphasise(cues, {"three", "months", "seven", "minutes", "impossible", "20", "years"})

    overlays.append({
        "type": "chrome", "id": "bug", "start": 0, "end": duration, "z": 85,
        "bug": "THE NEXT CURVE", "tone": "light",
    })
    overlays.append({
        "type": "progress", "id": "prog", "start": 0, "end": duration, "z": 95, "style": "bar",
    })
    overlays.append({
        "type": "cta", "id": "cta", "start": 21.0, "end": 23.4, "z": 88,
        "text": "SUBSCRIBE", "x": 0.5, "y": 0.87, "color": "#1D4ED8",
    })

    return {
        "version": 1,
        "meta": {
            "title": "Three months of work. Now seven minutes.",
            "slug": "yc-sam-01",
            "durationInSeconds": round(duration, 3),
            "fps": FPS,
        },
        "pacing": [
            {"start": 0, "end": 4, "energy": 1.0, "label": "hook"},
            {"start": 4, "end": 13, "energy": 1.2, "label": "build"},
            {"start": 13, "end": 25, "energy": 1.0, "label": "hold"},
            {"start": 25, "end": 35, "energy": 1.4, "label": "build"},
            {"start": 35, "end": 40.6, "energy": 2.5, "label": "payoff"},
        ],
        "clips": clips,
        "overlays": overlays,
        "captions": {
            "style": {
                "preset": "word-pop", "fontFamily": "Poppins", "fontWeight": 800,
                "fontSize": 64, "color": "#FFFFFF", "anchorY": 0.70,
                "pillColor": "rgba(0,0,0,0)", "pillRadius": 0, "strokeWidth": 9,
            },
            "cues": cues,
        },
        # Source clip audio is the narration here, so no separate VO track.
        # +6dB lifts the -25.3 LUFS source toward the -13 master target; the rest
        # comes from the loudnorm pass in pipeline/master.py.
        "audio": [{
            "id": "src", "src": AROLL, "role": "clip-audio",
            "start": 0, "offset": 0, "gainDb": 6, "duck": False,
            "fadeIn": 0, "fadeOut": 0.3,
        }],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--duration", type=float, default=40.6)
    args = ap.parse_args()

    project = Project(args.slug).ensure()
    words_path = project.dir / "words.json"
    raw = json.loads(words_path.read_text(encoding="utf-8"))
    words = [
        {"text": w["text"], "start": w["startMs"] / 1000, "end": w["endMs"] / 1000}
        for w in raw
    ]

    timeline = build(words, args.duration)
    project.timeline.write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    cuts = len(timeline["clips"])
    print(f"-> {project.timeline}")
    print(f"   {cuts} clips over {args.duration}s = {cuts / args.duration:.2f} cuts/sec")
    print(f"   {len(timeline['captions']['cues'])} caption cards")
    print(f"   {len(timeline['overlays'])} overlays")


if __name__ == "__main__":
    sys.exit(main())
