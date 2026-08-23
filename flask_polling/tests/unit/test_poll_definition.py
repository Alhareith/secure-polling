"""اختبارات تعريف الاستطلاع وقواعد صحته."""

from datetime import UTC, datetime, timedelta

import pytest

from core.polls import Poll, PollState, PollValidationError, VoteType


def _schedule() -> tuple[datetime, datetime]:
    opens_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    return opens_at, opens_at + timedelta(days=1)


def _draft(**overrides: object) -> Poll:
    opens_at, closes_at = _schedule()
    values: dict[str, object] = {
        "title": "اختيار موعد العرض",
        "question": "ما الموعد المناسب للعرض النهائي؟",
        "vote_type": VoteType.SINGLE,
        "options": ("السبت", "الأحد", "الاثنين"),
        "opens_at": opens_at,
        "closes_at": closes_at,
        "max_choices": 1,
    }
    values.update(overrides)
    return Poll.create_draft(**values)  # type: ignore[arg-type]


def test_create_draft_starts_with_a_unique_identity_and_draft_state() -> None:
    poll = _draft()

    assert poll.poll_id is not None
    assert poll.state is PollState.DRAFT
    assert poll.max_choices == 1


def test_multi_choice_poll_requires_a_valid_choice_limit() -> None:
    poll = _draft(vote_type=VoteType.MULTI, max_choices=2)

    assert poll.vote_type is VoteType.MULTI
    assert poll.max_choices == 2


def test_yes_no_poll_requires_its_stable_internal_options() -> None:
    poll = _draft(vote_type=VoteType.YES_NO, options=("yes", "no"), max_choices=1)

    assert poll.options == ("yes", "no")


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"title": "   "}, "title must not be blank"),
        ({"question": ""}, "question must not be blank"),
        ({"options": ("نعم", "نعم")}, "options must be unique"),
        ({"options": ("خيار واحد",)}, "at least two options are required"),
        ({"max_choices": 2}, "single-choice polls require max_choices=1"),
        (
            {"vote_type": VoteType.MULTI, "max_choices": 1},
            "multi-choice max_choices must be between 2 and option count",
        ),
        (
            {"vote_type": VoteType.YES_NO, "max_choices": 1},
            "yes/no polls require options: yes, no",
        ),
    ],
)
def test_invalid_poll_definitions_are_rejected(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(PollValidationError, match=message):
        _draft(**overrides)


def test_poll_requires_timezone_aware_schedule() -> None:
    opens_at, closes_at = _schedule()

    with pytest.raises(PollValidationError, match="opens_at must include timezone information"):
        _draft(opens_at=opens_at.replace(tzinfo=None), closes_at=closes_at)


def test_poll_requires_opening_before_closing() -> None:
    opens_at, closes_at = _schedule()

    with pytest.raises(PollValidationError, match="opens_at must be earlier than closes_at"):
        _draft(opens_at=closes_at, closes_at=opens_at)
