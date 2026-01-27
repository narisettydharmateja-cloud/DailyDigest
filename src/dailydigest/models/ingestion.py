"""Pydantic models used throughout the ingestion pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator

from dailydigest.utils.text import fingerprint_content


class IngestedContent(BaseModel):
    """Normalized representation of a scraped item before persistence."""

    source: str
    external_id: str
    title: str
    url: AnyUrl
    summary: str | None = None
    content: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    engagement: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    @field_validator("published_at", mode="before")
    @classmethod
    def ensure_timezone(cls, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("Z", "+00:00")
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        raise TypeError("Unsupported datetime type for published_at")

    def to_record(self) -> dict[str, Any]:
        """Return a dict ready for SQLAlchemy bulk inserts."""

        url = str(self.url)
        content_hash = fingerprint_content(
            self.source,
            self.external_id,
            url,
            self.title,
            self.content or self.summary or "",
        )
        return {
            "source": self.source,
            "external_id": self.external_id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "url": url,
            "language": self.language,
            "published_at": self.published_at,
            "metadata_json": self.metadata or None,
            "content_hash": content_hash,
            "engagement": self.engagement,
        }
