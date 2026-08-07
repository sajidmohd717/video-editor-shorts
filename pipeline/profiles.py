"""
Profile and job resolution.

A **profile** is channel identity: brand, caption style, pacing defaults, voice,
audio targets. It's reusable across every video on that channel.

A **job** is one video: which source, which passages, rights and attribution,
which assets, which beats. It's specific and disposable.

Resolution order, later layers winning key-by-key:

    profiles/default.json
      + profiles/<profile>.json          (via "extends")
      + job.profileOverrides             (per-video experiment)

Arrays are REPLACED, not merged. Merging a list of framings or keywords produces
something nobody asked for; replacing is predictable.

Keeping channel facts out of the planners is the whole point — a planner that
hardcodes a brand colour or an asset path can only ever make one video. If you
find yourself adding a channel name to engine code, add it to a profile instead.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ROOT, Project

PROFILES = ROOT / "profiles"


def _merge(base: dict, layer: dict) -> dict:
    out = dict(base)
    for key, value in layer.items():
        if key in ("id", "extends"):
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value  # arrays and scalars replace
    return out


def load_profile(name: str) -> dict:
    path = PROFILES / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"No profile at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    parent = data.get("extends")
    if parent:
        merged = _merge(load_profile(parent), data)
        # _merge skips "id" so a child can't accidentally rename its parent's
        # keys, but the RESULT should carry the child's identity.
        merged["id"] = data.get("id", parent)
        return merged
    return data


@dataclass(frozen=True)
class Job:
    """One video's configuration, with its profile already resolved into it."""

    slug: str
    raw: dict
    profile: dict

    @property
    def source(self) -> dict:
        return self.raw.get("source", {})

    @property
    def passages(self) -> list[tuple[float, float]]:
        """Source-clip spans worth keeping, in source time."""
        return [tuple(p) for p in self.source.get("passages", [])]

    @property
    def broll(self) -> dict[str, str]:
        return self.raw.get("broll", {})

    @property
    def beats(self) -> list[dict]:
        return self.raw.get("beats", [])

    @property
    def rights(self) -> dict:
        return self.raw.get("rights", {})

    def check_rights(self) -> list[str]:
        """
        Warn about anything that would make this unsafe to publish.

        Attribution does NOT satisfy YouTube's reused-content test — that asks
        whether you added something substantial. These checks are about catching
        an obviously-unpublishable job before render time, not about being a
        legal opinion.
        """
        problems: list[str] = []
        r = self.rights
        if not r.get("sourceUrl"):
            problems.append("rights.sourceUrl missing — can't credit the source")
        if not r.get("speaker"):
            problems.append("rights.speaker missing — channel promises to credit speakers")
        if r.get("clearance") not in ("commentary", "licensed", "own"):
            problems.append(
                f"rights.clearance is {r.get('clearance')!r}; expected "
                "'commentary', 'licensed' or 'own'"
            )
        return problems

    def get(self, path: str, default: Any = None) -> Any:
        """Dotted lookup into the resolved profile, e.g. get('pacing.arollShotSeconds')."""
        node: Any = self.profile
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def load_job(slug: str) -> Job:
    project = Project(slug)
    path = project.dir / "job.json"
    if not path.exists():
        raise SystemExit(
            f"No job at {path}.\n"
            "Create one — see projects/yc-sam-01/job.json for the shape."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))

    profile = load_profile(raw.get("profile", "default"))
    overrides = raw.get("profileOverrides")
    if overrides:
        profile = _merge(profile, overrides)

    return Job(slug=slug, raw=raw, profile=profile)
