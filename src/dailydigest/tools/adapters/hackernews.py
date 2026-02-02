"""Hacker News adapter using the official RSS feed."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential
import feedparser

from dailydigest.models.ingestion import IngestedContent

RSS_URL = "https://news.ycombinator.com/rss"
USER_AGENT = "DailyDigestBot/0.1 (+https://local.run/dailydigest)"


class HackerNewsAdapter:
    """Fetch recent Hacker News stories via the official RSS feed."""

    name = "hackernews"

    def __init__(self, query: str, timeout: float, max_items: int) -> None:
        self.query = query.lower() if query else ""
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
        
        response_text = self._fetch_rss()
        parsed = feedparser.parse(response_text)
        
        items: list[IngestedContent] = []
        for entry in parsed.entries:
            if len(items) >= self.max_items:
                break
            
            published = self._entry_datetime(entry)
            if published and published < since:
                continue
            
            try:
                item = self._map_entry(entry)
                # Filter by query keywords if provided
                if self.query:
                    title_lower = (item.title or "").lower()
                    if not any(kw in title_lower for kw in self.query.replace('"', '').split(' or ')):
                        continue
                items.append(item)
            except Exception as exc:  # noqa: BLE001
                self.log.warning("adapter.item_failed", reason=str(exc), entry_id=getattr(entry, "id", None))
        
        self.log.info("adapter.completed", count=len(items))
        return items

    def _fetch_rss(self) -> str:
        headers = {"User-Agent": USER_AGENT}
        for attempt in self._retryer:
            with attempt:
                with httpx.Client(timeout=self.timeout, headers=headers, verify=False, follow_redirects=True) as client:
                    response = client.get(RSS_URL)
                    response.raise_for_status()
                    return response.text
        raise RuntimeError("Retryer exhausted without raising")

    def _entry_datetime(self, entry: Any) -> datetime | None:
        struct_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not struct_time:
            return None
        timestamp = calendar.timegm(struct_time)
        return datetime.fromtimestamp(timestamp, tz=UTC)

    def _map_entry(self, entry: Any) -> IngestedContent:
        link = getattr(entry, "link", None)
        if not link:
            raise ValueError("Entry missing link")
        
        # Extract item ID from comments URL
        comments_url = getattr(entry, "comments", "")
        object_id = ""
        if "item?id=" in comments_url:
            object_id = comments_url.split("item?id=")[-1]
        else:
            object_id = link
        
        title = getattr(entry, "title", "(untitled)")
        summary = getattr(entry, "description", None)
        
        metadata = {
            "comments_url": comments_url,
        }

        return IngestedContent(
            source=self.name,
            external_id=str(object_id),
            title=title,
            summary=summary,
            content=summary,
            url=link,
            published_at=self._entry_datetime(entry),
            metadata=metadata,
        )
