import requests
from icalendar import Calendar, Component


def get_calendar(url: str) -> Component:
    resp = requests.get(url)
    resp.raise_for_status()
    return Calendar.from_ical(resp.text)
