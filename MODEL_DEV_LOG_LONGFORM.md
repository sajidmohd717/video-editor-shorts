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

### L5 — Source audio is front-loaded; the last third is pure narration

Measured from YouTube's auto-captions, which mark speaker changes with `>>`.
**21 speaker changes in L001, every one of them before 600s. Zero in the final
277s.**

| Block | Source-audio moments |
|---|---|
| 0–100s | 5 — the cold-open montage |
| 100–200s | 3 |
| 200–300s | **6 — peak** |
| 300–400s | 1 |
| 400–500s | 4 |
| 500–600s | 2 |
| 600–877s | **0** |

The shape is deliberate and worth copying:

- **Opening**: a montage of broadcasters delivering the news *in their own
  voices*. It establishes the event as real and externally reported before the
  narrator makes a single claim. Borrowed credibility, spent early.
- **Middle**: source audio punctuates — a clip speaks when hearing the person say
  it matters more than being told they said it.
- **Final third**: **not one** source clip speaks. The argument is being made and
  the conclusion drawn, and nothing is allowed to compete with the narrator.

**Rule:** let a clip speak when the fact that *they said it* is the evidence. Once
you're reasoning rather than establishing, the footage goes silent and the
narration carries it alone.

### L6 — The reference uses a music bed; we can't

20 `[music]` tags across the runtime, spread evenly (3s, 52s, 154s, 361s, 602s,
859s…). It's a continuous bed, not stingers.

This matters more than it did for shorts. In the final 277s there is **no source
audio at all** — just narration and music. Strip the music and that stretch is a
voice over silent pictures for nearly five minutes, which is exactly where a
viewer notices the silence.

**Open question, and the main one for long-form:** what fills that. Candidates:
diegetic ambience from the footage itself (F20's answer for shorts, but there's
far more to fill here), tighter cutting through the conclusion, or accepting a
drier documentary register and leaning on the writing. Needs testing, not
guessing.

### L7 — Devices that carry an argument

From L001, worth building:

- **Date cards** — plain serif date on black. Marks a chronology and resets
  attention between segments. Cheap, high value.
- **Pull-quote cards** — one sentence, white serif on black, held. The change of
  register makes the video feel like it's underlining something.
- **News chyrons as evidence** — a broadcaster's own lower-third as proof.
  Long-form equivalent of the shorts `article-clip`.
- **Stylised portrait motif** — one treatment (halftone/engraved) reserved for
  the thesis figure, separating "the idea" from "the news".

### L8 — Sound design carries over; scope it to chapters, not transitions

The shorts SFX kit (ding, pop, whoosh, film burn) transfers to long-form. An
earlier version of the long-form profile disabled burns and whooshes, reasoning
they'd be exhausting over 8 minutes.

**That reasoning confused transition frequency with the device.** In shorts a burn
fires on every voice handoff — four in 45 seconds. In long-form the natural unit
is the **chapter**, so the same device fires 4–5 times across 8 minutes. At that
spacing it stops being decoration and becomes a structural signal: *that section
is over*. Which is precisely what a viewer 6 minutes into an argument needs.

**Rule:** when porting a device between formats, port its *purpose*, not its
trigger. The burn's job is "mark a structural boundary". What counts as a
boundary is what changes between formats.

**Long-form additions worth having**, given the asset mix is document-heavy:

- **paper** — document/filing reveals. ~35 uses in lf-001; the highest-value
  addition by far.
- **impact** — deep low thud for the big number cards.
- **tick** — soft UI click for highlight sweeps and list items.

**Avoid** risers, drones, swells and anything with pitch content. Those are music
under another name, and the channel does not use music (F20). Percussive,
mechanical and diegetic sounds are fine; anything that implies a key is not.

### L9 — Cue visuals by phrase, never by timestamp

`plan_longform.py` places every visual by **the words the narration is saying**:

```json
{ "cue": "the prepaid and customer supplied hardware", "type": "quote-card" }
```

At 5,400 characters the narration *will* be regenerated — a rewrite, a voice
change, a pace change. Any of those shifts every timestamp in the file and
silently slides 150 assets out of sync. Phrases survive all three.

It also makes the job file readable as an edit decision list: you can see what
the video does without opening the video.

**Cost:** cue text must match the narration exactly. The planner **hard-fails**
on an unresolved cue rather than dropping the visual, because a silently missing
visual is exactly the class of bug that ships (cf. F28, where logo pops vanished
into removed pauses).

---

### L10 — Don't caption over a card that is already text

The first long-form render put a quote card on screen — the narrator reading
Oracle's own sentence — while the caption track printed *the same sentence*
underneath in a different font. Two renderings of one sentence is worse than
either alone.

`plan_longform.py` now drops caption cues that overlap a full-screen text card
(quote, date, comparison, word, kinetic title). 61 of 490 cues in lf-001.

This is an editorial decision, so it lives in the planner, not in `Captions.tsx`.

---

### L11 — A component that hardcodes canvas dimensions is a portrait component

Making the canvas configurable (`meta.width`/`meta.height`) was necessary but not
sufficient. Three components still assumed 9:16, and each failed differently:

- **`Annotation`** imported `WIDTH`/`HEIGHT` constants — trivially wrong, easy to
  spot by grep.
- **`Comparison`** stacked before-above-after. Correct in portrait, but in
  landscape it left the entire right half of the frame empty. *Nothing was
  broken; it was just a bad edit.* Now side-by-side when `width > height`, with
  the rule between the two doing the "versus".
- **`StatChart`** sized its SVG `width: 100%` against a fixed viewBox — so plot
  **height scaled with frame width**. At 1780px wide the plot became 1028px tall
  and pushed the title and counter off the top of the frame.

**The pattern:** the grep-able failures were the harmless ones. The two that
mattered were a layout that was merely *unflattering* and an aspect-ratio
coupling that was invisible in the code and obvious in one still.

Reinforces the shorts habit: `npx remotion still` on every new overlay type, at
**both** aspect ratios, before wiring it into a render.

Also: `tone` and card background were two independent knobs that had to agree. A
`tone: "dark"` comparison rendered white text on the profile's light canvas —
invisible on screen and invisible in review. The planner now derives one from the
other. **Two settings that must agree are one setting.**

---

### L12 — The cold open is an edit decision, so it belongs in the planner

The shot list wanted the video to open on broadcast voices before our narration
starts. That is impossible to express by editing the script, and it shouldn't be:
the narration text doesn't change at all, it just **starts later**.

`job.coldOpen` is a list of clips; the planner sums their durations into `lead`
and shifts the VO, every phrase cue, every chapter boundary and the whole caption
track by that amount. Authoring stays in narration time; the timeline is in video
time; one variable converts between them.

Worth doing because of the channel's only retention data point: yc-sam-01 opened
on abstract b-roll under a synthetic voice and held **32%** against ~63% for
clip-first cuts. Real human voices in the first second is the direct test.

**The bug this shape invites, and it's a quiet one.** Caption cues come out of
`captions.json` in *narration* time while everything else on the timeline is in
*video* time. Forget the shift on one of them and nothing errors — the captions
just run `lead` seconds early for the entire video. Two clocks in one file is a
standing hazard; convert at the boundary, once, and never carry both.

---

### L13 — A chyron is a headline, and it says what the story is about

The cold-open montage called for broadcast clips "with chyrons visible", the idea
being that a chyron proves the story was externally reported.

Rendering it showed the cost. A CNA clip whose *audio* fit perfectly ("raising
nearly $10 billion in its IPO") carried the lower third **"CHINA'S AI IPO WAVE"**.
Our video never discusses China. For three seconds the largest text on screen
told the viewer they were watching a different story.

**A chyron is not texture, it's a headline** — the strongest claim on screen,
usually larger than our own captions. Extends F38 (a legible logo is an
assertion) one level up: *legible headline text is an assertion about the
subject itself.*

**Rule:** read every chyron in a candidate clip as though the narration said it
out loud. If you wouldn't write that sentence into the script, don't put it on
screen.

Second cost, specific to a monetised channel: broadcaster clips carry heavy
idents — a full red BBC News lower third plus corner logo occupied roughly a
fifth of frame. Stacking three broadcaster idents in the opening ten seconds
makes the most claim-prone stretch of the video also the first thing anyone
sees. **Unresolved — flagged to the channel owner rather than decided here**,
because it trades retention against monetisation and that trade belongs to them.

Worth noting the alternative that keeps most of the benefit: the retention
argument is about hearing a *real human voice* early, not about seeing a
broadcaster's brand. A primary-source clip (an earnings call, a company keynote)
delivers the voice without the ident or the headline.

---

### L14 — Source audio needs a hole cut in the narration, not a duck

L5 ("let the clip speak") came from shorts, where narration and clip **alternate**
— a hole always exists. Long-form narration is continuous by design, so there is
never one. Measured at the Ch5 cue: **the largest gap anywhere in the surrounding
40 words is 0.68 seconds.** The clip that goes there is 15.6.

Playing it anyway stacks two voices. Ducking the VO doesn't fix it either — a
quiet second voice under a loud one is not "letting the clip speak", it's mud.

So the planner **cuts the narration and inserts the gap**, generalising the
cold-open shift (L12) from "shift everything at the top" to "shift everything
after each insertion point". The VO becomes several segments of one file; the
script is still never touched.

    coldOpen  → lead
    sourceAudio cue + duration → an insertion
    shift(t) = lead + t + Σ(gaps opened at or before t)

**The bug this produced, which is the real lesson.** The first version was
`shift(t) = lead + Σ(gaps)` — it dropped `t`. Every cue in the video collapsed
onto 9.65s. Nothing raised: cards came out with `start == end`, VO segments
overlapped each other by minutes, and the planner printed a cheerful summary
line. The only visible symptom was caption suppression quietly falling from 61
cues to 2, which is the kind of number you skim past.

**Two assertions now make the whole class unshippable**, in the spirit of F18:

- no two `vo`/`clip-audio` entries may overlap — *one voice at a time*
- no overlay may have a duration under 0.15s — *a card that never shows is the
  same failure as a clip that never plays*

Both are four lines. The planner will keep growing; invariants survive that,
care doesn't.

---

### L15 — Chase the clip back to the room it was filmed in

The Ch5 clip arrived as a Global News upload. Three problems, none in the
metadata and all in the frames: a broadcaster bug in every frame, a backdrop
reading **U.S.–SAUDI INVESTMENT FORUM 2025** (so it wasn't an NVIDIA event at
all), and **Elon Musk sitting in shot** — someone the script never mentions.

Searching the *event* rather than the *quote* found the host's own channel
(Saudi MCIT) with the same passage, no ident, at higher integrity.

**The method:** a re-upload's title tells you what a broadcaster found
interesting. The *backdrop* tells you where you actually are — and that is the
search term that finds the primary source.

It doesn't always resolve cleanly. Here the primary stream holds a **wide
three-shot for the entire quote**, with Musk in frame throughout, and the clean
single of Huang is 80 seconds earlier — so using it under this audio would put
visibly mismatched lips on screen. Neither "show Musk" nor "show wrong lips" is
acceptable, so the picture became a **pull quote with attribution** over his
voice. When no honest angle exists, stop looking for one and let the engine
carry it.

---

### L16 — Stock is connective tissue, not a vocabulary

lf-001's first cut: **90 clips from 22 stock assets, mean reuse 4.1×**, repeats
70–85s apart. It rendered, mastered, passed every automated check, and was
boring. The channel owner's verdict: *"all that it has is just b-roll stock
video… having it once in a while is fine, but the entire video being that is
just not it."*

Teardown L002 shows why. A comparable video runs **six** visual registers —
named-entity footage, purpose-built motion graphics, attributed interviews,
sourced charts, product surfaces, and generic stock. Generic stock is the
*connective tissue between* the others. We had made it the whole body.

**Diagnosis worth keeping:** the pipeline optimised what it could measure.
Uniqueness, coverage, and cadence all had checks; *variety of register* had none,
so a video could satisfy every invariant and still be monotonous. Assertions
catch defects, not dullness.

**The order to fix it in, by value per unit of work:**

1. Proper-noun visuals (L17) — mechanical, and we already have the machinery
2. The diagram the argument needs (L18)
3. Attributed source-audio blocks — now possible via L14
4. Product surfaces: logos, filings, UI, shot close
5. Generic stock, back to what it should have been: the gaps

---

### L17 — A proper noun is a visual cue

The most repeatable thing in L002: when the narration says a company's name, the
screen shows **that company** — its CEO on stage, its headquarters sign, its
product — never an anonymous server rack.

Naming a company while showing generic stock wastes the one moment when the
viewer is thinking about a specific company. Over lf-001's script, "NVIDIA",
"OpenAI", "Microsoft", "Anthropic" and "Oracle" occur dozens of times — that is
dozens of free, obvious visual cues that were being spent on circuit boards.

Fits our machinery exactly: visuals are already placed by phrase, so "when the
narration says NVIDIA, show NVIDIA" is a job entry rather than a feature.

**Sourcing is the hard part, and it costs more than it looks.** Measured on
lf-001, whose narration carries 22 proper-noun mentions in 5.5 minutes
(Microsoft 7, NVIDIA 6, Oracle 3, OpenAI 2, Anthropic 2, Azure 2):

- **Royalty-free stock has no branded HQ footage.** Searching "Nvidia
  headquarters", "Microsoft office building sign" and "Oracle headquarters"
  returned generic office blocks and — search drift again — a beach. Trademarked
  footage isn't licensable this way, which is why the reference channel shoots
  its own. *Checked by looking, not assumed.*
- **Official highlight reels are contaminated with partner branding.** Oracle's
  own CloudWorld highlights carry Fujitsu, Uber and MGM lower thirds throughout.
  Using it would put Uber on screen in a video that never mentions Uber — L13,
  from the company's own channel.
- **A clean CEO-alone shot usually means downloading the full keynote.** The
  2-minute official recap cuts every 2–3 seconds and is mostly product renders.
- **Sample densely before cutting.** Frames 10s apart missed every shot boundary;
  three first-attempt cuts landed on a glitch graphic, a slide, and an unrelated
  MGM customer story.

**What actually worked**, and the pattern to repeat: a company's own keynote
where it names a *partner* puts both brands on screen at once, cleanly. Microsoft
Build gave a sustained 5s split of Nadella and Huang — the exact two companies
our sentence names, primary source, no ident, nobody on screen the script
doesn't. **Look for the moment two subjects share a frame legitimately** rather
than sourcing each name separately.

Remaining rules from L13/L15: primary streams only, never a broadcaster
re-upload; and check the frame for people the script never mentions.

---

### L18 — Build the diagram the argument needs

L002 spends **47 seconds — 8% of runtime** — on a single animated node graph, and
earns it. *"The money moves in a circle"* is a **structural** claim, and no
sequence of photographs can state a structure. F3 says match the visual to the
shape of the claim; this is the same rule at the scale of a whole thesis.

Our shot list asked for this ("two boxes, arrows both ways") and it was never
built, so the thesis was carried by stock footage of circuit boards.

Now `entity-graph`: authored node positions, directed labelled edges, progressive
assembly. Three decisions worth keeping:

- **Directed, not a network.** Theirs shows companies are connected — which
  everyone assumes. Ours shows money leaving and coming back, which is the claim.
- **The return arrow is not muted.** It was grey in the first draft; grey said
  "footnote" about the single most important edge. It is now white and as strong
  as the outbound flows.
- **Four nodes, not eighteen.** Theirs is impressive and borderline unreadable.
  A diagram that can't be followed at speed is decoration.

**Gotcha:** for arcs between the same pair, the perpendicular flips with
direction, so the *same* curve keyword bows them apart and opposite keywords
stack them — the reverse of how it reads. Two edges silently drew on top of each
other until a still showed one missing.

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
