import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import type { Timeline } from "./timeline/schema";
import { ClipLayer } from "./components/ClipLayer";
import { Captions } from "./components/Captions";
import { OverlayLayer } from "./components/overlays";

const resolveSrc = (src: string) =>
  /^(https?:|data:|blob:)/.test(src) ? src : staticFile(src);

/**
 * Root composition.
 *
 * Layer order, bottom to top:
 *   1. clips      — the video spine
 *   2. overlays   — graphics, sorted by their own z
 *   3. captions   — always on top of graphics
 *   4. audio      — VO / music / sfx
 *
 * Every element is placed with a <Sequence>, so Remotion only mounts what's
 * on screen and each child sees a frame counter local to its own start.
 */
export const Short: React.FC<Timeline> = ({ meta, clips, overlays, captions, audio }) => {
  const fps = meta.fps;
  const toFrames = (s: number) => Math.round(s * fps);

  const sortedOverlays = [...overlays].sort((a, b) => a.z - b.z);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {clips.map((clip) => {
        const from = toFrames(clip.start);
        const duration = Math.max(1, toFrames(clip.end) - from);
        return (
          <Sequence key={clip.id} from={from} durationInFrames={duration} name={`clip:${clip.id}`}>
            <ClipLayer clip={clip} durationInFrames={duration} />
          </Sequence>
        );
      })}

      {sortedOverlays.map((overlay) => {
        const from = toFrames(overlay.start);
        const duration = Math.max(1, toFrames(overlay.end) - from);
        return (
          <Sequence
            key={overlay.id}
            from={from}
            durationInFrames={duration}
            name={`${overlay.type}:${overlay.id}`}
          >
            <OverlayLayer overlay={overlay} durationInFrames={duration} />
          </Sequence>
        );
      })}

      <Captions cues={captions.cues} style={captions.style} />

      {audio.map((track) => (
        <Sequence
          key={track.id}
          from={toFrames(track.start)}
          durationInFrames={track.duration ? toFrames(track.duration) : undefined}
          name={`audio:${track.role}`}
        >
          <Audio
            src={resolveSrc(track.src)}
            trimBefore={toFrames(track.offset)}
            trimAfter={
              track.duration ? toFrames(track.offset + track.duration) : undefined
            }
            volume={Math.pow(10, track.gainDb / 20)}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
