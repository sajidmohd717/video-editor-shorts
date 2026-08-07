"""
Long-form planner.

    python -m pipeline.plan_longform <slug>

Structurally different from `plan_narrated.py`, and the difference is the point.

In shorts, narration and clip **take turns** — one voice at a time, handoffs
marked by burns and whooshes. In long-form the narration runs **continuously**
and evidence appears *underneath* it: a filing, a chart, a clip, a card. Source
audio interrupts only where hearing someone say it is itself the evidence (L5).

So the shape is: one VO spine, a visual track laid against it, and a small number
of moments where a clip is allowed to speak.

## Cueing by phrase, not by timestamp

Visuals are placed by **the words the narration is saying**, not by a hardcoded
time:

    {"cue": "six hundred and thirty-eight", "type": "article-clip", ...}

Timestamps break every time the narration is regenerated — and at 5,400
characters a regeneration is inevitable (a rewrite, a voice change, a pace
change). Phrases survive all of that. Author once, re-render forever.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from .config import Project
from .profiles import Job, load_job

FPS = 30
WIDTH, HEIGHT = 1920, 1080


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def build(job: Job) -> dict:
    project = Project(job.slug).ensure()

    if not project.vo.exists():
        raise SystemExit(f"No narration at {project.vo}. Run pipeline.tts first.")
    shutil.copyfile(project.vo, project.assets / "vo.wav")
    vo_src = f"{job.slug}/vo.wav"

    caps = json.loads((project.dir / "captions.json").read_text(encoding="utf-8"))
    words = caps["words"]
    if not words:
        raise SystemExit("captions.json has no words — run pipeline.captions first")
    duration = round(words[-1]["end"] + job.get("pacing.tailSeconds", 2.0), 3)

    canvas = job.get("brand.canvas", "#0A0A0C")
    accent = job.get("brand.accent", "#FF5A3C")

    # Article screenshots and their located phrase boxes. The job names a
    # document and a phrase; where that phrase sits on the page is a fact about
    # the page, so it's looked up here rather than authored (see
    # `pipeline.screenshot --find`).
    art_manifest = project.assets / "articles" / "manifest.json"
    articles: dict[str, dict] = {}
    if art_manifest.exists():
        for a in json.loads(art_manifest.read_text(encoding="utf-8")).get("articles", []):
            articles[Path(a["file"]).stem] = a

    def article_box(name: str, phrase: str) -> tuple[dict | None, list[dict]]:
        entry = articles.get(name)
        if not entry:
            raise SystemExit(
                f"no captured article named {name!r} — run pipeline.screenshot first")
        for h in entry.get("find", []):
            if h.get("found") and norm(h["phrase"]) == norm(phrase):
                r = h.get("rel")
                if not r:
                    raise SystemExit(
                        f"article {name!r} was captured without --crop-pad, so "
                        f"phrase boxes have no image-relative coordinates")
                box = {"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"]}
                lines = [{"x": l["x"], "y": l["y"], "width": l["w"], "height": l["h"]}
                         for l in h.get("relLines", [])]
                return box, (lines if len(lines) > 1 else [])
        have = [h["phrase"] for h in entry.get("find", []) if h.get("found")]
        raise SystemExit(
            f"article {name!r} has no located phrase {phrase!r}.\n"
            f"  located: {have}\n"
            f"  re-run pipeline.screenshot with --find {phrase!r}")

    clips: list[dict] = []
    overlays: list[dict] = []
    audio: list[dict] = []

    # --- narration spine ------------------------------------------------------
    audio.append({
        "id": "vo", "src": vo_src, "role": "vo", "start": 0, "offset": 0,
        "duration": round(words[-1]["end"] + 0.4, 3),
        "gainDb": job.get("audio.voGainDb", 0), "duck": False,
        "fadeIn": 0.1, "fadeOut": 0.6,
    })

    # --- phrase cueing --------------------------------------------------------
    flat = [norm(w["text"]) for w in words]

    def find_cue(phrase: str, occurrence: int = 1) -> float | None:
        """Time of the first word of the nth occurrence of `phrase`."""
        target = norm(phrase).split()
        if not target:
            return None
        seen = 0
        for i in range(len(flat) - len(target) + 1):
            if flat[i:i + len(target)] == target:
                seen += 1
                if seen == occurrence:
                    return words[i]["start"]
        return None

    # --- chapters -------------------------------------------------------------
    # Chapter starts are themselves cued by phrase, so a rewrite doesn't
    # invalidate the structure.
    chapters = job.raw.get("chapters", [])
    chapter_times: list[tuple[float, dict]] = []
    for ch in chapters:
        t = find_cue(ch["cue"]) if ch.get("cue") else ch.get("at", 0.0)
        if t is None:
            print(f"  ! chapter cue not found: {ch['cue']!r}")
            continue
        chapter_times.append((t, ch))
    chapter_times.sort(key=lambda x: x[0])

    burn = job.get("overlays.transitionBurn")
    whoosh = job.get("overlays.transitionWhoosh")
    burn_dur = job.get("overlays.transitionBurnSeconds", 0.7)

    for n, (t, ch) in enumerate(chapter_times):
        if n == 0:
            continue  # nothing to transition from
        if burn:
            overlays.append({
                "type": "film-burn", "id": f"chburn{n}",
                "start": round(max(0, t - burn_dur * 0.55), 3),
                "end": round(t + burn_dur * 0.45, 3), "z": 78,
                "originX": 1.02 if n % 2 == 0 else -0.02,
                "originY": 0.3 + 0.1 * (n % 3),
                "intensity": job.get("overlays.transitionBurnIntensity", 0.75),
            })
        if whoosh and job.raw.get("sfx", {}).get(whoosh):
            audio.append({
                "id": f"sfx_ch{n}", "src": job.raw["sfx"][whoosh], "role": "sfx",
                "start": round(max(0, t - 0.3), 3), "offset": 0, "duration": 0.6,
                "gainDb": job.get("audio.whooshGainDb", -6), "duck": False,
                "fadeIn": 0, "fadeOut": 0.12,
            })

    # --- visuals --------------------------------------------------------------
    placed: list[tuple[float, float, dict]] = []
    missing: list[str] = []

    for i, v in enumerate(job.raw.get("visuals", [])):
        t = find_cue(v["cue"], v.get("occurrence", 1)) if "cue" in v else v.get("at")
        if t is None:
            missing.append(v.get("cue", "?"))
            continue
        t = max(0.0, t + v.get("offset", 0.0))
        dur = v.get("seconds", job.get("pacing.evidenceSeconds", 3.5))
        placed.append((t, t + dur, v))

    if missing:
        print(f"  ! {len(missing)} cue(s) not found in the narration:")
        for c in missing[:6]:
            print(f"      {c!r}")
        raise SystemExit(
            "Cues must match the narration exactly. Fix the cue text in job.json "
            "(it is matched on normalised words, so punctuation is ignored)."
        )

    placed.sort(key=lambda p: p[0])

    # Trim overlaps so an evidence shot never runs past the next one.
    for i in range(len(placed) - 1):
        s, e, v = placed[i]
        nxt = placed[i + 1][0]
        if e > nxt:
            placed[i] = (s, nxt, v)

    for i, (s, e, v) in enumerate(placed):
        kind = v["type"]
        if kind in ("broll", "news"):
            src = (job.broll if kind == "broll" else job.raw.get("newsClips", {})).get(v["asset"])
            if not src:
                raise SystemExit(f"no {kind} asset named {v['asset']!r}")
            clips.append({
                "id": f"v{i}", "start": round(s, 3), "end": round(e, 3),
                "layout": v.get("layout", "full"), "background": "#000000",
                "sources": [{"src": src, "offset": v.get("sourceOffset", 0.0),
                             "focusX": v.get("focusX", 0.5), "focusY": v.get("focusY", 0.5),
                             "panX": 0, "panY": 0, "scale": 1, "muted": True}],
                "camera": {"kind": "punch-in", "from": 1.0, "to": 1.05,
                           "originX": 0.5, "originY": 0.5},
                "filters": [], "transitionIn": "cut", "transitionDuration": 0,
            })
        else:
            # `tone` and the card background are one decision, not two. Wiring
            # them separately let a "dark" comparison render white text on the
            # profile's light canvas — invisible, and invisible in code too.
            if "background" in v:
                bg = v["background"]
            elif v.get("tone") == "dark":
                bg = job.get("brand.canvasDark", "#0B0B0F")
            else:
                bg = canvas
            clips.append({
                "id": f"v{i}", "start": round(s, 3), "end": round(e, 3),
                "layout": "graphic", "background": bg,
                "sources": [],
                "camera": {"kind": "none", "from": 1, "to": 1,
                           "originX": 0.5, "originY": 0.5},
                "filters": [], "transitionIn": "cut", "transitionDuration": 0,
            })
            payload = {k: val for k, val in v.items()
                       if k not in ("cue", "occurrence", "at", "offset", "seconds",
                                    "type", "asset", "why", "sfx", "background",
                                    "layout", "focusX", "focusY", "sourceOffset",
                                    "article")}
            if kind == "article-clip":
                entry = articles.get(v["article"]) if "article" in v else None
                if entry is None:
                    raise SystemExit("article-clip visual needs an 'article' name")
                payload["src"] = entry["file"]
                payload.setdefault("outlet", entry.get("outlet", ""))
                if v.get("highlight"):
                    box, lines = article_box(v["article"], v["highlight"])
                    payload["highlightBox"] = box
                    if lines:
                        payload["highlightLines"] = lines
                    # `highlight` on this overlay means "substring of the rendered
                    # headline"; over a screenshot the box does the work and the
                    # string would make the component look for text that isn't there.
                    payload.pop("highlight", None)
            overlays.append({"type": kind, "id": f"ov{i}",
                             "start": round(s, 3), "end": round(e, 3),
                             "z": v.get("z", 55),
                             **({"accent": accent} if kind == "comparison" else {}),
                             **payload})

        if v.get("sfx") and job.raw.get("sfx", {}).get(v["sfx"]):
            audio.append({
                "id": f"sfx_v{i}", "src": job.raw["sfx"][v["sfx"]], "role": "sfx",
                "start": round(max(0, s - 0.05), 3), "offset": 0,
                "duration": job.raw.get("sfxDurations", {}).get(v["sfx"], 0.6),
                "gainDb": job.get("audio.sfxGainDb", -2), "duck": False,
                "fadeIn": 0, "fadeOut": 0.1,
            })

    # --- fill the gaps --------------------------------------------------------
    # Anything the visuals list didn't claim gets filler b-roll, cut at the
    # profile's long-form cadence. Uncovered timeline renders as black (F18).
    filler = job.raw.get("fillerBroll", [])
    shot = job.get("pacing.brollShotSeconds", 3.2)
    fi = 0
    covered = sorted([(c["start"], c["end"]) for c in clips])
    cursor = 0.0
    gaps: list[tuple[float, float]] = []
    for s, e in covered:
        if s > cursor + 0.05:
            gaps.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < duration - 0.05:
        gaps.append((cursor, duration))

    for gs, ge in gaps:
        n = max(1, round((ge - gs) / shot))
        step = (ge - gs) / n
        for k in range(n):
            a, b = gs + k * step, gs + (k + 1) * step
            if filler:
                asset = filler[fi % len(filler)]
                fi += 1
                src = job.broll.get(asset)
                if not src:
                    raise SystemExit(f"fillerBroll references unknown asset {asset!r}")
                clips.append({
                    "id": f"f{fi}", "start": round(a, 3), "end": round(b, 3),
                    "layout": "full", "background": "#000000",
                    "sources": [{"src": src, "offset": 0.5 + 1.3 * (fi // max(1, len(filler))),
                                 "focusX": 0.5, "focusY": 0.5, "panX": 0, "panY": 0,
                                 "scale": 1, "muted": True}],
                    "camera": {"kind": "punch-in", "from": 1.0, "to": 1.06,
                               "originX": 0.5, "originY": 0.5},
                    "filters": [], "transitionIn": "cut", "transitionDuration": 0,
                })
            else:
                clips.append({
                    "id": f"f{fi}", "start": round(a, 3), "end": round(b, 3),
                    "layout": "graphic", "background": canvas, "sources": [],
                    "camera": {"kind": "none", "from": 1, "to": 1,
                               "originX": 0.5, "originY": 0.5},
                    "filters": [], "transitionIn": "cut", "transitionDuration": 0,
                })
                fi += 1

    clips.sort(key=lambda c: c["start"])

    # --- source-audio moments -------------------------------------------------
    # L5: a clip speaks only where the fact that THEY said it is the evidence.
    for i, sa in enumerate(job.raw.get("sourceAudio", [])):
        t = find_cue(sa["cue"], sa.get("occurrence", 1)) if "cue" in sa else sa.get("at")
        if t is None:
            print(f"  ! sourceAudio cue not found: {sa.get('cue')!r}")
            continue
        audio.append({
            "id": f"src{i}", "src": sa["src"], "role": "clip-audio",
            "start": round(t + sa.get("offset", 0.0), 3),
            "offset": sa.get("sourceOffset", 0.0), "duration": sa["seconds"],
            "gainDb": sa.get("gainDb", 0), "duck": False,
            "fadeIn": 0.1, "fadeOut": 0.3,
        })

    # --- coverage invariant (F18) --------------------------------------------
    holes: list[tuple[float, float]] = []
    cur = 0.0
    for c in clips:
        if c["start"] > cur + 0.001:
            holes.append((cur, c["start"]))
        cur = max(cur, c["end"])
    if cur < duration - 0.001:
        holes.append((cur, duration))
    if holes:
        raise SystemExit(
            "Clip track has uncovered gaps — these render as black:\n  "
            + "\n  ".join(f"{a:.2f}-{b:.2f}s" for a, b in holes))

    caption_style = {k: v for k, v in job.get("captions", {}).items()
                     if k not in ("maxWordsPerCard", "emphasisKeywords")}

    # --- don't caption over a card that is already text ------------------------
    # A quote card holds the words on screen while the narrator reads them; the
    # caption track then prints the same sentence a second time, in a different
    # font, lower down. Two renderings of one sentence is worse than either.
    TEXT_CARDS = {"quote-card", "date-card", "comparison", "word-card", "kinetic-title"}
    mute = [(o["start"], o["end"]) for o in overlays if o["type"] in TEXT_CARDS]
    cues = [c for c in caps.get("cues", [])
            if not any(c["start"] < e and c["end"] > s for s, e in mute)]
    if mute:
        print(f"   captions suppressed under {len(mute)} text cards "
              f"({len(caps.get('cues', [])) - len(cues)} cues dropped)")

    return {
        "version": 1,
        "meta": {
            "title": job.raw.get("title", job.slug), "slug": job.slug,
            "durationInSeconds": duration, "fps": FPS,
            "width": WIDTH, "height": HEIGHT,
        },
        "pacing": [
            {"start": round(t, 3),
             "end": round(chapter_times[i + 1][0] if i + 1 < len(chapter_times) else duration, 3),
             "energy": 0.4, "label": "build"}
            for i, (t, ch) in enumerate(chapter_times)
        ] or [{"start": 0, "end": duration, "energy": 0.4, "label": "build"}],
        "clips": clips,
        "overlays": overlays,
        "captions": {"style": caption_style, "cues": cues},
        "audio": audio,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    args = ap.parse_args()

    job = load_job(args.slug)
    problems = job.check_rights()
    if problems:
        print("RIGHTS WARNINGS:")
        for p in problems:
            print(f"  ! {p}")

    timeline = build(job)
    Project(args.slug).timeline.write_text(
        json.dumps(timeline, indent=2), encoding="utf-8")

    dur = timeline["meta"]["durationInSeconds"]
    n_clips = len(timeline["clips"])
    print(f"-> {Project(args.slug).timeline}")
    print(f"   {timeline['meta']['width']}x{timeline['meta']['height']} | "
          f"{dur/60:.1f} min | {len(timeline['pacing'])} chapters")
    print(f"   {n_clips} clips ({n_clips/dur:.2f}/s) | "
          f"{len(timeline['overlays'])} overlays | "
          f"{len([a for a in timeline['audio'] if a['role']=='clip-audio'])} source-audio moments")


if __name__ == "__main__":
    sys.exit(main())
