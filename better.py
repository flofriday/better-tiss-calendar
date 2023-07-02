from icalendar import Calendar
import re

summary_regex = re.compile("([0-9A-Z]{3}\.[0-9A-Z]{3}) ([A-Z]{2}) (.*)")


def improve_calendar(cal: Calendar) -> Calendar:
    cal = rename_subjects(cal)
    return cal


def rename_subjects(cal: Calendar) -> Calendar:
    shorthands = read_shorthands()

    for component in cal.walk():
        if component.name == "VEVENT":
            old_summary = component.get("summary")
            component.pop("summary")
            component.add("summary", better_summary(old_summary, shorthands))
    return cal


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

    if name.lower() in shorthands:
        name = shorthands[name.lower()].upper()

    summary = f"{name} {lecture_type}"
    if additional != "":
        summary += " - " + additional
    return summary
