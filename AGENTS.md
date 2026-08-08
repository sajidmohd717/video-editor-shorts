# Working on this repo

Orientation for AI agents (and anyone new). Read this first, then
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for reasoning and
[`MODEL_DEV_LOG.md`](MODEL_DEV_LOG.md) for what's already been learned.

> **This file is the only copy. Edit it here.** `CLAUDE.md` is one line —
> `@AGENTS.md` — so Claude Code imports this rather than holding a second copy.
> The two files were separately maintained once and drifted 15 lines apart
> without anyone noticing, including a gotcha list that was missing five entries
> and a "known gap" describing work already finished. If another tool needs its
> own filename (`.github/copilot-instructions.md`, `GEMINI.md`), point it here
> too — never fork the content.

---

## What this is

A pipeline that turns long-form video plus original narration into 1080×1920
shorts. Channel: **The Next Curve** (tech/AI explainers, sources credited).

Two deliverables from every session: the video, **and a better generator**. If you
learn something that generalises, add a finding to `MODEL_DEV_LOG.md`. Findings
are numbered `F1`, `F2`… and cited from code comments.

## Two products, two logs — do not mix them

| | Shorts | Long-form |
|---|---|---|
| Log | `MODEL_DEV_LOG.md` (`F1`…) | `MODEL_DEV_LOG_LONGFORM.md` (`L1`…) |
| Teardowns | `docs/style-analysis/` | `docs/longform/` |
| Decision point | first 1–3s (swipe) | title/thumbnail, then ~30s |
| Cut rate | 0.7–1.5/s | ~0.36/s |
| Loudness | −13 to −14 LUFS | −15 to −16 |
| Assets per video | ~10 | **~300** |

A rule that holds at 45 seconds is often false at 15 minutes. **A short is a
hook; a long-form video is an argument.** Never file a long-form finding as an
`F` number or apply a shorts default to a long-form job without checking it.

---

## The rule that matters most

**Everything compiles to `timeline.json`. The renderer only reads that.**

Before writing code, decide which side of that seam you're on:

- Changing *what the edit is* → a planner (`pipeline/plan_*.py`)
- Changing *what's expressible* → the schema + a React component
- Changing *how it looks* → a component in `src/components/`

Don't reach across. A planner that renders, or a component that decides editorial
timing, breaks the thing that makes this improvable.

**And the second rule:** never put a channel fact or an asset path in a planner.
Channel identity goes in `profiles/`, video specifics go in `job.json`.
Resolution is `default.json` → profile (via `extends`) → `job.profileOverrides`,
with arrays replaced rather than merged. A planner that hardcodes a brand colour
can only ever make one video.

---

## Layout

```
profiles/                   channel identity: brand, captions, pacing, voice
projects/<slug>/job.json    one video: source, rights, passages, assets, beats
src/timeline/schema.ts      THE CONTRACT — read this first, it's commented
src/Short.tsx               root composition: clips → overlays → captions → audio
src/components/             ClipLayer (layouts, camera), Captions
src/components/overlays/    15 overlay types, one file each
src/effects/                filters, grain
pipeline/                   python: tts, transcribe, captions, stock, screenshot, plan_*, master
docs/style-analysis/        reference teardowns — the training data
projects/<slug>/            per-video working files
public/<slug>/              assets (staticFile() only resolves here)
```

---

## Non-negotiables

**Determinism.** Remotion renders frames out of order across workers. Never use
`Math.random()`, `Date.now()`, or anything frame-dependent that isn't derived
from `useCurrentFrame()`. Non-deterministic output flickers. See `Grain.tsx` for
the pattern.

**Times are seconds** in the spec, never frames. The renderer converts.

**Assets go in `public/<slug>/`.** `staticFile()` resolves nowhere else. The
narrated planner copies `vo.wav` there for this reason.

**Rights.** Original narration is the spine; clips are evidence. This is not
style, it's what keeps the channel monetisable — attribution does *not* satisfy
the reused-content test. Don't wire `edge-tts` into anything publishable. Don't
add a TTS or asset source without checking its commercial licence.

**Look at stock before wiring it in.** Half of any search is unusable (F6).
Build a contact sheet, actually look, then pick.

**Content standards are hard constraints (F29).** The channel does not use music,
and no asset may show alcohol or revealing clothing. These belong to the channel
owner — never relitigate them, never trade them against visual impact, never
treat them as gaps to close. Check every candidate at **several timestamps**: a
clip can be clean at 1s and not at 5s, and wine glasses are dressed into a huge
share of dinner and celebration stock. When in doubt, pick a different clip.

---

## Verifying your work

Rendering the whole video to check one thing is slow. Faster:

```bash
npx remotion still src/index.ts Short out/check.png --frame=300 --props=projects/<slug>/timeline.json
```

Then `Read` the PNG. **Look at the output** — several real bugs this session were
invisible in code and obvious in a frame: a highlight that collapsed the text
flow, an arrow bowing the wrong way, a chart reading "0.2 months".

Contact sheet of a finished render:

```bash
ffmpeg -i out.mp4 -vf "fps=1,scale=170:-1,tile=10x5" grid.png
```

Always `npx tsc --noEmit` before rendering — it's seconds versus minutes.

---

## How defects actually get found here

Every real defect in this project so far — camera pumping, audio static, soft
A-roll, repeated b-roll, black frames, off-centre framing — was found by
**watching and listening to the output**. None were found by measurement, and on
one occasion twenty minutes of spectral analysis pointed at three wrong causes
while the answer was a filter-graph bug (F13).

Two habits follow:

1. **Reproduce the failure in the real artifact before simplifying.** Simplified
   test cases repeatedly failed to reproduce bugs — a single-sentence TTS sample
   has no paragraph gaps, so the concat bug never fired.
2. **Prefer an assertion to careful code.** The clip-coverage check (F18) is four
   lines and makes an entire bug class unshippable. The planner will keep growing;
   invariants survive that, care doesn't.

## Gotchas that already cost time

- **`drawtext` doesn't work** here (no fontconfig). Compose labels another way.
- **Absolute positioning breaks inline text flow.** The caption highlight needs a
  gradient background with `boxDecorationBreak: clone`, not an absolute bar.
- **Curved arrows need a perpendicular control point.** Offsetting along an axis
  bends the arc back across the label.
- **PowerShell mangles quotes in commit messages.** Write the message to a file
  and use `git commit -F`.
- **Pixabay video has no orientation param** (its image endpoint does). Everything
  comes back landscape (F7).
- **Never request MP3 from a TTS API.** 128kbps puts audible static under voiced
  speech. PCM only (F12).
- **Word timings lie about pauses.** ASR stretches a word's end across a following
  silence. Use `silencedetect` for anything about audio timing (F16).
- **Reusing one filter input across branches needs `asplit`.** Without it the
  output is corrupted, not merely inefficient (F13).
- **Crop first, scale last** — order of operations, not resolution, is what makes
  A-roll soft (F14).
- **Gain-match source clips to the narration** (F40). They arrive at whatever
  level the room left them at — one sat 15 dB low and still passed
  `blackdetect`, `silencedetect` and a contact sheet. Measure with `loudnorm`
  in print mode, apply a **static** `volume`; never single-pass loudnorm as a
  filter (F13).
- **Transcribe every clip you cut**, from the cut file, and read the last line.
  Two of four cuts this session ended one word early; one of them dropped the
  word carrying the whole quote (F39).
- **Read the chyron as if the narration said it aloud.** It's the biggest text on
  screen and it asserts what the story is about (L13).
- **SEC EDGAR blocks undeclared automated clients.** Use the company's own IR
  page — equally primary, no identity to send.
- **Two clocks in one file is a standing hazard.** Caption cues are in narration
  time; timelines are in video time. Convert once, at the boundary (L12).
- **Never convert seconds→frames with a literal.** Use `useVideoConfig()`; fps is
  a timeline property because one composition serves shorts *and* long-form
  (F41). When any value moves into `meta`, grep for its old literal the same day.
- **CRF isn't the only quality knob.** Frames are JPEG-encoded before x264 sees
  them, and the default quality is 80 regardless of CRF (F42).

---

## Conventions

**Comments explain *why*, not *what*.** The code says what. Reference findings by
number where relevant.

**Commits:** what changed and the reasoning. If a decision was a judgement call,
say what the alternative was and why it lost.

**Don't commit media.** `reference/`, `out/`, `models/`, `public/`, and
`projects/*/render/` are gitignored. The reference videos are third-party
copyrighted footage — analysis only, never committed.

**Tooling isn't sacred.** Every choice in ARCHITECTURE has a stated reason and a
"replace when". If something better appears, check it against the reason and
switch. Update the doc when you do.

---

## Current state

Working end-to-end: ingest → TTS → transcribe → captions → stock/screenshots →
plan → render → master → upload. Four shorts built, 45 findings logged.

**One data point so far.** `yc-sam-01` held **32%** stayed-to-watch against ~63%
for the channel's earlier clip-only cuts. Average view duration was 53%, so the
edit isn't the problem — the opening is. `yc-sam-02` and `yc-sam-03` both open
clip-first to test that, and neither has published numbers yet.

Everything else in `MODEL_DEV_LOG.md` is still reasoning from three reference
teardowns. Cut density, narration share, the no-end-card decision and b-roll
dosage remain untested against an audience. When numbers arrive, record them
against the experiment template — raw views alone are not a verdict.

## The editorial rules that matter most

Mechanics are handled by the engine and its invariants. These are the judgement
calls that decide whether a short works, and all of them came from review:

1. **Read the whole long-form transcript** before cutting (F32). Clip boundaries
   are a suggestion — extend back for the antecedent, forward for the payoff.
2. **Never cut away the sentence that establishes who and what** (F24). Take the
   runtime out of filler instead.
3. **Place a device where the viewer needs it**, a beat after the question forms,
   never before (F35).
4. **Match the visual to the shape of the claim** (F3) and put b-roll on concrete
   nouns, never on reasoning (F10).
5. **A capability is not a reason to use it** (F33).

Known gaps, roughly in priority order:

1. **Graphic placement is authored**, not derived. The mechanical parts are
   automated; choosing which graphic fits which sentence isn't.
2. **No music — a channel constraint, not a gap (F20).** Do not propose a music
   bed or list its absence as unfinished work. The energy music carries comes
   instead from diegetic b-roll ambience, pause cutting, and a dense vocal master.
3. **Article screenshots are built but unused in a real *short*.** The highlight
   box is no longer hand-placed — `pipeline.screenshot --find "<phrase>"` gets
   it from DOM range geometry (F37). First real use is lf-001.
4. **Stock relevance** — half of every search is unusable (F6). A CLIP re-rank
   would cut the manual review.
5. `plan_explainer.py` still hardcodes its asset map; only `plan_narrated.py` has
   been moved onto profiles/jobs.
6. Both planners duplicate helpers; they should share a base.
7. **Six Remotion packages are installed and imported nowhere** (three, r3f,
   transitions, media-utils, shapes). Two are worth adopting rather than
   deleting — see ARCHITECTURE, "Known weak points". `getVideoMetadata` as a
   clip-bounds assertion is the highest-value item on this list: it turns F39's
   class of defect from "found by watching" into "cannot ship".

## Improving from new references

The teardowns in `docs/style-analysis/` are the training data, and adding one is
the main way this system improves. The method that worked:

1. `yt-dlp` the short, then measure before interpreting — cut timestamps via
   `select='gt(scene,0.15)'`, loudness via `ebur128`, and a 1fps contact sheet.
2. **Read the gap distribution, not the average.** Every reference turned out to
   have discrete cutting regimes rather than one tempo (F1).
3. Check the numbers against performance. Ref 002 was a major broadcaster with 9k
   views; its format is the floor, not the target.
4. Write the teardown with a "what to take / what to fix" section, then compile
   the takeable parts into the schema, a component, or a profile default.
