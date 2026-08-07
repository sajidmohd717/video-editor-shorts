import { z } from "zod";

/**
 * The Timeline Spec.
 *
 * This is the contract between "thinking about the edit" and "rendering the edit".
 * Everything upstream (transcription, script, LLM planning) produces one of these.
 * Everything downstream (Remotion) only ever consumes one of these.
 *
 * All times are in SECONDS, absolute from the start of the video. The renderer converts
 * to frames. Keeping the spec in seconds means changing fps never invalidates a timeline.
 */

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

/* -------------------------------------------------------------------------- */
/* Captions                                                                    */
/* -------------------------------------------------------------------------- */

/** One word with its aligned timing, straight out of WhisperX. */
export const wordSchema = z.object({
  text: z.string(),
  start: z.number(),
  end: z.number(),
});

/**
 * A caption card = 2-4 words shown as a block, swapped on phrase boundaries.
 * Ref 001 does NOT use per-word karaoke; it replaces the whole card.
 */
export const captionCueSchema = z.object({
  start: z.number(),
  end: z.number(),
  words: z.array(wordSchema),
  /** Optional per-cue emphasis, e.g. the payoff word gets scaled/coloured. */
  emphasis: z.enum(["none", "pop", "shake", "color"]).default("none"),
});

export const captionStyleSchema = z.object({
  /**
   * `broadcast` reproduces ref 002's accessibility-style subtitles. It is
   * deliberately the least attention-grabbing option — included for completeness,
   * but `pill` outperforms it for retention and should stay the default even in
   * the news-update format.
   */
  /**
   * `word-pop` is ref 003's style and the best-performing of the three: heavy white
   * sans with a thick black stroke and no pill, 1-2 words per card. The stroke does
   * the legibility work the pill does, without boxing off part of the frame.
   */
  preset: z
    .enum(["pill", "karaoke", "outline", "bold-drop", "broadcast", "word-pop"])
    .default("pill"),
  /** Stroke width for word-pop/outline. */
  strokeWidth: z.number().default(8),
  fontFamily: z.string().default("Poppins"),
  fontWeight: z.number().default(600),
  fontSize: z.number().default(52),
  color: z.string().default("#FFFFFF"),
  /** Anchor as a fraction of frame height. 0.5 = optical centre (ref 001 stacked mode). */
  anchorY: z.number().default(0.5),
  pillColor: z.string().default("rgba(0,0,0,0.72)"),
  pillRadius: z.number().default(14),
});

/* -------------------------------------------------------------------------- */
/* Visual layers                                                               */
/* -------------------------------------------------------------------------- */

/** Where source video sits in the frame. Ref 001 uses all four of these. */
export const layoutSchema = z.enum([
  "full", // single source fills 1080x1920
  "stacked", // two sources, 960px each, hard seam at y=960
  "inset", // one full + one corner box
  "graphic", // no talking head; motion graphic or b-roll owns the frame
]);

/**
 * Camera move applied to a clip. The slow punch-in is the highest
 * value-per-line-of-code effect in the whole system.
 */
export const cameraSchema = z.object({
  kind: z.enum(["none", "punch-in", "punch-out", "drift", "shake"]).default("punch-in"),
  from: z.number().default(1.0),
  to: z.number().default(1.12),
  /** Normalised focal point to zoom toward; 0.5/0.4 biases to a face. */
  originX: z.number().default(0.5),
  originY: z.number().default(0.4),
});

export const clipSchema = z.object({
  id: z.string(),
  start: z.number(),
  end: z.number(),
  layout: layoutSchema.default("full"),
  /** Asset paths, relative to the project dir. Two entries for stacked/inset. */
  sources: z.array(
    z.object({
      src: z.string(),
      /** Seek offset into the source file at clip start. */
      offset: z.number().default(0),
      /**
       * Which point of the SOURCE frame to keep centred when cropping to 9:16,
       * normalised 0-1. This is how one landscape interview yields many distinct
       * "shots": vary focus + scale per clip and each crop reads as a new setup.
       * 0.72/0.5 keeps a subject sitting right-of-centre in frame.
       */
      focusX: z.number().default(0.5),
      focusY: z.number().default(0.5),
      /** Fine translate nudge on top of the crop, normalised to frame size. */
      panX: z.number().default(0),
      panY: z.number().default(0),
      scale: z.number().default(1),
      muted: z.boolean().default(true),
    }),
  ),
  camera: cameraSchema.default({}),
  /**
   * Backdrop when the clip has no video source — i.e. `graphic` layout. Ref 003's
   * "explainer canvas" is a light grey; the default black suits full-bleed b-roll.
   */
  background: z.string().default("#000000"),
  /** Colour/stylistic treatment stacked on top of the clip. */
  filters: z
    .array(
      z.enum([
        "none",
        "darken",
        "blur",
        "desaturate",
        "terminal-green",
        "vhs",
        "chromatic-aberration",
        "film-grain",
      ]),
    )
    .default([]),
  /**
   * Transition INTO this clip. Ref 001 is ~all hard cuts; ref 002 is ~all
   * cross-dissolves. In the hybrid news-update preset the *change* in transition
   * type is itself a signal — dissolve between stills, hard cut into a graphic.
   *
   * For a dissolve to have anything to dissolve from, the preceding clip's `end`
   * must overlap this clip's `start` by at least `transitionDuration`.
   */
  transitionIn: z
    .enum(["cut", "dissolve", "whip-pan", "flash", "zoom-blur", "glitch", "slide"])
    .default("cut"),
  transitionDuration: z.number().default(0.5),
});

/* -------------------------------------------------------------------------- */
/* Overlays: the stuff that makes it not look like a slideshow                 */
/* -------------------------------------------------------------------------- */

const baseOverlay = z.object({
  id: z.string(),
  start: z.number(),
  end: z.number(),
  /** Higher = drawn on top. Captions default to 100. */
  z: z.number().default(50),
});

export const overlaySchema = z.discriminatedUnion("type", [
  /** Word-by-word assembling kinetic title. The ref's 2-7s hook. */
  baseOverlay.extend({
    type: z.literal("kinetic-title"),
    lines: z.array(
      z.object({
        text: z.string(),
        style: z.enum(["serif-italic", "sans-heavy", "sans-light"]),
        size: z.number(),
        /** Seconds after overlay start that this line appears. */
        delay: z.number().default(0),
      }),
    ),
  }),

  /** Sequential chat bubbles, staggered ~200ms. Ref's 35-40s set-piece. */
  baseOverlay.extend({
    type: z.literal("chat-bubbles"),
    theme: z.enum(["imessage", "whatsapp", "x-dm"]).default("imessage"),
    bubbles: z.array(
      z.object({
        text: z.string(),
        side: z.enum(["left", "right"]).default("left"),
        delay: z.number(),
      }),
    ),
  }),

  /** Full-bleed image punchline (AI portraits, memes, screenshots). */
  baseOverlay.extend({
    type: z.literal("image-card"),
    src: z.string(),
    fit: z.enum(["cover", "contain"]).default("cover"),
    entrance: z.enum(["snap", "slide-up", "scale-in", "tilt-drop"]).default("scale-in"),
    caption: z.string().optional(),
  }),

  /** Headline / news-lower-third. Core to a "news commentary" channel. */
  baseOverlay.extend({
    type: z.literal("headline"),
    source: z.string(), // "REUTERS", "@elonmusk", etc.
    text: z.string(),
    variant: z.enum(["ticker", "breaking", "tweet", "article"]).default("breaking"),
  }),

  /** Scrolling code / terminal treatment. */
  baseOverlay.extend({
    type: z.literal("code-panel"),
    code: z.string(),
    language: z.string().default("python"),
    scrollSpeed: z.number().default(30),
  }),

  /** Emoji / sticker / arrow accents that punch in on a beat. */
  baseOverlay.extend({
    type: z.literal("accent"),
    glyph: z.string(),
    x: z.number(),
    y: z.number(),
    size: z.number().default(160),
    motion: z.enum(["pop", "spin-in", "bounce", "wiggle"]).default("pop"),
  }),

  /** Progress bar / countdown — a proven retention device on shorts. */
  baseOverlay.extend({
    type: z.literal("progress"),
    style: z.enum(["bar", "dots", "ring"]).default("bar"),
  }),

  /**
   * A news article screenshot with a highlight bar that sweeps across a phrase as
   * the VO reaches it. Ref 003's most-repeated device and its entire evidence layer:
   * it turns an assertion into a citation without leaving the vertical frame.
   */
  baseOverlay.extend({
    type: z.literal("article-clip"),
    src: z.string().optional(),
    /** Rendered fallback when no screenshot asset exists yet. */
    outlet: z.string().default(""),
    kicker: z.string().default(""),
    headline: z.string().default(""),
    byline: z.string().default(""),
    /** Substring of `headline` to sweep-highlight, and when. */
    highlight: z.string().optional(),
    /**
     * Highlight band for SCREENSHOT mode, normalised to the rendered image.
     * The rendered-card path finds the phrase in the text itself; over a
     * screenshot we can't know where words are, so the band is positioned by
     * hand once and reused.
     */
    highlightBox: z
      .object({
        x: z.number(),
        y: z.number(),
        width: z.number(),
        height: z.number(),
      })
      .optional(),
    /**
     * How the screenshot highlight reads:
     *  marker — translucent accent over the text, the familiar highlighter-pen
     *           metaphor. Predictable on any light page. Default.
     *  invert — white band in `difference` mode. High impact, but the result is
     *           the page's complementary colour, so it varies by site (a green
     *           masthead comes out magenta). Check it before shipping.
     */
    highlightMode: z.enum(["marker", "invert"]).default("marker"),
    highlightStart: z.number().default(0.4),
    highlightDuration: z.number().default(0.45),
    highlightColor: z.string().default("#111114"),
  }),

  /**
   * Display-serif label + curved hand-drawn arrow pointing at the subject.
   * Ref 003 uses this on a light "explainer canvas" — it reads as someone marking
   * up a slide, which is a very different register from a caption.
   */
  baseOverlay.extend({
    type: z.literal("annotation"),
    label: z.string(),
    /** Normalised label anchor. */
    labelX: z.number().default(0.5),
    labelY: z.number().default(0.2),
    /** Normalised arrow tip — where it points. */
    targetX: z.number().default(0.25),
    targetY: z.number().default(0.35),
    curve: z.enum(["left", "right"]).default("left"),
    color: z.string().default("#3B9EFF"),
    labelSize: z.number().default(84),
  }),

  /**
   * Animated area chart with a value counter. Ref 003 uses this for "a number went
   * up" — which, for a business/tech channel, is a large share of all claims.
   */
  baseOverlay.extend({
    type: z.literal("stat-chart"),
    title: z.string(),
    /** Normalised 0-1 series; the chart draws left-to-right over `drawDuration`. */
    series: z.array(z.number()),
    valueFrom: z.number().default(0),
    valueTo: z.number().default(100),
    valueSuffix: z.string().default("%"),
    drawDuration: z.number().default(1.2),
    accent: z.string().default("#22C55E"),
  }),

  /**
   * Before/after comparison — two values, the second slamming in after a beat.
   *
   * Distinct from `stat-chart` on purpose: a line chart asserts a TREND, a
   * comparison asserts a JUMP. Using the wrong one misrepresents the sentence,
   * and a chart counting "3 months" down to "0.2 months" reads as nonsense when
   * the actual claim is "three months became seven minutes".
   */
  baseOverlay.extend({
    type: z.literal("comparison"),
    beforeLabel: z.string(),
    beforeValue: z.string(),
    afterLabel: z.string(),
    afterValue: z.string(),
    /** Seconds after start that the "after" side lands. */
    afterDelay: z.number().default(0.9),
    accent: z.string().default("#FF5A3C"),
    tone: z.enum(["light", "dark"]).default("light"),
  }),

  /**
   * Full-screen typographic word card. Ref 003's cold open fires four of these in
   * five seconds, each in a deliberately different typeface.
   */
  baseOverlay.extend({
    type: z.literal("word-card"),
    text: z.string(),
    face: z.enum(["serif-display", "sans-heavy", "serif-light", "script-accent"]),
    size: z.number().default(150),
    color: z.string().default("#FFFFFF"),
    background: z.string().optional(),
  }),

  /** Mid-roll subscribe pill. Ref 003 fires this twice, not just at the end. */
  baseOverlay.extend({
    type: z.literal("cta"),
    text: z.string().default("SUBSCRIBE"),
    x: z.number().default(0.5),
    y: z.number().default(0.62),
    color: z.string().default("#1D4ED8"),
  }),

  /**
   * Persistent chrome: dateline + channel bug. Ref 002 keeps both on screen for
   * the entire runtime. The dateline is the single cheapest "this is current news"
   * signal available — span this across the whole video.
   */
  baseOverlay.extend({
    type: z.literal("chrome"),
    dateline: z.string().optional(),
    bug: z.string().optional(),
    bugImage: z.string().optional(),
    tone: z.enum(["light", "dark"]).default("light"),
  }),

  /** Subscribe / end card. */
  baseOverlay.extend({
    type: z.literal("end-card"),
    title: z.string(),
    subtitle: z.string().optional(),
    handle: z.string(),
  }),
]);

/* -------------------------------------------------------------------------- */
/* Audio                                                                       */
/* -------------------------------------------------------------------------- */

export const audioTrackSchema = z.object({
  id: z.string(),
  src: z.string(),
  role: z.enum(["vo", "music", "sfx", "clip-audio"]),
  start: z.number(),
  offset: z.number().default(0),
  /**
   * How much of the source to play from `offset`. Needed to interleave segments
   * of one clip's audio around narration — without it the clip keeps talking
   * underneath the VO.
   */
  duration: z.number().optional(),
  gainDb: z.number().default(0),
  /** Auto-duck under the VO track. Music should basically always be true. */
  duck: z.boolean().default(false),
  fadeIn: z.number().default(0),
  fadeOut: z.number().default(0),
});

/* -------------------------------------------------------------------------- */
/* Pacing                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * The barrage/hold model from ref 001. The planner emits these, and the clip
 * generator uses them to decide cut density. This is what stops the output from
 * feeling like a uniform 1-cut-per-second machine gun.
 */
export const energySegmentSchema = z.object({
  start: z.number(),
  end: z.number(),
  /** cuts per second target. Ref 001: 1.7 on hooks, 0.1 on the key argument. */
  energy: z.number(),
  label: z.enum(["cold-open", "hook", "build", "hold", "accent", "payoff", "outro"]),
});

/* -------------------------------------------------------------------------- */
/* Root                                                                        */
/* -------------------------------------------------------------------------- */

export const timelineSchema = z.object({
  version: z.literal(1),
  meta: z.object({
    title: z.string(),
    slug: z.string(),
    durationInSeconds: z.number(),
    fps: z.number().default(FPS),
  }),
  pacing: z.array(energySegmentSchema).default([]),
  clips: z.array(clipSchema),
  overlays: z.array(overlaySchema).default([]),
  captions: z.object({
    style: captionStyleSchema.default({}),
    cues: z.array(captionCueSchema),
  }),
  audio: z.array(audioTrackSchema),
});

export type Timeline = z.infer<typeof timelineSchema>;
export type Clip = z.infer<typeof clipSchema>;
export type Overlay = z.infer<typeof overlaySchema>;
export type CaptionCue = z.infer<typeof captionCueSchema>;
export type EnergySegment = z.infer<typeof energySegmentSchema>;
