"""
Narrated Explainer planner.

    python -m pipeline.plan_narrated <slug>

Builds a timeline where original narration is the SPINE and the source clip is
EVIDENCE — the structure that survives YouTube's reused-content rule. Attribution
alone doesn't; the test is whether you added something substantial.

Narration and clip interleave rather than overlap. Ducking the speaker under a
voiceover means two people talking at once, which is worse to listen to and
weaker editorially than simply taking turns.

The source clip is also trimmed: 40.6s of Altman plus 21s of narration would run
past a minute, so only the two strongest passages survive — the claim and the
payoff. The connective middle goes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys

from .config import Project
from .plan_explainer import BROLL, FRAMINGS, aroll_clip, broll_clip, graphic_clip

FPS = 30
AROLL = "yc-sam-01/aroll.mp4"
VO = "yc-sam-01/vo.wav"

# VO paragraph spans, measured from vo.words.json.
VO_PARAS = [(0.00, 7.84), (8.52, 13.58), (14.10, 21.00)]

# Source-clip passages worth keeping.
CLIP_A = (0.00, 12.78)    # "...three months to build ... seven minutes by a coding agent"
CLIP_B = (25.08, 39.80)   # "...you could either be sad ... things that were just impossible"

GAP = 0.30  # breath between a VO segment and the clip resuming


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    args = ap.parse_args()

    project = Project(args.slug).ensure()

    # Remotion's staticFile() only resolves under public/, so the VO has to live
    # there. Copying here keeps it a pipeline step rather than a manual one.
    vo_public = project.assets / "vo.wav"
    if not project.vo.exists():
        raise SystemExit(f"No narration at {project.vo}. Run pipeline.tts first.")
    shutil.copyfile(project.vo, vo_public)

    vo_words = json.loads((project.dir / "captions.json").read_text(encoding="utf-8"))["words"]
    clip_raw = json.loads((project.dir / "words.json").read_text(encoding="utf-8"))
    clip_words = [
        {"text": w["text"], "start": w["startMs"] / 1000, "end": w["endMs"] / 1000}
        for w in clip_raw
    ]

    clips: list[dict] = []
    overlays: list[dict] = []
    audio: list[dict] = []
    cues_src: list[dict] = []
    t = 0.0

    def place_vo(index: int) -> tuple[float, float]:
        """Lay a narration paragraph at the playhead; return its span."""
        nonlocal t
        s, e = VO_PARAS[index]
        dur = e - s + 0.25
        audio.append({
            "id": f"vo{index}", "src": VO, "role": "vo",
            "start": round(t, 3), "offset": round(s, 3), "duration": round(dur, 3),
            "gainDb": 2, "duck": False, "fadeIn": 0, "fadeOut": 0.15,
        })
        for w in vo_words:
            if s <= w["start"] < e:
                cues_src.append({
                    "text": w["text"],
                    "start": w["start"] - s + t,
                    "end": w["end"] - s + t,
                    "voice": "vo",
                })
        start = t
        t += dur + GAP
        return start, t - GAP

    def place_clip(span: tuple[float, float]) -> tuple[float, float]:
        nonlocal t
        s, e = span
        shift = t - s
        audio.append({
            "id": f"clip{s:.0f}", "src": AROLL, "role": "clip-audio",
            "start": round(t, 3), "offset": round(s, 3), "duration": round(e - s, 3),
            "gainDb": 6, "duck": False, "fadeIn": 0.05, "fadeOut": 0.15,
        })
        for w in clip_words:
            if s <= w["start"] < e:
                cues_src.append({
                    "text": w["text"],
                    "start": w["start"] + shift,
                    "end": w["end"] + shift,
                    "voice": "clip",
                })
        start = t
        t = e + shift
        return start, t

    def fill_broll(start: float, end: float, assets: list[str], tag: str,
                   shot: float = 1.9) -> None:
        """
        Fill a narration window with several b-roll shots rather than one long
        hold. A single 8-second shot under a voiceover is the fastest way to make
        an explainer feel like a slideshow — the ear is engaged but the eye isn't.
        Each shot also enters the source at a different offset so repeats of the
        same asset don't read as a loop.
        """
        span = end - start
        n = max(1, round(span / shot))
        step = span / n
        for i in range(n):
            asset = assets[i % len(assets)]
            clips.append(broll_clip(
                f"{tag}{i}", start + i * step, start + (i + 1) * step,
                BROLL[asset], offset=0.4 + 1.7 * (i // len(assets)),
                scale_from=1.02 + 0.03 * (i % 3), scale_to=1.12 + 0.03 * (i % 3),
            ))

    def fill_aroll(start: float, end: float, source_shift: float, tag: str) -> None:
        """Subdivide a clip passage into shots at ~1.1s, rotating framings."""
        span = end - start
        n = max(1, round(span / 1.1))
        step = span / n
        for i in range(n):
            f = FRAMINGS[i % len(FRAMINGS)]
            c = aroll_clip(f"{tag}{i}", start + i * step, start + (i + 1) * step, f)
            c["sources"][0]["offset"] = round(start + i * step - source_shift, 3)
            clips.append(c)

    # --- 1. Narration opens. B-roll only; he hasn't spoken yet. ---------------
    v0s, v0e = place_vo(0)
    fill_broll(v0s, v0e + GAP, ["datacenter", "typing", "vintage", "robotics"], "open", shot=1.7)
    overlays.append({
        "type": "word-card", "id": "hook", "start": v0s + 0.3, "end": v0s + 3.0,
        "z": 65, "text": "3 months.", "face": "serif-display", "size": 150,
        "color": "#FFFFFF",
    })
    overlays.append({
        "type": "word-card", "id": "hook2", "start": v0s + 3.3, "end": v0s + 6.2,
        "z": 65, "text": "Now 7 minutes.", "face": "sans-heavy", "size": 118,
        "color": "#FF5A3C",
    })

    # --- 2. Altman states the claim ------------------------------------------
    a_s, a_e = place_clip(CLIP_A)
    fill_aroll(a_s, a_e, a_s - CLIP_A[0], "a")

    # --- 3. Narration reframes it. The comparison graphic belongs exactly here,
    #        because paragraph 2 IS "three months, down to seven". -------------
    v1s, v1e = place_vo(1)
    clips.append(graphic_clip("cmp", v1s, v1e + GAP, "#E9E9EC"))
    overlays.append({
        "type": "comparison", "id": "cmp1", "start": v1s + 0.1, "end": v1e + GAP, "z": 40,
        "beforeLabel": "Then", "beforeValue": "3 months",
        "afterLabel": "Now", "afterValue": "7 minutes",
        "afterDelay": 1.4, "accent": "#FF5A3C", "tone": "light",
    })

    # --- 4. Altman delivers the payoff ---------------------------------------
    b_s, b_e = place_clip(CLIP_B)
    shift = b_s - CLIP_B[0]
    fill_aroll(b_s, b_e, shift, "b")

    # B-roll on the concrete nouns inside passage B, overwriting those shots.
    for src_a, src_b, asset in (
        (30.75, 32.34, "skyline"),
        (33.68, 34.90, "robotics"),
        (36.44, 37.70, "datacenter"),
    ):
        s, e = src_a + shift, src_b + shift
        clips[:] = [c for c in clips if not (c["start"] >= s - 0.55 and c["end"] <= e + 0.55)]
        clips.append(broll_clip(f"nb{src_a:.0f}", s, e, BROLL[asset]))

    # --- 5. Narration closes -------------------------------------------------
    v2s, v2e = place_vo(2)
    fill_broll(v2s, v2e - 1.2, ["skyline", "typing", "robotics"], "close", shot=1.9)
    # Hold the last shot through the end card — a cut under a subscribe prompt
    # pulls the eye away from the thing you're asking them to do.
    clips.append(broll_clip("close_end", v2e - 1.2, v2e + 0.9, BROLL["skyline"],
                            offset=4.0, scale_from=1.0, scale_to=1.12))
    overlays.append({
        "type": "end-card", "id": "end", "start": v2e - 0.4, "end": v2e + 0.9, "z": 92,
        "title": "THE NEXT CURVE", "subtitle": "big ideas, clear direction",
        "handle": "@thenextcurv3",
    })

    duration = round(v2e + 0.9, 3)
    clips.sort(key=lambda c: c["start"])

    # --- Captions ------------------------------------------------------------
    cues_src.sort(key=lambda w: w["start"])
    cues: list[dict] = []
    buf: list[dict] = []
    for i, w in enumerate(cues_src):
        buf.append(w)
        ends = w["text"].rstrip("\"'”’").endswith((".", "?", "!", ",", ":", ";"))
        nxt = cues_src[i + 1] if i + 1 < len(cues_src) else None
        gap = nxt["start"] - w["end"] if nxt else 0
        # Never let a card straddle a speaker change — merging the clip's last
        # word with the narration's first produced "coding Three", which reads
        # as a glitch rather than as either speaker.
        speaker_change = bool(nxt) and nxt["voice"] != w["voice"]
        if len(buf) >= 2 or ends or gap > 0.45 or speaker_change:
            cues.append({
                "start": round(buf[0]["start"], 3), "end": round(buf[-1]["end"], 3),
                "emphasis": "none", "words": [
                    {"text": x["text"], "start": round(x["start"], 3), "end": round(x["end"], 3)}
                    for x in buf
                ],
            })
            buf = []
    if buf:
        cues.append({
            "start": round(buf[0]["start"], 3), "end": round(buf[-1]["end"], 3),
            "emphasis": "none", "words": [
                {"text": x["text"], "start": round(x["start"], 3), "end": round(x["end"], 3)}
                for x in buf
            ],
        })

    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else c["end"] + 0.35
        c["end"] = round(min(nxt, c["end"] + 0.45), 3)
        joined = " ".join(w["text"] for w in c["words"]).lower()
        if any(k in joined for k in ("three months", "seven", "minutes", "impossible", "floor")):
            c["emphasis"] = "color"

    overlays.append({
        "type": "chrome", "id": "bug", "start": 0, "end": duration, "z": 85,
        "bug": "THE NEXT CURVE", "tone": "light",
    })
    overlays.append({
        "type": "progress", "id": "prog", "start": 0, "end": duration, "z": 95, "style": "bar",
    })

    timeline = {
        "version": 1,
        "meta": {
            "title": "Three months of work. Now seven minutes.",
            "slug": args.slug, "durationInSeconds": duration, "fps": FPS,
        },
        "pacing": [
            {"start": 0, "end": v0e, "energy": 0.6, "label": "hook"},
            {"start": v0e, "end": a_e, "energy": 1.0, "label": "build"},
            {"start": a_e, "end": v1e, "energy": 0.4, "label": "hold"},
            {"start": v1e, "end": b_e, "energy": 1.2, "label": "payoff"},
            {"start": b_e, "end": duration, "energy": 0.5, "label": "outro"},
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
        "audio": audio,
    }

    project.timeline.write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    vo_time = sum(a["duration"] for a in audio if a["role"] == "vo")
    print(f"-> {project.timeline}")
    print(f"   {duration:.1f}s total | {len(clips)} clips ({len(clips)/duration:.2f}/s)")
    print(f"   narration {vo_time:.1f}s ({100*vo_time/duration:.0f}%) | {len(cues)} caption cards")


if __name__ == "__main__":
    sys.exit(main())
