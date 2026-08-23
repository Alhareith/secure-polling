"""مفاهيم سجل التدقيق التي لا تحفظ هوية المصوّت أو اختياره."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class AuditAction(StrEnum):
    """الأحداث العامة المسموح بتدقيقها في الإصدار الأول."""

    POLL_CREATED = "poll_created"
    POLL_PUBLISHED = "poll_published"
    POLL_OPENED = "poll_opened"
    POLL_CLOSED = "poll_closed"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    VOTE_ACCEPTED = "vote_accepted"
    TALLY_COMPLETED = "tally_completed"
    REPORT_SIGNED = "report_signed"


class AuditValidationError(ValueError):
    """خطأ في خصوصية حدث التدقيق أو سلامة سلسلة الأحداث."""


SAFE_COUNT_NAMES = frozenset(
    {
        "accepted_count",
        "created_count",
        "invalid_count",
        "option_count",
        "rejected_count",
        "revoked_count",
        "token_count",
    }
)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """حدث تدقيق عام لا يحتوي بيانات تصويت فردية أو رمزًا خامًا."""

    event_id: UUID
    poll_id: UUID
    action: AuditAction
    occurred_at: datetime
    counts: tuple[tuple[str, int], ...] = ()

    @classmethod
    def create(
        cls,
        *,
        poll_id: UUID,
        action: AuditAction,
        occurred_at: datetime,
        counts: tuple[tuple[str, int], ...] = (),
    ) -> AuditEvent:
        """ينشئ حدث تدقيق بقيم عامة آمنة فقط."""

        return cls(
            event_id=uuid4(),
            poll_id=poll_id,
            action=action,
            occurred_at=occurred_at,
            counts=counts,
        )

    def __post_init__(self) -> None:
        _require_aware_datetime("occurred_at", self.occurred_at)
        _validate_counts(self.counts)


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """عنصر في سلسلة التدقيق؛ حساب البصمة الفعلية سيأتي من طبقة التشفير."""

    sequence: int
    event: AuditEvent
    previous_hash: str | None
    event_hash: str

    @classmethod
    def first(cls, *, event: AuditEvent, event_hash: str) -> AuditEntry:
        """ينشئ أول عنصر في السلسلة من دون بصمة سابقة."""

        return cls(sequence=1, event=event, previous_hash=None, event_hash=event_hash)

    @classmethod
    def append(cls, *, event: AuditEvent, previous: AuditEntry, event_hash: str) -> AuditEntry:
        """يربط حدثًا جديدًا ببصمة العنصر السابق داخل الاستطلاع نفسه."""

        if event.poll_id != previous.event.poll_id:
            raise AuditValidationError("audit entries must belong to the same poll")

        return cls(
            sequence=previous.sequence + 1,
            event=event,
            previous_hash=previous.event_hash,
            event_hash=event_hash,
        )

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise AuditValidationError("sequence must be positive")
        _require_sha256_hash("event_hash", self.event_hash)

        if self.sequence == 1 and self.previous_hash is not None:
            raise AuditValidationError("the first entry must not have a previous_hash")
        if self.sequence > 1:
            if self.previous_hash is None:
                raise AuditValidationError("non-first entries require a previous_hash")
            _require_sha256_hash("previous_hash", self.previous_hash)


def _require_aware_datetime(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AuditValidationError(f"{name} must include timezone information")


def _validate_counts(counts: tuple[tuple[str, int], ...]) -> None:
    count_names = [name for name, _ in counts]
    if len(set(count_names)) != len(count_names):
        raise AuditValidationError("audit count names must be unique")

    for name, value in counts:
        if name not in SAFE_COUNT_NAMES:
            raise AuditValidationError(f"audit count name is not allowed: {name}")
        if value < 0:
            raise AuditValidationError("audit counts must not be negative")


def _require_sha256_hash(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise AuditValidationError(f"{name} must be a lowercase SHA-256 hex digest")
