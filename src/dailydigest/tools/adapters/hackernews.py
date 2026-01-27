"""Hacker News adapter powered by the official Algolia API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from dailydigest.models.ingestion import IngestedContent

BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"
USER_AGENT = "DailyDigestBot/0.1 (+https://local.run/dailydigest)"


class HackerNewsAdapter:
    """Fetch recent Hacker News stories via the Algolia search API."""

    name = "hackernews"

    def __init__(self, query: str, timeout: float, max_items: int) -> None:
        self.query = query
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
        hits_per_page = min(self.max_items, 100)
        params = {
            "query": self.query,
            "tags": "story",
            "hitsPerPage": hits_per_page,
            "numericFilters": f"created_at_i>{int(since.timestamp())}",
        }

        response = self._perform_request(params)
        payload = response.json()
        hits = payload.get("hits", [])
        items: list[IngestedContent] = []
        for hit in hits[: self.max_items]:
            try:
                items.append(self._map_hit(hit))
            except Exception as exc:  # noqa: BLE001 - best effort ingestion
                self.log.warning("adapter.item_failed", reason=str(exc), hit_id=hit.get("objectID"))
        self.log.info("adapter.completed", count=len(items))
        return items

    def _perform_request(self, params: dict[str, Any]) -> httpx.Response:
        headers = {"User-Agent": USER_AGENT}
        for attempt in self._retryer:
            with attempt:
                with httpx.Client(timeout=self.timeout, headers=headers) as client:
                    response = client.get(BASE_URL, params=params)
                    response.raise_for_status()
                    return response
        raise RuntimeError("Retryer exhausted without raising")

    def _map_hit(self, hit: dict[str, Any]) -> IngestedContent:
        object_id = str(hit["objectID"])
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        title = hit.get("title") or hit.get("story_text") or "(untitled)"
        summary = hit.get("story_text") or hit.get("title")
        content = hit.get("story_text")
        published_raw = hit.get("created_at")
        metadata = {
            "author": hit.get("author"),
            "points": hit.get("points"),
            "num_comments": hit.get("num_comments"),
            "tags": hit.get("_tags", []),
        }

        return IngestedContent(
            source=self.name,
            external_id=object_id,
            title=title,
            summary=summary,
            content=content,
            url=url,
            published_at=published_raw,
            engagement=hit.get("points"),
            metadata=metadata,
        )
