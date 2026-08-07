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
  const { fps, width, height } = useVideoConfig();

  // Stacked reads well in 9:16, where vertical space is what there is. In 16:9
  // the same stack leaves the right half of the frame empty and shrinks both
  // numbers to fit the height — so landscape puts the two sides side by side
  // and lets the rule between them do the "versus".
  const wide = width > height;

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
    fontSize: wide ? 26 : 30,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: muted,
    marginBottom: 10,
  };

  const value: React.CSSProperties = {
    fontFamily: "Poppins, sans-serif",
    fontWeight: 800,
    fontSize: wide ? 112 : 138,
    lineHeight: 1,
    letterSpacing: "-0.045em",
  };

  // Landscape slides in from the left and grows; portrait rises and grows. Same
  // spring, different axis — the motion should follow the layout.
  const afterShift = wide
    ? `translateX(${(1 - enterAfter) * -40}px)`
    : `translateY(${(1 - enterAfter) * 40}px)`;

  return (
    <AbsoluteFill
      style={{
        flexDirection: wide ? "row" : "column",
        justifyContent: "center",
        alignItems: wide ? "center" : "flex-start",
        padding: wide ? "0 110px" : "0 78px",
        gap: wide ? 0 : undefined,
      }}
    >
      <div
        style={{
          flex: wide ? 1 : undefined,
          opacity: enterBefore * fade,
          transform: `translateY(${(1 - enterBefore) * 24}px)`,
        }}
      >
        <div style={label}>{beforeLabel}</div>
        <div style={{ ...value, color: fg, textDecoration: frame > delayFrames ? "line-through" : "none" }}>
          {beforeValue}
        </div>
      </div>

      <div
        style={{
          width: wide ? 8 : 96,
          height: wide ? 220 : 8,
          flexShrink: 0,
          background: accent,
          borderRadius: 4,
          margin: wide ? "0 82px" : "44px 0",
          transform: wide ? `scaleY(${enterAfter})` : `scaleX(${enterAfter})`,
          transformOrigin: wide ? "50% 0%" : "0% 50%",
        }}
      />

      <div
        style={{
          flex: wide ? 1 : undefined,
          opacity: Math.min(1, enterAfter * 1.4),
          transform: `${afterShift} scale(${0.86 + enterAfter * 0.14})`,
          transformOrigin: "0% 50%",
        }}
      >
        <div style={{ ...label, color: accent }}>{afterLabel}</div>
        <div style={{ ...value, color: accent, fontSize: wide ? 138 : 168 }}>{afterValue}</div>
      </div>
    </AbsoluteFill>
  );
};
