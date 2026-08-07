import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";
import { Grain } from "../../effects/Grain";

type Props = Extract<Overlay, { type: "code-panel" }>;

/**
 * Full-bleed scrolling code, phosphor-green terminal treatment.
 * Reference 001 leans on this constantly as generic "AI/tech is happening" b-roll —
 * it's cheap, it's on-brand for the niche, and it never needs licensing.
 */
export const CodePanel: React.FC<Props> = ({ code, scrollSpeed }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const y = -(frame / fps) * scrollSpeed;

  // Repeat the block so it never runs out of content mid-shot.
  const body = Array.from({ length: 6 }, () => code).join("\n");

  return (
    <AbsoluteFill style={{ background: "#04120A", overflow: "hidden" }}>
      <pre
        style={{
          position: "absolute",
          top: 0,
          left: 40,
          right: 0,
          margin: 0,
          transform: `translateY(${y}px)`,
          fontFamily: "'Cascadia Code', 'Consolas', monospace",
          fontSize: 34,
          lineHeight: 1.5,
          color: "#3BFF7E",
          textShadow: "0 0 12px rgba(59,255,126,0.55)",
          whiteSpace: "pre",
        }}
      >
        {body}
      </pre>

      {/* Scanlines + vignette sell the CRT read more than the colour does. */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 1px, transparent 4px)",
          pointerEvents: "none",
        }}
      />
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.85) 100%)",
          pointerEvents: "none",
        }}
      />
      <Grain opacity={0.1} />
    </AbsoluteFill>
  );
};
