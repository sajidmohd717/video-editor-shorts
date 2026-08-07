"""
YouTube upload.

    python -m pipeline.upload <slug> --file render/v6-master.mp4
    python -m pipeline.upload <slug> --file ... --privacy unlisted
    python -m pipeline.upload <slug> --file ... --publish-at "2026-08-10T14:00:00Z"
    python -m pipeline.upload --check          # verify credentials only

Metadata comes from the `publish` block of projects/<slug>/job.json, so title,
description and tags are versioned with the video rather than retyped.

DEFAULTS TO PRIVATE. Publishing is the one irreversible step in this pipeline —
a video is public the moment it lands, and unlisted/public require passing the
flag explicitly. The tool will also refuse to go public without --i-mean-it.

Setup (once):
  1. console.cloud.google.com -> new project
  2. Enable "YouTube Data API v3"
  3. Credentials -> OAuth client ID -> Desktop app -> download JSON
  4. Save it as .youtube-client-secret.json in the repo root (gitignored)
  5. First run opens a browser for you to authorise; the token is cached in
     .youtube-token.json (also gitignored)

NOTE ON THE AUDIT: until your Google Cloud project passes YouTube's API
compliance audit, uploaded videos are locked to private and cannot be made
public — including via publishAt scheduling. The upload and metadata still work,
so this is still worth using; you just flip visibility in Studio afterwards.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT, Project
from .profiles import load_job

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = ROOT / ".youtube-client-secret.json"
TOKEN = ROOT / ".youtube-token.json"

# 27 = Education, 28 = Science & Technology, 22 = People & Blogs
DEFAULT_CATEGORY = "28"


def get_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                raise SystemExit(
                    f"Missing {CLIENT_SECRET.name}.\n"
                    "  1. console.cloud.google.com -> new project\n"
                    "  2. Enable 'YouTube Data API v3'\n"
                    "  3. Credentials -> OAuth client ID -> Desktop app\n"
                    f"  4. Download the JSON and save it as {CLIENT_SECRET}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            # Opens your browser. You authorise in your own Google session —
            # the script never sees your password.
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def build_metadata(job, publish_at: str | None, privacy: str) -> dict:
    pub = job.raw.get("publish", {})
    if not pub.get("title"):
        raise SystemExit(
            f"job.json has no publish.title for {job.slug}.\n"
            "Add a publish block: title, description, tags."
        )

    description = pub.get("description", "")
    # Append source credit from the rights block — the channel promises every
    # speaker and source is credited, so it shouldn't depend on remembering.
    rights = job.rights
    credit_lines = []
    if rights.get("speaker"):
        credit_lines.append(f"Speaker: {rights['speaker']}")
    if rights.get("rightsHolder"):
        credit_lines.append(f"Source: {rights['rightsHolder']}")
    if credit_lines and "Speaker:" not in description:
        description = description.rstrip() + "\n\n" + "\n".join(credit_lines)

    body = {
        "snippet": {
            "title": pub["title"][:100],
            "description": description[:5000],
            "tags": pub.get("tags", [])[:60],
            "categoryId": str(pub.get("categoryId", DEFAULT_CATEGORY)),
        },
        "status": {
            "privacyStatus": privacy,
            # Required by YouTube; getting it wrong has legal consequences, so
            # it's explicit in the job rather than defaulted silently.
            "selfDeclaredMadeForKids": bool(pub.get("madeForKids", False)),
        },
    }

    if publish_at:
        # Scheduling requires the video to start private.
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at

    return body


def upload(service, path: Path, body: dict) -> str:
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), chunksize=4 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")
    request = service.videos().insert(
        part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  uploading… {int(status.progress() * 100)}%")
    return response["id"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--file", help="path relative to the project dir")
    ap.add_argument("--privacy", choices=["private", "unlisted", "public"],
                    default="private")
    ap.add_argument("--publish-at", default=None,
                    help="ISO8601 UTC, e.g. 2026-08-10T14:00:00Z (implies private)")
    ap.add_argument("--i-mean-it", action="store_true",
                    help="required to upload as public")
    ap.add_argument("--check", action="store_true", help="verify credentials and exit")
    args = ap.parse_args()

    if args.check:
        service = get_service()
        me = service.channels().list(part="snippet", mine=True).execute()
        items = me.get("items", [])
        if items:
            print(f"authorised as: {items[0]['snippet']['title']}")
        else:
            print("authorised, but no channel found on this account")
        return

    if not args.slug or not args.file:
        raise SystemExit("need <slug> and --file (or use --check)")

    if args.privacy == "public" and not args.i_mean_it:
        raise SystemExit(
            "Refusing to publish publicly without --i-mean-it.\n"
            "A public upload is immediate and effectively irreversible. Upload as\n"
            "private first, watch it back on YouTube, then flip it in Studio."
        )

    if args.publish_at:
        try:
            when = datetime.fromisoformat(args.publish_at.replace("Z", "+00:00"))
        except ValueError:
            raise SystemExit("--publish-at must be ISO8601, e.g. 2026-08-10T14:00:00Z")
        if when <= datetime.now(timezone.utc):
            raise SystemExit(f"--publish-at is in the past: {when.isoformat()}")

    job = load_job(args.slug)
    path = Project(args.slug).dir / args.file
    if not path.exists():
        raise SystemExit(f"No file at {path}")

    body = build_metadata(job, args.publish_at, args.privacy)

    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"file:    {path.name}  ({size_mb:.1f} MB)")
    print(f"title:   {body['snippet']['title']}")
    print(f"tags:    {', '.join(body['snippet']['tags']) or '(none)'}")
    print(f"privacy: {body['status']['privacyStatus']}", end="")
    print(f"  -> publishes {args.publish_at}" if args.publish_at else "")
    print()

    video_id = upload(get_service(), path, body)
    print(f"\nhttps://youtu.be/{video_id}")
    print(f"edit: https://studio.youtube.com/video/{video_id}/edit")

    # Record it on the job so the video is traceable back to the timeline.
    job.raw.setdefault("publish", {})["videoId"] = video_id
    job.raw["publish"]["uploadedAt"] = datetime.now(timezone.utc).isoformat()
    (Project(args.slug).dir / "job.json").write_text(
        json.dumps(job.raw, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
