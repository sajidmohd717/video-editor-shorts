import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "quote-card" }> & { durationInFrames: number };

/**
 * Full-screen pull quote (L7).
 *
 * The register change is the effect — no footage, no motion, just words — so the
 * component's job is mostly to get out of the way. Reserve it for load-bearing
 * claims; used often it stops meaning anything.
 *
 * `typeOn` reveals word by word at roughly reading speed rather than all at once.
 * A block of text appearing whole invites skimming; revealed at pace, the viewer
 * reads it with the narration instead of ahead of it.
 */
export const QuoteCard: React.FC<Props> = ({
  text,
  attribution,
  size,
  typeOn,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");
  // Reveal across the first 60% of the hold, so the finished quote sits complete
  // for a beat before the cut. Landing the last word on the cut feels rushed.
  const revealFrames = Math.max(1, durationInFrames * 0.6);
  const shown = typeOn
    ? Math.ceil(interpolate(frame, [0, revealFrames], [0, words.length], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }))
    : words.length;

  const fade = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "#000",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 130px",
      }}
    >
      <div style={{ opacity: fade, maxWidth: 1500 }}>
        <div
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontWeight: 400,
            fontSize: size,
            lineHeight: 1.42,
            color: "#FFFFFF",
            letterSpacing: "-0.005em",
          }}
        >
          {words.map((w, i) => (
            <span
              key={i}
              style={{
                // Unrevealed words hold their space so the block never reflows —
                // text jumping as it appears is far more distracting than the
                // reveal is useful.
                opacity: i < shown ? 1 : 0,
                transition: "none",
              }}
            >
              {w}
              {i < words.length - 1 ? " " : ""}
            </span>
          ))}
        </div>

        {attribution ? (
          <div
            style={{
              marginTop: 46,
              fontFamily: "Poppins, sans-serif",
              fontWeight: 600,
              fontSize: size * 0.34,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.55)",
              opacity: interpolate(frame, [revealFrames * 0.8, revealFrames], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {attribution}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
