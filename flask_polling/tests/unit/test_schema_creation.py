"""اختبارات إنشاء مخطط الاستطلاع وخياراته على SQLite تجريبية."""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from data.db import create_schema, create_sqlite_engine
from data.models import PollOptionRecord


def test_create_schema_creates_poll_and_option_tables(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'schema.db'}")

    try:
        create_schema(engine)

        assert set(inspect(engine).get_table_names()) == {"poll_options", "polls"}
    finally:
        engine.dispose()


def test_schema_rejects_an_orphan_poll_option(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'schema.db'}")

    try:
        create_schema(engine)

        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    PollOptionRecord.__table__.insert().values(
                        poll_id=uuid4(),
                        position=1,
                        label="خيار يتيم",
                    )
                )
    finally:
        engine.dispose()
