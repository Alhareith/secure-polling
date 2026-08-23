"""اختبارات تهيئة محرك SQLite من دون إنشاء جداول."""

from pathlib import Path

import pytest

from data.db import SQLITE_BUSY_TIMEOUT_MS, create_sqlite_engine


def test_sqlite_engine_enables_required_connection_safeguards(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'polling.db'}")

    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            busy_timeout = connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
            assert busy_timeout == SQLITE_BUSY_TIMEOUT_MS
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"
    finally:
        engine.dispose()


def test_sqlite_engine_rejects_a_non_sqlite_url() -> None:
    with pytest.raises(ValueError, match="must use SQLite"):
        create_sqlite_engine("postgresql://localhost/secure_polling")
