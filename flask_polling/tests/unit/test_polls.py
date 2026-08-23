"""اختبارات مفاهيم الاستطلاع الأساسية."""

import pytest

from core.polls import PollState, VoteType, can_transition, require_transition


def test_vote_types_are_limited_to_the_approved_scope() -> None:
    assert list(VoteType) == [VoteType.SINGLE, VoteType.MULTI, VoteType.YES_NO]


def test_poll_states_match_the_approved_lifecycle() -> None:
    assert list(PollState) == [
        PollState.DRAFT,
        PollState.PUBLISHED,
        PollState.OPEN,
        PollState.CLOSED,
        PollState.TALLIED,
        PollState.ARCHIVED,
        PollState.CANCELLED,
    ]


def test_domain_enums_keep_stable_storage_values() -> None:
    assert VoteType.SINGLE == "single"
    assert VoteType.MULTI == "multi"
    assert VoteType.YES_NO == "yes_no"
    assert PollState.DRAFT == "draft"
    assert PollState.TALLIED == "tallied"


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (PollState.DRAFT, PollState.PUBLISHED),
        (PollState.DRAFT, PollState.CANCELLED),
        (PollState.PUBLISHED, PollState.OPEN),
        (PollState.OPEN, PollState.CLOSED),
        (PollState.CLOSED, PollState.TALLIED),
        (PollState.TALLIED, PollState.ARCHIVED),
    ],
)
def test_approved_state_transitions_are_allowed(current: PollState, target: PollState) -> None:
    assert can_transition(current, target) is True
    require_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (PollState.DRAFT, PollState.OPEN),
        (PollState.PUBLISHED, PollState.CLOSED),
        (PollState.OPEN, PollState.TALLIED),
        (PollState.CLOSED, PollState.ARCHIVED),
        (PollState.ARCHIVED, PollState.OPEN),
        (PollState.CANCELLED, PollState.OPEN),
    ],
)
def test_unapproved_state_transitions_are_rejected(current: PollState, target: PollState) -> None:
    assert can_transition(current, target) is False

    with pytest.raises(ValueError, match="Invalid poll state transition"):
        require_transition(current, target)
