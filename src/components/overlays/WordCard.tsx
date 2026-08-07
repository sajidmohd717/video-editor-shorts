import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "word-card" }>;

/**
 * Full-screen typographic word card.
 *
 * Ref 003 fires four of these in the first five seconds, each in a deliberately
 * different typeface. The mismatch is the effect — it reads as urgent and assembled
 * rather than as a designed title sequence.
 */
const FACES: Record<Props["face"], React.CSSProperties> = {
  "serif-display": {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontWeight: 900,
    letterSpacing: "-0.02em",
  },
  "sans-heavy": {
    fontFamily: "Poppins, sans-serif",
    fontWeight: 800,
    letterSpacing: "-0.035em",
  },
  "serif-light": {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontWeight: 400,
    fontStyle: "italic",
    letterSpacing: "0",
  },
  "script-accent": {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontWeight: 700,
    fontStyle: "italic",
    letterSpacing: "-0.01em",
  },
};

export const WordCard: React.FC<Props> = ({ text, face, size, color, background }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.45, stiffness: 210 },
    durationInFrames: 8,
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 70px",
        background: background ?? "transparent",
      }}
    >
      <div
        style={{
          ...FACES[face],
          fontSize: size,
          lineHeight: 1.02,
          color,
          textAlign: "center",
          opacity: Math.min(1, enter * 1.6),
          transform: `scale(${0.88 + enter * 0.12})`,
          textShadow: background ? "none" : "0 8px 40px rgba(0,0,0,0.55)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
