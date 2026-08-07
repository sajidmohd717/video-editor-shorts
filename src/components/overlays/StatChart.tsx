import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "stat-chart" }>;

/**
 * Animated area chart with a ticking value counter.
 *
 * Ref 003 reaches for this whenever the VO says "a number went up", which for a
 * business/tech channel is a large share of all claims. The counter matters as much
 * as the line — a number that visibly climbs is what people screenshot.
 *
 * The plot box is measured from the canvas rather than fixed. A fixed viewBox
 * rendered at `width: 100%` scales its HEIGHT with the frame's width, so the
 * same chart that fits in 9:16 grows a 1028px-tall plot in 16:9 and pushes the
 * title and counter off the top of the frame.
 */
export const StatChart: React.FC<Props> = ({
  title,
  series,
  valueFrom,
  valueTo,
  valueSuffix,
  valuePrefix,
  drawDuration,
  accent,
}) => {
  const frame = useCurrentFrame();
  const { fps, width: CW, height: CH } = useVideoConfig();

  const wide = CW > CH;
  const padX = wide ? 120 : 70;
  const titleSize = wide ? 30 : 34;
  const valueSize = wide ? 108 : 132;
  // Keep the plot clear of the caption band rather than letting the line run
  // behind the words.
  const headerH = titleSize + 8 + valueSize * 1.05 + 18;
  const padTop = wide ? 96 : 0;
  // Measured against a rendered frame, not guessed: the caption block's top edge
  // sits around 0.66 of the frame height, so the plot floor has to clear that.
  const padBottom = wide ? CH * 0.36 : 0;

  const W = CW - padX * 2;
  const H = wide ? CH - headerH - padTop - padBottom : 520;

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
        justifyContent: wide ? "flex-start" : "center",
        alignItems: "center",
        padding: wide ? `${padTop}px ${padX}px 0` : `0 ${padX}px`,
      }}
    >
      <div style={{ width: "100%" }}>
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 500,
            fontSize: titleSize,
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
            fontSize: valueSize,
            lineHeight: 1.05,
            color: "#0B0B0F",
            letterSpacing: "-0.04em",
            marginBottom: 18,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {valuePrefix}
          {value.toFixed(decimals)}
          {valueSuffix}
        </div>

        <svg
          viewBox={`0 0 ${W} ${H}`}
          width={W}
          height={H}
          style={{ display: "block", overflow: "visible" }}
        >
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
