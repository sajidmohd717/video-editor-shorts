import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { CaptionCue, Timeline } from "../timeline/schema";

type Style = Timeline["captions"]["style"];

/**
 * Caption renderer.
 *
 * Reference 001's chunking is 2-4 words per card, swapped on phrase boundaries —
 * not per-word karaoke, and not full sentences. Word-level timings still come
 * through on every cue so the karaoke preset can use them, and so `emphasis`
 * can target the exact frame a payoff word lands.
 */

const EMPHASIS_SCALE = 1.14;

const CueBody: React.FC<{ cue: CaptionCue; style: Style; localFrame: number }> = ({
  cue,
  style,
  localFrame,
}) => {
  const { fps } = useVideoConfig();

  // Cards snap in with a short overshoot rather than fading — fades read as sluggish
  // at this cut density.
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 180 },
    durationInFrames: 8,
  });

  const emphasisScale =
    cue.emphasis === "pop"
      ? interpolate(entrance, [0, 1], [1, EMPHASIS_SCALE], { extrapolateRight: "clamp" })
      : 1;

  const shakeX =
    cue.emphasis === "shake" ? Math.sin(localFrame * 3.1) * (6 * (1 - entrance)) : 0;

  const text = cue.words.map((w) => w.text).join(" ");
  const absoluteFrame = localFrame + Math.round(cue.start * fps);

  const isKaraoke = style.preset === "karaoke";
  const isBroadcast = style.preset === "broadcast";
  const isWordPop = style.preset === "word-pop";

  return (
    <div
      style={{
        // Broadcast subtitles don't animate — they hard-swap, like a caption decoder.
        transform: isBroadcast
          ? "none"
          : `scale(${(0.86 + entrance * 0.14) * emphasisScale}) translateX(${shakeX}px)`,
        opacity: isBroadcast ? 1 : Math.min(1, entrance * 2),
        display: "inline-block",
        maxWidth: isBroadcast ? "72%" : "86%",
      }}
    >
      <span
        style={{
          display: "inline-block",
          fontFamily: `${style.fontFamily}, system-ui, sans-serif`,
          fontWeight: isBroadcast ? 400 : style.fontWeight,
          fontSize: style.fontSize,
          lineHeight: isBroadcast ? 1.32 : 1.24,
          letterSpacing: isBroadcast ? "0" : "-0.01em",
          color: cue.emphasis === "color" && !isBroadcast ? "#FFE45C" : style.color,
          textAlign: "center",
          padding: style.preset === "pill" ? "10px 22px" : isBroadcast ? "8px 18px" : 0,
          borderRadius: isBroadcast ? 0 : style.pillRadius,
          background: isBroadcast
            ? "rgba(60,60,60,0.62)"
            : style.preset === "pill"
              ? style.pillColor
              : "transparent",
          boxDecorationBreak: "clone",
          WebkitBoxDecorationBreak: "clone",
          // word-pop: the thick stroke does the legibility work a pill would, without
          // boxing off part of the frame. `paintOrder: stroke fill` is what keeps the
          // stroke outside the glyph instead of eating into it.
          textShadow: isWordPop
            ? "0 6px 22px rgba(0,0,0,0.55)"
            : style.preset === "outline" || style.preset === "bold-drop"
              ? "0 4px 0 rgba(0,0,0,0.85), 0 0 18px rgba(0,0,0,0.6)"
              : "none",
          WebkitTextStroke: isWordPop
            ? `${style.strokeWidth}px #000`
            : style.preset === "outline"
              ? "3px rgba(0,0,0,0.9)"
              : undefined,
          paintOrder: "stroke fill",
        }}
      >
        {isKaraoke
          ? cue.words.map((w, i) => {
              const active = absoluteFrame / fps >= w.start;
              return (
                <span
                  key={i}
                  style={{
                    color: active ? "#FFE45C" : style.color,
                    transition: "none",
                  }}
                >
                  {w.text}
                  {i < cue.words.length - 1 ? " " : ""}
                </span>
              );
            })
          : text}
      </span>
    </div>
  );
};

export const Captions: React.FC<{
  cues: CaptionCue[];
  style: Style;
}> = ({ cues, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const active = cues.find((c) => t >= c.start && t < c.end);
  if (!active) return null;

  const localFrame = frame - Math.round(active.start * fps);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          // anchorY 0.5 lands the card on the optical centre / stacked-layout seam.
          top: `${style.anchorY * 100}%`,
          transform: "translateY(-50%)",
          width: "100%",
          display: "flex",
          justifyContent: "center",
          textAlign: "center",
        }}
      >
        <CueBody cue={active} style={style} localFrame={localFrame} />
      </div>
    </AbsoluteFill>
  );
};
