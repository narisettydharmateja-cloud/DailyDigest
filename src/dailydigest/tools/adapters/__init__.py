"""Source adapter registry."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from dailydigest.config import AppConfig
from dailydigest.models.ingestion import IngestedContent
from dailydigest.tools.adapters.hackernews import HackerNewsAdapter
from dailydigest.tools.adapters.rss import RSSAdapter

AdapterFactory = Callable[[AppConfig], "SourceAdapter"]


class SourceAdapter(Protocol):
    """Small protocol implemented by every adapter."""

    name: str

    def fetch_items(self, hours: int) -> Sequence[IngestedContent]:
        ...


def hackernews_factory(config: AppConfig) -> SourceAdapter:
    return HackerNewsAdapter(
        query=config.hacker_news_query,
        timeout=config.request_timeout_seconds,
        max_items=config.max_items_per_source,
    )


def rss_factory(config: AppConfig) -> SourceAdapter:
    return RSSAdapter(
        feeds=config.rss_feeds,
        timeout=config.request_timeout_seconds,
        max_items=config.max_items_per_source,
    )


AVAILABLE_ADAPTERS: dict[str, AdapterFactory] = {
    "hackernews": hackernews_factory,
    "rss": rss_factory,
}
