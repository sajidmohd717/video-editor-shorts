"""
Stock footage / photo fetching.

    python -m pipeline.stock <slug> --query "server rack" --kind video --count 3
    python -m pipeline.stock <slug> --from-plan          # fetch everything a plan needs
    python -m pipeline.stock --check                     # verify keys work

Downloads into public/<slug>/stock/ and writes a manifest at
public/<slug>/stock/manifest.json so the planner can look up what's available
without re-hitting the APIs.

Pexels and Pixabay are queried together and results interleaved. Two reasons:
their libraries barely overlap, and if one search returns nothing usable the
other usually saves the shot. Both licences permit monetised commercial use with
no attribution required, which is why these two and not the alternatives.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import requests

from .config import Project, env

TIMEOUT = 30
UA = {"User-Agent": "video-editor-shorts/0.1"}


# --------------------------------------------------------------------------- #
# Providers                                                                     #
# --------------------------------------------------------------------------- #

def pexels(query: str, kind: str, count: int) -> list[dict]:
    key = env("PEXELS_API_KEY")
    if not key:
        return []

    if kind == "video":
        url = "https://api.pexels.com/videos/search"
        params = {"query": query, "per_page": count, "orientation": "portrait", "size": "medium"}
    else:
        url = "https://api.pexels.com/v1/search"
        params = {"query": query, "per_page": count, "orientation": "portrait"}

    r = requests.get(url, headers={**UA, "Authorization": key}, params=params, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  pexels {kind}: HTTP {r.status_code}")
        return []

    out: list[dict] = []
    if kind == "video":
        for v in r.json().get("videos", []):
            # Pick the largest file at or under 1920 tall — beyond that we're
            # downloading 4K to crop it into a 2-second cutaway.
            files = sorted(
                (f for f in v.get("video_files", []) if f.get("height")),
                key=lambda f: f["height"],
            )
            best = next((f for f in reversed(files) if f["height"] <= 1920), files[-1] if files else None)
            if not best:
                continue
            out.append({
                "provider": "pexels", "kind": "video", "id": str(v["id"]),
                "url": best["link"], "width": best.get("width"), "height": best.get("height"),
                "duration": v.get("duration"), "credit": v.get("user", {}).get("name", ""),
                "source": v.get("url", ""),
            })
    else:
        for p in r.json().get("photos", []):
            out.append({
                "provider": "pexels", "kind": "photo", "id": str(p["id"]),
                "url": p["src"]["large2x"], "width": p.get("width"), "height": p.get("height"),
                "credit": p.get("photographer", ""), "source": p.get("url", ""),
            })
    return out


def pixabay(query: str, kind: str, count: int) -> list[dict]:
    key = env("PIXABAY_API_KEY")
    if not key:
        return []

    if kind == "video":
        url = "https://pixabay.com/api/videos/"
        # NB: Pixabay's video endpoint has no orientation parameter — unlike its
        # image endpoint. Everything here comes back landscape, so these clips
        # must be reframed to 9:16 rather than used as-is. Fine for texture shots
        # (racks, hands, machinery); bad for anything with real composition.
        params = {"key": key, "q": query, "per_page": max(3, count), "video_type": "film"}
    else:
        url = "https://pixabay.com/api/"
        params = {
            "key": key, "q": query, "per_page": max(3, count),
            "image_type": "photo", "orientation": "vertical",
        }

    r = requests.get(url, headers=UA, params=params, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  pixabay {kind}: HTTP {r.status_code}")
        return []

    out: list[dict] = []
    for h in r.json().get("hits", []):
        if kind == "video":
            v = h.get("videos", {})
            best = v.get("large") or v.get("medium") or v.get("small")
            if not best or not best.get("url"):
                continue
            out.append({
                "provider": "pixabay", "kind": "video", "id": str(h["id"]),
                "url": best["url"], "width": best.get("width"), "height": best.get("height"),
                "duration": h.get("duration"), "credit": h.get("user", ""),
                "source": h.get("pageURL", ""),
            })
        else:
            out.append({
                "provider": "pixabay", "kind": "photo", "id": str(h["id"]),
                "url": h.get("largeImageURL", ""), "width": h.get("imageWidth"),
                "height": h.get("imageHeight"), "credit": h.get("user", ""),
                "source": h.get("pageURL", ""),
            })
    return [o for o in out if o["url"]]


def interleave(a: list[dict], b: list[dict], limit: int) -> list[dict]:
    merged: list[dict] = []
    for i in range(max(len(a), len(b))):
        if i < len(a):
            merged.append(a[i])
        if i < len(b):
            merged.append(b[i])
    return merged[:limit]


# --------------------------------------------------------------------------- #
# Download                                                                      #
# --------------------------------------------------------------------------- #

MAX_EDGE = 1920


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True,
    ).stdout.split()
    if len(out) < 3:
        return {}
    return {"width": int(out[0]), "height": int(out[1]), "duration": round(float(out[2]), 2)}


def normalise_video(path: Path) -> None:
    """
    Downscale anything above 1920 on the long edge, in place.

    A 4K source for a two-second cutaway costs render time on every frame and
    buys nothing — the clip is getting cropped to 1080x1920 regardless.
    """
    info = probe(path)
    if not info:
        return
    if max(info["width"], info["height"]) <= MAX_EDGE:
        return

    tmp = path.with_suffix(".tmp.mp4")
    scale = f"scale='if(gt(iw,ih),{MAX_EDGE},-2)':'if(gt(iw,ih),-2,{MAX_EDGE})'"
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", scale,
         "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-an", str(tmp)],
        capture_output=True,
    )
    if result.returncode == 0 and tmp.exists():
        before = path.stat().st_size
        path.unlink()
        tmp.rename(path)
        print(f"    downscaled {info['width']}x{info['height']} "
              f"({before // 1_000_000}MB -> {path.stat().st_size // 1_000_000}MB)")
    else:
        tmp.unlink(missing_ok=True)


def download(item: dict, dest_dir: Path) -> Path | None:
    ext = ".mp4" if item["kind"] == "video" else ".jpg"
    dest = dest_dir / f"{item['provider']}-{item['kind']}-{item['id']}{ext}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    try:
        with requests.get(item["url"], headers=UA, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
    except Exception as exc:  # noqa: BLE001 - a dead asset shouldn't kill the batch
        print(f"  ! {item['provider']}/{item['id']}: {exc}")
        dest.unlink(missing_ok=True)
        return None

    if item["kind"] == "video":
        normalise_video(dest)
    return dest


def fetch(project: Project, query: str, kind: str, count: int) -> list[dict]:
    stock_dir = project.assets / "stock"
    stock_dir.mkdir(parents=True, exist_ok=True)

    results = interleave(pexels(query, kind, count), pixabay(query, kind, count), count)
    if not results:
        print(f"  no results for {query!r} ({kind})")
        return []

    saved: list[dict] = []
    for item in results:
        path = download(item, stock_dir)
        if not path:
            continue
        item["query"] = query
        item["file"] = project.asset_ref(path)

        # Record the real dimensions from the file, not the API's claim, and flag
        # orientation so the planner knows which assets need reframing.
        actual = probe(path) if item["kind"] == "video" else {}
        if actual:
            item.update(actual)
        w, h = item.get("width") or 0, item.get("height") or 0
        item["orientation"] = "portrait" if h > w else "landscape" if w > h else "square"

        saved.append(item)
        print(f"  + {item['file']}  ({item['provider']}, {item.get('credit') or 'unknown'}, "
              f"{item['orientation']} {w}x{h})")
    return saved


def write_manifest(project: Project, entries: list[dict]) -> Path:
    """
    Manifest doubles as the attribution record.

    The channel's description promises every source is credited, so keeping
    provider/creator/source-URL per asset means a credit list can be generated
    rather than reconstructed from memory later.
    """
    manifest = project.assets / "stock" / "manifest.json"
    existing: list[dict] = []
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8")).get("assets", [])

    by_file = {e["file"]: e for e in existing}
    for e in entries:
        by_file[e["file"]] = e

    manifest.write_text(
        json.dumps({"assets": list(by_file.values())}, indent=2), encoding="utf-8"
    )
    return manifest


def check_keys() -> int:
    ok = True
    for name, fn in (("PEXELS_API_KEY", pexels), ("PIXABAY_API_KEY", pixabay)):
        if not env(name):
            print(f"  {name}: not set in .env")
            ok = False
            continue
        hits = fn("city skyline", "photo", 1)
        print(f"  {name}: {'OK' if hits else 'set, but returned nothing (key may be wrong)'}")
        ok = ok and bool(hits)
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--query", action="append", default=[], help="repeatable")
    ap.add_argument("--kind", choices=["video", "photo"], default="video")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--check", action="store_true", help="verify keys and exit")
    args = ap.parse_args()

    if args.check:
        raise SystemExit(check_keys())
    if not args.slug or not args.query:
        raise SystemExit("need <slug> and at least one --query (or use --check)")

    project = Project(args.slug).ensure()
    entries: list[dict] = []
    for q in args.query:
        print(f"{q!r} ({args.kind}):")
        entries += fetch(project, q, args.kind, args.count)

    manifest = write_manifest(project, entries)
    print(f"\n{len(entries)} asset(s) -> {manifest}")


if __name__ == "__main__":
    sys.exit(main())
