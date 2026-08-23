"""مفاهيم الاستطلاع الأساسية المستقلة عن Flask وقاعدة البيانات."""

from __future__ import annotations

from enum import StrEnum


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
