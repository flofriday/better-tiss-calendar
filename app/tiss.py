import requests
from icalendar import Calendar


def get_calendar(url: str) -> Calendar:
    resp = requests.get(url)
    resp.raise_for_status()

    cal = Calendar.from_ical(resp.content)
    return cal
