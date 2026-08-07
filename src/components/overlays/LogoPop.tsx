import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "logo-pop" }> & { durationInFrames: number };

/**
 * Logo that springs in on a beat, normally paired with a sound effect.
 *
 * The spring is deliberately under-damped so it overshoots and settles — that
 * overshoot is what makes it read as an *impact* rather than a fade-in, and it's
 * what a sound effect can land against. A critically-damped entrance timed to
 * the same sample sounds late even when it isn't.
 */
export const LogoPop: React.FC<Props> = ({
  src,
  x,
  y,
  size,
  tint,
  entrance,
  glow,
  exit,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    // Low damping = overshoot. See the note above; this is the whole effect.
    config: { damping: 9, mass: 0.5, stiffness: 220 },
    durationInFrames: 14,
  });

  // Scale back down just before the cut so it leaves deliberately.
  const exitFrames = Math.round(exit * fps);
  const out =
    exitFrames > 0
      ? interpolate(frame, [durationInFrames - exitFrames, durationInFrames], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  const scale = enter * out;

  const transforms: Record<Props["entrance"], string> = {
    pop: `scale(${scale})`,
    drop: `translateY(${(1 - enter) * -160}px) scale(${scale})`,
    spin: `scale(${scale}) rotate(${(1 - enter) * -180}deg)`,
  };

  const resolved = /^(https?:|data:)/.test(src) ? src : staticFile(src);

  // The bloom peaks on impact and decays fast — it reads as the light the
  // "landing" throws, so it must not linger.
  const bloom = interpolate(frame, [0, 5, 16], [0, 0.55, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          transform: `translate(-50%,-50%) ${transforms[entrance]}`,
          width: size,
          height: size,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {glow ? (
          <div
            style={{
              position: "absolute",
              inset: "-18%",
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(255,255,255,0.85) 0%, rgba(255,255,255,0) 68%)",
              opacity: bloom * out,
            }}
          />
        ) : null}

        <Img
          src={resolved}
          style={{
            position: "relative",
            width: "100%",
            height: "100%",
            objectFit: "contain",
            // brightness(0) flattens the mark to black whatever its source
            // colours, then invert(1) makes it white — works on any logo file
            // without editing the asset.
            filter:
              tint === "white"
                ? "brightness(0) invert(1) drop-shadow(0 6px 22px rgba(0,0,0,0.55))"
                : "drop-shadow(0 6px 22px rgba(0,0,0,0.45))",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
