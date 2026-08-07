import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "date-card" }>;

/**
 * Chronology marker (L7). A date, serif, on black.
 *
 * Deliberately the plainest thing in the video. Its value is the contrast — after
 * a run of news footage and documents, a bare date on black reads as a chapter
 * heading without needing to say "chapter". Any styling beyond a fade and a
 * slight drift starts competing with the footage either side of it.
 */
export const DateCard: React.FC<Props> = ({ text, sub, color, size, align }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 20, mass: 0.8, stiffness: 90 },
    durationInFrames: 18,
  });

  // A very slow rise. Enough to be alive, not enough to read as an animation.
  const drift = interpolate(frame, [0, 90], [8, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "#000",
        justifyContent: "center",
        alignItems: align === "center" ? "center" : "flex-start",
        paddingLeft: align === "center" ? 0 : 110,
        textAlign: align,
      }}
    >
      <div style={{ opacity: enter, transform: `translateY(${drift}px)` }}>
        <div
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontStyle: "italic",
            fontWeight: 400,
            fontSize: size,
            lineHeight: 1.1,
            color,
            letterSpacing: "0.01em",
          }}
        >
          {text}
        </div>
        {sub ? (
          <div
            style={{
              marginTop: 18,
              fontFamily: "Poppins, sans-serif",
              fontWeight: 600,
              fontSize: size * 0.28,
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.62)",
            }}
          >
            {sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
