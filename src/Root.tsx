import { Composition } from "remotion";
import "./fonts";
import { Short } from "./Short";
import { timelineSchema, WIDTH, HEIGHT, FPS, type Timeline } from "./timeline/schema";
import demo from "./timeline/demo.json";
import newsDemo from "./timeline/news-update-demo.json";
import explainerDemo from "./timeline/explainer-demo.json";

/**
 * Two compositions, one component. They differ only in the timeline they're fed —
 * which is the point of the whole design. A new format is a new JSON file, not a
 * new renderer.
 *
 *   Short      — ref 001 style: fast-cut clip commentary
 *   NewsUpdate — ref 002 style: slow stills + narration, with ref 001's captions
 */
const common = {
  component: Short,
  schema: timelineSchema,
  width: WIDTH,
  height: HEIGHT,
  fps: FPS,
  /**
   * Parse props through the schema here, and return the PARSED object.
   *
   * Props arriving via `--props` are raw JSON — zod's `.default()` values are
   * never applied to them, so any field a planner omits reaches the component as
   * `undefined`. That fails silently and weirdly: a gradient built from
   * undefined colours is invalid CSS, so the browser drops the whole
   * declaration and the element renders as nothing at all.
   *
   * Parsing here means defaults apply however props arrive, so planners can omit
   * anything that has a sensible default.
   */
  calculateMetadata: ({ props }: { props: Timeline }) => {
    const parsed = timelineSchema.parse(props);
    return {
      durationInFrames: Math.round(parsed.meta.durationInSeconds * parsed.meta.fps),
      fps: parsed.meta.fps,
      props: parsed,
    };
  },
} as const;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        {...common}
        id="Short"
        defaultProps={timelineSchema.parse(demo)}
        durationInFrames={Math.round(demo.meta.durationInSeconds * FPS)}
      />
      <Composition
        {...common}
        id="NewsUpdate"
        defaultProps={timelineSchema.parse(newsDemo)}
        durationInFrames={Math.round(newsDemo.meta.durationInSeconds * FPS)}
      />
      <Composition
        {...common}
        id="Explainer"
        defaultProps={timelineSchema.parse(explainerDemo)}
        durationInFrames={Math.round(explainerDemo.meta.durationInSeconds * FPS)}
      />
    </>
  );
};
