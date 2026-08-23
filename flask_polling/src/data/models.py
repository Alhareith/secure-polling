"""نماذج SQLAlchemy التي تفصل التخزين عن كائنات المجال غير القابلة للتعديل."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core.polls import Poll, PollState, VoteType


class Base(DeclarativeBase):
    """القاعدة التصريحية الوحيدة لجميع جداول منصة صوّت المستقبلية."""


class PollRecord(Base):
    """تمثيل SQLite لبيانات الاستطلاع الأساسية وخياراته المرتبة."""

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
    options: Mapped[list[PollOptionRecord]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
        order_by="PollOptionRecord.position",
        passive_deletes=True,
    )


class PollOptionRecord(Base):
    """خيار واحد مرتب ضمن استطلاع محدد، لا يحمل أي بيانات عن المصوّت."""

    __tablename__ = "poll_options"
    __table_args__ = (CheckConstraint("position >= 1", name="poll_option_position_is_positive"),)

    poll_id: Mapped[UUID] = mapped_column(
        ForeignKey("polls.poll_id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    poll: Mapped[PollRecord] = relationship(back_populates="options")


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


def poll_option_records_from_domain(poll: Poll) -> tuple[PollOptionRecord, ...]:
    """يحوّل خيارات Poll إلى سجلات مرتبة تبدأ من الموضع 1."""

    return tuple(
        PollOptionRecord(poll_id=poll.poll_id, position=position, label=label)
        for position, label in enumerate(poll.options, start=1)
    )


def poll_from_records(record: PollRecord, *, option_records: tuple[PollOptionRecord, ...]) -> Poll:
    """يبني Poll كاملًا من سجل الاستطلاع وسجلات خياراته المرتبة."""

    return Poll(
        poll_id=record.poll_id,
        title=record.title,
        question=record.question,
        vote_type=VoteType(record.vote_type),
        options=_option_labels_for_poll(record.poll_id, option_records),
        opens_at=_from_utc_microseconds(record.opens_at_us),
        closes_at=_from_utc_microseconds(record.closes_at_us),
        max_choices=record.max_choices,
        state=PollState(record.state),
    )


def _option_labels_for_poll(
    poll_id: UUID, option_records: tuple[PollOptionRecord, ...]
) -> tuple[str, ...]:
    if any(option_record.poll_id != poll_id for option_record in option_records):
        raise ValueError("option records must belong to the poll record")

    ordered_records = tuple(
        sorted(option_records, key=lambda option_record: option_record.position)
    )
    expected_positions = tuple(range(1, len(ordered_records) + 1))
    actual_positions = tuple(option_record.position for option_record in ordered_records)
    if actual_positions != expected_positions:
        raise ValueError("option record positions must be consecutive starting at 1")

    return tuple(option_record.label for option_record in ordered_records)


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
