"""DailyDigest package metadata."""

from __future__ import annotations

from importlib import metadata


def get_version() -> str:
    """Return the installed package version (best effort)."""

    try:
        return metadata.version("dailydigest")
    except metadata.PackageNotFoundError:  # pragma: no cover - local dev only
        return "0.0.0"


__all__ = ["get_version"]
