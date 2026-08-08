# lf-001 — publishing metadata

## Title

**Who Is Actually Paying for the AI Boom?**

Chosen by the channel owner from a shortlist. Keep it.

Two alternates worth an A/B if the first week underperforms — both put the
number in front, which usually helps a small channel in search:

- `$638 Billion: Who Is Actually Paying for the AI Boom?`
- `The AI Boom Runs on "Up To" — Here's What That Means`

Do **not** title it as a crash prediction. The video explicitly refuses to
predict one, and a title the video contradicts is the fastest way to lose the
audience it attracts.

## Description

```
Every few weeks there's another enormous number attached to AI. A hundred
billion. Three hundred billion. Six hundred and thirty-eight billion.

The numbers are real — they're in press releases and regulatory filings. But
almost nobody asks the simpler question: where did the money come from, and
whose hands has it passed through on the way?

This is what the primary documents actually say, and it turns out the headline
figures are consistently larger than the money that has changed hands.

0:00  The question
0:43  One deal, read carefully
1:44  The same shape, three times
2:45  What the filings say
4:12  The other side, and what to watch

Sources — every figure in this video is from a primary document:
• NVIDIA newsroom, "OpenAI and NVIDIA Announce Strategic Partnership" (22 Sep 2025)
• Anthropic, "Microsoft, NVIDIA, and Anthropic announce strategic partnerships"
• Oracle Q4 FY2026 results, investor.oracle.com
• Jensen Huang at the U.S.–Saudi Investment Forum 2025
• Oracle Q4 FY2026 earnings call

Corrections go in the pinned comment.
```

**Why it's written this way:**

- Opens with the video's own first lines. Someone reading the description has
  already heard them or is deciding whether to; either way it's the strongest
  copy we have.
- Chapters are the argument's structure, not a topic list (L4), and they let
  YouTube show a progress-bar breakdown.
- Sources are listed because the channel credits sources — and here it's also
  the defence of the whole thesis. The video's claim is that the *primary*
  documents say something different from the coverage; a description that
  doesn't cite them undercuts it.
- A corrections line invites the audience to check. On a video about people
  reading figures carelessly, that posture is the point.

## Tags

`ai`, `artificial intelligence`, `nvidia`, `openai`, `anthropic`, `oracle`,
`microsoft`, `ai bubble`, `circular financing`, `vendor financing`,
`ai investment`, `tech news`, `ai spending`, `remaining performance obligations`

## Thumbnail

**`projects/lf-001/art/thumbnail.png`** — 1280x720.

Two logos, two arrows, one headline:

    WHO IS ACTUALLY
    PAYING FOR AI?
    [Microsoft] --$5B IN--> [Anthropic]
                <--$30B BACK--

**Why this and not the four-node graph.** The full graph is the video's best
device and a bad thumbnail — four nodes and four labelled edges cannot be read
at 320px. Cutting to the single round trip keeps the entire argument (money out,
more money back) and loses nothing a viewer could have read anyway. **A thumbnail
holds one idea.**

Checked the only way that matters: downscaled to 320px wide and looked at it.
Headline, both logos and both figures survive.

### How it was made, so it can be redone

1. `projects/lf-001/thumb.json` — a 1280x720 timeline with one `entity-graph`
   overlay, two nodes, `labelScale: 2.6`, nodes pushed to `y: 0.70` so the
   headline owns the top third.
2. `npx remotion still src/index.ts Short out/thumb-graph.png --frame=90 --props=projects/lf-001/thumb.json`
3. Headline composited in PIL (Segoe UI Black, sized to 80% of frame width, dark
   halo). **Not** a `date-card` — that is a full-screen card with its own
   background and it painted over the graph.

### The rule this taught

**Video components are not thumbnail components.** Type tuned for full-screen
playback over seconds is illegible at 5% scale in a fraction of a second. Both
`big-number` and `entity-graph` gained a size multiplier (`scale`,
`labelScale`) purely so the same component can serve both, defaulting to 1 so
the video is untouched.

## Publishing

Upload **private** first, watch it through once at normal speed, then flip to
public by hand:

```bash
python -m pipeline.upload lf-001 --input render/lf-001-master.mp4
```
