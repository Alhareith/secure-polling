"""مفاهيم رمز أهلية التصويت المستقلة عن التخزين والتشفير الفعلي."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from core.polls import Poll, PollState


class TokenState(StrEnum):
    """حالات رمز التصويت خلال دورة حياته."""

    ISSUED = "issued"
    USED = "used"
    REVOKED = "revoked"
    EXPIRED = "expired"


class TokenValidationError(ValueError):
    """خطأ في أهلية رمز التصويت أو محاولة استخدامه."""


@dataclass(frozen=True, slots=True)
class VoterToken:
    """تمثيل رمز تصويت يخزن بصمته فقط، ولا يخزن الرمز الخام."""

    token_id: UUID
    poll_id: UUID
    token_hash: str
    expires_at: datetime
    state: TokenState = TokenState.ISSUED

    @classmethod
    def issue(cls, *, poll_id: UUID, token_hash: str, expires_at: datetime) -> VoterToken:
        """ينشئ رمزًا جديدًا بحالة صادرة من دون الاحتفاظ بالقيمة الخام."""

        return cls(
            token_id=uuid4(),
            poll_id=poll_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    def __post_init__(self) -> None:
        if not self.token_hash.strip():
            raise TokenValidationError("token_hash must not be blank")
        _require_aware_datetime("expires_at", self.expires_at)

    def state_at(self, now: datetime) -> TokenState:
        """يعيد حالة الرمز الفعلية عند وقت محدد، بما في ذلك الانتهاء الزمني."""

        _require_aware_datetime("now", now)
        if self.state is TokenState.ISSUED and now >= self.expires_at:
            return TokenState.EXPIRED
        return self.state

    def require_usable_for(self, poll: Poll, now: datetime) -> None:
        """يتحقق أن الرمز يخص الاستطلاع المفتوح وما زال صالحًا للاستخدام مرة واحدة."""

        if self.poll_id != poll.poll_id:
            raise TokenValidationError("token does not belong to this poll")
        if poll.state is not PollState.OPEN:
            raise TokenValidationError("token can be used only while the poll is open")

        current_state = self.state_at(now)
        if current_state is not TokenState.ISSUED:
            raise TokenValidationError(f"token is {current_state}")

    def mark_used(self, now: datetime) -> VoterToken:
        """يعيد نسخة مستهلكة من الرمز بعد التحقق أنه لم ينتهِ أو يُستخدم سابقًا."""

        current_state = self.state_at(now)
        if current_state is not TokenState.ISSUED:
            raise TokenValidationError(f"token is {current_state}")
        return replace(self, state=TokenState.USED)

    def revoke(self) -> VoterToken:
        """يلغي رمزًا صادرًا لم يُستخدم بعد."""

        if self.state is not TokenState.ISSUED:
            raise TokenValidationError("only an issued token can be revoked")
        return replace(self, state=TokenState.REVOKED)


def _require_aware_datetime(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise TokenValidationError(f"{name} must include timezone information")
