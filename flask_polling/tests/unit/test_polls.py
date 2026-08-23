"""اختبارات مفاهيم الاستطلاع الأساسية."""

from core.polls import PollState, VoteType


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
