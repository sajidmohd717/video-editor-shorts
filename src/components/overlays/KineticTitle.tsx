import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "kinetic-title" }>;

/**
 * The hook title from reference 001.
 *
 * The trick that makes it work isn't the animation — it's the *typographic contrast*:
 * light italic serif on the connective words ("whether", "is a") against a heavy sans
 * on the keywords. And because the assembled text persists while b-roll cuts underneath
 * it, it's the one continuous element on screen, which is what keeps a 1.7 cuts/sec
 * barrage from reading as chaos.
 */

const STYLES: Record<Props["lines"][number]["style"], React.CSSProperties> = {
  "serif-italic": {
    fontFamily: "Georgia, 'Times New Roman', serif",
    fontStyle: "italic",
    fontWeight: 400,
    letterSpacing: "0.01em",
  },
  "sans-heavy": {
    fontFamily: "Poppins, system-ui, sans-serif",
    fontWeight: 800,
    letterSpacing: "-0.025em",
  },
  "sans-light": {
    fontFamily: "Poppins, system-ui, sans-serif",
    fontWeight: 300,
    letterSpacing: "0.02em",
  },
};

export const KineticTitle: React.FC<Props> = ({ lines }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 90px",
        textAlign: "center",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {lines.map((line, i) => {
          const delayFrames = Math.round(line.delay * fps);
          const local = frame - delayFrames;
          const enter = spring({
            frame: local,
            fps,
            config: { damping: 16, mass: 0.6, stiffness: 140 },
            durationInFrames: 12,
          });
          if (local < 0) return <div key={i} style={{ height: line.size * 1.15 }} />;

          return (
            <div
              key={i}
              style={{
                ...STYLES[line.style],
                fontSize: line.size,
                lineHeight: 1.08,
                color: "#fff",
                opacity: enter,
                transform: `translateY(${(1 - enter) * 26}px)`,
                textShadow: "0 6px 34px rgba(0,0,0,0.7)",
              }}
            >
              {line.text}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
