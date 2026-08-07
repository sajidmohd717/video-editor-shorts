"""
Audio master.

    python -m pipeline.master <slug> --input render/explainer.mp4 --target -13

Two-pass ffmpeg loudnorm. The first pass measures, the second normalises against
those measurements — one-pass loudnorm guesses and drifts, which is audible on
short content where there isn't time to settle.

Targets by format (measured from the reference teardowns):
  Explainer (ref 003)  -13 LUFS   — dense, limited, never gets quiet
  Short (ref 001)      -14 LUFS
  NewsUpdate (ref 002) -14 LUFS

YouTube normalises to about -14 on playback, so going hotter buys perceived
density rather than volume. Past roughly -11 it just sounds crushed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from .config import Project


def measure(path: Path, target: float, tp: float, lra: float) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path),
         "-af", f"loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    match = re.search(r"\{[^{}]*\"input_i\"[\s\S]*?\}", proc.stderr)
    if not match:
        raise SystemExit("loudnorm measurement failed:\n" + proc.stderr[-1500:])
    return json.loads(match.group(0))


def normalise(src: Path, dst: Path, m: dict, target: float, tp: float, lra: float) -> None:
    filt = (
        f"loudnorm=I={target}:TP={tp}:LRA={lra}"
        f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true,"
        # Gentle limiter catches the inter-sample peaks loudnorm's TP ceiling misses
        # once the file is re-encoded to AAC.
        "alimiter=level_in=1:level_out=0.97:limit=0.97:attack=5:release=50"
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-af", filt, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", str(dst)],
        check=True,
    )


def report(path: Path) -> tuple[float, float]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    i = re.findall(r"I:\s*(-?[\d.]+) LUFS", proc.stderr)
    lra = re.findall(r"LRA:\s*(-?[\d.]+) LU", proc.stderr)
    return (float(i[-1]) if i else 0.0, float(lra[-1]) if lra else 0.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--input", required=True, help="path relative to the project dir")
    ap.add_argument("--target", type=float, default=-13.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    ap.add_argument("--lra", type=float, default=7.0)
    args = ap.parse_args()

    project = Project(args.slug)
    src = project.dir / args.input
    if not src.exists():
        raise SystemExit(f"No file at {src}")
    dst = src.with_name(src.stem + "-master.mp4")

    before = report(src)
    print(f"before: {before[0]} LUFS, LRA {before[1]}")

    print("measuring...")
    m = measure(src, args.target, args.tp, args.lra)
    print("normalising...")
    normalise(src, dst, m, args.target, args.tp, args.lra)

    after = report(dst)
    print(f"after:  {after[0]} LUFS, LRA {after[1]}")
    print(f"\n-> {dst}")


if __name__ == "__main__":
    sys.exit(main())
