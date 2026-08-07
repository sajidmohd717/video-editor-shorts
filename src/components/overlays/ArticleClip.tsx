import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Overlay } from "../../timeline/schema";

type Props = Extract<Overlay, { type: "article-clip" }>;

/**
 * News article screenshot with a highlight bar that sweeps across a phrase.
 *
 * This is ref 003's evidence layer and its single most-repeated device — it turns
 * "OpenAI is losing money" from an assertion into a citation, in about a second,
 * without leaving the vertical frame.
 *
 * Two modes:
 *  - `src` set  → real screenshot, with the highlight drawn over a caller-specified band
 *  - no `src`   → we render an article-shaped card from the text fields, so a timeline
 *                 can be built and reviewed before the screenshot pipeline exists
 */
export const ArticleClip: React.FC<Props> = ({
  src,
  outlet,
  kicker,
  headline,
  byline,
  highlight,
  highlightBox,
  highlightMode,
  highlightStart,
  highlightDuration,
  highlightColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 16, mass: 0.6, stiffness: 160 },
    durationInFrames: 9,
  });

  // The sweep is a width ramp on a coloured span behind the phrase — it reads as a
  // marker being dragged across the line.
  const sweep = interpolate(
    frame,
    [highlightStart * fps, (highlightStart + highlightDuration) * fps],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Split the headline so the highlighted phrase can be wrapped independently.
  const idx = highlight ? headline.indexOf(highlight) : -1;
  const before = idx >= 0 ? headline.slice(0, idx) : headline;
  const mid = idx >= 0 ? headline.slice(idx, idx + highlight!.length) : "";
  const after = idx >= 0 ? headline.slice(idx + highlight!.length) : "";

  return (
    <AbsoluteFill
      style={{
        background: "#EDEDEF",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 56px",
      }}
    >
      {src ? (
        <div
          style={{
            position: "relative",
            width: "100%",
            opacity: enter,
            transform: `scale(${0.97 + enter * 0.03})`,
            // Isolate so the highlight's blend mode acts on the screenshot only,
            // not on whatever clip is underneath.
            isolation: "isolate",
          }}
        >
          <Img
            src={/^(https?:|data:)/.test(src) ? src : staticFile(src)}
            style={{ width: "100%", objectFit: "contain", display: "block" }}
          />
          {highlightBox ? (
            // Neither mode covers the words — a flat rectangle would just hide
            // them, which is the opposite of highlighting. `marker` tints,
            // `invert` flips the region's luminance.
            <div
              style={{
                position: "absolute",
                left: `${highlightBox.x * 100}%`,
                top: `${highlightBox.y * 100}%`,
                height: `${highlightBox.height * 100}%`,
                width: `${highlightBox.width * sweep * 100}%`,
                background: highlightMode === "invert" ? "#FFFFFF" : highlightColor,
                mixBlendMode: highlightMode === "invert" ? "difference" : "multiply",
                opacity: highlightMode === "invert" ? 1 : 0.85,
                pointerEvents: "none",
              }}
            />
          ) : null}
        </div>
      ) : (
        <div
          style={{
            width: "100%",
            background: "#fff",
            padding: "44px 46px 50px",
            borderRadius: 6,
            boxShadow: "0 26px 70px rgba(0,0,0,0.22)",
            opacity: enter,
            transform: `translateY(${(1 - enter) * 26}px)`,
          }}
        >
          {kicker ? (
            <div
              style={{
                display: "inline-block",
                fontFamily: "Poppins, sans-serif",
                fontWeight: 600,
                fontSize: 22,
                color: "#4B5563",
                border: "1px solid #D1D5DB",
                borderRadius: 999,
                padding: "6px 16px",
                marginBottom: 24,
              }}
            >
              {kicker}
            </div>
          ) : null}

          <div
            style={{
              fontFamily: "'Roboto Slab', Georgia, serif",
              fontWeight: 700,
              fontSize: 52,
              lineHeight: 1.2,
              color: "#0B0B0F",
              letterSpacing: "-0.015em",
            }}
          >
            {before}
            {mid ? (
              // The bar is a hard-stop gradient on the span's own background, so it
              // wraps across lines correctly (`boxDecorationBreak: clone` repeats it
              // per line-box). Absolute positioning breaks inline flow here — it
              // collapses the phrase — so it can't be used.
              <span
                style={{
                  backgroundImage: `linear-gradient(to right, ${highlightColor} 0%, ${highlightColor} ${
                    sweep * 100
                  }%, rgba(0,0,0,0) ${sweep * 100}%)`,
                  boxDecorationBreak: "clone",
                  WebkitBoxDecorationBreak: "clone",
                  padding: "0.04em 0.06em",
                }}
              >
                {/* Per-character colour flip so the text turns white exactly as the
                    bar reaches it, rather than all at once mid-sweep. */}
                {Array.from(mid).map((ch, i) => (
                  <span
                    key={i}
                    style={{ color: (i + 0.5) / mid.length <= sweep ? "#FFFFFF" : "#0B0B0F" }}
                  >
                    {ch === " " ? " " : ch}
                  </span>
                ))}
              </span>
            ) : null}
            {after}
          </div>

          {byline ? (
            <div
              style={{
                marginTop: 28,
                fontFamily: "Poppins, sans-serif",
                fontSize: 24,
                color: "#6B7280",
              }}
            >
              {byline}
            </div>
          ) : null}

          {outlet ? (
            <div
              style={{
                marginTop: 10,
                fontFamily: "Poppins, sans-serif",
                fontWeight: 700,
                fontSize: 20,
                letterSpacing: "0.16em",
                textTransform: "uppercase",
                color: "#9CA3AF",
              }}
            >
              {outlet}
            </div>
          ) : null}
        </div>
      )}
    </AbsoluteFill>
  );
};
