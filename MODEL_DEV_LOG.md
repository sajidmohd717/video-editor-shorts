# Model Development Log

Every batch should produce two things: publishable shorts, **and a better
generator**. Finishing the MP4s without recording what the batch taught us is
incomplete work.

Record findings here. Promote something into the engine or a profile only when it
generalises; keep source-only facts (camera positions, specific asset picks) in
the project.

---

## Findings

Numbered so they can be cited from code comments and commit messages.

### F1 — Cut density is three discrete regimes, not one tempo

Sorting the 76 inter-cut gaps in ref 003 shows clustering, not a continuum:
strobe at **1 frame** (23 of them, fired in runs of 3–6), rapid montage at
**4 frames** (sustained, while the VO enumerates), and normal at **0.4–2.8s**.

Strobe runs aren't cuts in any editorial sense — the viewer can't read them as
images. They're percussive accents on a stressed word.

**Applied:** planners emit 1-frame clips for strobes. **Status:** keep.

### F2 — Density should alternate barrage and hold

Ref 001 averages 1.0 cuts/sec but spikes to 1.7/s on the hook and drops to 0.1/s
for 7 seconds where the actual argument lands. Uniform cutting reads as noise.

**Applied:** `pacing` segments in the schema carry per-segment energy.
**Status:** modelled, not yet fully driving generation.

### F3 — The visual must match the *shape* of the claim, not its topic

Built "three months became seven minutes" as a `stat-chart`. It rendered a
counter reading **"0.2 months"** — working code, nonsense output. A line chart
asserts a trend; the sentence asserts a jump.

**Applied:** added the `comparison` component; mapping table in ARCHITECTURE.
**Status:** keep. Generalises to every claim type.

### F4 — Whisper's timing is trustworthy; its wording is not

Whisper heard "productivity **game**" for "productivity **gain**". On a tech
channel most vocabulary is model and company names — exactly what ASR gets
wrong — and every mishearing would ship as an on-screen typo.

**Applied:** `captions.py` aligns via difflib; script wins on wording, Whisper
wins on timing. **Status:** keep. Also gives derived paragraph spans for free,
so voice swaps re-time the edit automatically.

Note: ElevenLabs output needed **zero** corrections where Kokoro needed one.
Clearer enunciation, fewer downstream repairs.

### F5 — Captions must never straddle a speaker change

Merging the clip's last word with the narration's first produced the card
**"coding Three"** — reads as a glitch rather than as either speaker.

**Applied:** every word carries a `voice` tag; cards break on change.
**Status:** keep. Recurs in every narrated video.

### F6 — Stock APIs match tags, not meaning

Roughly **half** of every search was unusable, and not subtly:

| Query | Returned |
|---|---|
| "city skyline aerial" | trees, power lines, a parked car |
| "server data center" | a screen of ping output in Spanish |
| "rocket launch" | a child playing with a toy rocket |

Wiring the first batch in unseen produced two wrong shots in v2.

**Applied:** contact-sheet review before wiring; note in the planner.
**Status:** keep. **Open:** a CLIP relevance re-rank would automate the filter.

### F7 — Pixabay's video endpoint has no orientation parameter

Unlike its image endpoint. Everything returns landscape and must be reframed.
One result arrived at 4K/64MB for what would be a two-second cutaway.

**Applied:** orientation recorded per asset; anything over 1920 on the long edge
is downscaled on download (64MB → 17MB). **Status:** keep. Pexels is primary for
video; Pixabay is fallback.

### F8 — One landscape source yields many shots

Varying the 9:16 crop focus and punch per clip turns a continuous take into
distinct setups. Took a clip with **1 cut in 40.7s** to **42 shots** at full
quality. Uses `objectPosition` rather than a transform so the crop stays
independent of the camera move.

**Applied:** `focusX`/`focusY` on sources; `FRAMINGS` rotation in the planners.
**Status:** keep. Highest value-per-line change made so far.

### F9 — Interleave narration and clip; don't duck

Ducking a speaker under a voiceover means two people talking at once — harder to
follow and editorially weaker than a clean handoff. Interleaving also makes the
two-distinct-voices reading unmistakable, which is the point under the reuse
policy.

**Applied:** `plan_narrated.py`; audio tracks gained a `duration` (trim-end)
field. **Status:** keep.

### F10 — B-roll on concrete nouns only

Never on reasoning. A face carries an argument; cutting away mid-point weakens
it. ~20% cutaway feels right.

**Status:** keep, but only one video of evidence. Worth A/B testing.

### F11 — Camera moves must be continuous across cuts

Giving each shot its own punch-in makes the zoom ramp up, snap back at the cut,
and ramp again. It reads as pumping and was the most unnatural thing the
mechanical edit did. Real multicam edits change the crop at a cut while the move
continues underneath.

**Applied:** one scale curve per passage; each shot's `from` is the previous
shot's `to`, and only `focusY` changes at the cut. The curve breathes on a slow
cosine over a gentle creep so it eases back rather than climbing forever.
**Status:** keep. Caught by the channel owner watching, not by any measurement.

### F12 — 128kbps MP3 puts audible static under synthesised speech

TTS returned as `mp3_44100_128` had clearly audible artifacts during voiced
content. Switching to `pcm_24000` (uncompressed, available on the cheapest paid
tier) removed it completely. `mp3_44100_192` and `pcm_44100` need higher tiers.

**Applied:** `outputFormat: pcm_24000` in the profile; PCM comes back headerless
so it's wrapped before use. **Status:** keep. Never ship MP3-sourced narration.

**How this was misdiagnosed, because the method matters more than the finding:**
MP3 was the first hypothesis. It was dismissed after testing for *band-limiting*
— a hard cutoff around 16kHz — and finding none. But 128kbps MP3 on speech
doesn't fail by band-limiting, it fails by coding artifacts during voiced
content. The test looked for the wrong signature, so a correct hypothesis was
ruled out and three wrong ones (room tone, low-frequency rumble, the mastering
limiter) were chased instead.

The lesson: **isolate before measuring.** Rendering three stems — narration
alone, clip alone, and the mix — and asking "which one has it?" resolved in one
listen what twenty minutes of spectral analysis on the mixed file did not.

### F13 — Reusing one filter input across branches corrupts concatenated audio

Audible static under the narration. Root cause: `concat()` built a single
`anullsrc` silence input and referenced it once per paragraph gap. Reusing one
filter input across multiple branches needs an explicit `asplit`; without one the
behaviour is undefined. With three paragraphs it was referenced twice.

**Applied:** every gap gets its own input; formats pinned to 48k/s16/mono before
concat; soxr resampling. **Status:** keep.

**Six wrong diagnoses before this one, and the reason is the lesson.** Ruled out
in turn: MP3 coding artifacts (a real problem, fixed, but not this one),
clipping, resampling aliasing, the mastering limiter, low-frequency rumble, and
TTS voice settings. Two of those "results" were artifacts my own test files
created — single-pass `loudnorm` is a *dynamic* normalizer and pumps gain up
during silent gaps, manufacturing the exact noise being hunted.

The reason every test disagreed with the next: **the simplified cases could not
reproduce the failure.** Single-sentence samples have no paragraph gaps, so the
filter graph had one input and one branch, so the bug never fired. Six rounds of
testing something adjacent to the artifact instead of the artifact itself.

**The rule:** reproduce the failure in the real artifact before simplifying
anything. The `-qc+10dB.m4a` file `pipeline.tts` now writes on every run exists
for this — the failure was inaudible at normal level and obvious once mastering
boosted it, so checking at high gain has to be routine rather than reactive.

Both real defects in this session (this and F11) were found by the channel owner
watching and listening, not by any measurement taken here.

### F14 — Crop from the full-resolution source, never downscale first

A-roll was extracted by scaling the 3840×2160 source to 1920×1080 and then
cropping 9:16. That crop is only **607px wide** and has to be upscaled 1.78× to
fill 1080 — visibly soft, and worse under a punch-in. Cropping from 2160p gives
**1215px**, a slight downscale.

**Applied:** extract `crop=1620:2160` around the subject from the 4K source, no
prior scaling; `subjectFocusX` remaps to the cropped frame. **Status:** keep.
Order of operations, not resolution, was the bug — the 4K source was there all
along.

**Rule:** crop first, scale last. Any 9:16 crop of a 16:9 source keeps only 32%
of the width, so the source needs ~3.2× the target width to avoid upscaling.

### F15 — Never repeat a b-roll asset within one short

Reusing clips reads as running out of material even when each placement is
right. Repeats crept in three ways: more shots than assets in a window, a
"hold the last shot" clip that reused `closeBroll[0]`, and — the one that took
two attempts to kill — **an asset used in a beat and again in a narration
window**.

That last one is the lesson: the first fix enforced uniqueness *within a window*,
which is not the same thing as within the video. `cooking` and `dinner` were
placed on clip beats and reappeared four seconds later under the closing
narration, and nothing complained.

**Applied:** a single `used_broll` set spanning the whole build, plus a **hard
failure** if any stock file appears on two clips. Like the coverage check (F18),
this is an invariant rather than a convention — it's invisible in the JSON and
obvious on screen.

**Consequence worth accepting:** strict uniqueness costs deliberate callbacks.
The dinner shot from the opening couldn't return for the "every Tuesday, over
dinner" line; a different warm shot carries it. That trade is right — an
unintentional repeat looks like a shortage far more often than an intentional one
reads as a callback.

**Budget ~10 distinct clips per 45s.** If a window falls back to repeats, the
planner says so; fetch more rather than accepting it.

### F16 — Detect silence in the audio, not gaps in word timings

Pause compression built on word gaps found only 1.45s of dead air. The real
figure was ~6.2s. ASR stretches a word's end time across a following pause — here
"three" is timed as spanning 1.16–2.76s, hiding a **1.77s silence** that is
plainly audible.

**Applied:** `ffmpeg silencedetect`; passages split at silences over
`maxPauseSeconds`, keeping half of it so the result breathes. Removed 3.6s and
lifted narration share from 37% to 40%. **Status:** keep.

**Rule:** word timings are for captions. For anything about the *audio*, measure
the audio.

### F17 — No end card

A subscribe prompt at the tail costs the loop. A short that ends and restarts
cleanly earns rewatches, and rewatch feeds the algorithm harder than the handful
of subscribes an end card converts.

**Applied:** `overlays.showEndCard: false`; b-roll now runs to the last frame.
**Status:** untested against platform data — worth an A/B once there are numbers.

### F18 — Carve, don't delete; and assert full clip coverage

Inserting b-roll over a-roll deleted every clip *overlapping* a padded window
while filling only the unpadded window, leaving the frame uncovered at the edges.
That renders as **black frames** — three of them, up to 0.47s.

**Applied:** overlapping clips are split and their source offsets recomputed, so
footage stays in sync; slivers below the minimum shot length are sealed by
extending the previous clip; and the planner now **hard-fails** if any moment of
the timeline is uncovered.

**Status:** keep. The assertion matters more than the fix — a coverage gap is
invisible in code, trivial to reintroduce, and glaring to a viewer. Cheap
invariants on the timeline are worth more than careful code, because the planner
will keep growing.

### F19 — Verify the subject's actual position; don't inherit it

`subjectFocusX` was carried over from the old job data as 0.72. Measured against
a gridded frame, the subject sat at **0.62** of the source. The crop was ~380px
off and he was noticeably off-centre.

**Applied:** measured from a gridded still, crop recentred, `subjectFocusX` set
to 0.44 rather than 0.5 — he faces screen-left, so the window shifts left to
leave looking room in the direction he's facing. Dead-centring a profile shot
crowds the face against the edge it looks toward.

**Status:** keep. Extract a gridded frame and look before trusting any inherited
framing number.

### F20 — Diegetic b-roll ambience replaces the music bed

**The Next Curve does not use music.** This is a standing channel constraint, not
an unfinished task — do not propose a music bed, and do not list its absence as a
gap.

Music was doing real work in the references: ref 003 runs at −9.2 LUFS with LRA
1.4, so nothing ever gets quiet and attention has no gap to escape through. Under
a no-music constraint that job has to be done another way.

**Applied:** b-roll audio, previously muted, now plays at `brollAmbienceDb`
(−26 dB) under the voice. Keyboard clatter, machinery, room tone and street
sound give each cut somewhere to *be*. It costs nothing — the audio is already in
the asset — and it is diegetic rather than musical.

**Also carrying the load:** silence cutting (F16) removes the dead air that a bed
would otherwise have covered, and a denser vocal master compensates for the
missing floor.

**Status:** keep at −26 dB. Confirmed subtle by the channel owner, which is the
intent — ambience must never compete with the narration or the speaker. If a
single asset's sound distracts, lower `audio.brollAmbienceDb`; `null` disables it.

**Approved future direction (not yet built):** sound effects are acceptable where
music is not — transition whooshes, pop-ins as graphics land, impacts on strobe
cuts. That's the next lever for energy if retention data suggests it's needed.
Deferred deliberately: the current video ships first so there's a baseline to
measure against.

### F21 — zod `.default()` does NOT apply to props passed via `--props`

The first overlay to rely on schema defaults instead of emitting every field
rendered as **nothing at all**. Props from `--props` are raw JSON; defaults are
only applied when something calls `.parse()`. Omitted fields arrive as
`undefined`, and a CSS gradient built from undefined colours is invalid, so the
browser drops the whole declaration silently.

**Applied:** `calculateMetadata` in `Root.tsx` now parses props through
`timelineSchema` and returns the parsed object, so defaults apply however props
arrive. **Status:** keep. This was a whole class of latent bug — every existing
overlay only worked because the planner happened to emit every field.

**Rule:** invalid CSS fails silently. When a component renders nothing, suspect a
malformed style string before suspecting the wiring.

### F22 — Sound effect + logo pop

A mark that springs in on a named entity, paired with a short sound effect. Two
details do the work:

- **Under-damped spring.** The overshoot is what reads as an *impact*; a
  critically-damped entrance on the same frame feels late.
- **Sound leads the visual by ~0.05s.** The eye registers a pop slightly after
  the ear, so exact alignment sounds late.

Logos are tinted with `brightness(0) invert(1)`, which whitens any source file
without editing the asset.

**Status:** keep, and keep rare. It works as an accent; firing it on every proper
noun turns it into wallpaper.

### F23 — Film burn, generated not stock

An amber light-leak that peaks across a cut. Generated procedurally, so it's
deterministic, recolourable, and licence-free. What makes it read as film rather
than a flash:

- asymmetric envelope — fast attack, slow decay (symmetric reads as a dissolve)
- three colour zones — near-white core, amber body, scorched red edge
- the bloom *spreads* as it decays rather than shrinking back
- grain confined to the burn, so clean frames stay clean

Note `radial-gradient(ellipse X% Y%)`, not `circle X%` — percentage sizes are
invalid for `circle` and the declaration is dropped without error.

**Placement:** only at VO↔clip handoffs. The device marks a change of *voice*,
not a change of shot; at 0.76 cuts/sec firing it on every cut would be
exhausting. **Status:** keep, untested against audience data.

---

## Baseline measurements

Reference teardowns are in [`docs/style-analysis/`](docs/style-analysis/).

| | Ref 001 | Ref 002 | Ref 003 | Our v1 (before) | Our narrated |
|---|---|---|---|---|---|
| Channel | Varun Mayya | NBC News | GrowthX | The Next Curve | — |
| Views | 302k | 9k | 698k | — | — |
| Cuts/sec | 1.0 | 0.13 | 1.5 | **0.02** | 0.73 |
| Loudness | −19.8 | −21.4 | −9.2 | **−25.3** | −13.9 |
| Original narration | 0% | 100% | ~100% | 0% | **37%** |

The two numbers that moved most: cut density 0.02 → 0.73, loudness −25.3 → −13.9.

### F24 — Cutting for length must never cost the antecedent

An early cut of yc-sam-02 opened on *"He himself would cook us dinner."* A pronoun
with nothing to attach to. The viewer never learns who is being described, why
they matter, or what the story is about — the short is 40 seconds of anecdote
about an unidentified "he".

The fix wasn't to restore length. It was to keep the **naming** line
("And my kind of Paul Graham memory is…") and cut the **filler** instead
("I think it was on Tuesdays"). Same runtime, context intact.

**Rule:** before cutting, identify the sentence that establishes *who* and
*what*. That one is load-bearing and can never go. Filler, asides, restarts and
hedges are what the budget comes from. When trimming a passage, read the result
cold and ask whether someone arriving at second zero knows what they're watching.

**Support:** logo-pops now do this job visually too — a portrait badge on the
person's name, an org mark on the org's. `shape: circle` for people (a photo must
keep its own colours), plain for logos.

### F25 — Only tint marks that are already monochrome

`brightness(0) invert(1)` whitens any logo, which is right for a single-colour
mark. Applied to the Y Combinator logo it flattened the orange field to black and
inverted it to a **solid white square**. Same treatment on a photograph would be
worse.

**Applied:** `tint: none` for coloured marks and photos. **Status:** keep.

### F26 — Introduce people the way a news channel does

A name alone assumes the viewer already knows why the person matters. On a feed
that's the wrong assumption. The broadcast lower-third convention answers it in
one line:

```
   (portrait)
  PAUL GRAHAM          ← name, white, larger
  YC CO-FOUNDER        ← role, accent colour, smaller, wider tracking
```

The role lands a few frames after the name so the eye takes them in order.

**Sizing, learned the hard way:** the role started at ~23px, which is perfectly
legible in a desktop preview and invisible on a phone. Now floors at 26px.
**Keep both strings short** — "Y COMBINATOR CO-FOUNDER" ran into the speaker's
head; "YC CO-FOUNDER" doesn't. Anything that needs more than ~15 characters is
being asked to do too much.

**Status:** keep. Use on the first mention of any person or organisation the
audience can't be assumed to know.

**Place it on the spoken name, not before it.** An early version of yc-sam-03
introduced Paul Graham during an interviewer's line 15 seconds ahead of Sam
saying "Paul had this thing he used to say". The badge is an *answer* to a
question the viewer is forming — firing it before the question exists wastes it,
and the viewer has forgotten by the time it's needed.

### F27 — Never leave 20 seconds without a cutaway

The first cut of yc-sam-02 ran ~20s of unbroken talking head before any b-roll.
Whatever the content, that's a long time on one face in a feed.

**Applied:** ~5s of b-roll inside the opening block, split into two shots
(cooking on "he would cook us dinner", the dinner table on "we would all walk in
feeling very hopeless"). Both literal, both on concrete nouns (F10).

**Rule of thumb:** no more than ~8–10s of continuous talking head without a
cutaway, a graphic, or a logo pop. Not for decoration — an unbroken face is a
static frame, and a static frame is a swipe.

### F28 — Beats must snap, not vanish, when a pause is removed

Pause compression removes spans of source time. An authored beat whose start or
end lands inside a removed span was silently dropped — two logo pops disappeared
because their end times drifted a tenth of a second into a trimmed silence.

Losing a deliberate editorial decision to a boundary drift is the wrong
behaviour. `src_to_timeline` now snaps to the nearest surviving edge.

**Rule:** when a transform can invalidate authored input, snap or clamp — don't
discard. A silently dropped element is worse than a slightly misplaced one,
because nothing tells you it happened.

### F29 — Content standards are constraints, and reviewing one frame isn't reviewing

The channel has standing content constraints: **no music, no alcohol, no
revealing clothing**. They belong to the channel owner, apply to every asset in
every video, and are not to be relitigated or traded against visual impact.

Two clips shipped past them into a cut: a champagne toast (alcohol *and* a
low-cut dress) and a candlelit dinner scene with wine glasses. Both had been
"reviewed" — against a single frame each. The dinner clip's wine glasses sit at
the edge of the frame and are easy to miss; the toast clip's first second shows
only raised hands.

**Applied:** `contentStandards` block in the profile, and the review rule
changed: **sample every candidate at several timestamps, not one thumbnail.**

**Note for asset search:** wine glasses are dressed into an enormous share of
restaurant, dinner-party and celebration stock. Queries like "friends dinner" or
"toast" will surface them constantly. "family eating dinner table home" and
"serving food plates table" returned six clean clips out of six.

**Status:** keep. When in doubt, pick a different clip — there is always another
clip.

### F30 — Revert the workaround once you fix the cause

Chasing the "static" I raised `stability` to 0.55 and zeroed `style`. The static
turned out to be a **filter-graph bug in `concat()`** (F13), nothing to do with
the voice. The bug got fixed; the flattened voice settings never got reverted.

Every video after that shipped with a deliberately de-expressive read
compensating for a problem that no longer existed — and "robotic" was the
result. High stability suppresses variation between phrases and `style: 0`
removes emphasis entirely, which is a fair description of robotic.

**Rule:** when a fix lands, go back and undo every workaround introduced while
hunting it. Workarounds outlive their reason silently, and nothing in the code
records that a value was defensive rather than chosen.

**Also settled:** `eleven_v3` is available and is a better synthesiser than
`multilingual_v2` — more natural prosody. It is also more variable run to run,
so the `-qc+10dB.m4a` check matters more, not less.

**Cost to know about:** voices differ in pace by a lot. Eric/v3 reads ~22% slower
than Matilda, which took this video from 46.2s to 50.8s with no other change.
The edit re-times itself (F4), but total runtime moves — check it after a voice
swap.

### F31 — Control pace in post, not through the TTS API

Eric on v3 read as "someone about to fall asleep on a beach" — the words were
right, the tempo wasn't. ElevenLabs' own `speed` voice setting proved useless
here: asking v3 for `speed: 1.15` returned a **longer** take than `1.0`, because
run-to-run variance swamps the parameter entirely.

**Applied:** `tts.rate` in the profile, applied with ffmpeg `atempo` after
concat. Deterministic, pitch-preserving, and transparent on speech up to ~1.25.
Pace becomes a dial rather than a hope.

**Settled at 1.18** for this channel. The unadjusted v3 read as "someone about to
fall asleep on a beach"; 1.26 sounded right on an isolated sample and was **too
fast once cut against the clip**. 1.18 is the sweet spot: VO 22.6s → 17.4s,
video 50.8s → 45.6s.

**Judge pace in context, not in isolation.** A bare VO sample has nothing to sit
against; the same read against a human speaker and cut b-roll feels quite
different. Any pace decision should be made on a finished cut.

**Rule:** when a provider's parameter can't be verified to work, measure it. One
API call each at two settings showed the parameter did nothing — cheaper than
shipping a video built on the assumption that it did.

### F32 — Read the whole long-form transcript, not just the clip

Standard step now for any clip cut from long-form: pull the full transcript and
read what surrounds the passage.

On yc-sam-03 it changed the edit three times over. The clip's own boundaries
started at "Paul had this thing he used to say" — **"Paul" is never identified
inside the clip**. The transcript showed the interviewer naming Paul Graham
~25s earlier, which gave both the antecedent and a much stronger opening line
(Graham had called Sam a top-five entrepreneur). It also revealed that Sam later
becomes YC president and does the same for others — not used, but it's why the
closing narration lands.

**Rule:** the clip's supplied boundaries are a starting suggestion, not the edit.
Extend backwards for the antecedent, forwards for the payoff, and cut the middle
if it drags.

### F33 — Not every shot should be cropped to 9:16

A wide two-shot cropped to 9:16 frames the table between the speakers. The
`fit` layout preserves the source aspect, centred, over a blurred copy of itself
— so the letterbox reads as a treatment rather than dead bars, and the backdrop
moves with the footage.

**Use `fit` when the composition IS the content:** two-shots, stages, diagrams,
anything where the crop would discard the point. `passageLayouts` sets it per
passage, so one video can mix both.

**But a capability is not a reason.** The wide two-shot went into yc-sam-03's
opening partly because `fit` had just been built and it was a chance to use it.
It was then cut: two seconds of an interviewer compliment that the video didn't
need, in front of a much stronger cold open. Ask what the shot does for the
viewer, not whether the engine can now render it.

**Also:** don't chop a `fit` shot at the usual cut rhythm or punch into it —
both undo the reason for using it. Shot length is stretched 2.2× and the camera
move reduced to a 3% drift.

### F34 — Clip captions need a correction map

Narration captions are protected by the script (F4). **Clip captions have no such
authority** — they come straight from ASR, so mishearings ship as on-screen
typos. This transcript rendered "Brownian motion" as "brownie and motion" and
"teacher as someone" as "teachers, someone".

**Applied:** `captionCorrections` in the job, a word→replacement map applied to
clip words before chunking. Authored per job because the errors are specific to
what was said.

**Check for these before rendering** — read the clip's transcript, don't assume
ASR got proper nouns and idioms right.

### F35 — Where a device fires matters as much as whether it fires

Three separate corrections this session were all the same underlying mistake:
the right element in the wrong place.

- The Paul Graham badge fired 15s **before** Sam said his name. It's an answer to
  a question the viewer is forming; spent early, it's wasted, and forgotten by
  the time it's needed.
- The wide two-shot opened the video because the `fit` layout had just been
  built, not because the video wanted it.
- An earlier cut opened on a pronoun with no antecedent (F24).

None were bugs. Each was a defensible element placed without asking *what is the
viewer thinking at this exact second?*

**Rule:** for every overlay, ask what question it answers and whether the viewer
is asking it yet. Devices land when they arrive a beat *after* the need, never
before.

### F36 — The narration-share floor is doing real work

`editorial.narrationShareFloor` caught yc-sam-03 at **28%**, under the 30% floor.
The right response was to lengthen the script, not to lower the floor — the
number exists because narration share is the reused-content posture (F9), and a
threshold you move when it's inconvenient isn't a threshold.

Lengthening also improved the writing: the extra clause on each paragraph gave
the close somewhere to land ("...telling you what you just got wrong, while you
can still do something about it") instead of stopping short.

**Status:** keep at 0.30. Aim for 35–40%.

---

### F37 — Ask the page where the words are; don't OCR your own screenshot

Highlight boxes over article screenshots were positioned by hand, and the
standing plan was to automate it with OCR. That was the wrong tool. **We own the
browser.** The DOM already knows, to the pixel, where every word was painted —
OCR would be a recognition step guessing at something we can simply ask for.

`pipeline.screenshot --find "<phrase>"` walks the text nodes, builds a
whitespace-collapsed index with node offsets kept alongside (so a phrase
straddling a `<b>` or a line break still resolves), makes a `Range`, and takes
`getClientRects()`. The boxes go into the article manifest and
`plan_longform.py` reads them, so the job file names a phrase and never a
coordinate.

Two details that matter:

- **`getClientRects()`, not `getBoundingClientRect()`.** A phrase that wraps is
  two rects. One box around both also paints the empty gutter right of line one
  and the indent left of line two — it reads as a block, not a sweep. Hence
  `highlightLines` in the schema.
- **`--crop-pad` is what makes it usable.** Oracle's Q4 release renders 39,524px
  tall. That is not an asset. The 900px around the sentence that matters is.

Same run also fixed a real bug: `highlightColor` defaulted to `#111114` under
`mix-blend-mode: multiply`, which paints a **black bar over the words** — the
exact opposite of highlighting. Marker ink must be light. If you wouldn't write
on paper with it, it's wrong.

**Bonus, and the reason to prefer primary sources:** locating the phrase meant
rendering the whole Oracle release, which surfaced a line no secondary coverage
mentioned — free cash flow was **negative $23.7 billion** for FY2026, in the
same document as the $638B of obligations. Reading the primary source is not
just about accuracy; it's where the good material is.

---

### F38 — Legible brand marks in stock make a claim you didn't write

A licensed Pexels clip of an office block with the **Citi** logo clearly readable
came back from "corporate office glass building" and was rejected.

The licence is fine. The problem is editorial: in a video about who is funding
the AI build-out, putting a named bank on screen tells the viewer Citi is part of
the story. Nothing in the narration says that, and it isn't true. **B-roll is not
neutral texture — a legible logo is an assertion**, and it's one the script never
made and can't defend.

Same reasoning as F3 (match the visual to the shape of the claim), one level
lower: it's not just that the visual should fit the claim, it's that a visual can
*add* a claim.

**Rule:** reject stock with a readable third-party brand unless that company is
actually in the argument. Generic is the point. Check the contact sheet for
signage, not just for content standards.

Related, from the same review: **search drift is worse for long-form.** "fiber
optic cable" returned a ski gondola and "data center construction" returned a
quarry. In shorts the b-roll is 1–2s and half-abstract, so a loose match survives;
over 8 minutes on a 3.2s cadence the viewer has time to notice the shot is wrong.

**Add to the fetcher when it's worth it:** `--orientation`. It was hardcoded to
`portrait` because the pipeline began with shorts, so the first long-form pull
came back two-thirds unusable. A portrait source in a 16:9 frame has to be
cropped so hard that whatever made the shot worth picking is gone.

---

## Platform data

### 2026-08-07 — first narrated short (El5XrIpsOCA)

- **Video:** "Sam Altman: 3 Months of Work → 7 Minutes", 43s, narrated format,
  40% original narration, 0.76 cuts/s, −14 LUFS
- **At ~1h20m:** 135 views · 41 engaged · **32% stayed to watch** · 68% swiped ·
  avg view 0:23 (53% of runtime)
- **Traffic:** 91.9% Shorts feed, 3% search
- **Baseline:** previous clip-only shorts (Sam + captions, no narration, no
  intro/outro) held **~63%**

**Read:** a 31-point hold gap. "Stayed to watch" is decided in the first 1–3
seconds, and that window changed completely: old videos opened on a human face
and a human voice, this one opens on abstract b-roll and synthetic narration
delivering a *setup* rather than a payoff.

Note the second number though — **53% average view duration**. Viewers who get
past three seconds watch about half. The edit isn't the problem; the front door
is. With 91.9% of traffic from the Shorts feed, hold rate is also what gates
further distribution, so it compounds.

**Sample size is small** (135 views). Treat 32% as directional.

**Next test (not yet run):** open on the speaker's face and voice for ~4s, bring
narration in second. Keeps the hook that earned 63%, keeps ~35% narration for the
rights position, changes one variable.

## Experiment template

Change one meaningful variable at a time.

```markdown
### YYYY-MM-DD — experiment name

- Source/format:
- Hypothesis:
- Changed variable:
- Control:
- Export evidence:
- Platform evidence:
- Decision: keep / revert / inconclusive
```

Record three-second hold, viewed-vs-swiped, average percentage watched,
completion, rewatch, saves, shares, comments demonstrating benefit, subscriber
conversion, revenue where available. **Raw views alone are not a verdict.**

---

## Open questions

- Does 0.73 cuts/sec beat 1.5 for narrated pieces, or are we under-cutting?
- Is 37% narration enough, or does more original content improve retention as
  well as rights posture?
- Does the progress bar help or distract? Untested, inherited from ref reading.
- Male vs female narration on this channel — no data.
- Does the running-gag device (ref 003 repeats a shot 3×) transfer?
