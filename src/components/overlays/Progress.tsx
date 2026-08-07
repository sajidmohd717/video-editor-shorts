import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "progress" }> & { durationInFrames: number };

/**
 * Progress indicator. A visible "how much is left" cue measurably reduces
 * mid-video drop-off on shorts — the viewer stops wondering whether to bail.
 * Span it across the whole video, not a segment.
 */
export const Progress: React.FC<Props> = ({ style, durationInFrames }) => {
  const frame = useCurrentFrame();
  const p = Math.min(1, frame / Math.max(1, durationInFrames));

  if (style === "dots") {
    const total = 5;
    return (
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 60 }}>
        <div style={{ display: "flex", gap: 14 }}>
          {Array.from({ length: total }, (_, i) => (
            <div
              key={i}
              style={{
                width: 54,
                height: 8,
                borderRadius: 4,
                background: p * total > i ? "#fff" : "rgba(255,255,255,0.28)",
              }}
            />
          ))}
        </div>
      </AbsoluteFill>
    );
  }

  if (style === "ring") {
    const r = 34;
    const c = 2 * Math.PI * r;
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg width={100} height={100} style={{ position: "absolute", top: 48, right: 44 }}>
          <circle cx={50} cy={50} r={r} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={7} />
          <circle
            cx={50}
            cy={50}
            r={r}
            fill="none"
            stroke="#fff"
            strokeWidth={7}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c * (1 - p)}
            transform="rotate(-90 50 50)"
          />
        </svg>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: `${p * 100}%`, background: "#FFE45C" }} />
    </AbsoluteFill>
  );
};
