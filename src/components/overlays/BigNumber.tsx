import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "big-number" }>;

/**
 * One enormous figure that counts up to itself.
 *
 * Built for the open, where the narration fires three numbers in six seconds
 * ("a hundred billion… three hundred billion… six hundred and thirty-eight
 * billion"). Holding a b-roll shot across all three wastes the most attentive
 * seconds of the video — a number that visibly climbs is the thing people stop
 * scrolling for (L19).
 *
 * The count is deliberately fast and front-loaded (ease-out): the figure should
 * arrive while the narrator is still saying it, then sit. A linear count that
 * finishes after the sentence has moved on reads as lag.
 */
export const BigNumber: React.FC<Props> = ({
  value,
  prefix,
  suffix,
  label,
  sub,
  accent,
  background,
  countSeconds,
  scale,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const raw = interpolate(t, [0, countSeconds], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Ease-out cubic — most of the distance covered early.
  const p = 1 - Math.pow(1 - raw, 3);
  const shown = value * p;

  const enter = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.7, stiffness: 170 },
    durationInFrames: 12,
  });

  // A rule that grows with the count gives the figure something to sit on and
  // makes the "arrival" legible even with the sound off.
  const ruleW = interpolate(p, [0, 1], [0, width * 0.26]);

  const decimals = value < 10 ? 1 : 0;
  const size = Math.min(width * 0.155, height * 0.28) * scale;

  return (
    <AbsoluteFill
      style={{
        background,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      {label ? (
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 600,
            fontSize: Math.min(width * 0.017, 34) * scale,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.42)",
            marginBottom: height * 0.03,
            opacity: enter,
          }}
        >
          {label}
        </div>
      ) : null}

      <div
        style={{
          fontFamily: "Poppins, sans-serif",
          fontWeight: 800,
          fontSize: size,
          lineHeight: 0.95,
          letterSpacing: "-0.045em",
          color: "#FFFFFF",
          // Tabular figures stop the number jittering horizontally as digits
          // change — without it the whole block twitches every frame.
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${0.92 + enter * 0.08})`,
          opacity: enter,
        }}
      >
        {prefix}
        {shown.toFixed(decimals)}
        {suffix}
      </div>

      <div
        style={{
          width: ruleW,
          height: Math.max(5, height * 0.007),
          background: accent,
          borderRadius: 4,
          marginTop: height * 0.045,
        }}
      />

      {sub ? (
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 500,
            fontSize: Math.min(width * 0.019, 38) * scale,
            color: "rgba(255,255,255,0.62)",
            marginTop: height * 0.04,
            opacity: interpolate(t, [countSeconds * 0.6, countSeconds * 0.6 + 0.5], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {sub}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
