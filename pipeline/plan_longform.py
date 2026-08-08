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
import subprocess
import sys
from pathlib import Path

from .config import Project
from .profiles import Job, load_job

FPS = 30
WIDTH, HEIGHT = 1920, 1080


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def measure_lufs(path: Path) -> tuple[float, float]:
    """Integrated loudness and true peak, via loudnorm in MEASURE mode."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r'\{[^{}]*"input_i"[\s\S]*?\}', r.stderr)
    if not m:
        raise SystemExit(f"could not measure loudness of {path}")
    d = json.loads(m.group(0))
    return float(d["input_i"]), float(d["input_tp"])


def match_gain(clip: Path, target_i: float, cache: dict) -> float:
    """
    Static dB gain that brings `clip` to the narration's loudness.

    Source clips arrive at whatever level the room, the mic and the platform
    left them at — measured here, a conference-floor recording sat 15.4 dB under
    our narration, which on the render was the single most important sentence in
    Ch5 being the quietest thing in the video.

    Deliberately a STATIC gain: measure with loudnorm, apply with `volume`.
    Single-pass loudnorm as a filter is a DYNAMIC normalizer that pumps gain up
    during quiet passages — that is what manufactured the phantom "static" that
    cost most of a session to chase (F13).
    """
    key = clip.name
    if key not in cache:
        i, tp = measure_lufs(clip)
        cache[key] = {"i": i, "tp": tp}
    i, tp = cache[key]["i"], cache[key]["tp"]
    gain = target_i - i
    # Never let the boost clip: leave 1 dB of true-peak headroom.
    return round(min(gain, -1.0 - tp), 2)


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

    # --- cold open ------------------------------------------------------------
    # The one place source audio leads (L5). Everything derived from the
    # narration — cues, captions, chapter boundaries — shifts by this much, so
    # it is applied once, here, and never thought about again.
    #
    # This is an EDIT decision, not a script change: the narration is untouched,
    # it just starts later. Worth having because the channel's one retention
    # data point says the opening is what failed — yc-sam-01 opened on abstract
    # b-roll under a synthetic voice and held 32% against ~63% for clip-first
    # cuts. Real broadcast voices first is the direct test of that.
    cold = job.raw.get("coldOpen", [])
    lead = round(sum(c["seconds"] for c in cold), 3)

    # NB: total inserted gap time is added after `inserts` is built, below.
    duration = round(lead + words[-1]["end"] + job.get("pacing.tailSeconds", 2.0), 3)

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

    # Loudness reference: everything that speaks is matched to the narration.
    lcache_path = project.dir / "loudness.json"
    lcache = (json.loads(lcache_path.read_text(encoding="utf-8"))
              if lcache_path.exists() else {})
    vo_i = lcache.get("_vo", {}).get("i")
    if vo_i is None:
        vo_i, vo_tp = measure_lufs(project.vo)
        lcache["_vo"] = {"i": vo_i, "tp": vo_tp}
    print(f"   narration {vo_i:.1f} LUFS")

    clips: list[dict] = []
    overlays: list[dict] = []
    audio: list[dict] = []

    # --- phrase cueing --------------------------------------------------------
    flat = [norm(w["text"]) for w in words]

    def raw_cue(phrase: str, occurrence: int = 1) -> float | None:
        """Time of the first word of the nth occurrence, in NARRATION time."""
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

    # --- making room for source audio ----------------------------------------
    # L5 says let the clip speak. That rule came from shorts, where narration and
    # clip ALTERNATE, so a hole always exists. Long-form narration is continuous
    # by design — measured here, the largest gap anywhere near the Ch5 cue is
    # 0.68s — so there is nowhere to put a 16-second clip. Playing it anyway
    # stacks two voices, which is not "letting the clip speak", it's mud.
    #
    # So the planner CUTS THE NARRATION and inserts the gap, exactly as the cold
    # open shifts it at the top. The script is still untouched; the VO becomes
    # several segments with silence between them.
    inserts: list[tuple[float, float]] = []
    for sa in job.raw.get("sourceAudio", []):
        ct = raw_cue(sa["cue"], sa.get("occurrence", 1)) if "cue" in sa else sa.get("at")
        if ct is None:
            print(f"  ! sourceAudio cue not found: {sa.get('cue')!r}")
            continue
        ct = max(0.0, ct + sa.get("offset", 0.0))
        pad = sa.get("padSeconds", job.get("pacing.sourceAudioPadSeconds", 0.45))
        inserts.append((ct, sa["seconds"] + pad))
        sa["_at"] = ct
    inserts.sort()

    # Every inserted gap lengthens the video.
    duration = round(duration + sum(d for _, d in inserts), 3)

    def shift(t: float) -> float:
        """
        Narration time -> video time.

        `t` itself has to be carried through, not just the offsets: video time is
        the narration clock PLUS the cold open PLUS every gap opened before this
        point. Dropping the `t` collapses the entire timeline onto `lead`, which
        renders as zero-length cards and overlapping VO segments rather than as
        an error.
        """
        return round(lead + t + sum(d for ct, d in inserts if ct <= t), 3)

    def shift_before(t: float) -> float:
        """As `shift`, but excluding a gap opened exactly at `t` — this is where
        the source-audio clip itself goes."""
        return round(lead + t + sum(d for ct, d in inserts if ct < t), 3)

    # --- narration spine ------------------------------------------------------
    # One VO file, played as segments with the source-audio gaps between them.
    vo_end = round(words[-1]["end"] + 0.4, 3)
    bounds = [0.0] + [ct for ct, _ in inserts] + [vo_end]
    for n in range(len(bounds) - 1):
        a, b = bounds[n], bounds[n + 1]
        if b - a < 0.05:
            continue
        audio.append({
            "id": f"vo{n}", "src": vo_src, "role": "vo",
            "start": shift(a), "offset": round(a, 3), "duration": round(b - a, 3),
            "gainDb": job.get("audio.voGainDb", 0), "duck": False,
            "fadeIn": 0.1 if n == 0 else 0.12,
            "fadeOut": 0.6 if n == len(bounds) - 2 else 0.12,
        })


    def find_cue(phrase: str, occurrence: int = 1) -> float | None:
        r = raw_cue(phrase, occurrence)
        return None if r is None else shift(r)

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

    # --- cold-open clips ------------------------------------------------------
    t = 0.0
    for i, c in enumerate(cold):
        src = job.raw.get("newsClips", {}).get(c["asset"])
        if not src:
            raise SystemExit(f"coldOpen references unknown newsClip {c['asset']!r}")
        clips.append({
            "id": f"co{i}", "start": round(t, 3), "end": round(t + c["seconds"], 3),
            "layout": "full", "background": "#000000",
            "sources": [{"src": src, "offset": 0.0,
                         "focusX": c.get("focusX", 0.5), "focusY": c.get("focusY", 0.5),
                         "panX": 0, "panY": 0, "scale": 1, "muted": True}],
            "camera": {"kind": "punch-in", "from": 1.0, "to": 1.03,
                       "originX": 0.5, "originY": 0.5},
            "filters": [], "transitionIn": "cut", "transitionDuration": 0,
        })
        # Source audio leads here — full level, not ducked under anything.
        audio.append({
            "id": f"coa{i}", "src": src, "role": "clip-audio",
            "start": round(t, 3), "offset": 0.0, "duration": c["seconds"],
            "gainDb": c.get("gainDb", 0), "duck": False,
            "fadeIn": 0.05 if i else 0.25, "fadeOut": 0.05,
        })
        t += c["seconds"]

    if cold and burn:
        # Mark the handover from broadcast voices to ours.
        overlays.append({
            "type": "film-burn", "id": "coburn",
            "start": round(lead - burn_dur * 0.6, 3),
            "end": round(lead + burn_dur * 0.4, 3), "z": 78,
            "originX": -0.02, "originY": 0.45,
            "intensity": job.get("overlays.transitionBurnIntensity", 0.75),
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
                png = project.assets / Path(entry["file"]).relative_to(job.slug)
                if png.exists():
                    from PIL import Image
                    with Image.open(png) as im:
                        payload["aspect"] = round(im.width / im.height, 4)
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
        # Anything under ~0.2s is not a shot, it's a flash. Filling a 60ms hole
        # between two cards puts two frames of unrelated b-roll on screen; those
        # holes are closed later by extending the previous clip instead.
        if s > cursor + 0.45:
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

    # Close short gaps by extending the previous clip.
    #
    # Adjacent visuals placed from cue times land a few milliseconds apart after
    # rounding. The gap filler ignores anything under 0.05s while the coverage
    # assertion checks at 0.001s, so a 40ms hole fell between the two and failed
    # the plan. Extending is better than emitting a 1-frame filler clip, which
    # would flash a different image for a single frame.
    for n in range(len(clips) - 1):
        gap = clips[n + 1]["start"] - clips[n]["end"]
        if 0 < gap <= 0.5:
            clips[n]["end"] = clips[n + 1]["start"]

    # --- source-audio moments -------------------------------------------------
    # L5: a clip speaks only where the fact that THEY said it is the evidence.
    for i, sa in enumerate(job.raw.get("sourceAudio", [])):
        if "_at" not in sa:
            continue
        pad = sa.get("padSeconds", job.get("pacing.sourceAudioPadSeconds", 0.45))
        # An explicit gainDb in the job wins; otherwise match the narration.
        if "gainDb" in sa:
            gain = sa["gainDb"]
        else:
            gain = match_gain(project.assets / Path(sa["src"]).relative_to(job.slug),
                              vo_i, lcache)
            print(f"   {Path(sa['src']).name:22} gain {gain:+.2f} dB")
        # Lands in the hole opened for it: a beat of air, then the clip.
        audio.append({
            "id": f"src{i}", "src": sa["src"], "role": "clip-audio",
            "start": round(shift_before(sa["_at"]) + pad * 0.6, 3),
            "offset": sa.get("sourceOffset", 0.0), "duration": sa["seconds"],
            "gainDb": gain, "duck": False,
            "fadeIn": 0.1, "fadeOut": 0.3,
        })

    # --- lip-sync invariant ---------------------------------------------------
    # If a clip is on screen while its own audio plays, the two must start
    # together. The source-audio pad opens a beat of air before the clip speaks,
    # which is right for a document but desyncs a talking head by exactly that
    # much — visible, and invisible in the job file.
    speech_starts = [(a["start"], a["src"]) for a in audio if a["role"] == "clip-audio"]
    for c in clips:
        if not c["sources"]:
            continue
        vsrc = Path(c["sources"][0]["src"]).stem
        for astart, asrc in speech_starts:
            if Path(asrc).stem == vsrc and abs(astart - c["start"]) > 0.04:
                raise SystemExit(
                    f"lip-sync: {vsrc} video starts at {c['start']:.2f}s but its audio "
                    f"at {astart:.2f}s ({abs(astart - c['start']):.2f}s out). "
                    f"Set padSeconds to 0 on that sourceAudio entry.")

    # --- one-voice invariant --------------------------------------------------
    # Narration and source audio must never overlap. This is four lines and it
    # makes a whole bug class unshippable (F18's lesson): the `shift()` bug that
    # dropped narration time produced overlapping VO segments and zero-length
    # cards, and NOTHING errored — it just silently rendered wrong. An assertion
    # would have caught it the first time it ran.
    speech = sorted(
        [(a["start"], a["start"] + a["duration"], a["id"])
         for a in audio if a["role"] in ("vo", "clip-audio")])
    for (s1, e1, i1), (s2, e2, i2) in zip(speech, speech[1:]):
        if s2 < e1 - 0.02:
            raise SystemExit(
                f"two voices overlap: {i1} runs to {e1:.2f}s but {i2} starts at "
                f"{s2:.2f}s. Source audio needs a gap cut into the narration.")

    # Nothing should be left with no duration — a card that never shows is the
    # same failure as a clip that never plays, and just as quiet.
    for o in overlays:
        if o["end"] - o["start"] < 0.15:
            raise SystemExit(f"overlay {o['id']} ({o['type']}) has no duration")

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

    # --- visual-density report -------------------------------------------------
    # The one thing no invariant caught: a video can satisfy coverage,
    # uniqueness, cadence and loudness and still be boring. Assertions catch
    # defects, not dullness — so measure the thing that actually correlates
    # (L19) and print it, per window, every run.
    win = 40.0
    weak = []
    n_win = int(duration // win) + 1
    for k in range(n_win):
        a, b = k * win, min((k + 1) * win, duration)
        if b - a < 10:
            continue
        g = sum(min(c["end"], b) - max(c["start"], a)
                for c in clips if not c["sources"] and c["start"] < b and c["end"] > a)
        if g / (b - a) < 0.20:
            weak.append((a, b, g / (b - a)))
    if weak:
        print(f"   ! {len(weak)} window(s) under 20% purpose-built visuals:")
        for a, b, f in weak:
            print(f"       {a:6.0f}-{b:6.0f}s  {f*100:3.0f}%")

    lcache_path.write_text(json.dumps(lcache, indent=2), encoding="utf-8")

    caption_style = {k: v for k, v in job.get("captions", {}).items()
                     if k not in ("maxWordsPerCard", "emphasisKeywords")}

    # --- caption the source audio too -----------------------------------------
    # A clip that speaks should be readable. The words come from ASR of the cut
    # file with the wording hand-corrected against the primary document (F4:
    # trust ASR's timing, never its wording — it heard "$638,000" for "$638
    # billion", which is a different claim, not a typo).
    src_caps_path = project.dir / "source_captions.json"
    src_cues: list[dict] = []
    if src_caps_path.exists():
        src_caps = json.loads(src_caps_path.read_text(encoding="utf-8"))
        for a in audio:
            if a["role"] != "clip-audio":
                continue
            ws = src_caps.get(Path(a["src"]).stem)
            if not ws:
                continue
            base = a["start"] - a.get("offset", 0.0)
            group: list[dict] = []
            for w in ws:
                if w["start"] > a.get("offset", 0.0) + a["duration"]:
                    break
                group.append({"text": w["text"],
                              "start": round(base + w["start"], 3),
                              "end": round(base + w["end"], 3)})
                # Break on punctuation or every third word, matching the
                # narration cards so the two tracks read as one system.
                if len(group) >= 3 or w["text"].endswith((".", ",", "?", "!")):
                    src_cues.append({"start": group[0]["start"], "end": group[-1]["end"],
                                     "words": group, "emphasis": "none"})
                    group = []
            if group:
                src_cues.append({"start": group[0]["start"], "end": group[-1]["end"],
                                 "words": group, "emphasis": "none"})
        if src_cues:
            print(f"   {len(src_cues)} caption cards over source audio")

    # --- don't caption over a card that is already text ------------------------
    # A quote card holds the words on screen while the narrator reads them; the
    # caption track then prints the same sentence a second time, in a different
    # font, lower down. Two renderings of one sentence is worse than either.
    TEXT_CARDS = {"quote-card", "date-card", "comparison", "word-card", "kinetic-title",
                  "entity-graph", "big-number", "list-card"}
    mute = [(o["start"], o["end"]) for o in overlays if o["type"] in TEXT_CARDS]
    # Caption cues are in NARRATION time; everything else on the timeline is in
    # video time. Shift before comparing, or the mute test silently uses two
    # different clocks and the whole track fires `lead` seconds early.
    shifted = [{**c, "start": shift(c["start"]), "end": shift(c["end"]),
                **({"words": [{**w, "start": shift(w["start"]), "end": shift(w["end"])}
                              for w in c["words"]]}
                   if c.get("words") else {})}
               for c in caps.get("cues", [])]
    # Nothing of OURS may be on screen while someone else is speaking. A cue that
    # straddles an insertion point gets stretched across the whole gap by shift(),
    # so it sits there for the entire clip — our words captioned over their voice.
    # We have no transcript of what they say, so the right answer is no caption.
    mute = mute + [(a["start"], a["start"] + a["duration"])
                   for a in audio if a["role"] == "clip-audio"]
    cues = [c for c in shifted
            if not any(c["start"] < e and c["end"] > s for s, e in mute)]
    # Source-audio cards are added AFTER the mute filter — they belong inside
    # exactly the spans that filter removes.
    cues = sorted(cues + src_cues, key=lambda c: c["start"])
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
