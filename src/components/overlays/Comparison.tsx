import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "comparison" }>;

/**
 * Before → after, stacked, with the "after" value slamming in on a delay.
 *
 * The delay is the whole point: the viewer reads the old number, forms an
 * expectation, and then the new one lands against it. Showing both at once
 * throws that away and it just becomes a table.
 */
export const Comparison: React.FC<Props> = ({
  beforeLabel,
  beforeValue,
  afterLabel,
  afterValue,
  afterDelay,
  accent,
  tone,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const dark = tone === "dark";
  const fg = dark ? "#FFFFFF" : "#0B0B0F";
  const muted = dark ? "rgba(255,255,255,0.55)" : "#6B7280";

  const enterBefore = spring({
    frame,
    fps,
    config: { damping: 16, mass: 0.6, stiffness: 160 },
    durationInFrames: 10,
  });

  const delayFrames = Math.round(afterDelay * fps);
  const enterAfter = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 10, mass: 0.5, stiffness: 230 },
    durationInFrames: 12,
  });

  // The old value dims once it's been superseded.
  const fade = interpolate(frame, [delayFrames, delayFrames + 8], [1, 0.32], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const label: React.CSSProperties = {
    fontFamily: "Poppins, sans-serif",
    fontWeight: 600,
    fontSize: 30,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: muted,
    marginBottom: 10,
  };

  const value: React.CSSProperties = {
    fontFamily: "Poppins, sans-serif",
    fontWeight: 800,
    fontSize: 138,
    lineHeight: 1,
    letterSpacing: "-0.045em",
  };

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "flex-start", padding: "0 78px" }}
    >
      <div style={{ opacity: enterBefore * fade, transform: `translateY(${(1 - enterBefore) * 24}px)` }}>
        <div style={label}>{beforeLabel}</div>
        <div style={{ ...value, color: fg, textDecoration: frame > delayFrames ? "line-through" : "none" }}>
          {beforeValue}
        </div>
      </div>

      <div
        style={{
          width: 96,
          height: 8,
          background: accent,
          borderRadius: 4,
          margin: "44px 0",
          transform: `scaleX(${enterAfter})`,
          transformOrigin: "0% 50%",
        }}
      />

      <div
        style={{
          opacity: Math.min(1, enterAfter * 1.4),
          transform: `translateY(${(1 - enterAfter) * 40}px) scale(${0.86 + enterAfter * 0.14})`,
          transformOrigin: "0% 50%",
        }}
      >
        <div style={{ ...label, color: accent }}>{afterLabel}</div>
        <div style={{ ...value, color: accent, fontSize: 168 }}>{afterValue}</div>
      </div>
    </AbsoluteFill>
  );
};
