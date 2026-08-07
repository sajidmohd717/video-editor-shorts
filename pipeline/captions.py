"""
Caption building — script wording, Whisper timing.

    python -m pipeline.captions <slug> [--max-words 2]

Reads projects/<slug>/script.md and projects/<slug>/vo.words.json, and writes
projects/<slug>/captions.json.

Why not just use Whisper's text: Whisper transcribes what it HEARS. On a real
run it turned "productivity gain" into "productivity game" — and it will do
worse on model names, company names, and jargon, which is most of a tech
channel's vocabulary. Shipping ASR output as captions means shipping typos.

So the script is the wording authority and Whisper is only the timing authority.
The two are aligned token-by-token; where they disagree, the script's words win
and timings are interpolated across the disputed span.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher

from .config import Project

WORD_RE = re.compile(r"[^a-z0-9']+")


def normalise(token: str) -> str:
    return WORD_RE.sub("", token.lower())


def script_paragraphs(text: str) -> list[list[str]]:
    """Script split into paragraphs, each a word list. Blank lines separate."""
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    blocks = re.split(r"\n\s*\n", "\n".join(lines))
    return [b.split() for b in blocks if b.strip()]


def script_words(text: str) -> list[str]:
    return [w for para in script_paragraphs(text) for w in para]


def align(script: list[str], heard: list[dict]) -> list[dict]:
    """
    Map script words onto Whisper timings.

    Matching blocks take their timings directly. For a mismatched span the
    script's words are kept and timings are spread evenly across whatever
    interval Whisper assigned to the words it thought it heard — a caption a few
    tens of milliseconds off is invisible; a misspelled one is not.
    """
    a = [normalise(w) for w in script]
    b = [normalise(w["text"]) for w in heard]
    matcher = SequenceMatcher(None, a, b, autojunk=False)

    out: list[dict] = []
    repaired = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                h = heard[j1 + k]
                out.append({
                    "text": script[i1 + k],
                    "start": round(h["start"], 3),
                    "end": round(h["end"], 3),
                })
            continue

        # Disputed span: keep script wording, interpolate across the heard window.
        n = i2 - i1
        if n == 0:
            continue
        repaired += n

        if j2 > j1:
            span_start = heard[j1]["start"]
            span_end = heard[j2 - 1]["end"]
        else:
            # Pure insertion — borrow the seam between neighbours.
            span_start = heard[j1 - 1]["end"] if j1 > 0 else 0.0
            span_end = heard[j1]["start"] if j1 < len(heard) else span_start + 0.3 * n

        span_end = max(span_end, span_start + 0.12 * n)
        step = (span_end - span_start) / n
        for k in range(n):
            out.append({
                "text": script[i1 + k],
                "start": round(span_start + k * step, 3),
                "end": round(span_start + (k + 1) * step, 3),
            })

    return out, repaired


def chunk(words: list[dict], max_words: int = 2, max_gap: float = 0.45) -> list[dict]:
    """Group into 1-2 word cards, breaking on pauses and sentence ends."""
    cues: list[dict] = []
    buf: list[dict] = []

    def flush() -> None:
        if buf:
            cues.append({
                "start": buf[0]["start"],
                "end": buf[-1]["end"],
                "emphasis": "none",
                "words": [dict(w) for w in buf],
            })
            buf.clear()

    for i, w in enumerate(words):
        buf.append(w)
        ends = w["text"].rstrip("\"'”’").endswith((".", "?", "!", ",", ":", ";"))
        gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 0
        if len(buf) >= max_words or ends or gap > max_gap:
            flush()
    flush()

    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else c["end"] + 0.4
        c["end"] = round(min(nxt, c["end"] + 0.5), 3)
    return cues


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--max-words", type=int, default=2)
    args = ap.parse_args()

    project = Project(args.slug)
    if not project.words.exists():
        raise SystemExit(f"No timings at {project.words}. Run pipeline.transcribe first.")

    heard = json.loads(project.words.read_text(encoding="utf-8"))["words"]
    raw = project.script.read_text(encoding="utf-8")
    paras = script_paragraphs(raw)
    script = [w for p in paras for w in p]

    words, repaired = align(script, heard)
    cues = chunk(words, args.max_words)

    # Paragraph spans, derived from where each paragraph's words actually landed.
    # These drive VO placement in the narrated planner — deriving them means a
    # voice or engine swap re-times the edit instead of needing hand-editing.
    spans: list[dict] = []
    i = 0
    for n, para in enumerate(paras):
        chunk_words = words[i:i + len(para)]
        if chunk_words:
            spans.append({
                "index": n,
                "start": chunk_words[0]["start"],
                "end": chunk_words[-1]["end"],
                "text": " ".join(para),
            })
        i += len(para)

    out = project.dir / "captions.json"
    out.write_text(
        json.dumps({"words": words, "cues": cues, "paragraphs": spans}, indent=2),
        encoding="utf-8",
    )

    print(f"script={len(script)} heard={len(heard)} aligned={len(words)}")
    for s in spans:
        print(f"  para {s['index']}: {s['start']:6.2f} - {s['end']:6.2f}  {s['text'][:52]}...")
    if repaired:
        print(f"  {repaired} word(s) corrected back to the script's wording")
    print(f"  {len(cues)} caption cards")
    print(f"\n-> {out}")


if __name__ == "__main__":
    sys.exit(main())
