import csv
import html
import re
import string
from dataclasses import dataclass
from functools import cache

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
    name: str = ""
    shorthand: str = ""
    lecture_type: str = ""
    additional: str = ""
    number: str = ""
    description: str = ""
    address: str = ""
    room: str = ""
    room_code: str = ""
    floor: MultiLangString | None = None
    tiss_url: str = ""
    tuwel_url: str = ""
    room_url: str = ""
    map_url: str = ""

    def plain_description_en(self) -> str:
        text = ""

        if self.shorthand != "":
            text += f"{self.name}\n"

        text += f"Room: {self.room}\n"
        if self.floor is not None:
            text += f"Floor: {self.floor.en}\n"
        text += f"\n{self.description}"

        return text

    def html_description_en(self) -> str:
        text = ""

        if self.shorthand != "":
            text += f"<b>{html.escape(self.name)}</b><br>"

        text += f'Details: <a href="{self.tiss_url}">Lecture</a>'
        if self.tuwel_url != "":
            text += f', <a href="{self.tuwel_url}">TUWEL</a>'
        if self.room_url != "":
            text += f', <a href="{self.room_url}">Room-Schedule</a>'
        text += "<br>"

        if self.map_url != "":
            text += f'Room: <a href="{self.map_url}">{self.room}</a><br>'
        else:
            text += f"Room: {self.room}<br>"

        if self.floor is not None:
            text += f"Floor: {self.floor.en}<br>"

        text += f"<br>{html.escape(self.description)}"

        return text

    def plain_description_de(self) -> str:
        text = ""

        if self.shorthand != "":
            text += f"{self.name}"
        text += f"\nRaum: {self.room}\n"
        if self.floor is not None:
            text += f"Stock: {self.floor.de}\n"
        text += f"\n{self.description}"

        return text

    def html_description_de(self) -> str:
        text = ""

        if self.shorthand != "":
            text += f"<b>{html.escape(self.name)}</b><br>"

        text += f'Details: <a href="{self.tiss_url}">LVA</a>'
        if self.tuwel_url != "":
            text += f', <a href="{self.tuwel_url}">TUWEL</a>'
        if self.room_url != "":
            text += f', <a href="{self.room_url}">Raum Reservierung</a>'
        text += "<br>"

        if self.map_url != "":
            text += f'Raum: <a href="{self.map_url}">{self.room}</a><br>'
        else:
            text += f"Raum: {self.room}<br>"

        if self.floor is not None:
            text += f"Stock: {self.floor.de}<br>"

        text += f"<br>{html.escape(self.description)}"

        return text


def improve_calendar(
    cal: Component,
    use_shorthand: bool = True,
    google_cal: bool = False,
    locale: str | None = None,
) -> Component:
    if locale is None:
        locale = "de"

    for component in cal.walk():
        if component.name != "VEVENT" or not summary_regex.match(
            component.get("summary")
        ):
            continue

        # Parse the event and enrich it
        event = event_from_ical(component)
        if use_shorthand:
            event.shorthand = create_shorthand(event.name)
        event = add_location(event)

        # Serialize the summary
        summary = ""
        summary += event.shorthand if event.shorthand != "" else event.name
        summary += f" {event.lecture_type}"
        if event.additional != "":
            summary += " - " + event.additional
        component.pop("summary")
        component.add("summary", summary)

        # Add tuwel
        event.tuwel_url = read_tuwel_urls().get(event.number, "")

        # Serialize the address
        if event.address != "":
            component.pop("location")
            component.add("location", event.address)

        # Serialize the description
        if locale == "de":
            plain_description = event.plain_description_de()
            html_description = event.html_description_de()
        else:
            plain_description = event.plain_description_en()
            html_description = event.html_description_en()

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
            component.add("url", event.map_url)
            component.add("x-alt-desc;fmttype=text/html", html_description)

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
        additional=additional,
        room=room,
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


@cache
def read_tuwel_urls() -> dict[str, str]:
    id_to_url = {}

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

            if id is None or tuwel is None:
                continue

            id_to_url[id] = tuwel

    return id_to_url


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
