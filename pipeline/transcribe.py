"""
Word-level transcription.

    python -m pipeline.transcribe <slug>          # transcribe the VO
    python -m pipeline.transcribe <slug> --input path/to/clip.mp4

Writes projects/<slug>/vo.words.json.

The important idea: we transcribe the GENERATED VO, not the written script.
The script tells us what was meant; only the audio tells us when each word
actually lands, including the TTS engine's own pauses and pacing quirks. Caption
timings derived from the audio are the difference between captions that feel
machine-made and captions that feel edited.

Runs faster-whisper int8 on CPU — this machine has no CUDA, and for clean
synthetic speech the word timestamps are already tight.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Project, env


def transcribe(audio: Path, model_size: str = "small") -> dict:
    from faster_whisper import WhisperModel

    print(f"loading whisper '{model_size}' (int8, cpu)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        str(audio),
        word_timestamps=True,
        # VAD trims silence, which stops Whisper from hallucinating filler text
        # into the gaps we deliberately inserted between paragraphs.
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        beam_size=5,
    )

    words: list[dict] = []
    text_parts: list[str] = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        for w in seg.words or []:
            token = w.word.strip()
            if not token:
                continue
            words.append({"text": token, "start": round(w.start, 3), "end": round(w.end, 3)})

    print(f"  {len(words)} words, language={info.language} ({info.language_probability:.2f})")
    return {
        "audio": audio.name,
        "language": info.language,
        "duration": round(info.duration, 3),
        "text": " ".join(text_parts).strip(),
        "words": words,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--input", default=None, help="transcribe this file instead of vo.wav")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    project = Project(args.slug).ensure()
    audio = Path(args.input) if args.input else project.vo
    if not audio.exists():
        raise SystemExit(f"No audio at {audio}. Run `python -m pipeline.tts {args.slug}` first.")

    model_size = args.model or env("WHISPER_MODEL", "small")
    result = transcribe(audio, model_size)

    out = Path(args.out) if args.out else project.words
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\n-> {out}")
    print(f"   next: python -m pipeline.captions {args.slug}")


if __name__ == "__main__":
    sys.exit(main())
