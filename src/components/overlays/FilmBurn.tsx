import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "film-burn" }> & { durationInFrames: number };

/**
 * Film-burn / light-leak transition, generated rather than composited from a
 * stock clip — deterministic, recolourable, and no licence to worry about.
 *
 * What makes it read as film rather than as a flash:
 *  - asymmetric envelope. Real leaks bloom fast and decay slow; a symmetric
 *    fade in/out looks like a dissolve.
 *  - three colour zones. A single orange gradient looks like a filter; film has
 *    a hot near-white core, an amber body, and a scorched red edge.
 *  - the bloom scales up as it decays, so the leak spreads while dying instead
 *    of shrinking back to its origin.
 *  - animated grain inside the burn, seeded from the frame so it stays
 *    deterministic across Remotion's out-of-order workers.
 */
export const FilmBurn: React.FC<Props> = ({
  originX,
  originY,
  intensity,
  hot,
  mid,
  edge,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const p = durationInFrames <= 1 ? 0 : frame / durationInFrames;

  // Fast attack, slow decay — peaks at ~28% through the window.
  const env =
    p < 0.28
      ? interpolate(p, [0, 0.28], [0, 1])
      : interpolate(p, [0.28, 1], [1, 0], { extrapolateRight: "clamp" });
  const eased = Math.pow(Math.max(0, env), 1.35) * intensity;

  // Spreads as it decays.
  const spread = interpolate(p, [0, 1], [55, 165]);
  const cx = originX * 100;
  const cy = originY * 100;

  const seed = frame % 10;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Body of the leak.
          NB: `ellipse X% Y%`, not `circle X%` — percentage sizes are invalid for
          `circle` in radial-gradient, and the browser drops the whole gradient
          silently rather than erroring. Costs an hour if you don't know it.
          The vertical radius is larger so the leak elongates down the 9:16
          frame instead of reading as a perfect disc. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse ${spread}% ${spread * 1.35}% at ${cx}% ${cy}%,
            ${hot} 0%, ${mid} 26%, ${edge} 52%, rgba(0,0,0,0) 74%)`,
          mixBlendMode: "screen",
          opacity: eased,
        }}
      />

      {/* Hot core, tighter and shorter-lived than the body */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse ${spread * 0.42}% ${spread * 0.56}% at ${cx}% ${cy}%,
            #FFFFFF 0%, ${hot} 38%, rgba(0,0,0,0) 70%)`,
          mixBlendMode: "screen",
          opacity: Math.pow(eased, 2.1) * 0.9,
        }}
      />

      {/* Warm lift across the whole frame — the leak spills light everywhere,
          not only where it's bright. */}
      <AbsoluteFill
        style={{
          background: mid,
          mixBlendMode: "soft-light",
          opacity: eased * 0.4,
        }}
      />

      {/* Grain, confined to the burn so clean frames stay clean */}
      <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: eased * 0.35 }}>
        <svg width="100%" height="100%">
          <filter id={`burn-grain-${seed}`}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.6"
              numOctaves={2}
              seed={seed}
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#burn-grain-${seed})`} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
