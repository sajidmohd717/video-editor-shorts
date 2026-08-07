"""
Narrated planner — profile + job driven.

    python -m pipeline.plan_narrated <slug>

Reads projects/<slug>/job.json (this video) and the profile it names (this
channel), and writes projects/<slug>/timeline.json.

Nothing channel-specific or video-specific lives in this file. Brand, caption
style, pacing and voice come from the profile; source passages, b-roll and beats
come from the job. If you find yourself adding a colour or an asset path here,
it belongs in one of those two instead — see pipeline/profiles.py.

Structure: original narration is the SPINE, the source clip is EVIDENCE. That's
what survives YouTube's reused-content rule; attribution alone does not.
Narration and clip interleave rather than overlap — ducking a speaker under a
voiceover means two people talking at once, which is worse to listen to and
weaker editorially than taking turns (F9).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys

from .config import Project
from .profiles import Job, load_job

FPS = 30


def build(job: Job) -> dict:
    project = Project(job.slug).ensure()

    # staticFile() only resolves under public/, so the VO has to live there.
    if not project.vo.exists():
        raise SystemExit(f"No narration at {project.vo}. Run pipeline.tts first.")
    shutil.copyfile(project.vo, project.assets / "vo.wav")
    vo_src = f"{job.slug}/vo.wav"
    aroll = job.source["aroll"]

    caps = json.loads((project.dir / "captions.json").read_text(encoding="utf-8"))
    vo_words = caps["words"]
    # Derived from the audio, so swapping voice or engine re-times the whole edit.
    vo_paras = [(p["start"], p["end"]) for p in caps["paragraphs"]]

    clip_raw = json.loads((project.dir / "words.json").read_text(encoding="utf-8"))
    clip_words = [
        {"text": w["text"], "start": w["startMs"] / 1000, "end": w["endMs"] / 1000}
        for w in clip_raw
    ]

    # --- profile-derived settings -------------------------------------------
    brand = job.get("brand", {})
    accent = brand.get("accent", "#FF5A3C")
    canvas = brand.get("canvas", "#E9E9EC")
    gap = job.get("pacing.handoffGapSeconds", 0.3)
    aroll_shot = job.get("pacing.arollShotSeconds", 1.1)
    broll_shot = job.get("pacing.brollShotSeconds", 1.9)
    vo_gain = job.get("audio.voGainDb", 2)
    clip_gain = job.get("audio.clipGainDb", 0)
    focus_x = job.source.get("subjectFocusX", 0.5)

    # Framings come from the profile but are re-centred on this source's subject.
    framings = [
        {**f, "focusX": focus_x} for f in job.get("camera.framings", [])
    ] or [{"focusX": focus_x, "focusY": 0.42, "from": 1.0, "to": 1.08}]

    clips: list[dict] = []
    overlays: list[dict] = []
    audio: list[dict] = []
    words_out: list[dict] = []
    t = 0.0

    def aroll_clip(cid: str, start: float, end: float, f: dict, src_off: float) -> dict:
        return {
            "id": cid, "start": round(start, 3), "end": round(end, 3),
            "layout": "full", "background": "#000000",
            "sources": [{
                "src": aroll, "offset": round(src_off, 3),
                "focusX": f["focusX"], "focusY": f["focusY"],
                "panX": 0, "panY": 0, "scale": 1, "muted": True,
            }],
            "camera": {"kind": "punch-in", "from": f["from"], "to": f["to"],
                       "originX": 0.5, "originY": 0.38},
            "filters": [], "transitionIn": "cut", "transitionDuration": 0,
        }

    def broll_clip(cid: str, start: float, end: float, asset: str,
                   offset: float = 0.6, sf: float = 1.04, st: float = 1.12) -> dict:
        src = job.broll.get(asset)
        if not src:
            raise SystemExit(f"job.broll has no entry named {asset!r}")
        return {
            "id": cid, "start": round(start, 3), "end": round(end, 3),
            "layout": "full", "background": "#000000",
            "sources": [{
                "src": src, "offset": offset, "focusX": 0.5, "focusY": 0.5,
                "panX": 0, "panY": 0, "scale": 1, "muted": True,
            }],
            "camera": {"kind": "punch-in", "from": sf, "to": st,
                       "originX": 0.5, "originY": 0.5},
            "filters": [], "transitionIn": "cut", "transitionDuration": 0,
        }

    def place_vo(index: int) -> tuple[float, float]:
        nonlocal t
        s, e = vo_paras[index]
        dur = e - s + 0.25
        audio.append({
            "id": f"vo{index}", "src": vo_src, "role": "vo",
            "start": round(t, 3), "offset": round(s, 3), "duration": round(dur, 3),
            "gainDb": vo_gain, "duck": False, "fadeIn": 0, "fadeOut": 0.15,
        })
        for w in vo_words:
            if s <= w["start"] < e:
                words_out.append({"text": w["text"], "start": w["start"] - s + t,
                                  "end": w["end"] - s + t, "voice": "vo"})
        start = t
        t += dur + gap
        return start, t - gap

    def place_clip(span: tuple[float, float]) -> tuple[float, float, float]:
        nonlocal t
        s, e = span
        shift = t - s
        audio.append({
            "id": f"clip{s:.0f}", "src": aroll, "role": "clip-audio",
            "start": round(t, 3), "offset": round(s, 3), "duration": round(e - s, 3),
            "gainDb": clip_gain, "duck": False, "fadeIn": 0.05, "fadeOut": 0.15,
        })
        for w in clip_words:
            if s <= w["start"] < e:
                words_out.append({"text": w["text"], "start": w["start"] + shift,
                                  "end": w["end"] + shift, "voice": "clip"})
        start = t
        t = e + shift
        return start, t, shift

    def fill_aroll(start: float, end: float, shift: float, tag: str) -> None:
        n = max(1, round((end - start) / aroll_shot))
        step = (end - start) / n
        for i in range(n):
            f = framings[i % len(framings)]
            a, b = start + i * step, start + (i + 1) * step
            clips.append(aroll_clip(f"{tag}{i}", a, b, f, a - shift))

    def fill_broll(start: float, end: float, assets: list[str], tag: str) -> None:
        """
        Several shots, not one long hold. A single 8-second shot under a
        voiceover is the fastest way to make an explainer feel like a slideshow:
        the ear is engaged but the eye isn't. Varying the source offset stops
        repeats of one asset reading as a loop.
        """
        if not assets:
            return
        n = max(1, round((end - start) / broll_shot))
        step = (end - start) / n
        for i in range(n):
            clips.append(broll_clip(
                f"{tag}{i}", start + i * step, start + (i + 1) * step,
                assets[i % len(assets)],
                offset=0.4 + 1.7 * (i // len(assets)),
                sf=1.02 + 0.03 * (i % 3), st=1.12 + 0.03 * (i % 3),
            ))

    def beats_at(where: str) -> list[dict]:
        return [b for b in job.beats if b.get("at") == where]

    def add_overlay(beat: dict, start: float, end: float, oid: str) -> None:
        payload = {k: v for k, v in beat.items()
                   if k not in ("at", "type", "start", "end", "why", "asset",
                                "sourceStart", "sourceEnd")}
        overlays.append({"type": beat["type"], "id": oid,
                         "start": round(start, 3), "end": round(end, 3),
                         "z": beat.get("z", 55), **payload})

    # --- 1. narration opens ---------------------------------------------------
    v0s, v0e = place_vo(0)
    fill_broll(v0s, v0e + gap, job.raw.get("openBroll", []), "open")
    for i, b in enumerate(beats_at("open")):
        add_overlay(b, v0s + b.get("start", 0), v0s + b.get("end", 3), f"open_ov{i}")

    # --- 2. clip states the claim --------------------------------------------
    passages = job.passages
    if not passages:
        raise SystemExit("job.source.passages is empty — nothing to cut")
    a_s, a_e, a_shift = place_clip(passages[0])
    fill_aroll(a_s, a_e, a_shift, "a")

    # --- 3. narration reframes it --------------------------------------------
    v1s, v1e = place_vo(1)
    clips.append({
        "id": "vo1bg", "start": round(v1s, 3), "end": round(v1e + gap, 3),
        "layout": "graphic", "background": canvas, "sources": [],
        "camera": {"kind": "none", "from": 1, "to": 1, "originX": 0.5, "originY": 0.5},
        "filters": [], "transitionIn": "cut", "transitionDuration": 0,
    })
    for i, b in enumerate(beats_at("vo1")):
        add_overlay({**b, "accent": b.get("accent", accent), "tone": b.get("tone", "light")},
                    v1s + 0.1, v1e + gap, f"vo1_ov{i}")

    # --- 4. clip pays it off --------------------------------------------------
    if len(passages) > 1:
        b_s, b_e, b_shift = place_clip(passages[1])
        fill_aroll(b_s, b_e, b_shift, "b")

        for i, beat in enumerate(beats_at("clip")):
            s = beat["sourceStart"] + b_shift
            e = beat["sourceEnd"] + b_shift
            if beat["type"] == "broll":
                clips[:] = [c for c in clips
                            if not (c["start"] >= s - 0.55 and c["end"] <= e + 0.55)]
                clips.append(broll_clip(f"nb{i}", s, e, beat["asset"]))
            else:
                add_overlay(beat, s, e, f"clip_ov{i}")
    else:
        b_e = a_e

    # --- 5. narration closes --------------------------------------------------
    v2s, v2e = place_vo(2)
    close = job.raw.get("closeBroll", [])
    fill_broll(v2s, v2e - 1.2, close, "close")
    if close:
        # Hold the last shot under the end card — a cut beneath a subscribe
        # prompt pulls the eye off the thing you're asking them to do.
        clips.append(broll_clip("close_end", v2e - 1.2, v2e + 0.9, close[0],
                                offset=4.0, sf=1.0, st=1.12))

    duration = round(v2e + 0.9, 3)
    clips.sort(key=lambda c: c["start"])

    # --- captions -------------------------------------------------------------
    words_out.sort(key=lambda w: w["start"])
    max_words = job.get("captions.maxWordsPerCard", 2)
    keywords = [k.lower() for k in job.get("captions.emphasisKeywords", [])]

    cues: list[dict] = []
    buf: list[dict] = []
    for i, w in enumerate(words_out):
        buf.append(w)
        ends = w["text"].rstrip("\"'”’").endswith((".", "?", "!", ",", ":", ";"))
        nxt = words_out[i + 1] if i + 1 < len(words_out) else None
        gap_to_next = nxt["start"] - w["end"] if nxt else 0
        # Never straddle a speaker change (F5) — merging the clip's last word
        # with the narration's first reads as a glitch, not as either speaker.
        speaker_change = bool(nxt) and nxt["voice"] != w["voice"]
        if len(buf) >= max_words or ends or gap_to_next > 0.45 or speaker_change:
            cues.append({
                "start": round(buf[0]["start"], 3), "end": round(buf[-1]["end"], 3),
                "emphasis": "none",
                "words": [{"text": x["text"], "start": round(x["start"], 3),
                           "end": round(x["end"], 3)} for x in buf],
            })
            buf = []
    if buf:
        cues.append({
            "start": round(buf[0]["start"], 3), "end": round(buf[-1]["end"], 3),
            "emphasis": "none",
            "words": [{"text": x["text"], "start": round(x["start"], 3),
                       "end": round(x["end"], 3)} for x in buf],
        })

    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else c["end"] + 0.35
        c["end"] = round(min(nxt, c["end"] + 0.45), 3)
        joined = " ".join(w["text"] for w in c["words"]).lower()
        if any(k in joined for k in keywords):
            c["emphasis"] = "color"

    # --- chrome ---------------------------------------------------------------
    if brand.get("bug"):
        overlays.append({"type": "chrome", "id": "bug", "start": 0, "end": duration,
                         "z": 85, "bug": brand["bug"],
                         "tone": brand.get("bugTone", "light")})
    if job.get("overlays.progress"):
        overlays.append({"type": "progress", "id": "prog", "start": 0, "end": duration,
                         "z": 95, "style": job.get("overlays.progress")})
    if job.get("overlays.showEndCard") and job.get("endCard"):
        ec = job.get("endCard")
        overlays.append({"type": "end-card", "id": "end",
                         "start": round(v2e - 0.4, 3), "end": duration, "z": 92,
                         "title": ec.get("title", ""), "subtitle": ec.get("subtitle"),
                         "handle": brand.get("handle", "")})

    caption_style = {k: v for k, v in job.get("captions", {}).items()
                     if k not in ("maxWordsPerCard", "emphasisKeywords")}

    return {
        "version": 1,
        "meta": {"title": job.raw.get("title", job.slug), "slug": job.slug,
                 "durationInSeconds": duration, "fps": FPS},
        "pacing": [
            {"start": 0, "end": round(v0e, 3), "energy": 0.6, "label": "hook"},
            {"start": round(v0e, 3), "end": round(a_e, 3), "energy": 1.0, "label": "build"},
            {"start": round(a_e, 3), "end": round(v1e, 3), "energy": 0.4, "label": "hold"},
            {"start": round(v1e, 3), "end": round(b_e, 3), "energy": 1.2, "label": "payoff"},
            {"start": round(b_e, 3), "end": duration, "energy": 0.5, "label": "outro"},
        ],
        "clips": clips,
        "overlays": overlays,
        "captions": {"style": caption_style, "cues": cues},
        "audio": audio,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--skip-rights-check", action="store_true")
    args = ap.parse_args()

    job = load_job(args.slug)

    problems = job.check_rights()
    if problems:
        print("RIGHTS WARNINGS:")
        for p in problems:
            print(f"  ! {p}")
        if not args.skip_rights_check:
            raise SystemExit("\nFix job.json rights, or pass --skip-rights-check.")
        print()

    timeline = build(job)
    Project(args.slug).timeline.write_text(
        json.dumps(timeline, indent=2), encoding="utf-8")

    dur = timeline["meta"]["durationInSeconds"]
    vo = sum(a["duration"] for a in timeline["audio"] if a["role"] == "vo")
    floor = job.get("editorial.narrationShareFloor", 0)
    share = vo / dur

    print(f"-> {Project(args.slug).timeline}")
    print(f"   profile: {job.profile.get('id')} | {dur:.1f}s")
    print(f"   {len(timeline['clips'])} clips ({len(timeline['clips'])/dur:.2f}/s)"
          f" | {len(timeline['captions']['cues'])} cards")
    print(f"   narration {vo:.1f}s ({share:.0%})", end="")
    if floor and share < floor:
        print(f"  ! below profile floor of {floor:.0%} — thin for the reuse policy")
    else:
        print()


if __name__ == "__main__":
    sys.exit(main())
