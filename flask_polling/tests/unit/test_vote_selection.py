"""اختبارات تحقق اختيار المصوّت."""

from datetime import UTC, datetime, timedelta

import pytest

from core.polls import Poll, PollState, VoteType, VoteValidationError


def _open_poll(
    *,
    vote_type: VoteType = VoteType.SINGLE,
    options: tuple[str, ...] = ("السبت", "الأحد", "الاثنين"),
    max_choices: int = 1,
) -> Poll:
    opens_at = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    draft = Poll.create_draft(
        title="اختيار موعد العرض",
        question="ما الموعد المناسب للعرض النهائي؟",
        vote_type=vote_type,
        options=options,
        opens_at=opens_at,
        closes_at=opens_at + timedelta(days=1),
        max_choices=max_choices,
    )
    return draft.transition_to(PollState.PUBLISHED).transition_to(PollState.OPEN)


def test_single_choice_returns_the_canonical_poll_option() -> None:
    poll = _open_poll()

    selection = poll.validate_selection((" الأحد ",))

    assert selection == ("الأحد",)


def test_multi_choice_accepts_a_selection_within_its_limit() -> None:
    poll = _open_poll(vote_type=VoteType.MULTI, max_choices=2)

    selection = poll.validate_selection(("السبت", "الاثنين"))

    assert selection == ("السبت", "الاثنين")


def test_selection_is_rejected_when_the_poll_is_not_open() -> None:
    draft = Poll.create_draft(
        title="اختيار موعد العرض",
        question="ما الموعد المناسب للعرض النهائي؟",
        vote_type=VoteType.SINGLE,
        options=("السبت", "الأحد"),
        opens_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
        closes_at=datetime(2026, 9, 2, 8, 0, tzinfo=UTC),
        max_choices=1,
    )

    with pytest.raises(VoteValidationError, match="poll is open"):
        draft.validate_selection(("السبت",))


@pytest.mark.parametrize(
    "selected_options, message",
    [
        ((), "at least one option"),
        (("السبت", "الأحد"), "exactly one selected option"),
        (("الخميس",), "must belong to the poll"),
        (("السبت", " السبت "), "must not contain duplicates"),
    ],
)
def test_invalid_single_choice_selections_are_rejected(
    selected_options: tuple[str, ...], message: str
) -> None:
    poll = _open_poll()

    with pytest.raises(VoteValidationError, match=message):
        poll.validate_selection(selected_options)


def test_multi_choice_rejects_more_than_the_configured_limit() -> None:
    poll = _open_poll(vote_type=VoteType.MULTI, max_choices=2)

    with pytest.raises(VoteValidationError, match="within the allowed limit"):
        poll.validate_selection(("السبت", "الأحد", "الاثنين"))


def test_yes_no_accepts_only_one_of_its_defined_options() -> None:
    poll = _open_poll(vote_type=VoteType.YES_NO, options=("yes", "no"), max_choices=1)

    assert poll.validate_selection(("yes",)) == ("yes",)

    with pytest.raises(VoteValidationError, match="must belong to the poll"):
        poll.validate_selection(("maybe",))
