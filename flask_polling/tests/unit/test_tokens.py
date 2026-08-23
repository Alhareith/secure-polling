"""اختبارات رمز أهلية التصويت."""

from datetime import UTC, datetime, timedelta

import pytest

from core.polls import Poll, PollState, VoteType
from core.tokens import TokenState, TokenValidationError, VoterToken


def _open_poll() -> Poll:
    opens_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    draft = Poll.create_draft(
        title="اختيار موعد العرض",
        question="ما الموعد المناسب للعرض النهائي؟",
        vote_type=VoteType.SINGLE,
        options=("السبت", "الأحد"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=1),
        max_choices=1,
    )
    return draft.transition_to(PollState.PUBLISHED).transition_to(PollState.OPEN)


def _token(poll: Poll, *, expires_at: datetime | None = None) -> VoterToken:
    return VoterToken.issue(
        poll_id=poll.poll_id,
        token_hash="stored-hash-only",
        expires_at=expires_at or datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
    )


def test_issued_token_contains_a_hash_but_not_a_raw_secret() -> None:
    poll = _open_poll()

    token = _token(poll)

    assert token.token_id is not None
    assert token.token_hash == "stored-hash-only"
    assert token.state is TokenState.ISSUED


def test_issued_token_can_be_used_for_its_open_poll() -> None:
    poll = _open_poll()
    token = _token(poll)

    token.require_usable_for(poll, datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_mark_used_returns_a_new_token_without_changing_the_old_one() -> None:
    poll = _open_poll()
    token = _token(poll)

    used = token.mark_used(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))

    assert used is not token
    assert token.state is TokenState.ISSUED
    assert used.state is TokenState.USED
    assert used.token_id == token.token_id


def test_token_rejects_a_second_use() -> None:
    poll = _open_poll()
    used = _token(poll).mark_used(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))

    with pytest.raises(TokenValidationError, match="token is used"):
        used.require_usable_for(poll, datetime(2026, 9, 1, 12, 1, tzinfo=UTC))


def test_token_expires_at_its_expiration_time() -> None:
    poll = _open_poll()
    expires_at = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    token = _token(poll, expires_at=expires_at)

    assert token.state_at(expires_at) is TokenState.EXPIRED

    with pytest.raises(TokenValidationError, match="token is expired"):
        token.require_usable_for(poll, expires_at)


def test_token_rejects_a_different_poll() -> None:
    token = _token(_open_poll())
    other_poll = _open_poll()

    with pytest.raises(TokenValidationError, match="does not belong"):
        token.require_usable_for(other_poll, datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_revoked_token_cannot_be_used() -> None:
    poll = _open_poll()
    revoked = _token(poll).revoke()

    assert revoked.state is TokenState.REVOKED
    with pytest.raises(TokenValidationError, match="token is revoked"):
        revoked.require_usable_for(poll, datetime(2026, 9, 1, 12, 0, tzinfo=UTC))


def test_token_requires_a_non_empty_hash_and_timezone_aware_expiration() -> None:
    poll = _open_poll()

    with pytest.raises(TokenValidationError, match="token_hash must not be blank"):
        VoterToken.issue(
            poll_id=poll.poll_id,
            token_hash=" ",
            expires_at=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
        )

    with pytest.raises(TokenValidationError, match="expires_at must include timezone information"):
        VoterToken.issue(
            poll_id=poll.poll_id,
            token_hash="stored-hash-only",
            expires_at=datetime(2026, 9, 2, 8, 0),
        )
