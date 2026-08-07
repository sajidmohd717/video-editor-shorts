import { loadFont as loadPoppins } from "@remotion/google-fonts/Poppins";
import { loadFont as loadSlab } from "@remotion/google-fonts/RobotoSlab";

/**
 * Fonts must be loaded at module scope so they're ready before the first frame
 * is captured — otherwise early frames render in the fallback face and the text
 * visibly reflows a few frames in.
 *
 * Poppins    — captions, titles, UI chrome (ref 001's geometric sans)
 * Roboto Slab — news headline cards (ref 002's credibility serif)
 */
export const { fontFamily: poppins } = loadPoppins("normal", {
  weights: ["300", "400", "600", "700", "800"],
  subsets: ["latin"],
});

export const { fontFamily: robotoSlab } = loadSlab("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});
