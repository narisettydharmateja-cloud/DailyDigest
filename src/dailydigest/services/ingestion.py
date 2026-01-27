"""Ingestion orchestration helpers."""

from __future__ import annotations

from typing import Iterable

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from dailydigest.models.db import IngestedItem
from dailydigest.models.ingestion import IngestedContent

logger = structlog.get_logger(__name__)


def persist_ingested_items(session: Session, items: Iterable[IngestedContent]) -> int:
    """Persist unique ingested items to the database."""

    payloads = _prepare_payloads(items)
    if not payloads:
        logger.info("ingestion.noop", reason="no-new-items")
        return 0

    stmt = pg_insert(IngestedItem).values(payloads)
    stmt = stmt.on_conflict_do_nothing(index_elements=[IngestedItem.__table__.c.content_hash])
    result = session.execute(stmt)
    inserted = result.rowcount or 0
    logger.info("ingestion.persisted", inserted=inserted, attempted=len(payloads))
    return inserted


def _prepare_payloads(items: Iterable[IngestedContent]) -> list[dict]:
    seen_hashes: set[str] = set()
    payloads: list[dict] = []
    for item in items:
        record = item.to_record()
        content_hash = record["content_hash"]
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)
        payloads.append(record)
    return payloads