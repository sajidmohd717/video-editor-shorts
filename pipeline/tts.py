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
    # Strip anything that isn't spoken. Long-form scripts carry editing notes,
    # chapter headings, checklists and tables inline — a backticked [note] would
    # otherwise be read aloud, and you'd only find out after paying for it.
    lines = []
    for ln in raw.splitlines():
        s = ln.strip()
        if s.startswith(("#", ">", "//", "|", "- ", "* ", "---")):
            continue
        if s.startswith("`[") or (s.startswith("[") and s.endswith("]")):
            continue
        # Drop inline editing notes wherever they appear on a spoken line.
        s = re.sub(r"`\[.*?\]`", "", s)
        s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)   # bold markers aren't speech
        lines.append(s)
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


def _elevenlabs(paragraphs: list[str], out_dir: Path, voice: str | None,
                settings: dict | None = None) -> list[Path]:
    from elevenlabs.client import ElevenLabs

    cfg = settings or {}
    client = ElevenLabs(api_key=require_env("ELEVENLABS_API_KEY"))
    voice_id = voice or cfg.get("voice") or require_env("ELEVENLABS_VOICE_ID")
    model = cfg.get("model") or env("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    fmt = cfg.get("outputFormat", "pcm_24000")
    rate = fmt.rsplit("_", 1)[-1] if fmt.startswith("pcm_") else "24000"

    parts: list[Path] = []
    for i, text in enumerate(paragraphs):
        print(f"  [{i + 1}/{len(paragraphs)}] {text[:64]}...")
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model,
            text=text,
            # Uncompressed PCM, never MP3. 128kbps MP3 produces coding artifacts
            # on voiced speech that are clearly audible as static (F12). 24kHz
            # caps bandwidth at 12kHz, far above anything that matters for
            # speech. mp3_44100_192 and pcm_44100 need higher tiers; this doesn't.
            output_format=fmt,
            voice_settings={
                # Lower stability = more expressive, which suits commentary.
                # Above ~0.5 the read flattens out and starts sounding like an IVR.
                "stability": cfg.get("stability", 0.38),
                "similarity_boost": cfg.get("similarityBoost", 0.80),
                "style": cfg.get("style", 0.35),
                "use_speaker_boost": cfg.get("speakerBoost", True),
            },
        )
        # pcm_* returns headerless PCM, so it has to be wrapped before anything
        # else can read it. s16le mono at the requested rate.
        raw = out_dir / f"part_{i:03d}.pcm"
        with raw.open("wb") as fh:
            for chunk in audio:
                fh.write(chunk)

        part = out_dir / f"part_{i:03d}.wav"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", rate,
             "-ac", "1", "-i", str(raw), str(part)],
            check=True,
        )
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


def concat(parts: list[Path], out: Path, gap: float = PARAGRAPH_GAP,
           rate: float = 1.0) -> None:
    """
    Concatenate parts with a fixed silence between them, into 48k mono WAV.

    Each gap gets its OWN anullsrc input. An earlier version built one silence
    input and referenced it once per gap, which reuses a single filter input
    across multiple branches — that needs an explicit asplit, and without one the
    behaviour is undefined rather than merely wasteful.

    Everything is normalised to 48kHz mono s16 before concat, so the filter never
    has to reconcile mismatched formats mid-graph.
    """
    inputs: list[str] = []
    filters: list[str] = []
    labels: list[str] = []
    idx = 0

    for i, part in enumerate(parts):
        inputs += ["-i", str(part)]
        filters.append(
            f"[{idx}:a]aresample=48000:resampler=soxr:precision=28,"
            f"aformat=sample_fmts=s16:channel_layouts=mono[a{idx}]"
        )
        labels.append(f"[a{idx}]")
        idx += 1

        if i < len(parts) - 1:
            inputs += ["-f", "lavfi", "-t", str(gap),
                       "-i", "anullsrc=channel_layout=mono:sample_rate=48000"]
            filters.append(
                f"[{idx}:a]aformat=sample_fmts=s16:channel_layouts=mono[a{idx}]"
            )
            labels.append(f"[a{idx}]")
            idx += 1

    # Pace. ElevenLabs' own `speed` setting proved unreliable on v3 — asking for
    # 1.15 returned a LONGER take than 1.0, i.e. run-to-run variance swamped it.
    # atempo is deterministic and pitch-preserving, so pace becomes a dial rather
    # than a hope. Values up to ~1.25 are transparent on speech.
    pace = "" if abs(rate - 1.0) < 1e-3 else f",atempo={rate:.3f}"

    filter_complex = (
        ";".join(filters) + ";" + "".join(labels)
        + f"concat=n={len(labels)}:v=0:a=1{pace}[out]"
    )

    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", *inputs,
         "-filter_complex", filter_complex, "-map", "[out]",
         "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", str(out)],
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
    ap.add_argument("--rate", type=float, default=None,
                    help="pace multiplier, e.g. 1.15 for a brisker read")
    args = ap.parse_args()

    if args.list_voices:
        list_voices()
        return
    if not args.slug:
        raise SystemExit("need <slug> (or use --list-voices)")

    project = Project(args.slug).ensure()
    paragraphs = read_script(project)

    # Voice, model and output format are channel decisions, so they come from the
    # profile when this project has a job. CLI flags still win.
    tts_cfg: dict = {}
    if (project.dir / "job.json").exists():
        try:
            from .profiles import load_job
            tts_cfg = load_job(args.slug).get("tts", {}) or {}
        except SystemExit:
            tts_cfg = {}

    engine = args.engine if args.engine != ap.get_default("engine") else tts_cfg.get("engine", args.engine)
    voice = args.voice or tts_cfg.get("voice")

    label = tts_cfg.get("voiceName") or voice or "default voice"
    print(f"{len(paragraphs)} paragraph(s) via {engine} ({label})")
    args.engine = engine

    if args.engine == "edge":
        print("  NOTE: edge is draft-only — unlicensed for commercial use.")

    def run(paras: list[str], tmp: Path) -> list[Path]:
        if args.engine == "elevenlabs":
            return _elevenlabs(paras, tmp, voice, tts_cfg)
        if args.engine == "kokoro":
            return _kokoro(paras, tmp, voice)
        return _edge(paras, tmp, voice)

    # --out lets you audition an engine or voice without clobbering the vo.wav
    # the current timeline was built against.
    dest = project.dir / args.out if args.out else project.vo

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        parts = run(paragraphs, tmp_dir)
        concat(parts, dest,
               gap=tts_cfg.get("paragraphGapSeconds", PARAGRAPH_GAP),
               rate=args.rate or tts_cfg.get("rate", 1.0))

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(dest)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    # QC preview: the same audio at +10dB. TTS generation is stochastic, so a
    # bad draw with an audible noise floor happens occasionally even with good
    # settings — and it is inaudible at normal level but obvious once the master
    # boosts it. Listening to THIS file, not a fresh test sentence, is the check
    # that matters (F13).
    qc = dest.with_name(dest.stem + "-qc+10dB.m4a")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(dest),
         "-af", "volume=10dB", "-c:a", "aac", "-b:a", "256k", str(qc)],
        check=True,
    )

    print(f"\n-> {dest}  ({float(dur):.2f}s)")
    print(f"   QC: {qc.name} — listen for a noise floor; regenerate if present")
    if dest == project.vo:
        print(f"   next: python -m pipeline.transcribe {args.slug}")


if __name__ == "__main__":
    sys.exit(main())
