"""Text and hashing helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def fingerprint_content(*values: str | Iterable[str | None] | None) -> str:
    """Return a deterministic hash for the provided textual fields."""

    flattened: list[str] = []
    for value in values:
        if value is None:
            flattened.append("")
            continue
        if isinstance(value, str):
            flattened.append(value)
            continue
        parts = [part or "" for part in value]
        flattened.append("||".join(parts))

    joined = "::".join(flattened)
    return hashlib.sha256(joined.encode("utf-8", errors="ignore")).hexdigest()
