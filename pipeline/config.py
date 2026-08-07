"""Shared paths and environment config for the pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PROJECTS = ROOT / "projects"
PUBLIC = ROOT / "public"  # Remotion's staticFile() root


@dataclass(frozen=True)
class Project:
    """
    One video. Everything for a given short lives under projects/<slug>/.

    Assets land in public/<slug>/ rather than the project dir, because Remotion's
    staticFile() can only resolve paths under public/. The timeline stores the
    public-relative path.
    """

    slug: str

    @property
    def dir(self) -> Path:
        return PROJECTS / self.slug

    @property
    def script(self) -> Path:
        return self.dir / "script.md"

    @property
    def vo(self) -> Path:
        return self.dir / "vo.wav"

    @property
    def words(self) -> Path:
        return self.dir / "vo.words.json"

    @property
    def timeline(self) -> Path:
        return self.dir / "timeline.json"

    @property
    def assets(self) -> Path:
        return PUBLIC / self.slug

    @property
    def render(self) -> Path:
        return self.dir / "render"

    def ensure(self) -> "Project":
        for p in (self.dir, self.assets, self.render):
            p.mkdir(parents=True, exist_ok=True)
        return self

    def asset_ref(self, path: Path) -> str:
        """Path as Remotion's staticFile() expects it, relative to public/."""
        return path.relative_to(PUBLIC).as_posix()


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default) or default


def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise SystemExit(
            f"Missing {key}. Copy .env.example to .env and fill it in.\n"
            f"  (see {ROOT / '.env.example'})"
        )
    return value
