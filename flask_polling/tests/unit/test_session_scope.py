"""اختبارات مصنع الجلسات وسياق المعاملات القصير."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.polls import Poll, VoteType
from data.db import create_schema, create_session_factory, create_sqlite_engine, session_scope
from data.models import PollRecord, poll_record_from_domain


def _poll_record() -> PollRecord:
    opens_at = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)
    poll = Poll.create_draft(
        title="استطلاع جلسات الاختبار",
        question="هل تعمل المعاملة القصيرة؟",
        vote_type=VoteType.SINGLE,
        options=("نعم", "لا"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(hours=1),
        max_choices=1,
    )
    return poll_record_from_domain(poll)


def test_session_scope_commits_a_successful_transaction(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'sessions.db'}")
    create_schema(engine)
    session_factory = create_session_factory(engine)
    record = _poll_record()

    try:
        with session_scope(session_factory) as session:
            session.add(record)

        with session_scope(session_factory) as session:
            assert session.get(PollRecord, record.poll_id) is not None
    finally:
        engine.dispose()


def test_session_scope_rolls_back_when_an_error_is_raised(tmp_path: Path) -> None:
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'sessions.db'}")
    create_schema(engine)
    session_factory = create_session_factory(engine)
    record = _poll_record()

    try:
        with pytest.raises(RuntimeError, match="stop transaction"):
            with session_scope(session_factory) as session:
                session.add(record)
                raise RuntimeError("stop transaction")

        with session_scope(session_factory) as session:
            assert session.get(PollRecord, record.poll_id) is None
    finally:
        engine.dispose()
