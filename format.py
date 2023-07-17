import html
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

    def plain_description(self) -> str:
        text = f"{self.name}\nRoom: {self.room}\n"
        if self.floor != "":
            text += f"Floor: {self.floor}\n"
        text += f"\n{self.description}"
        return text

    def html_description(self) -> str:
        text = f"<b>{html.escape(self.name)}</b><br>"

        if self.tiss_url != "":
            text += f'Details: <a href="{self.tiss_url}">TISS</a><br>'

        if self.room_url != "":
            text += f'Room: <a href="{self.room_url}">{self.room}</a><br>'
        else:
            text += f"Room: {self.room}<br>"

        if self.floor != "":
            text += f"Floor: {self.floor}<br>"

        text += f"<br>{html.escape(self.description)}"

        return text


def improve_calendar(
    cal: Calendar, use_shorthand: bool = True, google_cal: bool = False
) -> Calendar:
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
        component.pop("description")
        if google_cal:
            # So google calendar ignored the standard that says that the
            # description should only contain plain text. Then when some clients
            # (rightfully so) didn't support html in the description where the
            # standard says that there should be no html, they blamed it on the
            # clients and gaslight them.
            # Normally, I would congratulate such a bold and wrongfully confident
            # move but now I need to adapt to it in my code and I am pissed.
            component.add("description", event.html_description())
        else:
            component.add("description", event.plain_description())

        component.add("x-alt-desc;fmttype=text/html", event.html_description())

    # Set some metadata
    cal.pop("prodid")
    cal.add("prodid", "-//flofriday//Better TISS CAL//EN")
    cal.add("x-wr-calname", "Better TISS")

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

    # FIXME: We could also set the semester, but that would mean we would need
    # to calculate the semester.
    tiss_url = (
        "https://tiss.tuwien.ac.at/course/courseDetails.xhtml?courseNr="
        + number.strip().replace(".", "")
    )

    return Event(
        name=name,
        number=number,
        lecture_type=lecture_type,
        additional=additional,
        room=room,
        description=description,
        tiss_url=tiss_url,
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
    # FIXME: Shorthands mostly only work when the calendar is in german, we should also
    # have the english names in shorthands.csv, and simply add both version into
    # the dict.
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
