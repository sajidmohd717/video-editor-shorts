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
  calculateMetadata: ({ props }: { props: Timeline }) => ({
    durationInFrames: Math.round(props.meta.durationInSeconds * props.meta.fps),
    fps: props.meta.fps,
  }),
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
