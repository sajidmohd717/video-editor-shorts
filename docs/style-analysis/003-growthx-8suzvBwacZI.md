# Style Analysis 003 — GrowthX, "OpenAI Is Broke… So Sam Altman Did THIS"

- **Source:** https://www.youtube.com/shorts/8suzvBwacZI
- **Channel:** GrowthX (693k subs) · **Uploaded:** 2025-10-14
- **Performance:** 697,500 views · 15,510 likes (**2.2%**) · 360 comments
- **Specs:** 1080×1920, **23.976 fps**, 51.4 s
- **Audio:** **−9.2 LUFS**, **LRA 1.4 LU**

This is the best of the three references and the one to build the flagship preset around.
It is also the most *manufactured* — almost nothing here is found footage used as-is.

## Headline numbers

**77 cuts in 51.4 s = 1.50/s.** But as with ref 001, the average hides the mechanism. Sorting
the 76 inter-cut gaps reveals **three discrete cutting regimes**, not a continuum:

| Regime | Gap | Frames @24fps | Count | Use |
|---|---|---|---|---|
| **Strobe** | 0.04 s | **1 frame** | 23 | Single-frame flash inserts, fired in runs of 3–6 |
| **Rapid montage** | 0.08–0.17 s | 2–4 frames | 14 | Sustained bursts — 7 consecutive 4-frame shots at 14.3–15.5 s |
| **Normal** | 0.4–2.8 s | 10–68 frames | 39 | Everything else |

The strobe runs are the signature. At 23.4 s there are **six cuts one frame apart** — a
6-frame stutter burst. At 38.4 s, five. At 4.3 s, three. These aren't cuts in any editorial
sense; they're **percussive accents**, cut to the music, that fire on a stressed word. The
viewer doesn't read them as images at all — they read as an impact.

The 14.3–15.5 s block is different: seven distinct shots at exactly 4-frame intervals, each one
legible. That's a **list being delivered visually** while the VO lists it.

## Audio — the most aggressive number in the whole study

**−9.2 LUFS with LRA 1.4.**

For comparison: ref 001 was −19.8/6.0, ref 002 was −21.4/2.5. This is **10 dB hotter than
ref 001** with almost no dynamic range left. Music bed and VO are compressed and limited into
a single brick. YouTube will normalise it down to ~−14 on playback, so the loudness itself
isn't the point — the point is that **nothing ever gets quiet**, so there's no auditory gap for
attention to escape through. Combined with 1.5 cuts/sec, neither eye nor ear ever gets a rest.

Practical target for us: VO ~−16 LUFS, music bed ~−22, bus compression + limiter, master to
−11 to −13. Hotter than broadcast, not quite this brutal.

## Shot vocabulary — what the user asked about

Roughly 8 categories, and **the mix is the format**:

1. **Talking-head source clips** — Altman, Trump, Jensen Huang, Lisa Su. Podcast, keynote,
   press. Always muted, always punched in.
2. **News article screenshots with animated highlight** — real FT/Reuters/TechCrunch pages,
   with a dark bar sweeping across the key phrase as the VO says it. Used ~6 times. This is
   the *evidence* layer and it's the single most-repeated device.
3. **Product macro / brand footage** — GPU dies, server racks, NVIDIA signage, AMD chip renders.
   Pure texture. Fills space between facts.
4. **Screen recordings** — the ChatGPT model picker (a real list of model names), a trading
   terminal. Shows rather than tells.
5. **Custom motion graphics on a light-grey "explainer canvas"** — animated area chart with a
   value counter ticking 7% → 10%, product render with a curved arrow annotation. This is where
   the production budget went and it's what separates this from a clip compilation.
6. **A recurring visual gag** — the same shot of Altman in white sunglasses at a press scrum
   returns 3+ times. A running joke gives the video an internal reference the viewer can feel
   smart about catching.
7. **Establishing/atmosphere** — city skyline, conference stage wide.
8. **In-video SUBSCRIBE pill** — appears mid-roll around 19–21 s and again at 47–50 s. Not just
   an end card; a repeated mid-video CTA.

**The rule this implies:** every single sentence of the VO gets its own visual, and the visual
is chosen by *what kind of claim it is*. A number → chart. A quote/fact → article screenshot.
A company → product footage. A person → their face. Nothing is generic b-roll.

## Cold open (0 – 5 s) — typographic hook stack

Four full-screen word cards over b-roll, each held ~1 s, each in a **different typeface**:

```
"OpenAI"          light/serif, white
"enough"          orange-red, heavier
"power."          bold white sans
"Let me explain." light serif, on a grey canvas
```

The deliberate typeface mismatch is the effect. It reads as urgent and assembled, not as a
title card. And "Let me explain." is a **direct-address promise** — it names a payoff and buys
the next 45 seconds.

## Captions

Different from both earlier references and, on this evidence, the best of the three:

- **Heavy geometric sans** (Poppins/Montserrat ExtraBold family), white
- **Thick black stroke (~8 px) + soft drop shadow. No pill background.** The stroke does the
  legibility work the pill did in ref 001, without boxing off part of the frame
- ~62 px, **1–2 words per card** — faster than ref 001's 2–4
- Position ≈ y 0.68 (lower-middle, above the caption-safe zone)
- Swapped on the word, so the text changes even when the shot doesn't

At 1.5 cuts/sec plus word-rate captions, something on screen changes roughly **3× per second**.

## Persistent branding

Channel bug top-right on every frame: wordmark in white on a translucent dark rounded pill,
with one letter in brand blue. Never moves, never fades. Cheap, and it means every frame is
attributable when the video gets clipped and reposted.

## Notable individual techniques

- **Reveal wipe on product renders** — the AMD chip is desaturated and wipes to full colour
  left-to-right as the arrow lands.
- **Curved hand-drawn arrow** in brand blue, pointing from a display-serif label to the subject.
  Used at least twice. Reads as annotation, like someone marking up a slide.
- **Display serif with a metallic/gradient fill** for graphic labels ("10% of AMD") — high-
  contrast Didone-ish serif, sharply different from the sans captions. Two-font system,
  same idea as ref 001's serif/sans contrast.
- **Highlight sweep** on article text, timed to the VO reaching that phrase.
- **23.976 fps** rather than 30 — subtly more motion blur per frame, slightly filmic. Probably
  inherited from source footage rather than chosen, but it doesn't hurt.

## The preset: `explainer`

```
0.0–5.0    HOOK          4 word-cards, different faces, ~1s each, b-roll under
5.0–12.0   PROBLEM       talking head + article screenshot w/ highlight. strobe on the number
12.0–16.0  RAPID LIST    7 shots at 4-frame intervals while VO lists items
16.0–21.0  PIVOT         "but then..." — product footage, SUBSCRIBE pill appears
21.0–40.0  MECHANISM     alternating: fact→article, number→chart, company→product
                         strobe bursts on stressed words
40.0–48.0  PAYOFF        explainer canvas: annotated graphic, the "aha"
48.0–51.4  KICKER        callback to the running gag + SUBSCRIBE
```

Cut density ~1.5/s. Something changes ~3×/s. Master to −12 LUFS.

## Where this format is strongest — and its one real risk

It is genuinely well-suited to **compressing long-form into short-form**, which is what makes it
attractive: a 90-minute podcast plus three news articles collapses into 51 seconds because the
narration carries the argument and the clips are only ever *illustration*. Every visual is a
citation for a sentence.

The risk is volume of assets. This video needs ~40 distinct visuals for 51 seconds. That is the
actual bottleneck for us — not the rendering, not the script. **Asset sourcing is the hard part
of this preset**, which is why the pipeline needs an automated way to grab article screenshots,
stock footage, and product shots. See the "Asset sourcing" section of the README.
