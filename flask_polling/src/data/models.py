"""نماذج SQLAlchemy التي تفصل التخزين عن كائنات المجال غير القابلة للتعديل."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.polls import Poll, PollState, VoteType


class Base(DeclarativeBase):
    """القاعدة التصريحية الوحيدة لجميع جداول منصة صوّت المستقبلية."""


class PollRecord(Base):
    """تمثيل SQLite لبيانات الاستطلاع الأساسية، دون خياراته المنفصلة."""

    __tablename__ = "polls"
    __table_args__ = (
        CheckConstraint("opens_at_us < closes_at_us", name="poll_opening_precedes_closing"),
        CheckConstraint("max_choices >= 1", name="poll_max_choices_is_positive"),
    )

    poll_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    question: Mapped[str] = mapped_column(String(2_000), nullable=False)
    vote_type: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    opens_at_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    closes_at_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_choices: Mapped[int] = mapped_column(nullable=False)


def poll_record_from_domain(poll: Poll) -> PollRecord:
    """يحوّل القيم الأساسية من Poll إلى سجل تخزين، من دون تخزين الخيارات هنا."""

    return PollRecord(
        poll_id=poll.poll_id,
        title=poll.title,
        question=poll.question,
        vote_type=poll.vote_type.value,
        state=poll.state.value,
        opens_at_us=_to_utc_microseconds(poll.opens_at),
        closes_at_us=_to_utc_microseconds(poll.closes_at),
        max_choices=poll.max_choices,
    )


def poll_from_record(record: PollRecord, *, options: tuple[str, ...]) -> Poll:
    """يبني Poll كاملًا من سجل SQLite وخياراته التي سيحفظها جدول مستقل لاحقًا."""

    return Poll(
        poll_id=record.poll_id,
        title=record.title,
        question=record.question,
        vote_type=VoteType(record.vote_type),
        options=options,
        opens_at=_from_utc_microseconds(record.opens_at_us),
        closes_at=_from_utc_microseconds(record.closes_at_us),
        max_choices=record.max_choices,
        state=PollState(record.state),
    )


def _to_utc_microseconds(value: datetime) -> int:
    """يحفظ وقتًا واعيًا بالمنطقة الزمنية كعدد صحيح دقيق بالميكروثانية في UTC."""

    utc_value = value.astimezone(UTC)
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    difference = utc_value - epoch
    return (
        difference.days * 86_400_000_000 + difference.seconds * 1_000_000 + difference.microseconds
    )


def _from_utc_microseconds(value: int) -> datetime:
    """يعيد وقت UTC واعيًا بالمنطقة الزمنية من القيمة المخزنة."""

    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=value)
