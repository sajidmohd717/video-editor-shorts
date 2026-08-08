# video-editor-shorts

A production pipeline for narrated commentary shorts (1080×1920). Built for
**The Next Curve**, but nothing channel-specific lives in the engine.

The goal isn't "a script that makes a video." It's a system that gets measurably
better each time we study a reference video or ship a clip. Reference teardowns in
[`docs/style-analysis/`](docs/style-analysis/) are the training data; the timeline
spec in [`src/timeline/schema.ts`](src/timeline/schema.ts) is what they compile into.

**New here?** Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how it works and
why, then [`MODEL_DEV_LOG.md`](MODEL_DEV_LOG.md) for what we've learned so far.
Working as an AI agent? Start with [`AGENTS.md`](AGENTS.md) — the portable
convention other agents read too. `CLAUDE.md` just imports it, so there is
one source of truth and nothing to keep in sync.

---

## Quickstart

```bash
npm install
pip install -r pipeline/requirements.txt
cp .env.example .env      # then fill in your keys
```

Kokoro (local TTS) needs its weights:

```bash
mkdir -p models && curl -L -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
```

```bash
curl -L -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Verify everything is wired:

```bash
python -m pipeline.stock --check
```

---

## New video checklist

- [ ] **Read the full long-form transcript first** (F32), not just the clip. The
      supplied clip boundaries are a suggestion — extend back for the antecedent,
      forward for the payoff, cut the middle if it drags.

Nineteen findings are already baked into the defaults, so the mechanical parts
are handled. These are the steps that still need a human, in order:

- [ ] **Extract A-roll by cropping the highest-resolution source — never downscale
      first** (F14). A 9:16 crop keeps 32% of a 16:9 frame's width, so the source
      needs ~3.2× the target width. From 2160p that's a downscale; from 1080p it's
      a 1.78× upscale and visibly soft.
- [ ] **Measure where the subject actually is** (F19). Extract a gridded still and
      look; don't inherit a framing number. Set `source.subjectFocusX`, offset
      *toward* the direction they face so there's looking room.
- [ ] **Decide the crop per passage** (F33). Wide two-shots, stages and diagrams
      want `fit`, not a 9:16 crop that frames the table. Set `passageLayouts`.
- [ ] **Read the clip's ASR output for mishearings** (F34) and add
      `captionCorrections`. Clip captions have no script to check against.
- [ ] **Write the script.** Blank lines separate VO segments. Use an em dash, not
      a full stop, where you want a short connective pause.
- [ ] **Listen to `vo-qc+10dB.m4a`** after TTS — the actual narration, not a test
      sentence (F13). Regenerate if there's a noise floor.
- [ ] **Look at stock before wiring it in** (F6). Roughly half of any search is
      unusable. Build a contact sheet. Budget ~10 distinct clips per 45s; never
      reuse one (F15).
- [ ] **Check every candidate against the content standards** (F29) — no alcohol,
      no revealing clothing. Sample **several timestamps per clip**, not one
      thumbnail; both assets that slipped through passed a single-frame glance.
- [ ] **Choose graphics by the shape of the claim, not its topic** (F3). A jump is
      a `comparison`, a trend is a `stat-chart`, a sourced fact is an
      `article-clip`.
- [ ] **Check the cut still makes sense cold** (F24). Find the sentence that
      establishes *who* and *what* — it's load-bearing and can never be cut. Take
      the runtime out of filler, asides and restarts instead. Read the opening as
      if you know nothing: does a pronoun appear before its antecedent?
- [ ] **Introduce anyone the audience may not know** (F26) — portrait badge, name,
      and a short role line in the accent colour. Fire it **on the spoken name**,
      not before: a badge answers a question the viewer is forming (F35).
- [ ] **For every overlay, ask what question it answers** (F35) and whether the
      viewer is asking it yet. A capability is not a reason to use it.
- [ ] **No more than ~8–10s of unbroken talking head** (F27). An unbroken face is
      a static frame, and a static frame is a swipe.
- [ ] **Watch the render.** Every real defect so far was found by watching, not by
      measuring.

The planner hard-fails on uncovered timeline (F18) and warns if narration share
drops below the profile floor, so those two can't ship silently.

## Making a video

Each video is a **project** — a slug with its own directory. Assets live under
`public/<slug>/` because Remotion's `staticFile()` only resolves there.

```
projects/<slug>/           script.md, vo.wav, words.json, captions.json, timeline.json, render/
public/<slug>/             aroll.mp4, stock/, articles/, vo.wav
```

### 1. Prepare the source clip

Extract your passage from the long-form source at full resolution. Keep it
**landscape** — the renderer crops to 9:16 per-shot, which is how one continuous
take becomes many distinct-looking shots.

```bash
ffmpeg -ss 71.92 -i source.webm -t 40.64 -vf scale=1920:-2 -c:v libx264 -crf 19 public/<slug>/aroll.mp4
```

### 2. Write the narration

`projects/<slug>/script.md`. Blank lines separate paragraphs; each paragraph
becomes one VO segment. Lines starting with `#`, `>` or `//` are notes and are
stripped before synthesis.

### 3. Generate the voice

```bash
python -m pipeline.tts <slug> --engine elevenlabs --voice <voice-id>
```

Engines: `kokoro` (default, local, free, Apache-2.0), `elevenlabs` (best prosody,
needs a paid plan for commercial use), `edge` (**drafts only** — unlicensed).

```bash
python -m pipeline.tts --list-voices
```

Audition without overwriting your current track with `--out vo-test.wav`.

### 4. Transcribe and build captions

```bash
python -m pipeline.transcribe <slug>
```

```bash
python -m pipeline.captions <slug>
```

Transcription runs over the **generated audio**, not the script — that's what
gives timings matching actual delivery. Captions then take their *wording* from
the script and only their *timing* from Whisper. See ARCHITECTURE for why.

### 5. Gather assets

```bash
python -m pipeline.stock <slug> --kind video --count 3 --query "server room" --query "typing code"
```

```bash
python -m pipeline.screenshot <slug> --url "https://..." --name codex-launch
```

**Look at what comes back before wiring it in.** Roughly half of any stock search
is unusable — see MODEL_DEV_LOG for how badly.

### 6. Plan, render, master

```bash
python -m pipeline.plan_narrated <slug>
```

```bash
npx remotion render src/index.ts Short "projects/<slug>/render/out.mp4" --props=projects/<slug>/timeline.json
```

```bash
python -m pipeline.master <slug> --input render/out.mp4 --target -13
```

Preview interactively instead of re-rendering:

```bash
npm run studio
```

---

## The three formats

All use the same renderer. They differ only in the timeline fed to it.

| | `Explainer` | `Narrated` ⭐ | `NewsUpdate` |
|---|---|---|---|
| Use when | you have a clip and want maximum density | **default** — clip + your commentary | no clip exists |
| Cuts/sec | ~1.5 | ~0.7 | ~0.35 |
| Spine | clip | **your narration** | stills + narration |
| Master | −13 LUFS | −13 LUFS | −14 LUFS |
| Reuse-policy risk | high | **low** | low |
| Planner | `plan_explainer.py` | `plan_narrated.py` | (timeline by hand) |

`plan_narrated` is the one to use. Original narration as the spine with the clip
as evidence is what makes the format defensible — see ARCHITECTURE, "Rights".

---

## Tuning

Most of what you'd want to change is one number.

| Want | Where |
|---|---|
| Faster/slower cutting | `shot=` in `fill_broll`, `/ 1.1` in `fill_aroll` |
| More/less b-roll | the `for src_a, src_b, asset` loop in `plan_narrated.py` |
| Different clip passages | `CLIP_A` / `CLIP_B` |
| Caption size, position, style | `captions.style` in the timeline, or `Captions.tsx` |
| Words per caption card | `len(buf) >= 2` in the planner |
| Louder/quieter master | `--target` on `pipeline.master` |
| Voice liveliness | `stability` in `tts.py` (lower = more expressive) |
| Brand bug, end card | `chrome` and `end-card` overlays |

Or edit `timeline.json` directly and re-render. It's plain JSON and the renderer
is the only thing that reads it.
