"""Generic RSS/Atom adapter built on feedparser."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

import feedparser

from dailydigest.models.ingestion import IngestedContent

USER_AGENT = "DailyDigestBot/0.1 (+https://local.run/dailydigest)"


class RSSAdapter:
    """Fetch and normalize entries from a list of RSS/Atom feeds."""

    name = "rss"

    def __init__(self, feeds: list[str], timeout: float, max_items: int) -> None:
        self.feeds = feeds
        self.timeout = timeout
        self.max_items = max_items
        self.log = structlog.get_logger(__name__).bind(adapter=self.name)
        self._retryer = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, max=5),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        )

    def fetch_items(self, hours: int) -> list[IngestedContent]:
        since = datetime.now(tz=UTC) - timedelta(hours=hours)
        collected: list[IngestedContent] = []
        for feed_url in self.feeds:
            response_text = self._fetch_feed(feed_url)
            parsed = feedparser.parse(response_text)
            feed_title = parsed.feed.get("title") if parsed.feed else feed_url
            language = parsed.feed.get("language") if parsed.feed else None
            feed_items = []
            for entry in parsed.entries:
                published = self._entry_datetime(entry)
                if published and published < since:
                    continue
                try:
                    feed_items.append(self._map_entry(entry, feed_title, language))
                except Exception as exc:  # noqa: BLE001
                    self.log.warning(
                        "adapter.entry_failed",
                        reason=str(exc),
                        feed=feed_url,
                        entry_id=getattr(entry, "id", None),
                    )
                if len(feed_items) >= self.max_items:
                    break
            collected.extend(feed_items)
        self.log.info("adapter.completed", count=len(collected))
        return collected

    def _fetch_feed(self, url: str) -> str:
        headers = {"User-Agent": USER_AGENT}
        for attempt in self._retryer:
            with attempt:
                with httpx.Client(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.text
        raise RuntimeError("Retryer exhausted without raising")

    def _entry_datetime(self, entry: Any) -> datetime | None:
        struct_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not struct_time:
            return None
        timestamp = calendar.timegm(struct_time)
        return datetime.fromtimestamp(timestamp, tz=UTC)

    def _map_entry(self, entry: Any, feed_title: str, feed_language: str | None) -> IngestedContent:
        link = getattr(entry, "link", None)
        if not link:
            raise ValueError("Entry missing link")
        entry_id = getattr(entry, "id", link)
        summary = getattr(entry, "summary", None)
        content_parts = []
        for content in getattr(entry, "content", []) or []:
            value = content.get("value") if isinstance(content, dict) else getattr(content, "value", None)
            if value:
                content_parts.append(value)
        content_text = "\n\n".join(content_parts) if content_parts else summary
        categories = [
            term.get("term") if isinstance(term, dict) else term
            for term in (getattr(entry, "tags", None) or [])
        ]
        metadata = {
            "feed": feed_title,
            "categories": categories,
        }
        return IngestedContent(
            source=self.name,
            external_id=str(entry_id),
            title=getattr(entry, "title", feed_title),
            summary=summary,
            content=content_text,
            url=link,
            published_at=self._entry_datetime(entry),
            language=getattr(entry, "language", feed_language),
            metadata=metadata,
        )
