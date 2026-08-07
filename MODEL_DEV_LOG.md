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

---

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
