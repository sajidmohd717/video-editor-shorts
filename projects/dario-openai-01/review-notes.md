# Review notes — dario-openai-01

## 2026-08-08 — owner review

**Overall verdict:** “Great video.” Keep the concept, structure, narration,
graphics, captions, and pacing.

### Opening crop defect

- **Feedback:** during the first second, Dario was pushed into the right edge and
  half his face was outside the frame.
- **Cause:** the opening passage contains a source camera cut. It begins on
  Dario's reaction at 4.76–5.30s, then cuts to Emily for the question. The one
  passage-level crop was centered on Emily and incorrectly applied to both shots.
- **Fix:** `source.focusRanges` now centers Dario at `focusX: 0.64` through the
  source cut at 5.30s; the passage default then centers Emily at `focusX: 0.40`.
  Only the visual layer splits, so the interviewer's sentence and audio remain
  continuous.
- **Verification:** frame 5 renders Dario centered with his whole face visible;
  the crop changes on the source camera cut, not during a shot.

### Anthropic logo-pop

- **Feedback:** add a small logo pop with a pop sound on “built Anthropic,” like
  the ChatGPT mark in the first narrated short. The owner considers these small,
  semantically timed accents useful for engagement.
- **Applied:** Anthropic mark lands at timeline 43.781s, exactly on the word
  “Anthropic,” with the existing `pop.wav`. It sits to the right of the
  `ARGUE → BUILD` comparison and above the caption safe area.
- **Rule:** use one meaningful logo-pop when a named entity lands and the frame
  has genuine room for it. Do not turn every proper noun into a sound cue.
- **Evidence level:** owner-approved editorial pattern; audience effect remains
  untested until retention data is available.

### Generator takeaway

Review the first second frame-by-frame whenever the source passage begins near a
camera cut. A still from the middle of a passage cannot validate its opening
crop. Each review correction should change both the artifact and the reusable
rule that allowed the defect.
