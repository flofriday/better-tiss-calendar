from datetime import datetime

from icalendar import Event

from app.utils import merge_group


def make_event(
    location: str | None, description: str = "Vorlesung", summary: str = "x"
) -> Event:
    event = Event()
    event.add("summary", summary)
    event.add("dtstart", datetime(2025, 12, 11, 10, 0))
    event.add("description", description)
    if location is not None:
        event.add("location", location)
    return event


def test_merge_group_single_event_is_returned_as_is():
    event = make_event("A")
    assert merge_group([event]) is event


def test_merge_group_adds_extra_rooms_to_description():
    merged = merge_group([make_event("A"), make_event("B")])

    assert merged.get("LOCATION") == "A"
    assert str(merged.get("DESCRIPTION")) == "Vorlesung"
    assert str(merged.get("X-EXTRA-ROOMS")) == "B"


def test_merge_group_prefers_non_alternative_event():
    main = make_event("Z")
    alternative = make_event("A", description="Vorlesung (Alternative premises)")

    merged = merge_group([alternative, main])

    assert merged.get("LOCATION") == "Z"
    assert str(merged.get("X-EXTRA-ROOMS")) == "A"


def test_merge_group_all_alternative_still_picks_one():
    merged = merge_group(
        [
            make_event("B", description="Ausweichtermin"),
            make_event("A", description="Ausweichtermin"),
        ]
    )

    assert merged.get("LOCATION") == "A"
    assert str(merged.get("X-EXTRA-ROOMS")) == "B"


def test_merge_group_sorts_extra_rooms():
    merged = merge_group([make_event("A"), make_event("D"), make_event("C")])

    assert str(merged.get("X-EXTRA-ROOMS")) == "C,D"


def test_merge_group_does_not_modify_the_input():
    first, second = make_event("A"), make_event("B")

    merge_group([first, second])

    assert first.get("X-EXTRA-ROOMS") is None
    assert second.get("X-EXTRA-ROOMS") is None


def test_merge_group_falls_back_to_first_event_on_error(caplog):
    group = [make_event("A"), make_event(None), make_event(None)]
    assert merge_group(group) is group[0]
