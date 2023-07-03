from icalendar import Calendar
from dataclasses import dataclass, KW_ONLY
import re

summary_regex = re.compile("([0-9A-Z]{3}\.[0-9A-Z]{3}) ([A-Z]{2}) (.*)")


@dataclass(kw_only=True)
class Event:
    name: str = ""
    shorthand: str = ""
    lecture_type: str = ""
    additional: str = ""
    number: str = ""
    description: str = ""
    address: str = ""
    room: str = ""
    tiss_url: str = ""
    room_url: str = ""


def improve_calendar(
    cal: Calendar, noshorthand: bool = False, keepNumber: bool = False
) -> Calendar:
    shorthands = read_shorthands()

    for component in cal.walk():
        if component.name != "VEVENT" or not summary_regex.match(
            component.get("summary")
        ):
            continue

        # Parse the event and enrich it
        event = event_from_ical(component)
        event = add_shorthand(event, shorthands)

        # Serialize the summary
        summary = ""
        summary += event.shorthand if event.shorthand != "" else event.name
        summary += f" {event.lecture_type}"
        if event.additional != "":
            summary += " - " + event.additional
        component.pop("summary")
        component.add("summary", summary)

        # Serialize the address

        # Serialize the description

    return cal


def event_from_ical(component) -> Event:
    summary = component.get("summary")
    match = summary_regex.match(summary)
    print(summary)
    print(match)

    [number, lecture_type, name] = match.groups()
    additional = ""
    if " - " in name:
        [name, additional] = name.rsplit(" - ", 1)

    room = component.get("location")

    return Event(
        name=name,
        number=number,
        lecture_type=lecture_type,
        additional=additional,
        room=room,
    )


def add_shorthand(event: Event, shorthands: dict[str, str]) -> Event:
    if event.name.lower() in shorthands:
        event.shorthand = shorthands[event.name.lower()].upper()
    return event


def read_shorthands() -> dict[str, str]:
    with open("resources/shorthands.csv") as f:
        lines = f.readlines()[1:]
    return {l.split(",")[1].lower().strip(): l.split(",")[0].strip() for l in lines}


def better_summary(old: str, shorthands: dict[str, str]) -> str:
    match = summary_regex.match(old)
    if match is None:
        return old

    # FIXME: Might be better to write our own parser here
    [number, lecture_type, name] = match.groups()
    additional = ""
    if " - " in name:
        [name, additional] = name.rsplit(" - ", 1)

    summary = f"{name} {lecture_type}"
    if additional != "":
        summary += " - " + additional
    return summary
