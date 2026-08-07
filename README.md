# video-editor-shorts

An automated production pipeline for AI-narrated commentary shorts (1080×1920, 30fps).

The goal is not "a script that makes a video." It is a **system that gets better every time we
feed it a reference video** — the style analyses in `docs/style-analysis/` are the training
data, and the timeline spec in `src/timeline/schema.ts` is the model those analyses compile into.

---

## Architecture

```
  ┌── SOURCE CLIPS ──┐        ┌── SCRIPT ──┐
  │  yt-dlp          │        │  you / LLM │
  └────────┬─────────┘        └──────┬─────┘
           │                         │
           │                    ElevenLabs TTS
           │                         │
           │                    vo.wav (the spine)
           │                         │
           ▼                         ▼
      ┌─────────────────────────────────────┐
      │  WhisperX  — word-level alignment    │
      │  · transcribe source clips (search)  │
      │  · transcribe the VO (caption sync)  │
      └──────────────────┬───────────────────┘
                         │
                         ▼
      ┌─────────────────────────────────────┐
      │  PLANNER  →  timeline.json           │
      │  pacing · clips · overlays · captions│
      └──────────────────┬───────────────────┘
                         │
                         ▼
      ┌─────────────────────────────────────┐
      │  RENDER  — Remotion (React+WebGL)    │
      └──────────────────┬───────────────────┘
                         │
                         ▼
      ffmpeg master → −14 LUFS → short.mp4
```

### The key trick: caption the VO, not the script

Do **not** try to time captions from the written script. Generate the ElevenLabs audio first,
then run WhisperX over that generated audio. You get word-level timings that match the actual
delivered speech to within ~50 ms, including the TTS engine's own pauses and pacing quirks.
This is the difference between captions that feel machine-made and captions that feel edited.

### The timeline spec is the whole design

Everything upstream produces a `timeline.json`; the renderer only ever consumes one. That
separation is what makes this improvable:

- Want a new effect? Add an overlay variant to the schema + a React component. Every future
  video can use it.
- Want smarter editing? Improve the planner. The renderer doesn't change.
- Want to hand-fix one video? Edit its JSON directly and re-render.
- Want to reuse a style? Copy a timeline, swap the assets.

---

## Tooling choices, and why

| Job | Choice | Why not the alternative |
|---|---|---|
| Download | **yt-dlp** | Nothing else is close. |
| Transcribe | **WhisperX** (faster-whisper + wav2vec2 forced alignment) | Plain Whisper gives segment timings that drift; WhisperX gives word timings that don't. Runs int8 on CPU — this machine's AMD 860M has no CUDA, so GPU Whisper isn't on the table anyway. |
| TTS | **ElevenLabs** | Best-in-class prosody, and the v3 models take emotional direction. Local fallback (Kokoro/Piper) is worth wiring as a cost escape hatch. |
| Render | **Remotion** | See below. |
| Master | **ffmpeg** `loudnorm` | Two-pass to −14 LUFS, sidechain-duck music under VO. |

### On Remotion and "I don't want simple edits"

Remotion renders React in a real browser, frame by frame. That means the ceiling is *the
browser's* ceiling, not a template engine's:

- **WebGL/GLSL** via `@remotion/three` — real 3D, custom shaders, displacement, particles
- **CSS 3D transforms, filters, masks, blend modes** — free, fast, deterministic
- **SVG filter chains** — turbulence, morphology, custom glitch
- **Canvas 2D** for anything procedural
- Lottie and Rive both drop in if we want designer-authored motion

The thing Remotion is genuinely bad at is being fast: it's CPU-bound, and heavy shader work on
a 49 s vertical video will take minutes, not seconds. That's an acceptable trade for a batch
pipeline. The realistic risk isn't the tool's ceiling, it's us writing boring components — so
the effects library is where the ongoing work goes.

**Licensing:** Remotion is free for individuals and companies of ≤3 people. A solo monetised
YouTube channel is fine. If this ever becomes a company with 4+ people, it needs a paid licence.

---

## Layout

```
docs/style-analysis/   reference video teardowns — the training data
pipeline/              python: ingest, transcribe, tts, master
src/
  timeline/schema.ts   the contract
  components/          captions, layouts, overlays
  effects/             shaders + filter treatments
projects/<slug>/       per-video working dir (assets, timeline.json, render)
reference/             downloaded reference videos + frame analysis
```

## The two formats

Both are driven by the same renderer; they differ only in the timeline fed to it.

| | `Short` (ref 001) | `NewsUpdate` (ref 002 hybrid) |
|---|---|---|
| Use when | a usable clip exists | no clip exists, or the story is the story |
| Cut density | 1.0/s, barrage-and-hold | ~0.35/s |
| Spine | clips + AI narration | stills + AI narration |
| Transitions | hard cuts | dissolve between stills, hard cut into graphics |
| Captions | centre, 2–4 words, pill | lower third, same pill style |
| Chrome | none | persistent dateline + channel bug |

Preview both: `npm run studio`

## Status

- [x] Environment verified (node 24, python 3.11, ffmpeg 8.1, yt-dlp)
- [x] Reference 001 analysed (creator / fast-cut clip commentary)
- [x] Reference 002 analysed (broadcast / slow stills + narration)
- [x] Timeline schema v1
- [x] Renderer: layouts, camera moves, dissolves, captions (5 presets), 9 overlay types
- [x] Both format presets rendering
- [ ] WhisperX pipeline
- [ ] ElevenLabs TTS module (+ local fallback)
- [ ] Planner (script → timeline.json)
- [ ] Audio master (−14 LUFS, music ducking)
- [ ] Asset sourcing (stills, b-roll, generated imagery)
