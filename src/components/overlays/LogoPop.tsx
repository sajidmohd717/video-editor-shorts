import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "logo-pop" }> & { durationInFrames: number };

/**
 * Logo that springs in on a beat, normally paired with a sound effect.
 *
 * The spring is deliberately under-damped so it overshoots and settles — that
 * overshoot is what makes it read as an *impact* rather than a fade-in, and it's
 * what a sound effect can land against. A critically-damped entrance timed to
 * the same sample sounds late even when it isn't.
 */
export const LogoPop: React.FC<Props> = ({
  src,
  x,
  y,
  size,
  tint,
  shape,
  caption,
  role,
  roleColor,
  entrance,
  glow,
  exit,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    // Low damping = overshoot. See the note above; this is the whole effect.
    config: { damping: 9, mass: 0.5, stiffness: 220 },
    durationInFrames: 14,
  });

  // Scale back down just before the cut so it leaves deliberately.
  const exitFrames = Math.round(exit * fps);
  const out =
    exitFrames > 0
      ? interpolate(frame, [durationInFrames - exitFrames, durationInFrames], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  const scale = enter * out;

  const transforms: Record<Props["entrance"], string> = {
    pop: `scale(${scale})`,
    drop: `translateY(${(1 - enter) * -160}px) scale(${scale})`,
    spin: `scale(${scale}) rotate(${(1 - enter) * -180}deg)`,
  };

  const resolved = /^(https?:|data:)/.test(src) ? src : staticFile(src);

  // The bloom peaks on impact and decays fast — it reads as the light the
  // "landing" throws, so it must not linger.
  const bloom = interpolate(frame, [0, 5, 16], [0, 0.55, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          transform: `translate(-50%,-50%) ${transforms[entrance]}`,
          width: size,
          height: size,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {glow ? (
          <div
            style={{
              position: "absolute",
              inset: "-18%",
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(255,255,255,0.85) 0%, rgba(255,255,255,0) 68%)",
              opacity: bloom * out,
            }}
          />
        ) : null}

        <Img
          src={resolved}
          style={{
            position: "relative",
            width: "100%",
            height: "100%",
            // A circular badge must COVER, not contain — contain would letterbox
            // a portrait inside the circle.
            objectFit: shape === "circle" ? "cover" : "contain",
            borderRadius: shape === "circle" ? "50%" : 0,
            border: shape === "circle" ? "5px solid rgba(255,255,255,0.92)" : "none",
            // brightness(0) flattens the mark to black whatever its source
            // colours, then invert(1) makes it white — works on any logo file
            // without editing the asset. Never do this to a photograph.
            filter:
              tint === "white"
                ? "brightness(0) invert(1) drop-shadow(0 6px 22px rgba(0,0,0,0.55))"
                : "drop-shadow(0 8px 26px rgba(0,0,0,0.55))",
          }}
        />

        {caption || role ? (
          <div
            style={{
              position: "absolute",
              top: "104%",
              left: "50%",
              transform: "translateX(-50%)",
              whiteSpace: "nowrap",
              textAlign: "center",
              fontFamily: "Poppins, sans-serif",
              textShadow: "0 4px 18px rgba(0,0,0,0.85)",
              opacity: Math.min(1, enter * 1.2) * out,
            }}
          >
            {caption ? (
              <div
                style={{
                  fontWeight: 700,
                  fontSize: Math.max(26, size * 0.13),
                  letterSpacing: "0.02em",
                  color: "#fff",
                  lineHeight: 1.1,
                }}
              >
                {caption}
              </div>
            ) : null}
            {role ? (
              // Smaller and wider-tracked than the name — reads as a subtitle
              // rather than competing with it. Lands a beat later so the eye
              // takes the name first.
              <div
                style={{
                  marginTop: 5,
                  fontWeight: 700,
                  // Big enough to read on a phone at arm's length. The earlier
                  // 0.088 factor produced ~23px, which is legible on a desktop
                  // preview and invisible on the device this is watched on.
                  fontSize: Math.max(26, size * 0.115),
                  letterSpacing: "0.06em",
                  color: roleColor,
                  lineHeight: 1.1,
                  opacity: interpolate(frame, [4, 11], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }),
                }}
              >
                {role}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
