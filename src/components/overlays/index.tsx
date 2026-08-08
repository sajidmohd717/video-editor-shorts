import React from "react";
import type { Overlay } from "../../timeline/schema";
import { KineticTitle } from "./KineticTitle";
import { ChatBubbles } from "./ChatBubbles";
import { ImageCard } from "./ImageCard";
import { Headline } from "./Headline";
import { CodePanel } from "./CodePanel";
import { Accent } from "./Accent";
import { Progress } from "./Progress";
import { EndCard } from "./EndCard";
import { Chrome } from "./Chrome";
import { ArticleClip } from "./ArticleClip";
import { Annotation } from "./Annotation";
import { StatChart } from "./StatChart";
import { WordCard } from "./WordCard";
import { Cta } from "./Cta";
import { Comparison } from "./Comparison";
import { LogoPop } from "./LogoPop";
import { FilmBurn } from "./FilmBurn";
import { DateCard } from "./DateCard";
import { QuoteCard } from "./QuoteCard";
import { EntityGraph } from "./EntityGraph";
import { BigNumber } from "./BigNumber";
import { ListCard } from "./ListCard";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Overlays that are otherwise a STILL RECTANGLE for their whole duration.
 *
 * A talking-head or b-roll clip already moves by itself; a card, chart or
 * document does not, and a static rectangle held for eight seconds is the exact
 * thing that made lf-001's first cut feel like a slideshow (L19).
 */
const DRIFTS = new Set([
  "date-card", "quote-card", "comparison", "stat-chart",
  "article-clip", "entity-graph", "word-card", "headline", "image-card",
  "big-number", "list-card",
]);

/**
 * Slow continuous camera on a graphic. Ref L003 never lets its data sit still —
 * the chart lives inside a set and the camera drifts through it for the whole
 * shot. We can't build a 3D set, but the *motion* is most of the effect and it
 * costs one transform.
 *
 * Deterministic by construction: the phase comes from a hash of the overlay id,
 * never from randomness, so out-of-order frame workers agree (same rule as
 * Grain.tsx). Different overlays drift differently; the same overlay always
 * drifts identically.
 */
const Drift: React.FC<{ id: string; durationInFrames: number; children: React.ReactNode }> = ({
  id,
  durationInFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) % 997;

  const p = durationInFrames > 0 ? frame / durationInFrames : 0;
  // Push in over the hold. Small — this should be felt, not seen.
  const scale = 1.012 + p * 0.038;
  // Drift direction alternates by hash so consecutive cards don't slide the
  // same way, which would read as a single long move rather than a new shot.
  const dir = h % 4;
  const amp = width * 0.012;
  const dx = (dir === 0 ? 1 : dir === 1 ? -1 : 0) * amp * p;
  const dy = (dir === 2 ? 1 : dir === 3 ? -1 : 0) * amp * 0.6 * p;

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${dx}px, ${dy}px) scale(${scale})`,
        transformOrigin: "50% 50%",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

export const OverlayLayer: React.FC<{ overlay: Overlay; durationInFrames: number }> = ({
  overlay,
  durationInFrames,
}) => {
  const inner = renderOverlay(overlay, durationInFrames);
  return DRIFTS.has(overlay.type) ? (
    <Drift id={overlay.id} durationInFrames={durationInFrames}>
      {inner}
    </Drift>
  ) : (
    inner
  );
};

const renderOverlay = (overlay: Overlay, durationInFrames: number) => {
  switch (overlay.type) {
    case "kinetic-title":
      return <KineticTitle {...overlay} />;
    case "chat-bubbles":
      return <ChatBubbles {...overlay} />;
    case "image-card":
      return <ImageCard {...overlay} durationInFrames={durationInFrames} />;
    case "headline":
      return <Headline {...overlay} />;
    case "code-panel":
      return <CodePanel {...overlay} />;
    case "accent":
      return <Accent {...overlay} />;
    case "progress":
      return <Progress {...overlay} durationInFrames={durationInFrames} />;
    case "chrome":
      return <Chrome {...overlay} />;
    case "article-clip":
      return <ArticleClip {...overlay} />;
    case "annotation":
      return <Annotation {...overlay} />;
    case "stat-chart":
      return <StatChart {...overlay} />;
    case "comparison":
      return <Comparison {...overlay} />;
    case "entity-graph":
      return <EntityGraph {...overlay} />;
    case "big-number":
      return <BigNumber {...overlay} />;
    case "list-card":
      return <ListCard {...overlay} />;
    case "word-card":
      return <WordCard {...overlay} />;
    case "cta":
      return <Cta {...overlay} />;
    case "logo-pop":
      return <LogoPop {...overlay} durationInFrames={durationInFrames} />;
    case "film-burn":
      return <FilmBurn {...overlay} durationInFrames={durationInFrames} />;
    case "date-card":
      return <DateCard {...overlay} />;
    case "quote-card":
      return <QuoteCard {...overlay} durationInFrames={durationInFrames} />;
    case "end-card":
      return <EndCard {...overlay} />;
    default:
      return null;
  }
};
