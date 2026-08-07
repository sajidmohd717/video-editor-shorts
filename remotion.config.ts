import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// x264 at CRF 18 is visually transparent for vertical talking-head + graphics,
// and YouTube re-encodes anyway. Going lower just costs render time.
Config.setCodec("h264");
Config.setCrf(18);

// Chromium needs this to decode the h264/AV1 source clips we feed in.
Config.setChromiumOpenGlRenderer("angle");

export {};
