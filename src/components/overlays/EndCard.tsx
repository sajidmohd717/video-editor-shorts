import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "end-card" }>;

/** Subscribe driver. Held ~3s at the tail, per reference 001. */
export const EndCard: React.FC<Props> = ({ title, subtitle, handle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 120 }, durationInFrames: 14 });

  return (
    <AbsoluteFill
      style={{
        background: "#08080A",
        justifyContent: "center",
        alignItems: "center",
        gap: 28,
        opacity: enter,
      }}
    >
      <div
        style={{
          fontFamily: "Poppins, sans-serif",
          fontWeight: 800,
          fontSize: 96,
          color: "#FFD400",
          textAlign: "center",
          lineHeight: 1.02,
          letterSpacing: "-0.03em",
          transform: `translateY(${(1 - enter) * 30}px)`,
        }}
      >
        {title}
      </div>
      {subtitle ? (
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 600,
            fontSize: 42,
            color: "#fff",
            textAlign: "center",
            letterSpacing: "0.04em",
          }}
        >
          {subtitle}
        </div>
      ) : null}
      <div
        style={{
          marginTop: 40,
          display: "flex",
          alignItems: "center",
          gap: 16,
          background: "#FF0033",
          borderRadius: 999,
          padding: "18px 44px",
          fontFamily: "Poppins, sans-serif",
          fontWeight: 700,
          fontSize: 40,
          color: "#fff",
        }}
      >
        ▶ {handle}
      </div>
    </AbsoluteFill>
  );
};
