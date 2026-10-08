from datetime import datetime

from icalendar import Event

from app.constants import SessionType
from app.utils import merge_group, parse_session_type


def test_parse_session_type_vorlesung_de():
    assert parse_session_type("Vorlesung", None) == SessionType.VORLESUNG


def test_parse_session_type_lecture_en():
    assert parse_session_type("Lecture", None) == SessionType.VORLESUNG


def test_parse_session_type_lecture_with_alternative_rooms():
    assert (
        parse_session_type("Lecture (Alternative premises)", None)
        == SessionType.VORLESUNG
    )


def test_parse_session_type_vorbesprechung():
    assert parse_session_type("Vorbesprechung", None) == SessionType.VORBESPRECHUNG


def test_parse_session_type_testeinsicht():
    assert (
        parse_session_type("Testeinsicht Test 2 10:00-11:00", None)
        == SessionType.TESTEINSICHT
    )


def test_parse_session_type_exam():
    assert parse_session_type("Prüfung", None) == SessionType.EXAM


def test_parse_session_type_group_by_category():
    assert parse_session_type("some group description", ["GROUP"]) == (
        SessionType.GROUP
    )


def test_parse_session_type_group_takes_priority_over_description():
    # Even if the description happens to say "Vorlesung", a GROUP category
    # should win, since it is the more reliable signal
    assert parse_session_type("Vorlesung", ["GROUP"]) == SessionType.GROUP


def test_parse_session_type_no_categories_falls_back_to_description():
    assert parse_session_type("Vorlesung", []) == SessionType.VORLESUNG


def test_parse_session_type_unrecognized_description():
    assert (
        parse_session_type("Orientierung: 1. Block - Röpke", None) == SessionType.OTHER
    )


def test_parse_session_type_none_description():
    assert parse_session_type(None, None) == SessionType.OTHER


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
    assert "Could not merge 3 events" in caplog.text
    assert "2 of 3 events have no LOCATION" in caplog.text
