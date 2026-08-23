"""اختبارات تحويل بيانات الاستطلاع الأساسية بين المجال وSQLite."""

from datetime import UTC, datetime, timedelta

from core.polls import Poll, PollState, VoteType
from data.models import Base, PollRecord, poll_record_from_domain


def _poll() -> Poll:
    opens_at = datetime(2026, 10, 1, 9, 30, 15, 123_456, tzinfo=UTC)
    return Poll.create_draft(
        title="تحديد موعد العرض",
        question="ما الموعد الأنسب للعرض النهائي؟",
        vote_type=VoteType.MULTI,
        options=("الاثنين", "الثلاثاء", "الأربعاء"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=2),
        max_choices=2,
    ).transition_to(PollState.PUBLISHED)


def test_poll_record_stores_only_the_poll_scalar_values() -> None:
    poll = _poll()

    record = poll_record_from_domain(poll)

    assert record.poll_id == poll.poll_id
    assert record.title == poll.title
    assert record.vote_type == "multi"
    assert record.state == "published"


def test_poll_table_exists_alongside_the_option_table() -> None:
    assert set(Base.metadata.tables) == {"poll_options", "polls"}
    assert set(PollRecord.__table__.columns.keys()) == {
        "poll_id",
        "title",
        "question",
        "vote_type",
        "state",
        "opens_at_us",
        "closes_at_us",
        "max_choices",
    }
