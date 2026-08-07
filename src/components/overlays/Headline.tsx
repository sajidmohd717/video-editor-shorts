import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "headline" }>;

/**
 * News lower-third / quote card. The workhorse graphic for a tech-news channel:
 * every claim in the script that came from somewhere should be able to show
 * where it came from, without leaving the vertical frame.
 */
export const Headline: React.FC<Props> = ({ source, text, variant }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 18, mass: 0.7, stiffness: 130 },
    durationInFrames: 14,
  });

  if (variant === "ticker") {
    const x = interpolate(frame, [0, 300], [1080, -1600]);
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", paddingBottom: 260 }}>
        <div
          style={{
            background: "#B00020",
            color: "#fff",
            fontFamily: "Poppins, sans-serif",
            fontWeight: 700,
            fontSize: 40,
            padding: "16px 0",
            overflow: "hidden",
            whiteSpace: "nowrap",
          }}
        >
          <div style={{ transform: `translateX(${x}px)` }}>{text}</div>
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "article") {
    // Ref 002's white card in a dark news serif. This is the fastest available
    // "this is journalism, not a take" cue, and it sits lower-third, not centred.
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", paddingBottom: 470 }}>
        <div
          style={{
            marginLeft: 68,
            marginRight: 150,
            background: "#FFFFFF",
            padding: "26px 30px 30px",
            opacity: enter,
            transform: `translateX(${(1 - enter) * -40}px)`,
            boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
          }}
        >
          <div
            style={{
              fontFamily: "'Roboto Slab', Georgia, serif",
              fontWeight: 700,
              fontSize: 54,
              lineHeight: 1.12,
              letterSpacing: "-0.015em",
              color: "#141E3C",
            }}
          >
            {text}
          </div>
          {source ? (
            <div
              style={{
                marginTop: 14,
                fontFamily: "Poppins, sans-serif",
                fontWeight: 700,
                fontSize: 22,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "#6B7280",
              }}
            >
              {source}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    );
  }

  const isTweet = variant === "tweet";

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 70px" }}>
      <div
        style={{
          width: "100%",
          background: isTweet ? "#16181C" : "rgba(10,10,12,0.94)",
          border: isTweet ? "1px solid #2F3336" : "none",
          borderLeft: variant === "breaking" ? "10px solid #E11D2E" : undefined,
          borderRadius: isTweet ? 26 : 10,
          padding: isTweet ? "34px 36px" : "30px 34px",
          opacity: enter,
          transform: `translateY(${(1 - enter) * 40}px) scale(${0.96 + enter * 0.04})`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
        }}
      >
        <div
          style={{
            fontFamily: "Poppins, sans-serif",
            fontWeight: 700,
            fontSize: 26,
            letterSpacing: "0.12em",
            color: variant === "breaking" ? "#FF4D5E" : "#7A8794",
            marginBottom: 14,
            textTransform: isTweet ? "none" : "uppercase",
          }}
        >
          {source}
        </div>
        <div
          style={{
            fontFamily: isTweet
              ? "system-ui, sans-serif"
              : "Poppins, sans-serif",
            fontWeight: isTweet ? 400 : 600,
            fontSize: isTweet ? 44 : 50,
            lineHeight: 1.26,
            color: "#fff",
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
