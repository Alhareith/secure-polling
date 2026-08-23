"""اختبارات مستودع الاستطلاع وخياراته المرتبة."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from core.polls import Poll, PollState, VoteType
from data.db import create_schema, create_session_factory, create_sqlite_engine, session_scope
from data.repo import PollAlreadyExistsError, PollRepository


def _poll() -> Poll:
    opens_at = datetime(2026, 12, 1, 10, 0, tzinfo=UTC)
    return Poll.create_draft(
        title="استطلاع المستودع",
        question="هل يعيد المستودع الخيارات بالترتيب؟",
        vote_type=VoteType.MULTI,
        options=("الخيار الأول", "الخيار الثاني", "الخيار الثالث"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=1),
        max_choices=2,
    ).transition_to(PollState.PUBLISHED)


def _session_factory(tmp_path: Path):
    engine = create_sqlite_engine(f"sqlite+pysqlite:///{tmp_path / 'repository.db'}")
    create_schema(engine)
    return engine, create_session_factory(engine)


def test_repository_adds_and_restores_a_poll_with_ordered_options(tmp_path: Path) -> None:
    engine, session_factory = _session_factory(tmp_path)
    poll = _poll()

    try:
        with session_scope(session_factory) as session:
            PollRepository(session).add(poll)

        with session_scope(session_factory) as session:
            restored_poll = PollRepository(session).get(poll.poll_id)

        assert restored_poll == poll
    finally:
        engine.dispose()


def test_repository_returns_none_for_a_missing_poll(tmp_path: Path) -> None:
    engine, session_factory = _session_factory(tmp_path)

    try:
        with session_scope(session_factory) as session:
            assert PollRepository(session).get(uuid4()) is None
    finally:
        engine.dispose()


def test_repository_rejects_a_duplicate_poll_id(tmp_path: Path) -> None:
    engine, session_factory = _session_factory(tmp_path)
    poll = _poll()

    try:
        with session_scope(session_factory) as session:
            PollRepository(session).add(poll)

        with pytest.raises(PollAlreadyExistsError, match="already exists"):
            with session_scope(session_factory) as session:
                PollRepository(session).add(poll)
    finally:
        engine.dispose()
