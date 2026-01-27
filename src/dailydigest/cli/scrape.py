"""Command-line interface for running ingestion scrapers."""

from __future__ import annotations

import structlog
import typer

from dailydigest.config import AppConfig, get_config
from dailydigest.logging import configure_logging
from dailydigest.services.database import (
    build_engine,
    create_session_factory,
    init_database,
    session_scope,
)
from dailydigest.services.ingestion import persist_ingested_items
from dailydigest.tools.adapters import AVAILABLE_ADAPTERS, AdapterFactory, SourceAdapter

app = typer.Typer(add_completion=False, help="Fetch and store news content locally.")


def _parse_sources(value: str | None) -> list[str]:
    if not value:
        return []
    return [entry.strip().lower() for entry in value.split(",") if entry.strip()]


@app.command("run")
def run(
    sources: str = typer.Option(
        ",".join(AVAILABLE_ADAPTERS.keys()),
        "--sources",
        help="Comma-separated adapter names to run (available: " + ", ".join(AVAILABLE_ADAPTERS.keys()) + ")",
    ),
    hours: int | None = typer.Option(
        None,
        "--hours",
        min=1,
        help="Ingestion lookback window in hours (defaults to config value)",
    ),
) -> None:
    """Run selected adapters once and persist outputs to PostgreSQL."""

    configure_logging()
    log = structlog.get_logger("cli.scrape")
    config = get_config()

    requested = _parse_sources(sources) or list(AVAILABLE_ADAPTERS.keys())
    missing = [name for name in requested if name not in AVAILABLE_ADAPTERS]
    if missing:
        raise typer.BadParameter(f"Unknown adapter(s): {', '.join(missing)}")

    window = hours or config.default_ingestion_window_hours

    engine = build_engine(config.database_url)
    init_database(engine)
    session_factory = create_session_factory(engine)

    adapters = [_instantiate_adapter(name, AVAILABLE_ADAPTERS[name], config) for name in requested]

    all_items = []
    for adapter in adapters:
        try:
            items = adapter.fetch_items(window)
            log.info("adapter.success", adapter=adapter.name, fetched=len(items))
            all_items.extend(items)
        except Exception as exc:  # noqa: BLE001
            log.exception("adapter.failure", adapter=adapter.name, error=str(exc))

    log.info("scrape.fetch_complete", total=len(all_items))

    with session_scope(session_factory) as session:
        inserted = persist_ingested_items(session, all_items)

    log.info("scrape.completed", inserted=inserted, fetched=len(all_items))


@app.command("sources")
def list_sources() -> None:
    """List available adapters."""

    for name in AVAILABLE_ADAPTERS:
        typer.echo(f"- {name}")


def _instantiate_adapter(name: str, factory: AdapterFactory, config: AppConfig) -> SourceAdapter:
    adapter = factory(config)
    if adapter.name != name:
        raise RuntimeError(f"Adapter name mismatch: expected {name}, got {adapter.name}")
    return adapter
