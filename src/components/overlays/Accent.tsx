import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "accent" }>;

/** Emoji / arrow / sticker that punches in on a beat. Cheap energy. */
export const Accent: React.FC<Props> = ({ glyph, x, y, size, motion }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 9, mass: 0.4, stiffness: 220 },
    durationInFrames: 12,
  });

  const transforms: Record<Props["motion"], string> = {
    pop: `scale(${enter})`,
    "spin-in": `scale(${enter}) rotate(${(1 - enter) * 220}deg)`,
    bounce: `scale(${enter}) translateY(${Math.sin(frame * 0.35) * 14}px)`,
    wiggle: `scale(${enter}) rotate(${Math.sin(frame * 0.5) * 11}deg)`,
  };

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          fontSize: size,
          lineHeight: 1,
          transform: `translate(-50%,-50%) ${transforms[motion]}`,
          filter: "drop-shadow(0 10px 24px rgba(0,0,0,0.55))",
        }}
      >
        {glyph}
      </div>
    </AbsoluteFill>
  );
};
