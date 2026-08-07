import type { Clip } from "../timeline/schema";

/**
 * Colour/stylistic treatments, expressed as CSS filter chains where possible.
 * CSS filters are GPU-composited in Chromium and cost essentially nothing at
 * render time, which is why they're the first stop before reaching for WebGL.
 *
 * Anything genuinely shader-shaped (displacement, real chromatic aberration,
 * feedback) lives in `src/effects/shaders/` instead.
 */
type FilterName = Clip["filters"][number];

const CSS_FILTERS: Record<FilterName, string | null> = {
  none: null,
  darken: "brightness(0.55)",
  blur: "blur(18px)",
  desaturate: "saturate(0.25) contrast(1.1)",
  // Push everything toward phosphor green — the "scrolling terminal" look.
  "terminal-green": "grayscale(1) sepia(1) hue-rotate(65deg) saturate(6) contrast(1.35)",
  vhs: "saturate(1.6) contrast(1.15) brightness(1.05)",
  // Approximated in CSS; the real version is an SVG/GLSL channel offset.
  "chromatic-aberration": "saturate(1.3)",
  "film-grain": null, // handled as an overlay layer, not a filter
};

export const buildFilterChain = (filters: FilterName[]): string => {
  const chain = filters.map((f) => CSS_FILTERS[f]).filter(Boolean);
  return chain.length > 0 ? chain.join(" ") : "none";
};

/** Filters that need a sibling overlay element rather than a CSS filter. */
export const needsGrainOverlay = (filters: FilterName[]) => filters.includes("film-grain");
export const needsAberration = (filters: FilterName[]) =>
  filters.includes("chromatic-aberration");
