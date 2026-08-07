import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "cta" }>;

/**
 * Mid-roll subscribe pill.
 *
 * Ref 003 fires this around 19-21s and again at 47-50s — not just as an end card.
 * A mid-video CTA reaches the people who will never see the last frame, which on
 * shorts is most of them.
 */
export const Cta: React.FC<Props> = ({ text, x, y, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 11, mass: 0.45, stiffness: 200 },
    durationInFrames: 10,
  });

  // A small persistent pulse keeps it alive without being obnoxious.
  const pulse = 1 + Math.sin(frame * 0.22) * 0.025;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          transform: `translate(-50%,-50%) scale(${enter * pulse})`,
          background: color,
          color: "#fff",
          fontFamily: "Poppins, sans-serif",
          fontWeight: 700,
          fontSize: 34,
          letterSpacing: "0.06em",
          padding: "16px 38px",
          borderRadius: 10,
          boxShadow: "0 14px 40px rgba(0,0,0,0.45)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
