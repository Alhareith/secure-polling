"""اختبارات تغيير حالة كائن الاستطلاع."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from core.polls import Poll, PollState, VoteType


def _draft() -> Poll:
    opens_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    return Poll.create_draft(
        title="اختيار موعد العرض",
        question="ما الموعد المناسب للعرض النهائي؟",
        vote_type=VoteType.SINGLE,
        options=("السبت", "الأحد", "الاثنين"),
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=1),
        max_choices=1,
    )


def test_transition_returns_a_new_poll_without_changing_the_previous_one() -> None:
    draft = _draft()

    published = draft.transition_to(PollState.PUBLISHED)

    assert published is not draft
    assert draft.state is PollState.DRAFT
    assert published.state is PollState.PUBLISHED
    assert published.poll_id == draft.poll_id


def test_transition_rejects_an_unapproved_state_change() -> None:
    draft = _draft()

    with pytest.raises(ValueError, match="Invalid poll state transition"):
        draft.transition_to(PollState.OPEN)

    assert draft.state is PollState.DRAFT


def test_poll_state_cannot_be_mutated_directly() -> None:
    draft = _draft()

    with pytest.raises(FrozenInstanceError):
        draft.state = PollState.PUBLISHED  # type: ignore[misc]
