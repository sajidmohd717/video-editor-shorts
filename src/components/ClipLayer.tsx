import React from "react";
import { AbsoluteFill, OffthreadVideo, interpolate, useCurrentFrame, staticFile } from "remotion";
import type { Clip } from "../timeline/schema";
import { buildFilterChain, needsGrainOverlay } from "../effects/filters";
import { Grain } from "../effects/Grain";

/**
 * Resolves the camera move to a transform for the current frame.
 *
 * The slow punch-in is the highest value-per-line effect in the system: it makes a
 * locked-off webcam feel like it's being operated. Scale ramps across the clip's own
 * duration and resets on every cut, which is what produces the "reset and push"
 * feel from reference 001.
 */
const useCameraTransform = (clip: Clip, localFrame: number, durationInFrames: number) => {
  const { kind, from, to, originX, originY } = clip.camera;
  const progress = durationInFrames <= 1 ? 0 : localFrame / (durationInFrames - 1);

  if (kind === "none") {
    return { transform: "none", transformOrigin: "50% 50%" };
  }

  if (kind === "shake") {
    // Deterministic pseudo-noise — must not use Math.random(), every frame has to be
    // reproducible or the render will strobe.
    const x = Math.sin(localFrame * 2.7) * 6 + Math.sin(localFrame * 6.1) * 3;
    const y = Math.cos(localFrame * 3.3) * 6 + Math.cos(localFrame * 7.7) * 3;
    return {
      transform: `scale(1.06) translate(${x}px, ${y}px)`,
      transformOrigin: "50% 50%",
    };
  }

  if (kind === "drift") {
    const dx = interpolate(progress, [0, 1], [-2.5, 2.5]);
    return {
      transform: `scale(${Math.max(from, to)}) translateX(${dx}%)`,
      transformOrigin: `${originX * 100}% ${originY * 100}%`,
    };
  }

  const scale = interpolate(progress, [0, 1], kind === "punch-out" ? [to, from] : [from, to]);
  return {
    transform: `scale(${scale})`,
    transformOrigin: `${originX * 100}% ${originY * 100}%`,
  };
};

const resolveSrc = (src: string) => {
  if (!src) return null;
  if (/^(https?:|data:|blob:)/.test(src)) return src;
  return staticFile(src);
};

/** A single video source rendered into a given box, cropped to fill. */
const SourceView: React.FC<{
  source: Clip["sources"][number];
  clip: Clip;
  localFrame: number;
  durationInFrames: number;
}> = ({ source, clip, localFrame, durationInFrames }) => {
  const camera = useCameraTransform(clip, localFrame, durationInFrames);
  const filter = buildFilterChain(clip.filters);
  const src = resolveSrc(source.src);

  const inner: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    ...camera,
    // Per-source manual nudge composes on top of the camera move.
    ...(source.panX || source.panY || source.scale !== 1
      ? {
          transform: `${camera.transform === "none" ? "" : camera.transform} translate(${
            source.panX * 100
          }%, ${source.panY * 100}%) scale(${source.scale})`,
        }
      : {}),
  };

  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden", filter, position: "relative" }}>
      {src ? (
        <OffthreadVideo
          src={src}
          startFrom={Math.round(source.offset * 30)}
          muted={source.muted}
          style={inner}
        />
      ) : (
        // Placeholder so a timeline can be previewed before assets exist.
        <div
          style={{
            ...inner,
            background: "linear-gradient(145deg,#1b2735 0%,#090a0f 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#3d4c60",
            fontFamily: "monospace",
            fontSize: 28,
          }}
        >
          {clip.id}
        </div>
      )}
      {needsGrainOverlay(clip.filters) ? <Grain /> : null}
    </div>
  );
};

export const ClipLayer: React.FC<{ clip: Clip; durationInFrames: number }> = ({
  clip,
  durationInFrames,
}) => {
  const localFrame = useCurrentFrame();
  const [a, b] = clip.sources;

  // Cross-dissolve is just an opacity ramp on the incoming clip — the outgoing clip
  // is still mounted underneath because the planner overlaps their time ranges.
  const dissolveFrames = Math.max(1, Math.round(clip.transitionDuration * 30));
  const opacity =
    clip.transitionIn === "dissolve"
      ? interpolate(localFrame, [0, dissolveFrames], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  const wrap = (children: React.ReactNode) => (
    <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>
  );

  if (clip.layout === "stacked" && a && b) {
    // Hard seam at y=960. Reference 001 hides it under the caption pill.
    return wrap(
      <AbsoluteFill style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ height: "50%", width: "100%" }}>
          <SourceView source={a} clip={clip} localFrame={localFrame} durationInFrames={durationInFrames} />
        </div>
        <div style={{ height: "50%", width: "100%" }}>
          <SourceView source={b} clip={clip} localFrame={localFrame} durationInFrames={durationInFrames} />
        </div>
      </AbsoluteFill>,
    );
  }

  if (clip.layout === "inset" && a && b) {
    return wrap(
      <AbsoluteFill>
        <SourceView source={a} clip={clip} localFrame={localFrame} durationInFrames={durationInFrames} />
        <div
          style={{
            position: "absolute",
            left: 56,
            bottom: 300,
            width: 380,
            height: 500,
            borderRadius: 24,
            overflow: "hidden",
            boxShadow: "0 24px 60px rgba(0,0,0,0.55)",
            border: "3px solid rgba(255,255,255,0.12)",
          }}
        >
          <SourceView source={b} clip={clip} localFrame={localFrame} durationInFrames={durationInFrames} />
        </div>
      </AbsoluteFill>,
    );
  }

  // "full" and "graphic" both render a single source; "graphic" simply expects the
  // overlay stack to own the frame.
  return wrap(
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {a ? (
        <SourceView source={a} clip={clip} localFrame={localFrame} durationInFrames={durationInFrames} />
      ) : null}
    </AbsoluteFill>,
  );
};
