import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// Frames are JPEG-encoded before x264 ever sees them, and Remotion's default
// quality is 80 — which caps the output regardless of CRF. Flat brand cards, the
// blurred `fit` backdrop and gradients are where that ringing shows. 95 removes
// the ceiling; PNG would remove it entirely but costs render time for no visible
// gain at this bitrate.
Config.setJpegQuality(95);

// x264 at CRF 18 is visually transparent for vertical talking-head + graphics,
// and YouTube re-encodes anyway. Going lower just costs render time.
Config.setCodec("h264");
Config.setCrf(18);

// Chromium needs this to decode the h264/AV1 source clips we feed in.
Config.setChromiumOpenGlRenderer("angle");

export {};
