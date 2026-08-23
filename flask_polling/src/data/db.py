"""إنشاء اتصال SQLite محلي مضبوط لاحتياجات منصة صوّت."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from data.models import Base

SQLITE_BUSY_TIMEOUT_MS = 5_000
SessionFactory = sessionmaker[Session]


def create_sqlite_engine(database_url: str) -> Engine:
    """ينشئ محرك SQLite مع ضوابط السلامة المطلوبة لكل اتصال جديد."""

    if not database_url.startswith("sqlite"):
        raise ValueError("database_url must use SQLite")

    engine = create_engine(
        database_url,
        connect_args={"timeout": SQLITE_BUSY_TIMEOUT_MS / 1_000},
    )

    @event.listens_for(engine, "connect")
    def _configure_connection(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
            cursor.execute("PRAGMA journal_mode = WAL")
        finally:
            cursor.close()

    return engine


def create_schema(engine: Engine) -> None:
    """ينشئ جداول طبقة البيانات المعرفة حاليًا على محرك SQLite المحدد."""

    Base.metadata.create_all(bind=engine)


def create_session_factory(engine: Engine) -> SessionFactory:
    """ينشئ مصنع جلسات قصيرة المعاملة من دون حالة مشتركة بين الطلبات."""

    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(session_factory: SessionFactory) -> Iterator[Session]:
    """يلتزم بالمعاملة عند النجاح ويتراجع عنها عند الخطأ ثم يغلق الجلسة."""

    session = session_factory()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
