"""مفاهيم الاستطلاع الأساسية المستقلة عن Flask وقاعدة البيانات."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class VoteType(StrEnum):
    """أنواع الاختيار التي يدعمها الإصدار الأول."""

    SINGLE = "single"
    MULTI = "multi"
    YES_NO = "yes_no"


class PollState(StrEnum):
    """حالات دورة حياة الاستطلاع."""

    DRAFT = "draft"
    PUBLISHED = "published"
    OPEN = "open"
    CLOSED = "closed"
    TALLIED = "tallied"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class PollValidationError(ValueError):
    """خطأ في بيانات تعريف الاستطلاع أو قواعده الأساسية."""


YES_NO_OPTIONS = ("yes", "no")


@dataclass(frozen=True, slots=True)
class Poll:
    """وصف استطلاع لا يعتمد على Flask أو قاعدة البيانات."""

    poll_id: UUID
    title: str
    question: str
    vote_type: VoteType
    options: tuple[str, ...]
    opens_at: datetime
    closes_at: datetime
    max_choices: int
    state: PollState = PollState.DRAFT

    @classmethod
    def create_draft(
        cls,
        *,
        title: str,
        question: str,
        vote_type: VoteType,
        options: tuple[str, ...],
        opens_at: datetime,
        closes_at: datetime,
        max_choices: int,
    ) -> Poll:
        """ينشئ استطلاعًا جديدًا يبدأ دائمًا في حالة المسودة."""

        return cls(
            poll_id=uuid4(),
            title=title,
            question=question,
            vote_type=vote_type,
            options=options,
            opens_at=opens_at,
            closes_at=closes_at,
            max_choices=max_choices,
        )

    def __post_init__(self) -> None:
        _require_text("title", self.title, maximum_length=160)
        _require_text("question", self.question, maximum_length=2_000)
        _require_aware_datetime("opens_at", self.opens_at)
        _require_aware_datetime("closes_at", self.closes_at)

        if self.opens_at >= self.closes_at:
            raise PollValidationError("opens_at must be earlier than closes_at")

        _validate_options(self.options)
        _validate_choice_rules(self.vote_type, self.options, self.max_choices)

    def transition_to(self, target: PollState) -> Poll:
        """يعيد نسخة جديدة بالحالة المطلوبة بعد التحقق من سياسة الانتقال."""

        require_transition(self.state, target)
        return replace(self, state=target)


def _require_text(name: str, value: str, *, maximum_length: int) -> None:
    if not value.strip():
        raise PollValidationError(f"{name} must not be blank")
    if len(value) > maximum_length:
        raise PollValidationError(f"{name} must be at most {maximum_length} characters")


def _require_aware_datetime(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PollValidationError(f"{name} must include timezone information")


def _validate_options(options: tuple[str, ...]) -> None:
    if len(options) < 2:
        raise PollValidationError("at least two options are required")
    if any(not option.strip() for option in options):
        raise PollValidationError("options must not be blank")

    normalized_options = [option.strip().casefold() for option in options]
    if len(set(normalized_options)) != len(normalized_options):
        raise PollValidationError("options must be unique")


def _validate_choice_rules(vote_type: VoteType, options: tuple[str, ...], max_choices: int) -> None:
    if vote_type is VoteType.SINGLE and max_choices != 1:
        raise PollValidationError("single-choice polls require max_choices=1")

    if vote_type is VoteType.MULTI and not 2 <= max_choices <= len(options):
        raise PollValidationError("multi-choice max_choices must be between 2 and option count")

    if vote_type is VoteType.YES_NO:
        normalized_options = tuple(option.strip().casefold() for option in options)
        if normalized_options != YES_NO_OPTIONS:
            raise PollValidationError("yes/no polls require options: yes, no")
        if max_choices != 1:
            raise PollValidationError("yes/no polls require max_choices=1")


ALLOWED_STATE_TRANSITIONS: dict[PollState, frozenset[PollState]] = {
    PollState.DRAFT: frozenset({PollState.PUBLISHED, PollState.CANCELLED}),
    PollState.PUBLISHED: frozenset({PollState.OPEN, PollState.CANCELLED}),
    PollState.OPEN: frozenset({PollState.CLOSED}),
    PollState.CLOSED: frozenset({PollState.TALLIED}),
    PollState.TALLIED: frozenset({PollState.ARCHIVED}),
    PollState.ARCHIVED: frozenset(),
    PollState.CANCELLED: frozenset(),
}


def can_transition(current: PollState, target: PollState) -> bool:
    """يتحقق من أن انتقال الاستطلاع بين حالتين مسموح به."""

    return target in ALLOWED_STATE_TRANSITIONS[current]


def require_transition(current: PollState, target: PollState) -> None:
    """يرفض أي انتقال غير مسموح به قبل تغيير حالة الاستطلاع."""

    if not can_transition(current, target):
        raise ValueError(f"Invalid poll state transition: {current} -> {target}")
