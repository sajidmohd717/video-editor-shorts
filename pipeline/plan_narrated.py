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
import re
import shutil
import subprocess
import sys

from .config import PUBLIC, Project
from .profiles import Job, load_job

FPS = 30


def detect_silences(path, noise_db: float = -38, min_dur: float = 0.30) -> list[tuple[float, float]]:
    """
    Real silences in the audio, via ffmpeg silencedetect.

    Word-gap detection is not enough: ASR frequently stretches a word's end time
    across a following pause. In this clip "three" is timed as spanning
    1.16-2.76s, hiding a 1.77s silence that is plainly audible. Only the waveform
    knows where the dead air actually is.
    """
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path),
         "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr

    starts = [float(m) for m in re.findall(r"silence_start:\s*([\d.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", out)]
    return list(zip(starts, ends))


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
    max_pause = job.get("pacing.maxPauseSeconds", 0.34)
    ambience_db = job.get("audio.brollAmbienceDb")
    sfx_gain = job.get("audio.sfxGainDb", -8)
    silences = detect_silences(PUBLIC / aroll)
    print(f"   {len(silences)} silence(s) detected in the source clip")
    focus_x = job.source.get("subjectFocusX", 0.5)

    # Framings come from the profile but are re-centred on this source's subject.
    framings = [
        {**f, "focusX": focus_x} for f in job.get("camera.framings", [])
    ] or [{"focusX": focus_x, "focusY": 0.42, "from": 1.0, "to": 1.08}]

    clips: list[dict] = []
    overlays: list[dict] = []
    audio: list[dict] = []
    words_out: list[dict] = []
    # (time, direction) — direction matters because a whoosh belongs on the way
    # INTO the clip ("here he comes"), not on the way back out.
    handoffs: list[tuple[float, str]] = []
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

        # Diegetic ambience: let the b-roll's own sound through, well under the
        # voice. Keyboard clatter, machine noise, room tone and street sound give
        # a cut somewhere to *be* — which is most of what a music bed was doing.
        # Where a channel forbids music this is the substitute, and it costs
        # nothing because the audio is already in the asset.
        if ambience_db is not None:
            audio.append({
                "id": f"amb_{cid}", "src": src, "role": "sfx",
                "start": round(start, 3), "offset": round(offset, 3),
                "duration": round(end - start, 3),
                "gainDb": ambience_db, "duck": False,
                "fadeIn": 0.25, "fadeOut": 0.35,
            })

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

    def compress_pauses(span: tuple[float, float]) -> list[tuple[float, float]]:
        """
        Split a passage at over-long silences, keeping only `max_pause` of each.

        Speakers leave dead air that reads as hesitation on a short — this clip
        has a 1.77s silence in the middle of "what took ... three months". A human
        editor cuts those and nobody notices. Keeping a fraction rather than all
        of it means the result still breathes instead of sounding clipped.
        """
        s, e = span
        segs: list[tuple[float, float]] = []
        cur = s
        keep = max_pause / 2

        for ss, se in silences:
            if se <= s or ss >= e:
                continue
            ss, se = max(ss, s), min(se, e)
            if se - ss <= max_pause:
                continue
            cut_from, cut_to = ss + keep, se - keep
            if cut_to <= cur:
                continue
            segs.append((cur, cut_from))
            cur = cut_to

        segs.append((cur, e))
        return [(a, b) for a, b in segs if b - a > 0.08]

    def place_clip(span: tuple[float, float]) -> tuple[float, float, list[tuple]]:
        """
        Lay a passage down, minus its long pauses. Returns the sub-segment map so
        beats authored in SOURCE time can be translated to timeline time.
        """
        nonlocal t
        start = t
        segments: list[tuple[float, float, float]] = []  # (src_a, src_b, shift)

        for si, (s, e) in enumerate(compress_pauses(span)):
            shift = t - s
            audio.append({
                "id": f"clip{s:.2f}".replace(".", "_"), "src": aroll, "role": "clip-audio",
                "start": round(t, 3), "offset": round(s, 3), "duration": round(e - s, 3),
                "gainDb": clip_gain, "duck": False,
                # Short fades at each internal join so the splice isn't a click.
                "fadeIn": 0.02 if si else 0.05, "fadeOut": 0.02,
            })
            for w in clip_words:
                if s <= w["start"] < e:
                    words_out.append({"text": w["text"], "start": w["start"] + shift,
                                      "end": w["end"] + shift, "voice": "clip"})
            segments.append((s, e, shift))
            t = e + shift

        return start, t, segments

    def src_to_timeline(src_t: float, segments: list[tuple]) -> float | None:
        """
        Map a SOURCE time onto the timeline, snapping to the nearest kept moment.

        Pause compression removes spans of source time, so an authored beat can
        land inside a hole. Dropping the whole beat for that is wrong — it loses a
        deliberate editorial decision because a boundary drifted by a tenth of a
        second. Snapping to the nearest surviving edge keeps the intent.
        """
        if not segments:
            return None
        for s, e, shift in segments:
            if s <= src_t <= e:
                return src_t + shift

        best, best_gap = None, None
        for s, e, shift in segments:
            edge = s if src_t < s else e
            gap = abs(src_t - edge)
            if best_gap is None or gap < best_gap:
                best, best_gap = edge + shift, gap
        return best

    def passage_scale(p: float) -> float:
        """
        Scale at normalised position `p` through a passage.

        One continuous curve across the WHOLE passage, not per shot. Giving each
        shot its own punch-in makes the zoom ramp up, snap back at the cut, and
        ramp again — it reads as pumping, and it's the single most unnatural
        thing a mechanical edit does (F11).

        Real multicam edits change the crop at a cut while the move continues
        underneath. So the cut changes `focusY`; the scale just keeps going.

        The curve breathes (a slow cosine) on top of a gentle overall creep, so
        it pushes in and eases back rather than climbing forever.
        """
        import math
        breathe = 0.5 - 0.5 * math.cos(2 * math.pi * p * 1.5)
        return 1.03 + 0.07 * breathe + 0.09 * p

    def fill_aroll_segments(segments: list[tuple], tag: str) -> None:
        """Subdivide each sub-segment into shots, so cuts never span a splice."""
        for si, (s, e, shift) in enumerate(segments):
            fill_aroll(s + shift, e + shift, shift, f"{tag}{si}_")

    def fill_aroll(start: float, end: float, shift: float, tag: str) -> None:
        n = max(1, round((end - start) / aroll_shot))
        step = (end - start) / n
        for i in range(n):
            a, b = start + i * step, start + (i + 1) * step
            f = framings[i % len(framings)]
            clip = aroll_clip(f"{tag}{i}", a, b, f, a - shift)
            # Continuous across the cut: this shot starts exactly where the last
            # one ended. Only the framing changes.
            clip["camera"]["from"] = round(passage_scale(i / n), 4)
            clip["camera"]["to"] = round(passage_scale((i + 1) / n), 4)
            clips.append(clip)

    def fill_broll(start: float, end: float, assets: list[str], tag: str) -> None:
        """
        Several shots, not one long hold. A single 8-second shot under a
        voiceover is the fastest way to make an explainer feel like a slideshow:
        the ear is engaged but the eye isn't. Varying the source offset stops
        repeats of one asset reading as a loop.
        """
        if not assets:
            return
        # Never repeat an asset inside one window — a repeat reads as running out
        # of material even when the placement is right. If that means fewer, longer
        # shots than the target cadence, take the longer shots.
        n = max(1, min(round((end - start) / broll_shot), len(assets)))
        step = (end - start) / n
        for i in range(n):
            clips.append(broll_clip(
                f"{tag}{i}", start + i * step, start + (i + 1) * step,
                assets[i % len(assets)],
                offset=0.4 + 1.7 * (i // len(assets)),
                sf=1.02 + 0.03 * (i % 3), st=1.12 + 0.03 * (i % 3),
            ))

    MIN_SHOT = 0.16

    def carve(s: float, e: float) -> None:
        """
        Clear the window [s, e] in the clip track, trimming rather than deleting.

        Deleting every clip that *overlaps* a padded window leaves the frame
        uncovered at the edges — which renders as black. Overlapping clips are
        split and their source offsets recomputed so the footage stays in sync.
        Fragments shorter than MIN_SHOT are dropped rather than left to flicker.
        """
        out: list[dict] = []
        for c in clips:
            if c["end"] <= s + 1e-6 or c["start"] >= e - 1e-6:
                out.append(c)
                continue

            for a, b, tag in ((c["start"], s, "L"), (e, c["end"], "R")):
                if b - a < MIN_SHOT:
                    continue
                piece = json.loads(json.dumps(c))
                piece["id"] = f"{c['id']}{tag}"
                piece["start"], piece["end"] = round(a, 3), round(b, 3)
                for src in piece["sources"]:
                    # offset tracks timeline position, so shifting start shifts it.
                    shift = c["start"] - src["offset"]
                    src["offset"] = round(a - shift, 3)
                out.append(piece)

        clips[:] = out

    def beats_at(where: str) -> list[dict]:
        return [b for b in job.beats if b.get("at") == where]

    def place_sfx(name: str, at: float, gain: float | None = None) -> None:
        """
        Fire a one-shot sound effect at an absolute timeline moment.

        Level defaults well under the voice: an accent should punctuate the
        narration, not interrupt it. If you can hear it as a separate event
        competing for attention, it's too loud.
        """
        src = job.raw.get("sfx", {}).get(name)
        if not src:
            raise SystemExit(f"job.sfx has no entry named {name!r}")
        dur = job.raw.get("sfxDurations", {}).get(
            name, job.get("audio.sfxDurationSeconds", 0.75))
        audio.append({
            "id": f"sfx_{name}_{at:.2f}".replace(".", "_").replace("-", "m"),
            "src": src, "role": "sfx",
            "start": round(max(0.0, at), 3), "offset": 0,
            "duration": dur,
            "gainDb": sfx_gain if gain is None else gain,
            "duck": False, "fadeIn": 0, "fadeOut": 0.12,
        })

    def add_overlay(beat: dict, start: float, end: float, oid: str) -> None:
        payload = {k: v for k, v in beat.items()
                   if k not in ("at", "type", "start", "end", "why", "asset",
                                "sourceStart", "sourceEnd", "sfx")}
        overlays.append({"type": beat["type"], "id": oid,
                         "start": round(start, 3), "end": round(end, 3),
                         "z": beat.get("z", 55), **payload})

    # --- running order --------------------------------------------------------
    # `structure` makes the order explicit — ["clip:0","vo:0","clip:1","vo:1"]
    # opens on the speaker, ["vo:0","clip:0",...] opens on narration. This is the
    # highest-leverage variable in the format: the first short opened on b-roll
    # plus synthetic voice and held 32%, against ~63% for clip-only cuts that
    # opened on a face. Making it a job field rather than a hardcoded sequence is
    # what lets that be tested rather than argued about.
    passages = job.passages
    if not passages:
        raise SystemExit("job.source.passages is empty — nothing to cut")

    structure = job.raw.get("structure")
    if not structure:
        # Legacy default: narration first, alternating.
        structure = []
        for i in range(max(len(vo_paras), len(passages))):
            if i < len(vo_paras):
                structure.append(f"vo:{i}")
            if i < len(passages):
                structure.append(f"clip:{i}")

    vo_broll = job.raw.get("voBroll", {})
    legacy_open = job.raw.get("openBroll", [])
    legacy_close = job.raw.get("closeBroll", [])
    vo_items = [s for s in structure if s.startswith("vo:")]
    tail = round(0.9, 3)  # extra hold on the final segment

    spans: dict[str, tuple[float, float]] = {}
    clip_segs: dict[str, list] = {}

    prev_kind: str | None = None

    for pos, item in enumerate(structure):
        kind, idx_s = item.split(":")
        idx = int(idx_s)
        last = pos == len(structure) - 1
        pad = tail if last else gap

        # A transition marks a change of VOICE. Two clip segments in a row are the
        # same speaker continuing across an internal cut — burning and whooshing
        # there would announce a handoff that isn't happening.
        if prev_kind is not None and kind != prev_kind:
            handoffs.append((round(t, 3), f"to-{kind}"))
        prev_kind = kind

        if kind == "vo":
            if idx >= len(vo_paras):
                raise SystemExit(
                    f"structure references {item} but the script has only "
                    f"{len(vo_paras)} paragraph(s)")
            s, e = place_vo(idx)
            spans[item] = (s, e)

            assets = vo_broll.get(idx_s)
            if assets is None:
                if item == vo_items[0]:
                    assets = legacy_open
                elif item == vo_items[-1]:
                    assets = legacy_close
            if assets:
                fill_broll(s, e + pad, assets, f"vb{idx}_")
            else:
                # No footage for this segment — the canvas, so a graphic can own it.
                clips.append({
                    "id": f"vo{idx}bg", "start": round(s, 3), "end": round(e + pad, 3),
                    "layout": "graphic", "background": canvas, "sources": [],
                    "camera": {"kind": "none", "from": 1, "to": 1,
                               "originX": 0.5, "originY": 0.5},
                    "filters": [], "transitionIn": "cut", "transitionDuration": 0,
                })
        else:
            if idx >= len(passages):
                raise SystemExit(
                    f"structure references {item} but the job has only "
                    f"{len(passages)} passage(s)")
            s, e, segs = place_clip(passages[idx])
            fill_aroll_segments(segs, f"c{idx}_")
            clip_segs[item] = segs
            spans[item] = (s, e)

        # Beats keyed to this segment. "open" means whichever segment is first.
        keys = [f"{kind}{idx}"] + (["open"] if pos == 0 else [])
        for i, b in enumerate([x for x in job.beats if x.get("at") in keys]):
            if "sourceStart" in b and kind == "clip":
                bs = src_to_timeline(b["sourceStart"], clip_segs[item])
                be = src_to_timeline(b["sourceEnd"], clip_segs[item])
                if bs is None or be is None:
                    print(f"  ! beat ({b.get('why', b['type'])}) falls inside a "
                          f"removed pause — skipped")
                    continue
            else:
                bs = s + b.get("start", 0.1)
                be = s + b.get("end", (e + pad) - s)

            if b["type"] == "broll":
                carve(bs, be)
                clips.append(broll_clip(f"nb_{pos}_{i}", bs, be, b["asset"]))
                continue

            add_overlay({**b, "accent": b.get("accent", accent),
                         "tone": b.get("tone", "light")}, bs, be, f"{kind}{idx}_ov{i}")
            if b.get("sfx"):
                # Land the effect a hair before the visual. The eye registers a
                # pop slightly after the ear, so exact alignment reads as late.
                place_sfx(b["sfx"], bs - job.get("audio.sfxLeadSeconds", 0.05))

    v2e = t - gap + tail

    # --- transition burns -----------------------------------------------------
    # Only at VO<->clip handoffs, which are the structural seams of the piece.
    # Firing one at every cut would be exhausting at 0.76 cuts/sec — the device
    # works because it marks a change of *voice*, not a change of shot.
    burn = job.get("overlays.transitionBurn")
    burn_on = job.get("overlays.transitionBurnOn", "all")   # all | to-clip
    whoosh = job.get("overlays.transitionWhoosh")
    whoosh_on = job.get("overlays.transitionWhooshOn", "to-clip")

    if burn or whoosh:
        burn_dur = job.get("overlays.transitionBurnSeconds", 0.55)
        for n, (at, direction) in enumerate(handoffs):
            if burn and burn_on in ("all", direction):
                overlays.append({
                    "type": "film-burn", "id": f"burn{n}",
                    # Envelope peaks at ~28% in, so start early enough that the
                    # peak lands on the cut and the shot changes while blown out.
                    "start": round(max(0.0, at - burn_dur * 0.28), 3),
                    "end": round(at + burn_dur * 0.72, 3),
                    "z": 78,
                    # Alternate the entry side so repeats don't feel mechanical.
                    "originX": 1.02 if n % 2 == 0 else -0.02,
                    "originY": 0.28 + 0.12 * (n % 3),
                    "intensity": job.get("overlays.transitionBurnIntensity", 0.85),
                })
            # A whoosh belongs on the approach INTO the clip — it announces the
            # speaker arriving. Going the other way there's nothing to announce.
            if whoosh and whoosh_on in ("all", direction):
                place_sfx(whoosh, at - job.get("audio.whooshLeadSeconds", 0.22),
                          gain=job.get("audio.whooshGainDb", -9))

    # --- one-shot cues authored on the job ------------------------------------
    for cue in job.raw.get("sfxCues", []):
        place_sfx(cue["name"], cue.get("at", 0.0), gain=cue.get("gainDb"))

    duration = round(v2e, 3)
    clips.sort(key=lambda c: c["start"])

    # Seal slivers left behind when a carved fragment was too short to keep as its
    # own shot. Extending the previous clip is right rather than merely expedient:
    # the alternative is a sub-frame cut nobody can perceive as an edit.
    for prev, nxt in zip(clips, clips[1:]):
        hole = nxt["start"] - prev["end"]
        if 0 < hole < MIN_SHOT:
            prev["end"] = nxt["start"]

    # Any uncovered moment renders as black. Cheap to check, invisible in code,
    # and obvious to a viewer — so it's a hard failure rather than a warning.
    covered = 0.0
    holes: list[tuple[float, float]] = []
    for c in clips:
        if c["start"] > covered + 0.001:
            holes.append((covered, c["start"]))
        covered = max(covered, c["end"])
    if covered < duration - 0.001:
        holes.append((covered, duration))
    if holes:
        detail = ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in holes)
        raise SystemExit(
            f"Clip track has {len(holes)} uncovered gap(s) — these render as "
            f"black frames: {detail}"
        )

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
        # One pacing segment per structural segment, labelled by position so the
        # spec stays readable whatever running order the job chose.
        "pacing": [
            {
                "start": round(spans[item][0], 3),
                "end": round(spans[item][1], 3),
                "energy": 1.0 if item.startswith("clip") else 0.6,
                "label": ("hook" if i == 0
                          else "outro" if i == len(structure) - 1
                          else "payoff" if item.startswith("clip")
                          else "hold"),
            }
            for i, item in enumerate(structure)
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
