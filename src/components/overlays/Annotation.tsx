import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";
import { WIDTH, HEIGHT } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "annotation" }>;

/**
 * Display-serif label + curved arrow that draws itself toward a target.
 *
 * Ref 003 uses this over a light "explainer canvas". The register matters: a caption
 * is the narrator talking, but an arrow is someone *marking up* the thing on screen.
 * It implies explanation, which is exactly the promise this format makes.
 */
export const Annotation: React.FC<Props> = ({
  label,
  labelX,
  labelY,
  targetX,
  targetY,
  curve,
  color,
  labelSize,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const labelEnter = spring({
    frame,
    fps,
    config: { damping: 15, mass: 0.6, stiffness: 150 },
    durationInFrames: 10,
  });

  // The arrow starts drawing once the label has landed.
  const draw = interpolate(frame, [6, 6 + 0.45 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const x2 = targetX * WIDTH;
  const y2 = targetY * HEIGHT;

  // Start below the label's baseline rather than at its centre, so the stroke never
  // runs through the text, then pull the origin slightly toward the target.
  const anchorX = labelX * WIDTH;
  const anchorY = labelY * HEIGHT + labelSize * 0.55;
  const toTarget = Math.hypot(x2 - anchorX, y2 - anchorY) || 1;
  const x1 = anchorX + ((x2 - anchorX) / toTarget) * 40;
  const y1 = anchorY + ((y2 - anchorY) / toTarget) * 40;

  // Control point offset along the PERPENDICULAR of the chord — that's what makes the
  // arc bow out to one side. Offsetting along an axis instead (the obvious-looking
  // approach) bends it back across the label.
  const dx = x2 - x1;
  const dy = y2 - y1;
  const chord = Math.hypot(dx, dy) || 1;
  const bulge = (curve === "left" ? -1 : 1) * chord * 0.42;
  const cx = (x1 + x2) / 2 + (-dy / chord) * bulge;
  const cy = (y1 + y2) / 2 + (dx / chord) * bulge;

  const path = `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
  // Rough arc length is good enough to drive a dash-offset draw.
  const len = Math.hypot(cx - x1, cy - y1) + Math.hypot(x2 - cx, y2 - cy);

  const angle = (Math.atan2(y2 - cy, x2 - cx) * 180) / Math.PI;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
        <path
          d={path}
          fill="none"
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={len}
          strokeDashoffset={len * (1 - draw)}
        />
        {draw > 0.94 ? (
          <polygon
            points="0,-17 34,0 0,17"
            fill={color}
            transform={`translate(${x2},${y2}) rotate(${angle})`}
          />
        ) : null}
      </svg>

      <div
        style={{
          position: "absolute",
          left: `${labelX * 100}%`,
          top: `${labelY * 100}%`,
          transform: `translate(-50%,-50%) scale(${0.9 + labelEnter * 0.1})`,
          opacity: labelEnter,
          fontFamily: "'Playfair Display', Georgia, serif",
          fontWeight: 900,
          fontSize: labelSize,
          lineHeight: 1,
          whiteSpace: "nowrap",
          // Metallic-ish gradient fill, matching ref 003's display labels. The sans
          // captions stay flat white — the contrast between the two is the system.
          background: "linear-gradient(175deg,#3A3A3E 0%,#8A8A92 45%,#2B2B30 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          filter: "drop-shadow(0 3px 2px rgba(0,0,0,0.28))",
        }}
      >
        {label}
      </div>
    </AbsoluteFill>
  );
};
