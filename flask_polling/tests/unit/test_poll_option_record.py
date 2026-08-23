"""اختبارات خيارات الاستطلاع المرتبة في SQLite."""

from datetime import UTC, datetime, timedelta

import pytest

from core.polls import Poll, VoteType
from data.models import (
    PollOptionRecord,
    poll_from_records,
    poll_option_records_from_domain,
    poll_record_from_domain,
)


def _poll() -> Poll:
    opens_at = datetime(2026, 10, 1, 9, 30, tzinfo=UTC)
    return Poll.create_draft(
        title="تحديد موعد العرض",
        question="ما الموعد الأنسب للعرض النهائي؟",
        vote_type=VoteType.MULTI,
        options=("الاثنين", "الثلاثاء", "الأربعاء"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=2),
        max_choices=2,
    )


def test_option_records_keep_a_stable_one_based_order() -> None:
    poll = _poll()

    option_records = poll_option_records_from_domain(poll)

    assert [(record.position, record.label) for record in option_records] == [
        (1, "الاثنين"),
        (2, "الثلاثاء"),
        (3, "الأربعاء"),
    ]
    assert all(record.poll_id == poll.poll_id for record in option_records)


def test_option_table_uses_a_cascading_poll_foreign_key_and_composite_key() -> None:
    foreign_key = next(iter(PollOptionRecord.__table__.foreign_keys))

    assert foreign_key.target_fullname == "polls.poll_id"
    assert foreign_key.ondelete == "CASCADE"
    assert [column.name for column in PollOptionRecord.__table__.primary_key.columns] == [
        "poll_id",
        "position",
    ]


def test_poll_round_trip_restores_options_in_position_order() -> None:
    poll = _poll()
    option_records = poll_option_records_from_domain(poll)

    restored_poll = poll_from_records(
        poll_record_from_domain(poll),
        option_records=tuple(reversed(option_records)),
    )

    assert restored_poll == poll


def test_option_records_must_belong_to_the_same_poll() -> None:
    poll = _poll()
    record = poll_record_from_domain(poll)
    mismatched_option = PollOptionRecord(
        poll_id=Poll.create_draft(
            title="استطلاع مختلف",
            question="سؤال مختلف؟",
            vote_type=VoteType.SINGLE,
            options=("أ", "ب"),
            opens_at=poll.opens_at,
            closes_at=poll.closes_at,
            max_choices=1,
        ).poll_id,
        position=1,
        label="الاثنين",
    )

    with pytest.raises(ValueError, match="must belong to the poll record"):
        poll_from_records(record, option_records=(mismatched_option,))


def test_option_positions_must_be_consecutive_from_one() -> None:
    poll = _poll()
    record = poll_record_from_domain(poll)
    option_records = (
        PollOptionRecord(poll_id=poll.poll_id, position=1, label="الاثنين"),
        PollOptionRecord(poll_id=poll.poll_id, position=3, label="الأربعاء"),
    )

    with pytest.raises(ValueError, match="must be consecutive"):
        poll_from_records(record, option_records=option_records)
