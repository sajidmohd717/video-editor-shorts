import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "entity-graph" }>;

/**
 * Directed money graph: named companies as nodes, flows as labelled arrows.
 *
 * Built one element at a time. A graph that appears complete is a picture; a
 * graph that assembles is an argument, and the viewer can follow it because each
 * step lands while the narration is saying that step (L16).
 *
 * Everything derives from `useCurrentFrame()` — no simulation, no randomness, so
 * frames rendered out of order across workers agree.
 */
export const EntityGraph: React.FC<Props> = ({
  title,
  nodes,
  edges,
  accent,
  background,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  // Circles must stay circles: radius is a fraction of the SHORTER edge, or a
  // node drawn as a fraction of width turns into an ellipse in landscape.
  const unit = Math.min(width, height);

  return (
    <AbsoluteFill style={{ background }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <marker
            id="eg-arrow-out"
            markerWidth={7}
            markerHeight={7}
            refX={5.6}
            refY={3.5}
            orient="auto"
          >
            <path d="M0,0 L7,3.5 L0,7 Z" fill={accent} />
          </marker>
          <marker
            id="eg-arrow-back"
            markerWidth={7}
            markerHeight={7}
            refX={5.6}
            refY={3.5}
            orient="auto"
          >
            <path d="M0,0 L7,3.5 L0,7 Z" fill="#EDEDF2" />
          </marker>
        </defs>

        {edges.map((e, i) => {
          const a = byId[e.from];
          const b = byId[e.to];
          if (!a || !b) return null;

          const draw = interpolate(t, [e.at, e.at + 0.75], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          if (draw <= 0) return null;

          const ax = a.x * width;
          const ay = a.y * height;
          const bx = b.x * width;
          const by = b.y * height;

          // Stop the arrow at each circle's edge rather than its centre, so the
          // head sits against the node instead of buried under the label.
          const dx = bx - ax;
          const dy = by - ay;
          const len = Math.hypot(dx, dy) || 1;
          const ar = a.r * unit;
          const br = b.r * unit;
          const x1 = ax + (dx / len) * (ar + 6);
          const y1 = ay + (dy / len) * (ar + 6);
          const x2 = bx - (dx / len) * (br + 14);
          const y2 = by - (dy / len) * (br + 14);

          // Perpendicular control point — offsetting along an axis bows the arc
          // back across the label instead of out from it.
          const bulge = (e.curve === "left" ? -1 : 1) * len * 0.22;
          const cx = (x1 + x2) / 2 + (-(y2 - y1) / len) * bulge;
          const cy = (y1 + y2) / 2 + ((x2 - x1) / len) * bulge;

          const path = `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
          const approx = Math.hypot(cx - x1, cy - y1) + Math.hypot(x2 - cx, y2 - cy);
          // The money coming BACK is the whole argument, so it reads as a second
          // strong colour rather than a muted one — distinct from the outbound
          // flow, but never quieter than it.
          const stroke = e.tone === "back" ? "#EDEDF2" : accent;

          // Label rides the arc's midpoint (t=0.5 on the quadratic).
          const mx = 0.25 * x1 + 0.5 * cx + 0.25 * x2;
          const my = 0.25 * y1 + 0.5 * cy + 0.25 * y2;
          const labelIn = interpolate(t, [e.at + 0.45, e.at + 0.95], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <g key={`e${i}`}>
              <path
                d={path}
                fill="none"
                stroke={stroke}
                strokeWidth={e.tone === "back" ? 3.5 : 4.5}
                strokeLinecap="round"
                strokeDasharray={approx}
                strokeDashoffset={approx * (1 - draw)}
                markerEnd={draw > 0.985
                  ? `url(#eg-arrow-${e.tone === "back" ? "back" : "out"})`
                  : undefined}
              />
              {e.label && labelIn > 0 ? (
                <g opacity={labelIn}>
                  <rect
                    x={mx - e.label.length * 5.6 - 10}
                    y={my - 17}
                    width={e.label.length * 11.2 + 20}
                    height={34}
                    rx={17}
                    fill={background}
                    stroke={stroke}
                    strokeWidth={1.5}
                  />
                  <text
                    x={mx}
                    y={my + 6}
                    textAnchor="middle"
                    fill={stroke}
                    style={{
                      fontFamily: "Poppins, sans-serif",
                      fontWeight: 700,
                      fontSize: 19,
                      letterSpacing: "0.02em",
                    }}
                  >
                    {e.label}
                  </text>
                </g>
              ) : null}
            </g>
          );
        })}

        {nodes.map((n) => {
          const enter = spring({
            frame: frame - Math.round(n.at * fps),
            fps,
            config: { damping: 13, mass: 0.7, stiffness: 150 },
            durationInFrames: 14,
          });
          if (enter <= 0.001) return null;
          const r = n.r * unit * enter;
          const fill =
            n.tone === "accent" ? accent : n.tone === "muted" ? "#2A2A32" : "#F2F2F4";
          const fg = n.tone === "dark" ? "#0B0B0F" : "#FFFFFF";
          // Long names would overflow the circle at a fixed size.
          const size = Math.min(r * 0.44, (r * 1.7) / Math.max(4, n.label.length) * 2.1);
          return (
            <g key={n.id} opacity={Math.min(1, enter * 1.5)}>
              <circle cx={n.x * width} cy={n.y * height} r={r} fill={fill} />
              <text
                x={n.x * width}
                y={n.y * height + size * 0.35}
                textAnchor="middle"
                fill={fg}
                style={{
                  fontFamily: "Poppins, sans-serif",
                  fontWeight: 700,
                  fontSize: size,
                  letterSpacing: "-0.02em",
                }}
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>

      {title ? (
        <div
          style={{
            position: "absolute",
            top: height * 0.07,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: "Poppins, sans-serif",
            fontWeight: 600,
            fontSize: 30,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.5)",
            opacity: interpolate(t, [0, 0.5], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {title}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
