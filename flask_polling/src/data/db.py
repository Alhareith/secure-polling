"""إنشاء اتصال SQLite محلي مضبوط لاحتياجات منصة صوّت."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, event

SQLITE_BUSY_TIMEOUT_MS = 5_000


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
