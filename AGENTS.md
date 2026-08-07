# Working on this repo

Orientation for AI agents (and anyone new). Read this first, then
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for reasoning and
[`MODEL_DEV_LOG.md`](MODEL_DEV_LOG.md) for what's already been learned.

---

## What this is

A pipeline that turns long-form video plus original narration into 1080×1920
shorts. Channel: **The Next Curve** (tech/AI explainers, sources credited).

Two deliverables from every session: the video, **and a better generator**. If you
learn something that generalises, add a finding to `MODEL_DEV_LOG.md`. Findings
are numbered `F1`, `F2`… and cited from code comments.

---

## The rule that matters most

**Everything compiles to `timeline.json`. The renderer only reads that.**

Before writing code, decide which side of that seam you're on:

- Changing *what the edit is* → a planner (`pipeline/plan_*.py`)
- Changing *what's expressible* → the schema + a React component
- Changing *how it looks* → a component in `src/components/`

Don't reach across. A planner that renders, or a component that decides editorial
timing, breaks the thing that makes this improvable.

---

## Layout

```
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
plan → render → master. One video shipped (`yc-sam-01`).

Known gaps, roughly in priority order:

1. **Per-project asset maps are hardcoded** in the planners. Fine for one video,
   wrong for a channel. The job/profile infrastructure in the sibling
   `shorts-generator` repo is the intended fix and hasn't been ported.
2. **Graphic placement is authored**, not derived. The mechanical parts are
   automated; choosing which graphic fits which sentence isn't.
3. **No music bed.** Needs a licensed source.
4. **Stock relevance** — a CLIP re-rank would cut the manual review.
5. `plan_explainer.py` and `plan_narrated.py` share helpers by import; they
   should probably share a common base.
