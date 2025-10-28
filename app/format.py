import csv
import html
import re
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cache

import icalendar
from icalendar import Component

summary_regex = re.compile("([0-9A-Z]{3}\\.[0-9A-Z]{3}) ([A-Z]{2}) (.*)")
word_split_regex = re.compile(
    re.escape(string.punctuation) + re.escape(string.whitespace)
)


class MultiLangString:
    "A string to hold multiple languages"

    def __init__(self, de: str, en: str | None = None) -> None:
        self.de = de
        self.en = en if en is not None else de


@dataclass(kw_only=True, slots=True)
class Event:
    name: str
    shorthand: str | None = None
    lecture_type: str
    additional: str | None = None
    number: str
    description: str
    address: str | None = None
    room: str | None = None
    room_code: str | None = None
    floor: MultiLangString | None = None
    tiss_url: str
    tuwel_url: str | None = None
    room_url: str | None = None
    map_url: str | None = None
    lecturetube_url: str | None = None

    def plain_description(self, lang: str) -> str:
        text = ""
        if self.shorthand is not None:
            text += f"{self.name} {self.lecture_type}\n"
        text += f"{self.description}\n\n"

        if self.room:
            text += "Room:\n" if lang == "en" else "Raum:\n"
            text += self.room
            if self.floor is not None:
                text += f", {self.floor.en if lang == 'en' else self.floor.de}"
            text += "\n"
            if self.map_url is not None:
                text += f"{self.map_url}\n"
            text += "\n"

        details = [
            (self.tiss_url, "TISS"),
            (self.tuwel_url, "TUWEL"),
            (self.room_url, "Room-Info" if lang == "en" else "Raum-Info"),
            (self.lecturetube_url, "Lecture Tube"),
        ]

        for url, name in filter(lambda d: d[0] is not None, details):
            text += f"{name}:\n{url}\n\n"

        return text.strip()

    def html_description(self, lang: str) -> str:
        text = ""

        if self.shorthand is not None:
            text += (
                f"<b>{html.escape(self.name)} {html.escape(self.lecture_type)}</b><br>"
            )
        text += f"{html.escape(self.description)}<br><br>"

        if self.room:
            text += "Room:<br>" if lang == "en" else "Raum:<br>"

            if self.map_url:
                text += f'<a href="{self.map_url}">{html.escape(self.room)}</a>'
            else:
                text += html.escape(self.room)

            if self.floor is not None:
                text += (
                    f", {html.escape(self.floor.en if lang == 'en' else self.floor.de)}"
                )

            text += "<br><br>"

        details = [
            (self.tiss_url, "TISS"),
            (self.tuwel_url, "TUWEL"),
            (self.room_url, "Room-Info" if lang == "en" else "Raum-Info"),
            (self.lecturetube_url, "Lecture Tube"),
        ]
        details = [d for d in details if d[0] is not None]

        if details != []:
            text += "Details:<br><ul>"
            for url, name in details:
                text += f'<li><a href="{url}">{name}</a></li>'
            text += "</ul>"

        return text


def improve_calendar(
    cal: Component,
    use_shorthand: bool = True,
    google_cal: bool = False,
    locale: str | None = None,
) -> Component:
    if locale is None:
        locale = "de"

    seen_lecture_numbers: set[str] = set()

    for component in cal.walk():
        if component.name != "VEVENT" or not summary_regex.match(
            component.get("summary")
        ):
            continue

        # Parse the event and enrich it
        event = event_from_ical(component)
        seen_lecture_numbers.add(event.number)
        if use_shorthand:
            event.shorthand = create_shorthand(event.name)
        event = add_location(event)

        # Serialize the summary
        summary = event.shorthand if event.shorthand is not None else event.name
        summary += f" {event.lecture_type}"
        if event.additional is not None:
            summary += " - " + event.additional
        component.pop("summary")
        component.add("summary", summary)

        # Add tuwel
        if course := read_courses().get(event.number, None):
            event.tuwel_url = course.tuwel_url
        # Serialize the address
        if event.address is not None:
            component.pop("location")
            component.add("location", event.address)

        # Serialize the description
        plain_description = event.plain_description(locale)
        html_description = event.html_description(locale)

        component.pop("description")
        if google_cal:
            # So google calendar ignored the standard that says that the
            # description should only contain plain text. Then when some clients
            # (rightfully so) didn't support html in the description where the
            # standard says that there should be no html, they blamed it on the
            # clients and gaslight them.
            # Normally, I would congratulate such a bold and wrongfully confident
            # move but now I need to adapt to it in my code and I am pissed.
            component.add("description", html_description)
        else:
            component.add("description", plain_description)
            component.add("x-alt-desc;fmttype=text/html", html_description)

    # Insert signup dates
    for lecture in sorted(seen_lecture_numbers):
        course = read_courses().get(lecture, None)
        if course is None:
            continue

        # FIXME:
        # We cannot insert the url directly to the singup, because it requries
        # the semester and we don't know for which semester you are signed up for
        # (we could invent some heuristic though).
        # So for now just insert the default url to TISS, the user will figure
        # it out.

        name = course.name

        if course.registration_start is not None:
            signup = icalendar.Event()
            signup.add(
                "summary",
                f"Anmeldung {name}" if locale == "de" else f"Signup {name}",
            )
            signup.add("dtstart", course.registration_start)
            end = course.registration_start + timedelta(minutes=30)

            # Some signups start at midnight but are easy to oversee so lets
            # stretch them.
            if end.hour < 8:
                end = end.replace(hour=8, minute=0)

            signup.add("dtend", end)
            signup.add("categories", "COURSE")

            description = f"Registrations for {name} are now open."
            description_html = (
                f"Registrations for {name} are now open.\n"
                f'<a href="{course.tiss_url}">Register on Tiss</a>'
            )
            if google_cal:
                signup.add("description", description_html)
            else:
                signup.add("description", description)
                signup.add("url", course.tiss_url)
                signup.add(
                    "x-alt-desc;fmttype=text/html",
                    f'<a href="{course.tiss_url}">Register on Tiss</a>',
                )

            cal.add_component(signup)

    # Set some metadata
    cal.pop("prodid")
    cal.add("prodid", "-//flofriday//Better TISS CAL//EN")
    cal.add("name", "Better TISS")
    cal.add("x-wr-calname", "Better TISS")

    return cal


def event_from_ical(component) -> Event:
    summary = component.get("summary")
    match = summary_regex.match(summary)

    [number, lecture_type, name] = match.groups()  # type: ignore
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
        additional=additional if additional.strip() else None,
        room=room if room.strip() else None,
        description=description,
        tiss_url=tiss_url,
    )


def create_shorthand(name: str) -> str:
    shorthands = read_shorthands()
    if name.lower() in shorthands:
        return shorthands[name.lower()].upper()

    return create_shorthand_fallback(name)


def create_shorthand_fallback(name: str) -> str:
    # Shorthands are all the uppercase letters
    iter = filter(lambda c: c.isupper(), name)
    shorthand = "".join(iter)
    if is_valid_shorthand(shorthand):
        return shorthand

    # Shorthands are the first letters of all capitalized words.
    iter = word_split_regex.split(name)
    iter = filter(lambda w: len(w) > 1 and w[0].isupper(), iter)
    iter = map(lambda w: w[0], iter)
    shorthand = "".join(iter)

    # The generated shorthand can be somewhat bad so lets add some checks:
    if is_valid_shorthand(shorthand):
        return shorthand

    # Couldn't generate a shorthand, default to original
    return name


def is_valid_shorthand(shorthand: str) -> bool:
    """The generated shorthand has to be meaning full without beeing offending.

    Requirements:
        - At least 2 Symbols
        - At most 6
        - No offending words
    """

    if len(shorthand) < 2 or len(shorthand) > 6:
        return False

    forbidden = ["SS", "NAZI"]
    return shorthand not in forbidden


def add_location(event: Event) -> Event:
    rooms = read_rooms()
    if event.room not in rooms:
        return event

    (address, floor, code, url) = rooms[event.room]
    event.address = address

    # FIXME: the floor information in the dataset is all over the place.
    # We should create a better more universal dataset
    event.floor = floor if floor is not None else create_floor_fallback(code)
    event.room_code = code
    event.room_url = url
    event.map_url = f"https://maps.tuwien.ac.at/?q={code}#map"
    if code in read_lecturetube_available_rooms():
        event.lecturetube_url = (
            f"https://live.video.tuwien.ac.at/room/{code}/player.html"
        )
    return event


def create_floor_fallback(room_code: str) -> MultiLangString | None:
    """The floor information is encoded in the room code.

    Format: TTFFRR[R]
    In that format TT is the trackt, FF the floor and RR the room specific
    code.
    """

    if len(room_code) < 6 or len(room_code) > 7:
        return None

    floor_code = room_code[2:4]

    if floor_code.isnumeric():
        floor = int(floor_code)
        return MultiLangString(f"{floor}. Stock", f"{floor}. Floor")
    elif floor_code == "EG":
        return MultiLangString("Erdgeschoß", "Ground Floor")
    elif floor_code == "DG":
        return MultiLangString("Dachgeschoß", "Roof Floor")
    elif floor_code[0] == "U" and floor_code[1].isnumeric():
        floor = int(floor_code[1])
        return MultiLangString(f"{floor}. Untergeschoß", f"{floor}. Underground Floor")
    else:
        return MultiLangString(floor_code)


@dataclass(frozen=True)
class Course:
    id: str | None
    name: str | None
    tiss_url: str
    tuwel_url: str | None
    registration_start: datetime | None
    registration_end: datetime | None
    deregistration_end: datetime | None


@cache
def read_courses() -> dict[str, Course]:
    id_to_course: dict[str, Course] = {}

    # FIXME: Probably refactor into something that can be reused to also process
    # all the other informations.
    with open("app/resources/courses.csv") as f:
        # The first line is a header
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            (
                id,
                name,
                tiss,
                tuwel,
                registration_start,
                registration_end,
                deregistration_end,
            ) = row

            if id is None or id == "":
                continue

            name = name.strip() if name.strip() != "" else None
            tuwel = tuwel.strip() if tuwel.strip() != "" else None
            registration_start = (
                datetime.fromisoformat(registration_start)
                if registration_start.strip() != ""
                else None
            )
            registration_end = (
                datetime.fromisoformat(registration_end)
                if registration_end.strip() != ""
                else None
            )
            deregistration_end = (
                datetime.fromisoformat(deregistration_end)
                if deregistration_end.strip() != ""
                else None
            )
            course = Course(
                id,
                name,
                tiss,
                tuwel,
                registration_start,
                registration_end,
                deregistration_end,
            )

            id_to_course[id] = course

    return id_to_course


@cache
def read_shorthands() -> dict[str, str]:
    with open("app/resources/shorthands.csv") as f:
        # The first line is a header
        lines = f.readlines()[1:]

    shorthands = {}
    for line in lines:
        shorthand, lecture_de, lecture_en = line.split(",")
        lecture_de = lecture_de.lower().strip()
        lecture_en = lecture_en.lower().strip()

        if lecture_de != "" and lecture_de != "N/A":
            shorthands[lecture_de] = shorthand
        if lecture_en != "" and lecture_en != "N/A":
            shorthands[lecture_en] = shorthand

    return shorthands


@cache
def read_rooms() -> dict[str, tuple[str, MultiLangString, str, str]]:
    upper_floor_patttern = re.compile(r"(\d). ?(Stock|Obergescho(ss|ß)|OG)")
    ground_floor_patttern = re.compile(r"(EG|Erdgescho(ss|ß))")
    roof_floor_patttern = re.compile(r"(DG|Erdgescho(ss|ß))")

    with open("app/resources/rooms.csv") as f:
        reader = csv.reader(f)

        rooms = {}
        for fields in reader:
            name = fields[0]
            address = fields[6].split(",")[0].strip()

            # The floor information is in any of the address fields but never
            # the first one
            floor_fields = fields[6].split(",")[1:]
            keywords = ["OG", "UG", "DG", "EG", "Stock", "geschoß", "geschoss"]
            floor_fields = [
                field for field in floor_fields if any([kw in field for kw in keywords])
            ]

            # Parsing the floor description for localization and consistency
            floor = None
            if floor_fields != []:
                floor_description = floor_fields[0].strip()

                if (match := upper_floor_patttern.match(floor_description)) is not None:
                    number = int(match.group(1))
                    floor = MultiLangString(f"{number}. Stock", f"{number}. Floor")
                elif ground_floor_patttern.match(floor_description) is not None:
                    floor = MultiLangString("Erdgeschoß", "Ground Floor")
                elif roof_floor_patttern.match(floor_description) is not None:
                    floor = MultiLangString("Dachgeschoß", "Roof Floor")
                else:
                    floor = MultiLangString(floor_description)

            code = fields[7].strip()
            url = fields[8].strip()

            rooms[name] = (address, floor, code, url)

    return rooms


@cache
def read_lecturetube_available_rooms() -> set[str]:
    available_rooms = set()

    with open("app/resources/lecturetube_availability.csv") as f:
        reader = csv.reader(f)

        for fields in reader:
            available_rooms.add(fields[0])
    return available_rooms
