# Architecture

How the system works, and — more usefully — *why* each part is the way it is.
Every decision here was made for a reason that's written down. If a reason stops
being true, change the decision.

---

## The one idea

**Everything compiles to a `timeline.json`. The renderer only ever reads one.**

```
reference teardowns ─┐
scripts, clips, assets ├─→ PLANNER ─→ timeline.json ─→ RENDERER ─→ mp4 ─→ MASTER
research, judgement ─┘
```

That single seam is what makes the system improvable instead of a pile of
one-off edits:

- New visual effect? Add an overlay type to the schema plus a React component.
  Every future video can use it.
- Smarter editing? Improve the planner. The renderer doesn't change.
- Need to hand-fix one video? Edit its JSON and re-render.
- New format? A new planner emitting the same schema. Not a new renderer.

The schema lives in [`src/timeline/schema.ts`](../src/timeline/schema.ts) and is
the contract. Read it first — it's commented and it's the densest description of
what the system can express.

All times in the spec are **seconds**, never frames, so changing fps never
invalidates a timeline.

---

## Pipeline stages

```
script.md ──tts──→ vo.wav ──transcribe──→ vo.words.json ──captions──→ captions.json
                                                                          │
source clip ──ffmpeg──→ aroll.mp4                                        │
stock APIs ──stock──→ public/<slug>/stock/                               │
article URLs ──screenshot──→ public/<slug>/articles/                     │
                                    │                                     │
                                    └──────────→ PLANNER ←───────────────┘
                                                    │
                                            timeline.json
                                                    │
                                            Remotion render
                                                    │
                                            ffmpeg loudnorm
```

| Stage | Module | Does |
|---|---|---|
| Narration | `pipeline/tts.py` | script → speech (Kokoro / ElevenLabs / Edge) |
| Timing | `pipeline/transcribe.py` | speech → word timings (faster-whisper) |
| Captions | `pipeline/captions.py` | script wording + Whisper timing → cues |
| Footage | `pipeline/stock.py` | Pexels + Pixabay search, download, normalise |
| Evidence | `pipeline/screenshot.py` | article URL → headline screenshot |
| Edit | `pipeline/plan_narrated.py` | everything above → timeline.json |
| Render | `src/` (Remotion) | timeline.json → mp4 |
| Master | `pipeline/master.py` | two-pass loudnorm + limiter |

---

## Decisions, and the reasoning behind them

### Transcribe the generated audio, not the script

The script says what was *meant*. Only the audio knows when each word actually
lands, including the TTS engine's pauses and pacing quirks. Captions timed from
the audio are the difference between "machine-made" and "edited".

### …but the script is the wording authority

Whisper transcribes what it *hears*. On the first real run it turned
"productivity gain" into "productivity game". It'll do worse on model names and
company names, which is most of a tech channel's vocabulary — and every
mishearing would ship as an on-screen typo.

So `captions.py` aligns the two with `difflib`: matching spans take Whisper's
timings directly; on disagreement the script's words win and timings are
interpolated across the disputed interval. A caption 40ms off is invisible. A
misspelled one is not.

Paragraph spans are derived the same way, which is why swapping voice or engine
re-times the whole edit automatically instead of needing hand-editing.

### Narration and clip take turns; they don't overlap

The obvious design is to duck the speaker under the voiceover. Interleaving is
better: two people talking at once is harder to follow, and a clean handoff makes
"these are two distinct voices" unmistakable — which is the entire point when the
reuse policy is the thing you're managing.

Consequence: captions must never straddle a speaker change. Every word carries a
`voice` tag and cards break on change. Without it you get cards like
"coding Three" that read as a glitch rather than as either speaker.

### One landscape source becomes many shots

The renderer crops to 9:16 using `objectPosition`, per clip. Varying the crop
focus and punch turns one continuous take into distinct-looking setups — that's
how a clip with *zero* cuts in it yields 30+ shots at full quality.

`objectPosition` rather than a transform, so the crop is independent of the
camera move and a punch-in can't drag framing off the subject.

### Cut density is three regimes, not one number

From the GrowthX teardown: the gaps between cuts cluster into **strobe**
(1 frame, fired in runs of 3–6, percussive not editorial), **rapid montage**
(4 frames, sustained, while the VO lists things), and **normal** (0.4–2.8s).
The average hides this. Planners model it explicitly.

Equally: density should alternate barrage and hold. Uniform cutting reads as
noise. Ref 001 spikes to 1.7/s on hooks and drops to 0.1/s where the actual
argument is made.

### The visual must match the shape of the claim

Not just its topic. A line chart asserts a *trend*; a comparison asserts a
*jump*. Building "three months became seven minutes" as a chart produced a
counter reading "0.2 months" — technically working, editorially nonsense. Hence
the separate `comparison` component.

| Claim | Component |
|---|---|
| a number moved over time | `stat-chart` |
| a jump between two states | `comparison` |
| a fact someone reported | `article-clip` |
| a company / product | stock footage |
| a person | their face, punched in |
| a mechanism | `annotation` on a light canvas |

### B-roll goes on concrete nouns only

Never on the reasoning. When someone is making an argument their face carries it,
and cutting away mid-point weakens the claim. Target ~20% cutaway.

### Rights

Two separate systems, often confused:

1. **YPP reused-content policy** — asks whether *you* added something
   substantial. Captions and cutaways over someone else's footage is close to
   the textbook failing example. Original narration as the spine is the fix.
   **Attribution does not satisfy this test.**
2. **Content ID / copyright** — the rights holder can claim regardless of YPP
   status. No amount of narration changes this.

Stock assets: Pexels and Pixabay both permit monetised commercial use without
attribution. The stock manifest still records provider, creator and source URL
per asset, so a credit list can be *generated* rather than reconstructed later.

TTS licensing: Kokoro is Apache-2.0 (clear). ElevenLabs free tier is
non-commercial — a paid plan is required, and audio should be **regenerated**
after upgrading. `edge-tts` calls an undocumented Microsoft endpoint not
published as a commercial API; it warns on use and is drafts-only.

### Audio targets

Measured from the references: ref 001 −19.8 LUFS, ref 002 −21.4, ref 003 −9.2
(LRA 1.4 — brickwalled). YouTube normalises to about −14 on playback, so going
hotter buys perceived *density*, not volume. The point of ref 003's master is
that nothing ever gets quiet, so attention has no gap to escape through.

We target **−13**, two-pass loudnorm plus a limiter. Past about −11 it just
sounds crushed.

### The render has two lossy steps, not one

Remotion captures each frame as an image, then hands the sequence to x264. So
`crf` only governs the *second* compression. `videoImageFormat: "jpeg"` sets the
first, and its default quality is 80 — which caps output quality no matter how
low the CRF goes (F42). We set `jpegQuality: 95`.

PNG frames would remove the first step entirely, but render time is already the
stated replace-when for Remotion, and the difference isn't visible at this
bitrate. Revisit if graphics-heavy long-form starts showing banding.

### fps and canvas belong to the timeline, not the components

`meta.fps`, `meta.width` and `meta.height` are read in `calculateMetadata`, which
is what lets **one composition serve both 9:16 shorts and 16:9 long-form**. That
only holds if no component hardcodes them. Two rounds of this have now been
found and fixed — components assuming a portrait canvas (L11) and a clip layer
assuming 30fps (F41) — so treat it as a standing audit, not a solved problem:
any seconds→frames conversion outside `Short.tsx` goes through
`useVideoConfig()`.

---

## Tool choices — and when to replace them

Nothing here is sacred. Each was chosen for a stated reason; if a better option
appears, the reason is what you check it against.

| Job | Current | Why | Replace when |
|---|---|---|---|
| Download | yt-dlp | nothing close | — |
| Transcribe | faster-whisper (int8, CPU) | WhisperX needs ~2.5GB of torch for forced alignment, and this machine has no CUDA. Clean TTS audio doesn't need it. | captioning noisy source audio, or a GPU appears |
| TTS | Kokoro / ElevenLabs | licence clarity / prosody | a better open model with a clear licence |
| Stock | Pexels + Pixabay | free, commercial-safe, no attribution required | need better hit rate — both match tags, not meaning |
| Screenshots | Playwright | real pages, scriptable | — |
| Render | Remotion | React in a real browser: WebGL, GLSL, SVG filters, Canvas. Ceiling is the browser's, not a template engine's. | need faster batch render — it's CPU-bound |
| Master | ffmpeg loudnorm | two-pass is accurate | — |

**Remotion licensing:** free for individuals and companies of ≤3 people. A solo
monetised channel is fine.

### Known weak points

- **Stock search quality.** About half of any query is unusable. Always eyeball
  before wiring. A CLIP-based relevance re-rank would help.
- **Graphic placement is authored**, not automated. The mechanical parts (shot
  subdivision, caption chunking, framing rotation, strobe placement) are
  automated; choosing *which* graphic fits *which* sentence isn't.
- **Asset maps are hardcoded in `plan_explainer.py`.** `plan_narrated.py` has
  been moved onto profiles/jobs; the explainer planner hasn't. Both also
  duplicate helpers that should live in a shared base.
- **Unused render dependencies.** `@remotion/three`, `three`,
  `@react-three/fiber`, `@remotion/transitions`, `@remotion/media-utils` and
  `@remotion/shapes` are installed and imported nowhere. Two are worth adopting
  rather than dropping: `getVideoMetadata` would let `calculateMetadata` assert
  that every clip's `offset + duration` fits inside its source — the same
  four-line assertion shape as the coverage check (F18), against the class of
  defect F39 found by hand. `<TransitionSeries>` would move cross-dissolve
  overlap out of the planner, where it currently leaks across the planner/
  renderer seam.

Note: **no music bed is not a weak point.** It's a channel constraint (F20, F29)
and it is not to be relitigated here.
