"""مستودعات طبقة البيانات التي تحفظ وتسترجع كائنات المجال دون منطق واجهة."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.polls import Poll
from data.models import (
    PollRecord,
    poll_from_records,
    poll_option_records_from_domain,
    poll_record_from_domain,
)


class PollAlreadyExistsError(ValueError):
    """يُرفع عند محاولة حفظ استطلاع يملك معرفًا موجودًا مسبقًا."""


class PollRepository:
    """يحفظ ويسترجع الاستطلاعات وخياراتها المرتبة داخل جلسة معاملة معطاة."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, poll: Poll) -> None:
        """يضيف الاستطلاع وخياراته إلى المعاملة الحالية من دون تنفيذ commit."""

        if self._session.get(PollRecord, poll.poll_id) is not None:
            raise PollAlreadyExistsError("poll already exists")

        self._session.add(poll_record_from_domain(poll))
        self._session.add_all(poll_option_records_from_domain(poll))

    def get(self, poll_id: UUID) -> Poll | None:
        """يعيد الاستطلاع وخياراته كاملة أو None إذا لم يكن موجودًا."""

        statement = (
            select(PollRecord)
            .options(selectinload(PollRecord.options))
            .where(PollRecord.poll_id == poll_id)
        )
        record = self._session.scalar(statement)
        if record is None:
            return None

        return poll_from_records(record, option_records=tuple(record.options))
