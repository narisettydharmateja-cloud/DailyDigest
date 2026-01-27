"""Database helpers for PostgreSQL access."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from dailydigest.models import db

SessionFactory = sessionmaker[Session]
SessionT = TypeVar("SessionT", bound=Session)


def build_engine(database_url: str) -> Engine:
    """Create an SQLAlchemy engine with sensible defaults."""

    return create_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)


def create_session_factory(engine: Engine) -> SessionFactory:
    """Create a configured session factory bound to the engine."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: Callable[[], SessionT]) -> Iterator[SessionT]:
    """Provide a transactional scope for a series of operations."""

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(engine: Engine) -> None:
    """Create required tables if they do not already exist."""

    db.Base.metadata.create_all(engine)
