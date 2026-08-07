import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "chrome" }>;

/**
 * Persistent dateline + channel bug (ref 002).
 *
 * The dateline is doing more work than it looks like: a news short has to answer
 * "is this current?" within the first second, and a date in the corner answers it
 * without spending a word of the script. Span this across the whole runtime.
 */
export const Chrome: React.FC<Props> = ({ dateline, bug, bugImage, tone }) => {
  const color = tone === "light" ? "#fff" : "#0B0B0F";
  const shadow = tone === "light" ? "0 2px 14px rgba(0,0,0,0.6)" : "none";

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {dateline ? (
        <div
          style={{
            position: "absolute",
            top: 218,
            left: 68,
            fontFamily: "Poppins, system-ui, sans-serif",
            fontWeight: 700,
            fontSize: 44,
            letterSpacing: "-0.01em",
            color,
            textShadow: shadow,
          }}
        >
          {dateline}
        </div>
      ) : null}

      {bugImage ? (
        <Img
          src={/^(https?:|data:)/.test(bugImage) ? bugImage : staticFile(bugImage)}
          style={{ position: "absolute", top: 208, right: 62, height: 78, objectFit: "contain" }}
        />
      ) : bug ? (
        <div
          style={{
            position: "absolute",
            top: 220,
            right: 66,
            fontFamily: "Poppins, system-ui, sans-serif",
            fontWeight: 800,
            fontSize: 36,
            letterSpacing: "0.06em",
            color,
            textShadow: shadow,
          }}
        >
          {bug}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
