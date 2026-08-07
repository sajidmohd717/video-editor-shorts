import { loadFont as loadPoppins } from "@remotion/google-fonts/Poppins";
import { loadFont as loadSlab } from "@remotion/google-fonts/RobotoSlab";
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";

/**
 * Fonts must be loaded at module scope so they're ready before the first frame
 * is captured — otherwise early frames render in the fallback face and the text
 * visibly reflows a few frames in.
 *
 * The two-font contrast (geometric sans for captions, high-contrast serif for
 * graphic labels) is common to refs 001 and 003, and it's most of what makes
 * their typography read as designed rather than typed.
 *
 * Poppins         — captions, UI chrome, charts
 * Playfair Display — display labels, word cards (ref 003)
 * Roboto Slab     — news headline cards (ref 002)
 */
export const { fontFamily: poppins } = loadPoppins("normal", {
  weights: ["300", "400", "500", "600", "700", "800"],
  subsets: ["latin"],
});

export const { fontFamily: robotoSlab } = loadSlab("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

export const { fontFamily: playfair } = loadPlayfair("normal", {
  weights: ["400", "700", "900"],
  subsets: ["latin"],
});

export const { fontFamily: playfairItalic } = loadPlayfair("italic", {
  weights: ["400", "700"],
  subsets: ["latin"],
});
