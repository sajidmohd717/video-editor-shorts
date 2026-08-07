# Style Analysis 002 — NBC News, "Man arrested after molotov cocktail thrown at ... Sam Altman's house"

- **Source:** https://www.youtube.com/shorts/psKiVZVOulA
- **Channel:** NBC News · **Uploaded:** 2026-04-10 · **Views:** 9,064 · **Likes:** 154
- **Specs:** 1080×1920, 29.97 fps, 22.5 s
- **Audio:** −21.4 LUFS, **LRA 2.5 LU**

## Read the numbers before you copy the format

NBC News has millions of subscribers. This short did **9,064 views**. Reference 001, from a
single independent creator, did **301,628**. That is a ~33× gap, and the format is most of the
reason: this is a wire story with a voiceover laid over five stock photos. It is *broadcast
repurposing* — cheap to produce, brand-safe, and not built to be watched to the end.

So: build this preset, absolutely. A news channel needs a way to cover a story when no usable
clip exists. But treat it as the **floor**, not the target — and where it's lazy, fix it. The
"hybrid" section at the bottom is the version we should actually ship.

## Structure — the whole thing is five photos

Detected changes: **3 hard changes in 22.5 s (0.13/s)**, at 4.97, 9.94, 14.91 s. Perfectly
even ~5 s intervals. Lowering the detection threshold reveals paired timestamps one frame apart
(9.943/9.977, 10.811/10.844, 18.318/18.352) — those are **cross-dissolve ramps**, not cuts.

| # | Window | Image | Environment |
|---|---|---|---|
| 1 | 0.0 – 5.0 | Altman, suit + tie, press event | deep red/orange background |
| 2 | 5.0 – 9.9 | Altman, blazer, conference stage | pale blue/green |
| 3 | 9.9 – 14.9 | Altman, grey tee, speaking | black background |
| 4 | 14.9 – 18.3 | Altman with mic, seated | white/grey |
| 5 | 18.3 – 22.5 | Altman at TechCrunch Disrupt | white + green branding |

Every image is a **different Altman photo from a different event** — the pool is "whatever the
photo desk has on file." Note that the backgrounds cycle through visibly different colour
environments (red → pale → black → white → green). Whether or not that was deliberate, it's the
one thing keeping five near-identical head-and-shoulders shots from blurring together. **When we
pick stills, sequence them for background contrast.** It's free variety.

- **Hold length:** ~4.5–5 s per image
- **Transition:** ~0.5–1 s cross-dissolve, every time. No hard cuts anywhere.
- **Motion:** slow Ken Burns push on each still, ~1.0 → 1.08 over the hold.

## Persistent chrome

Two elements never leave the screen:

- **"April 10"** — top-left, ~(68, 235), white bold sans, ~44 px. A **dateline**. This is doing
  real work: it tells the viewer at a glance that this is current, which is exactly the anxiety a
  news short has to resolve in the first second.
- **Network bug** — top-right, logo + wordmark, white.

## Headline card (0 – ~6 s)

- Solid **white** box, hard corners, full-bleed-ish (left margin ~68 px, extends to ~930 px)
- Text: very dark navy (≈ `#141E3C`), **bold condensed slab/news serif**, ~54 px, left-aligned,
  3 lines, tight leading (~1.12)
- Sits just above the caption band, i.e. lower-third — *not* centred
- Removed after ~6 s; the rest of the video runs on captions alone

The white-box-with-dark-serif is the visual signature of "this is journalism, not a take." It's
the fastest credibility cue available and it costs one component.

## Captions — broadcast style, not engagement style

Completely different from reference 001, and the contrast is the most useful thing in this teardown:

| | Ref 001 (creator) | Ref 002 (broadcast) |
|---|---|---|
| Size | ~52 px | ~38 px |
| Chunk | 2–4 words | full clause, 2 lines |
| Font | heavy geometric sans | regular-weight sans |
| Background | tight dark pill, high contrast | wide translucent grey band |
| Position | optical centre (y≈0.5) | lower third (y≈0.78) |
| Purpose | **drive attention** | **accessibility / sound-off legibility** |

Broadcast captions are designed to be ignorable. Creator captions are designed to be
unignorable. We want the second one, always — even in the news-update format.

## Audio

−21.4 LUFS with **LRA 2.5** is the fingerprint of a dry, heavily-compressed studio read with
**no music bed at all**. Flat, even, no dynamics. It is professional and it is inert.

For our version: keep the compressed read, but add a low bed. A quiet tension/newsroom pad at
roughly −26 to −24 LUFS under a −16 LUFS VO gives the same authority without the deadness, and
master the sum to −14.

## What to take, what to fix

**Take:**
1. **Persistent dateline** — cheap, and it's the whole "this is news" signal.
2. **White headline card in a news serif** — instant credibility.
3. **Cross-dissolve between stills** — correct for this format; hard cuts on stills look broken.
4. **Sequence stills by background colour** so they don't blend into each other.
5. **Slow Ken Burns on every still** — same as ref 001's punch-in, same reason.

**Fix:**
1. **5 s per image is too long.** 2.5–3.5 s, driven by the sentence structure of the VO, not a
   timer. Each new fact gets a new image.
2. **Use ref 001's captions**, not broadcast subtitles.
3. **Add graphics between the photos** — a map of the location, a quote card, a timeline of
   events, a headline screenshot. Every one of these is more interesting than a sixth portrait,
   and for a story like this the concrete details (where, when, what was said) *are* the content.
4. **Open on the hook, not the headline.** 5 s of a static portrait while the headline is read
   aloud is the most-skipped structure on the platform. Lead with the sharpest fact.
5. **Add a bed and master to −14 LUFS.**

## The hybrid — what we actually ship

`news-update` preset:

```
0.0–1.5   HOOK        one still, hard push-in, big centre caption, dateline appears
1.5–4.0   HEADLINE    white news-serif card slides in over still #2, cross-dissolve
4.0–14.0  BODY        stills + graphics alternating every 2.5–3.5s, cross-dissolves
                      between photos, HARD CUTS into graphics (the change in
                      transition type is itself a signal that something new is happening)
14.0–19.0 DETAIL      map / quote card / timeline — the specifics
19.0–23.0 OUTRO       last still + end card
```

Ref 002's skeleton, ref 001's craft. Cut density lands around 0.35/s — four times slower than
the podcast format, three times faster than NBC.
