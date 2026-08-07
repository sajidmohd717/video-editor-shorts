import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "image-card" }> & { durationInFrames: number };

/**
 * Full-bleed image punchline — AI portraits, screenshots, memes.
 *
 * Reference 001's single best gag is rendering the subject as a doctor and as a
 * lawyer to literalise a hypothetical. Any abstract noun in a script is a candidate
 * for one of these, and they cost one image generation each.
 */
export const ImageCard: React.FC<Props> = ({ src, fit, entrance, caption, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 15, mass: 0.6, stiffness: 170 },
    durationInFrames: 10,
  });

  // A slow drift across the hold keeps a still image from feeling like a freeze.
  const drift = interpolate(frame, [0, Math.max(1, durationInFrames)], [1.0, 1.07]);

  const transforms: Record<Props["entrance"], string> = {
    snap: `scale(${enter < 0.5 ? 1.04 : drift})`,
    "slide-up": `translateY(${(1 - enter) * 100}%) scale(${drift})`,
    "scale-in": `scale(${(0.82 + enter * 0.18) * drift})`,
    "tilt-drop": `rotate(${(1 - enter) * -7}deg) translateY(${(1 - enter) * -80}px) scale(${drift})`,
  };

  const resolved = /^(https?:|data:)/.test(src) ? src : staticFile(src);

  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <Img
        src={resolved}
        style={{
          width: "100%",
          height: "100%",
          objectFit: fit,
          opacity: enter,
          transform: transforms[entrance],
        }}
      />
      {caption ? (
        <div
          style={{
            position: "absolute",
            bottom: 220,
            width: "100%",
            textAlign: "center",
            fontFamily: "Poppins, sans-serif",
            fontWeight: 700,
            fontSize: 54,
            color: "#fff",
            textShadow: "0 6px 26px rgba(0,0,0,0.85)",
            opacity: enter,
          }}
        >
          {caption}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
