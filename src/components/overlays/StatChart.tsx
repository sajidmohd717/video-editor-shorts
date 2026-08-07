import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "stat-chart" }>;

const W = 900;
const H = 520;

/**
 * Animated area chart with a ticking value counter.
 *
 * Ref 003 reaches for this whenever the VO says "a number went up", which for a
 * business/tech channel is a large share of all claims. The counter matters as much
 * as the line — a number that visibly climbs is what people screenshot.
 */
export const StatChart: React.FC<Props> = ({
  title,
  series,
  valueFrom,
  valueTo,
  valueSuffix,
  drawDuration,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const p = interpolate(frame, [0, drawDuration * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pts = series.length > 1 ? series : [0, 1];
  const coords = pts.map((v, i) => ({
    x: (i / (pts.length - 1)) * W,
    y: H - v * H,
  }));

  // Clip the drawn area horizontally so the line reveals left-to-right.
  const clipW = p * W;
  const line = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
  const area = `${line} L ${W} ${H} L 0 ${H} Z`;

  const value = valueFrom + (valueTo - valueFrom) * p;
  const decimals = Math.abs(valueTo - valueFrom) < 10 ? 1 : 0;

  return (
    <AbsoluteFill
      style={{
        background: "#E9E9EC",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 70px",
      }}
    >
      <div style={{ width: "100%" }}>
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 500,
            fontSize: 34,
            color: "#4B5563",
            marginBottom: 8,
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 800,
            fontSize: 132,
            lineHeight: 1.05,
            color: "#0B0B0F",
            letterSpacing: "-0.04em",
            marginBottom: 18,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value.toFixed(decimals)}
          {valueSuffix}
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: "block", overflow: "visible" }}>
          <defs>
            <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity={0.55} />
              <stop offset="100%" stopColor={accent} stopOpacity={0.04} />
            </linearGradient>
            <clipPath id="reveal">
              <rect x={0} y={-40} width={clipW} height={H + 80} />
            </clipPath>
          </defs>

          {[0, 0.25, 0.5, 0.75, 1].map((g) => (
            <line
              key={g}
              x1={0}
              x2={W}
              y1={g * H}
              y2={g * H}
              stroke="#CBCBD2"
              strokeWidth={1.5}
            />
          ))}

          <g clipPath="url(#reveal)">
            <path d={area} fill="url(#fill)" />
            <path d={line} fill="none" stroke={accent} strokeWidth={7} strokeLinejoin="round" />
          </g>

          {p > 0.02 ? (
            <circle
              cx={clipW}
              cy={
                // Interpolate the y position along the polyline at the reveal edge.
                (() => {
                  const t = p * (pts.length - 1);
                  const i = Math.min(pts.length - 2, Math.floor(t));
                  const f = t - i;
                  return coords[i].y + (coords[i + 1].y - coords[i].y) * f;
                })()
              }
              r={14}
              fill={accent}
              stroke="#fff"
              strokeWidth={5}
            />
          ) : null}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
