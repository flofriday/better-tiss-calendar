from datetime import datetime

from icalendar import Calendar, Event, Timezone

from app.format import _dedupe, event_from_ical, improve_calendar


def make_lecture(summary: str, start: datetime, location: str = "A") -> Event:
    event = Event()
    event.add("summary", summary)
    event.add("dtstart", start)
    event.add("location", location)
    event.add("description", "Vorlesung")
    return event


def make_calendar(*components) -> Calendar:
    cal = Calendar()
    for component in components:
        cal.add_component(component)
    return cal


START = datetime(2025, 12, 11, 10, 0)
LATER = datetime(2025, 12, 18, 10, 0)


def locations(components) -> list[str | None]:
    return [c.get("LOCATION") for c in components]


def test_dedupe_without_duplicates_changes_nothing():
    first = make_lecture("194.193 VU AI Programming", START)
    second = make_lecture("194.193 VU AI Programming", LATER)

    result = _dedupe(make_calendar(first, second))

    assert result == [first, second]


def test_dedupe_merges_same_name_and_start():
    cal = make_calendar(
        make_lecture("194.193 VU AI Programming", START, "A"),
        make_lecture("194.193 VU AI Programming", START, "B"),
    )

    result = _dedupe(cal)

    assert len(result) == 1
    assert result[0].get("LOCATION") == "A"
    assert str(result[0].get("X-EXTRA-ROOMS")) == "B"


def test_dedupe_does_not_merge_different_start():
    cal = make_calendar(
        make_lecture("194.193 VU AI Programming", START),
        make_lecture("194.193 VU AI Programming", LATER),
    )

    assert len(_dedupe(cal)) == 2


def test_dedupe_does_not_merge_different_names():
    cal = make_calendar(
        make_lecture("194.193 VU AI Programming", START),
        make_lecture("194.194 VU Other Course", START),
    )

    assert len(_dedupe(cal)) == 2


def test_dedupe_merged_group_keeps_position_of_first_event():
    before = make_lecture("194.100 VO Before", START, "X")
    after = make_lecture("194.200 VO After", START, "Y")
    cal = make_calendar(
        before,
        make_lecture("194.193 VU AI Programming", START, "A"),
        after,
        make_lecture("194.193 VU AI Programming", START, "B"),
    )

    result = _dedupe(cal)

    assert locations(result) == ["X", "A", "Y"]


def test_dedupe_passes_non_lectures_through_in_place():
    timezone = Timezone()
    holiday = Event()
    holiday.add("summary", "Pfingsten, vorlesungsfrei")
    holiday.add("dtstart", START.date())
    lecture = make_lecture("194.193 VU AI Programming", START)

    result = _dedupe(make_calendar(timezone, lecture, holiday))

    assert result == [timezone, lecture, holiday]


def test_event_from_ical_reads_extra_rooms():
    component = make_lecture("194.193 VU AI Programming", START)
    component.add("X-EXTRA-ROOMS", "B,C")

    assert event_from_ical(component).extra_rooms == ["B", "C"]


def test_event_from_ical_without_extra_rooms():
    component = make_lecture("194.193 VU AI Programming", START)

    assert event_from_ical(component).extra_rooms is None


def test_improve_calendar_merges_rooms_and_drops_the_helper_property():
    cal = make_calendar(
        make_lecture("194.193 VU AI Programming", START, "A"),
        make_lecture("194.193 VU AI Programming", START, "B"),
    )

    result = improve_calendar(cal, locale="en")

    lectures = [c for c in result.subcomponents if c.name == "VEVENT"]
    assert len(lectures) == 1
    assert "Further rooms: B" in str(lectures[0].get("DESCRIPTION"))
    assert "X-EXTRA-ROOMS" not in lectures[0]
