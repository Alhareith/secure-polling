"""اختبارات سجل التدقيق الآمن للخصوصية."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from core.audit import AuditAction, AuditEntry, AuditEvent, AuditValidationError

FIRST_HASH = "a" * 64
SECOND_HASH = "b" * 64


def _event(
    *, action: AuditAction = AuditAction.POLL_CREATED, poll_id: UUID | None = None
) -> AuditEvent:
    return AuditEvent.create(
        poll_id=poll_id or uuid4(),
        action=action,
        occurred_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
    )


def test_audit_event_keeps_only_general_event_data() -> None:
    event = AuditEvent.create(
        poll_id=uuid4(),
        action=AuditAction.VOTE_ACCEPTED,
        occurred_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        counts=(("accepted_count", 1),),
    )

    assert event.action is AuditAction.VOTE_ACCEPTED
    assert event.counts == (("accepted_count", 1),)
    assert not hasattr(event, "token_hash")
    assert not hasattr(event, "selection")
    assert not hasattr(event, "voter_id")


@pytest.mark.parametrize(
    "counts, message",
    [
        ((("token_hash", 1),), "not allowed"),
        ((("selected_option", 1),), "not allowed"),
        ((("accepted_count", -1),), "must not be negative"),
        ((("accepted_count", 1), ("accepted_count", 2)), "must be unique"),
    ],
)
def test_audit_event_rejects_sensitive_or_invalid_counts(
    counts: tuple[tuple[str, int], ...], message: str
) -> None:
    with pytest.raises(AuditValidationError, match=message):
        AuditEvent.create(
            poll_id=uuid4(),
            action=AuditAction.VOTE_ACCEPTED,
            occurred_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
            counts=counts,
        )


def test_first_audit_entry_has_no_previous_hash() -> None:
    first = AuditEntry.first(event=_event(), event_hash=FIRST_HASH)

    assert first.sequence == 1
    assert first.previous_hash is None
    assert first.event_hash == FIRST_HASH


def test_appended_entry_links_to_the_previous_hash() -> None:
    first = AuditEntry.first(event=_event(), event_hash=FIRST_HASH)
    second = AuditEntry.append(
        event=_event(action=AuditAction.POLL_PUBLISHED, poll_id=first.event.poll_id),
        previous=first,
        event_hash=SECOND_HASH,
    )

    assert second.sequence == 2
    assert second.previous_hash == FIRST_HASH


def test_appended_entry_rejects_a_different_poll() -> None:
    first = AuditEntry.first(event=_event(), event_hash=FIRST_HASH)

    with pytest.raises(AuditValidationError, match="same poll"):
        AuditEntry.append(event=_event(), previous=first, event_hash=SECOND_HASH)


@pytest.mark.parametrize(
    "sequence, previous_hash, event_hash, message",
    [
        (0, None, FIRST_HASH, "sequence must be positive"),
        (1, FIRST_HASH, FIRST_HASH, "first entry must not"),
        (2, None, SECOND_HASH, "require a previous_hash"),
        (1, None, "not-a-hash", "lowercase SHA-256"),
        (2, "A" * 64, SECOND_HASH, "lowercase SHA-256"),
    ],
)
def test_audit_entry_rejects_a_broken_hash_chain(
    sequence: int, previous_hash: str | None, event_hash: str, message: str
) -> None:
    with pytest.raises(AuditValidationError, match=message):
        AuditEntry(
            sequence=sequence,
            event=_event(),
            previous_hash=previous_hash,
            event_hash=event_hash,
        )
