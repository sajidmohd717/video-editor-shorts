"""
Narration synthesis.

    python -m pipeline.tts <slug> [--engine kokoro|elevenlabs|edge] [--voice ID]

Reads projects/<slug>/script.md and writes projects/<slug>/vo.wav.

Three engines:
  kokoro     — DEFAULT. Runs locally, Apache 2.0, no key, no quota. Runs about
               1x realtime on CPU. Unambiguously fine for monetised content,
               which is why it's the default rather than a fallback.
  elevenlabs — best prosody and the only one that takes direction. Costs credits;
               the free tier is non-commercial, so a paid plan is required here.
  edge       — free and keyless, but it calls an undocumented Microsoft endpoint
               that isn't published as a commercial API. DRAFTS ONLY. Don't ship
               a monetised video narrated with this.

The script is split on blank lines into paragraphs and synthesised per-paragraph,
then concatenated with explicit silences. Two reasons: a failed request costs one
paragraph rather than the whole read, and inter-paragraph pauses become something
we control rather than something the model guesses at.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import Project, env, require_env

# Pause inserted between paragraphs. Long enough to breathe, short enough that
# the cut density doesn't stall waiting for the VO.
PARAGRAPH_GAP = 0.32


def read_script(project: Project) -> list[str]:
    if not project.script.exists():
        raise SystemExit(f"No script at {project.script}")
    raw = project.script.read_text(encoding="utf-8")
    # Strip markdown headings and comments — they're notes to us, not narration.
    lines = [
        ln for ln in raw.splitlines() if not ln.lstrip().startswith(("#", ">", "//"))
    ]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lines))]
    return [re.sub(r"\s+", " ", p) for p in paragraphs if p.strip()]


KOKORO_MODEL = "models/kokoro-v1.0.onnx"
KOKORO_VOICES = "models/voices-v1.0.bin"
# am_michael reads closest to a news-explainer register. af_heart and bm_george
# are the other two worth auditioning.
KOKORO_DEFAULT_VOICE = "am_michael"


def _kokoro(paragraphs: list[str], out_dir: Path, voice: str | None) -> list[Path]:
    import soundfile as sf
    from kokoro_onnx import Kokoro

    from .config import ROOT

    model, voices = ROOT / KOKORO_MODEL, ROOT / KOKORO_VOICES
    if not model.exists() or not voices.exists():
        raise SystemExit(
            f"Kokoro weights missing. Expected:\n  {model}\n  {voices}\n"
            "Download them from the kokoro-onnx model-files-v1.0 release."
        )

    engine = Kokoro(str(model), str(voices))
    voice_name = voice or KOKORO_DEFAULT_VOICE

    parts: list[Path] = []
    for i, text in enumerate(paragraphs):
        print(f"  [{i + 1}/{len(paragraphs)}] {text[:64]}...")
        audio, sr = engine.create(text, voice=voice_name, speed=1.0, lang="en-us")
        part = out_dir / f"part_{i:03d}.wav"
        sf.write(str(part), audio, sr)
        parts.append(part)
    return parts


def list_voices() -> None:
    """Print the account's available voices with their IDs."""
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=require_env("ELEVENLABS_API_KEY"))
    voices = client.voices.get_all().voices

    print(f"{len(voices)} voice(s) available:\n")
    for v in voices:
        labels = getattr(v, "labels", None) or {}
        traits = ", ".join(
            str(labels[k]) for k in ("gender", "age", "accent", "use_case", "description")
            if labels.get(k)
        )
        print(f"  {v.voice_id}  {v.name}")
        if traits:
            print(f"  {' ' * len(v.voice_id)}  {traits}")
    print("\nPut the ID you want in .env as ELEVENLABS_VOICE_ID.")
    print("For a news explainer, look for: male/female, american or british,")
    print("use_case 'news' or 'narration'. Avoid 'characters' and 'social media'.")


def _elevenlabs(paragraphs: list[str], out_dir: Path, voice: str | None) -> list[Path]:
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=require_env("ELEVENLABS_API_KEY"))
    voice_id = voice or require_env("ELEVENLABS_VOICE_ID")
    model = env("ELEVENLABS_MODEL", "eleven_multilingual_v2")

    parts: list[Path] = []
    for i, text in enumerate(paragraphs):
        print(f"  [{i + 1}/{len(paragraphs)}] {text[:64]}...")
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model,
            text=text,
            output_format="mp3_44100_128",
            voice_settings={
                # Lower stability = more expressive, which suits commentary.
                # Above ~0.5 the read flattens out and starts sounding like an IVR.
                "stability": 0.38,
                "similarity_boost": 0.80,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        )
        part = out_dir / f"part_{i:03d}.mp3"
        with part.open("wb") as fh:
            for chunk in audio:
                fh.write(chunk)
        parts.append(part)
    return parts


def _edge(paragraphs: list[str], out_dir: Path, voice: str | None) -> list[Path]:
    import edge_tts

    # Guy is a well-paced US male news-read voice; Aria is the female equivalent.
    voice_name = voice or "en-US-GuyNeural"

    async def run() -> list[Path]:
        parts: list[Path] = []
        for i, text in enumerate(paragraphs):
            print(f"  [{i + 1}/{len(paragraphs)}] {text[:64]}...")
            part = out_dir / f"part_{i:03d}.mp3"
            await edge_tts.Communicate(text, voice_name, rate="+6%").save(str(part))
            parts.append(part)
        return parts

    return asyncio.run(run())


def concat(parts: list[Path], out: Path, gap: float = PARAGRAPH_GAP) -> None:
    """Concatenate parts with a fixed silence between them, into 48k mono WAV."""
    inputs: list[str] = []
    filters: list[str] = []
    for i, part in enumerate(parts):
        inputs += ["-i", str(part)]
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono[a{i}]")

    # anullsrc supplies the gap; interleave it between the speech segments.
    gap_idx = len(parts)
    inputs += [
        "-f", "lavfi",
        "-t", str(gap),
        "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
    ]

    chain: list[str] = []
    for i in range(len(parts)):
        chain.append(f"[a{i}]")
        if i < len(parts) - 1:
            chain.append(f"[{gap_idx}:a]")

    n = len(chain)
    filter_complex = ";".join(filters) + ";" + "".join(chain) + f"concat=n={n}:v=0:a=1[out]"

    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", *inputs,
         "-filter_complex", filter_complex, "-map", "[out]",
         "-c:a", "pcm_s16le", str(out)],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--engine", choices=["kokoro", "elevenlabs", "edge"], default="kokoro")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--list-voices", action="store_true",
                    help="list ElevenLabs voices and IDs, then exit")
    ap.add_argument("--out", default=None, help="write to this filename instead of vo.wav")
    args = ap.parse_args()

    if args.list_voices:
        list_voices()
        return
    if not args.slug:
        raise SystemExit("need <slug> (or use --list-voices)")

    project = Project(args.slug).ensure()
    paragraphs = read_script(project)
    print(f"{len(paragraphs)} paragraph(s) via {args.engine}")

    if args.engine == "edge":
        print("  NOTE: edge is draft-only — unlicensed for commercial use.")

    engines = {"kokoro": _kokoro, "elevenlabs": _elevenlabs, "edge": _edge}

    # --out lets you audition an engine or voice without clobbering the vo.wav
    # the current timeline was built against.
    dest = project.dir / args.out if args.out else project.vo

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        parts = engines[args.engine](paragraphs, tmp_dir, args.voice)
        concat(parts, dest)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(dest)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    print(f"\n-> {dest}  ({float(dur):.2f}s)")
    if dest == project.vo:
        print(f"   next: python -m pipeline.transcribe {args.slug}")


if __name__ == "__main__":
    sys.exit(main())
