"""Engine lifecycle and one session per request."""
from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    options = {"hide_parameters": True}
    if url.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False, "timeout": 10}
        if not url.database or url.database == ":memory:":
            options["poolclass"] = StaticPool
        else:
            path = Path(url.database)
            if not path.is_absolute():
                path = BACKEND_DIR / path
            path = path.resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            url = url.set(database=str(path))
    return create_engine(url, **options)


def init_database(engine: Engine) -> None:
    from app.models.analysis_record import AnalysisRecord  # noqa: F401

    Base.metadata.create_all(engine)


def get_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.session_factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
