import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "chat-bubbles" }>;

const THEMES = {
  imessage: { bg: "#F2F2F7", left: "#E9E9EB", right: "#0B93F6", leftText: "#000", rightText: "#fff" },
  whatsapp: { bg: "#0B141A", left: "#202C33", right: "#005C4B", leftText: "#E9EDEF", rightText: "#E9EDEF" },
  "x-dm": { bg: "#000", left: "#2F3336", right: "#1D9BF0", leftText: "#fff", rightText: "#fff" },
} as const;

/**
 * Sequential chat bubbles, staggered ~200ms apart, entering bottom-up.
 * Reference 001 uses this to stage a remembered conversation — it turns a
 * quoted line into something the viewer reads rather than just hears.
 */
export const ChatBubbles: React.FC<Props> = ({ theme, bubbles }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = THEMES[theme];

  return (
    <AbsoluteFill
      style={{
        background: t.bg,
        justifyContent: "center",
        padding: "0 60px",
        gap: 22,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {bubbles.map((b, i) => {
        const local = frame - Math.round(b.delay * fps);
        const enter = spring({
          frame: local,
          fps,
          config: { damping: 13, mass: 0.5, stiffness: 190 },
          durationInFrames: 10,
        });
        if (local < 0) return null;

        return (
          <div
            key={i}
            style={{
              alignSelf: b.side === "right" ? "flex-end" : "flex-start",
              maxWidth: "78%",
              background: b.side === "right" ? t.right : t.left,
              color: b.side === "right" ? t.rightText : t.leftText,
              borderRadius: 34,
              padding: "22px 30px",
              fontFamily: "system-ui, -apple-system, sans-serif",
              fontSize: 42,
              lineHeight: 1.3,
              opacity: enter,
              transform: `translateY(${(1 - enter) * 34}px) scale(${0.9 + enter * 0.1})`,
              transformOrigin: b.side === "right" ? "100% 100%" : "0% 100%",
            }}
          >
            {b.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
