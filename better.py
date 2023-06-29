from icalendar import Calendar
import re

summary_regex = re.compile("([0-9A-Z]{3}\.[0-9A-Z]{3}) ([A-Z]{2}) (.*)")


def improve_calendar(cal: Calendar) -> Calendar:
    cal = rename_subjects(cal)
    return cal


def rename_subjects(cal: Calendar) -> Calendar:
    for component in cal.walk():
        if component.name == "VEVENT":
            old_summary = component.get("summary")
            component.pop("summary")
            component.add("summary", better_summary(old_summary))
    return cal


def better_summary(old: str) -> str:
    match = summary_regex.match(old)
    if match is None:
        return old

    # FIXME: Might be better to write our own parser here
    [number, lecture_type, name] = match.groups()
    return f"{name} {lecture_type}"
