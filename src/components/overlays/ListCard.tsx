import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "list-card" }>;

/**
 * Numbered list that builds one item at a time, in step with the narration.
 *
 * The shot list asked for this from the start ("three-item card, items appearing
 * as spoken") and it never got built, so lf-001's closing 26 seconds — the part
 * that tells the viewer what to actually watch for — played as stock b-roll.
 * Measured, that stretch was 10% graphics against 62% in the working opening
 * (L19).
 *
 * Why a list earns a device: three parallel items are a STRUCTURE, and a viewer
 * who can see all three at once can hold them. Spoken alone they arrive and
 * vanish. Earlier items stay on screen and dim rather than disappearing, so the
 * shape of the whole list is visible while the last one lands.
 */
export const ListCard: React.FC<Props> = ({
  title,
  items,
  accent,
  background,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const padX = width * 0.11;
  const numSize = Math.min(width * 0.036, 72);
  const textSize = Math.min(width * 0.030, 60);

  return (
    <AbsoluteFill
      style={{
        background,
        justifyContent: "center",
        padding: `0 ${padX}px`,
      }}
    >
      {title ? (
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 600,
            fontSize: Math.min(width * 0.016, 32),
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.40)",
            marginBottom: height * 0.07,
            opacity: interpolate(t, [0, 0.5], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {title}
        </div>
      ) : null}

      {items.map((it, i) => {
        const enter = spring({
          frame: frame - Math.round(it.at * fps),
          fps,
          config: { damping: 15, mass: 0.7, stiffness: 150 },
          durationInFrames: 12,
        });
        if (enter <= 0.001) {
          // Reserve the row so later items don't jump upward as they arrive.
          return <div key={i} style={{ height: textSize * 2.35 }} />;
        }
        // Once the next item lands, this one steps back rather than leaving.
        const next = items[i + 1];
        const dim = next
          ? interpolate(t, [next.at, next.at + 0.5], [1, 0.42], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          : 1;

        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: width * 0.028,
              height: textSize * 2.35,
              opacity: Math.min(1, enter * 1.4) * dim,
              transform: `translateX(${(1 - enter) * -40}px)`,
            }}
          >
            <div
              style={{
                fontFamily: "Poppins, sans-serif",
                fontWeight: 800,
                fontSize: numSize,
                color: accent,
                letterSpacing: "-0.04em",
                minWidth: numSize * 1.4,
              }}
            >
              {i + 1}
            </div>
            <div
              style={{
                fontFamily: "Poppins, sans-serif",
                fontWeight: 600,
                fontSize: textSize,
                lineHeight: 1.25,
                color: "#FFFFFF",
                letterSpacing: "-0.015em",
              }}
            >
              {it.text}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
