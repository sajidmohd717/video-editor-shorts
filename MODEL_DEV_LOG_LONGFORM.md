# Long-form Development Log

**Separate from `MODEL_DEV_LOG.md` on purpose.** Shorts and long-form are
different products for different viewers, and mixing their findings would
corrupt both — a rule that's true at 45 seconds is often false at 15 minutes.

Findings here are numbered **L1, L2…** so they can never be confused with the
shorts findings (F1, F2…).

Teardowns live in [`docs/longform/`](docs/longform/).

---

## What actually differs from shorts

Worth stating explicitly, because the temptation is to reuse everything:

| | Shorts | Long-form |
|---|---|---|
| Decision point | first 1–3s (swipe) | title + thumbnail, then ~30s |
| Traffic | ~92% algorithmic feed | search, suggested, subscribers |
| Cut rate | 0.7–1.5/s | ~0.36/s |
| Loudness | −13 to −14 LUFS | −15 to −16 |
| Assets per video | ~10 | **~300** |
| Structure | one idea | chaptered argument |
| Failure mode | swiped in 2s | closed at 3 minutes |

The single biggest difference: **a short is a hook, a long-form video is an
argument.** Retention in shorts is won by density; in long-form it's won by the
viewer wanting to know how it ends.

---

## Findings

### L1 — Archival montage is a viable format with zero original footage

L001 contains not one frame shot by its creator. Broadcast clips, press
conferences, testimony, document screenshots, tweets, charts. The creator's
contribution is narration, research, sequencing and design.

**149 subscribers, 5,240 views** — a ~35× view-to-subscriber ratio, so the
performance is coming from the video rather than an existing audience.

This is also the same rights posture we already run for shorts: original
narration is the spine, third-party material is evidence.

**Status:** adopt as the base long-form format.

### L2 — Bursts and holds, at long-form scale

316 cuts over 877s averages one every 2.8s, but **35% of gaps are sub-second**
and 2% run past 12s. Rapid montage bursts, evidence shots at 3–6s, and a handful
of long holds where the argument is being made.

Same principle as shorts (F1/F2): the average is meaningless, the distribution is
the technique. Long holds are not laziness — they're where you stop cutting so
the viewer can think.

### L3 — Sourcing is the whole cost

15 minutes at 0.36 cuts/s needs **~300 distinct visuals** — 30× a short. The edit
is not the bottleneck; finding, clearing and organising 300 assets is.

**Implication:** long-form needs asset tooling that shorts didn't — bulk
acquisition, a searchable library, reuse tracking across an episode, and probably
relaxing the strict no-repeat rule (F15) that works fine at 10 assets.

### L4 — Chapters are structure, not metadata

L001's seven chapter titles read as a thesis progression, not a topic list.
They're also a retention aid: a viewer who can see where they are is likelier to
stay, and chapters make drop-off measurable per section.

**Applied:** long-form jobs should define chapters as part of the argument, and
the analytics review should read retention per chapter.

### L5 — Devices that carry an argument

From L001, worth building:

- **Date cards** — plain serif date on black. Marks a chronology and resets
  attention between segments. Cheap, high value.
- **Pull-quote cards** — one sentence, white serif on black, held. The change of
  register makes the video feel like it's underlining something.
- **News chyrons as evidence** — a broadcaster's own lower-third as proof.
  Long-form equivalent of the shorts `article-clip`.
- **Stylised portrait motif** — one treatment (halftone/engraved) reserved for
  the thesis figure, separating "the idea" from "the news".

---

## Open questions

1. **What carries pacing without music?** The channel doesn't use music (F20).
   Over 15 minutes there is far more silence to fill than in a 45-second short.
   This is the biggest unknown and should be the focus of L002.
2. Is the sub-second burst rate this creator's signature or general to the
   format? Needs more teardowns.
3. Narration-to-evidence ratio for long-form. Shorts settled near 35–40%.
4. Does the shorts no-repeat rule (F15) survive at 300 assets, or does a
   deliberate visual motif become an asset instead?

---

## On making versions of studied videos

Topics are not ownable and a video on the same subject is entirely legitimate.
**Scripts are.** Any video we make on a studied topic must come from our own
research and our own argument, built from primary sources.

Beyond being right, it's the only thing that works: in this format the entire
value is the thinking, and borrowed thinking has no edge over the original.

**Take the technique. Write the argument ourselves.**

---

## Experiment template

```markdown
### YYYY-MM-DD — experiment name

- Video / chapter:
- Hypothesis:
- Changed variable:
- Control:
- Retention evidence (overall + per chapter):
- Decision: keep / revert / inconclusive
```

Long-form retention is read **per chapter**, not just as an average — that's the
main analytical advantage the format has over shorts.
