from icalendar import Calendar
from dataclasses import dataclass
from functools import cache
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
    floor: str = ""
    tiss_url: str = ""
    room_url: str = ""


def improve_calendar(cal: Calendar, use_shorthand: bool = True) -> Calendar:
    for component in cal.walk():
        if component.name != "VEVENT" or not summary_regex.match(
            component.get("summary")
        ):
            continue

        # Parse the event and enrich it
        event = event_from_ical(component)
        if use_shorthand:
            event = add_shorthand(event)
        event = add_location(event)

        # Serialize the summary
        summary = ""
        summary += event.shorthand if event.shorthand != "" else event.name
        summary += f" {event.lecture_type}"
        if event.additional != "":
            summary += " - " + event.additional
        component.pop("summary")
        component.add("summary", summary)

        # Serialize the address
        if event.address != "":
            component.pop("location")
            component.add("location", event.address)

        # Serialize the description
        # FIXME: Add something special for HTMl enabled clients
        description = f"{event.name}\nRoom: {event.room}\n"
        if event.floor != "":
            description += f"Floor: {event.floor}\n"
        description += f"\n{event.description}"
        component.pop("description")
        component.add("description", description)

    return cal


def event_from_ical(component) -> Event:
    summary = component.get("summary")
    match = summary_regex.match(summary)

    [number, lecture_type, name] = match.groups()
    additional = ""
    if " - " in name:
        [name, additional] = name.rsplit(" - ", 1)

    room = component.get("location")
    description = component.get("description")

    return Event(
        name=name,
        number=number,
        lecture_type=lecture_type,
        additional=additional,
        room=room,
        description=description,
    )


def add_shorthand(event: Event) -> Event:
    shorthands = read_shorthands()
    if event.name.lower() in shorthands:
        event.shorthand = shorthands[event.name.lower()].upper()
    return event


def add_location(event: Event) -> Event:
    rooms = read_rooms()
    if event.room not in rooms:
        return event

    (address, floor, url) = rooms[event.room]
    event.address = address
    event.floor = floor
    event.room_url = url
    return event


@cache
def read_shorthands() -> dict[str, str]:
    with open("resources/shorthands.csv") as f:
        lines = f.readlines()[1:]
    return {l.split(",")[1].lower().strip(): l.split(",")[0].strip() for l in lines}


@cache
def read_rooms() -> dict[str, tuple[str, str, str]]:
    with open("resources/rooms.csv") as f:
        lines = f.readlines()

    rooms = {}
    for line in lines:
        fields = line.split(";")
        # FIXME: do something with the floor
        name, address, floor, url = (
            fields[0],
            fields[6].split(",")[0].strip(),
            fields[6].split(",")[-1].strip(),
            fields[-1].strip(),
        )
        rooms[name] = (address, floor, url)

    return rooms


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
