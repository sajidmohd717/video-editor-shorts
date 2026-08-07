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

export const OverlayLayer: React.FC<{ overlay: Overlay; durationInFrames: number }> = ({
  overlay,
  durationInFrames,
}) => {
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
    case "word-card":
      return <WordCard {...overlay} />;
    case "cta":
      return <Cta {...overlay} />;
    case "logo-pop":
      return <LogoPop {...overlay} durationInFrames={durationInFrames} />;
    case "film-burn":
      return <FilmBurn {...overlay} durationInFrames={durationInFrames} />;
    case "end-card":
      return <EndCard {...overlay} />;
    default:
      return null;
  }
};
