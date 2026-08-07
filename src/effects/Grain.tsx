import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

/**
 * Animated film grain via an SVG turbulence filter.
 *
 * The seed is derived from the frame number so the grain moves, but stays
 * deterministic — critical, because Remotion may render frames out of order
 * across worker processes and anything non-deterministic will flicker.
 */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => {
  const frame = useCurrentFrame();
  const seed = frame % 12;
  const id = `grain-${seed}`;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity, mixBlendMode: "overlay" }}>
      <svg width="100%" height="100%">
        <filter id={id}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={3} seed={seed} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#${id})`} />
      </svg>
    </AbsoluteFill>
  );
};
