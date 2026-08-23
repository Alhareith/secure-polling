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
