"""
Find and pull news/interview clips for the long-form archival format.

    python -m pipeline.newsclip search "openai board fires sam altman" --news
    python -m pipeline.newsclip search "charlie munger incentives" --channel CNBC
    python -m pipeline.newsclip grab <slug> <videoId> --start 71.5 --end 76.0 --name board-fires

Search uses the YouTube Data API (already authorised for upload); download uses
yt-dlp. Together that turns "I need footage of X" into a shortlist you can
actually look at, instead of an afternoon of manual searching.

RIGHTS — read this before using it
----------------------------------
Broadcast news clips are a **different and weaker** position than the conference
footage we've used so far:

  * A talk posted by Y Combinator is one rights holder, and our use is
    commentary on the speaker's own words.
  * A CNBC or CNN segment is owned by a broadcaster who actively runs Content ID
    and whose business is licensing footage.

Short excerpts used as evidence for a claim the narration is making is the
standard practice for commentary channels, and it's a defensible position. It is
NOT a risk-free one. Practical guidance:

  * Keep excerpts short — a few seconds, only as long as the point needs.
  * The excerpt must be evidence for something the narration says, never filler.
  * Never build a segment that would still work if our narration were removed.
  * Expect Content ID claims. A claim usually redirects revenue rather than
    striking the channel, but on a monetised video that still costs money.
  * Prefer the primary source when it exists: if a broadcaster is reporting on a
    hearing, use the hearing (C-SPAN, often public domain) rather than the report.

Every clip pulled is recorded in the manifest with its source URL, channel and
date, so an attribution list can be generated rather than reconstructed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import Project

# Broadcasters and primary sources worth searching first. C-SPAN and official
# government channels are listed first deliberately — hearings and press
# briefings are frequently public domain or freely licensed, which is a far
# better position than a network's report about the same hearing.
PRIMARY = ["C-SPAN", "The White House", "Forbes Breaking News"]
NEWS = ["CNBC", "Bloomberg Television", "CNN", "CBS News", "ABC News",
        "Reuters", "Associated Press", "Yahoo Finance", "Fox Business"]


def service():
    from .upload import get_service
    return get_service()


def search(query: str, limit: int, channel: str | None, news: bool) -> list[dict]:
    yt = service()
    q = query if not channel else f"{query} {channel}"
    resp = yt.search().list(
        part="snippet", q=q, type="video", maxResults=min(limit, 25),
        order="relevance", relevanceLanguage="en",
    ).execute()

    items = []
    for it in resp.get("items", []):
        sn = it["snippet"]
        items.append({
            "videoId": it["id"]["videoId"],
            "title": sn["title"],
            "channel": sn["channelTitle"],
            "published": sn["publishedAt"][:10],
            "url": f"https://youtu.be/{it['id']['videoId']}",
        })

    if news:
        wanted = [c.lower() for c in PRIMARY + NEWS]
        items.sort(key=lambda i: next(
            (n for n, c in enumerate(wanted) if c in i["channel"].lower()), 99))
    return items


def grab(project: Project, video_id: str, start: float, end: float,
         name: str, height: int) -> Path:
    """Download just the needed span and cut it, rather than the whole video."""
    clips = project.assets / "news"
    clips.mkdir(parents=True, exist_ok=True)
    raw = clips / f"_{video_id}.mp4"

    if not raw.exists():
        subprocess.run([
            "yt-dlp", "--no-playlist", "-f",
            f"bv*[height<={height}]+ba/b[height<={height}]",
            "--merge-output-format", "mp4",
            # Fetch only the span we need plus a margin — a 40-minute source for
            # a 4-second excerpt is pure waste.
            "--download-sections", f"*{max(0, start - 3)}-{end + 3}",
            "--force-keyframes-at-cuts",
            "-o", str(raw), f"https://youtu.be/{video_id}",
        ], check=True)

    out = clips / f"{name}.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(raw),
        "-ss", str(max(0, 3 if start >= 3 else start)), "-t", str(end - start),
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "160k", str(out),
    ], check=True)
    return out


def record(project: Project, entry: dict) -> Path:
    manifest = project.assets / "news" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    data = {"clips": []}
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
    data["clips"] = [c for c in data["clips"] if c["file"] != entry["file"]] + [entry]
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=12)
    s.add_argument("--channel", default=None)
    s.add_argument("--news", action="store_true",
                   help="rank primary sources and broadcasters first")

    g = sub.add_parser("grab")
    g.add_argument("slug")
    g.add_argument("video_id")
    g.add_argument("--start", type=float, required=True)
    g.add_argument("--end", type=float, required=True)
    g.add_argument("--name", required=True)
    g.add_argument("--why", default="", help="what claim this clip evidences")
    g.add_argument("--height", type=int, default=1080)

    args = ap.parse_args()

    if args.cmd == "search":
        for i in search(args.query, args.limit, args.channel, args.news):
            print(f"  {i['videoId']}  {i['published']}  {i['channel'][:22]:<22} {i['title'][:58]}")
        print("\n  grab with: python -m pipeline.newsclip grab <slug> <videoId> "
              "--start S --end E --name NAME --why '...'")
        return

    if args.end - args.start > 12:
        print("  ! excerpt is over 12s — keep it to what the point needs (see module docstring)")

    project = Project(args.slug).ensure()
    out = grab(project, args.video_id, args.start, args.end, args.name, args.height)
    entry = {
        "file": project.asset_ref(out),
        "videoId": args.video_id,
        "url": f"https://youtu.be/{args.video_id}",
        "sourceStart": args.start,
        "sourceEnd": args.end,
        "seconds": round(args.end - args.start, 2),
        "why": args.why,
        "grabbedAt": datetime.now(timezone.utc).isoformat(),
    }
    m = record(project, entry)
    print(f"-> {out}  ({entry['seconds']}s)")
    print(f"   manifest: {m}")


if __name__ == "__main__":
    sys.exit(main())
