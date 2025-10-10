# /// script
# dependencies = [
#   "beautifulsoup4==4.14.2",
#   "httpx==0.28.1",
#   "aiohttp==3.13.0",
# ]
# ///


import argparse
import asyncio
import csv
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import aiohttp
from bs4 import BeautifulSoup

req_id = str(random.randint(0, 999))
window_id = str(random.randint(1000, 9999))


class CustomSession(aiohttp.ClientSession):
    def __init__(self):
        super().__init__(
            connector=aiohttp.TCPConnector(limit=0, limit_per_host=200),
            cookies={f"dsrwid-{req_id}": f"{window_id}", "TISS_LANG": "en"},
        )

    def get(self, url, **kwargs):
        new_url = url + (
            ("&" if "?" in url else "?") + f"dswid={window_id}&dsrid={req_id}"
        )

        return super().get(new_url, **kwargs)


session: None | CustomSession = None

total_programs = 0
counter_programs = 0


async def fetch_program_courses(program_url) -> set[str]:
    html = await (await session.get(program_url)).text()

    global counter_programs
    counter_programs += 1
    print(f"\t[{counter_programs}/{total_programs}] Downloaded {program_url}")

    courses = re.findall(r"/course/courseDetails\.xhtml\?courseNr=\d+", html)
    return set(courses)


@dataclass(frozen=True)
class Course:
    id: str | None
    name: str | None
    tiss_url: str
    tuwel_url: str | None
    registration_start: datetime | None
    registration_end: datetime | None
    deregistration_end: datetime | None


total_courses = 0
counter_courses = 0


async def fetch_course_info(course_url) -> Course:
    html = await (await session.get(course_url)).text()

    global counter_courses
    counter_courses += 1
    print(f"\t[{counter_courses}/{total_courses}] Downloaded {course_url}")

    soup = BeautifulSoup(html, "html.parser")

    course_soup = soup.find("span", class_="light")
    course_number = course_soup.get_text().strip() if course_soup else None

    h1_soup = soup.select_one("#contentInner > h1:nth-child(1)")
    name = (
        h1_soup.find_all(string=True, recursive=False)[1].strip()
        if h1_soup and len(h1_soup.find_all(string=True, recursive=False)) >= 2
        else None
    )

    tuwel_match = re.search(
        r"https://tuwel\.tuwien\.ac\.at/course/view\.php\?id=\d+",
        html,
    )
    tuwel_url = tuwel_match.group(0) if tuwel_match else None

    registration_tables = [
        t for t in soup.find_all("table") if "Deregistration end" in t.get_text()
    ]

    registration_start, registration_end, deregistration_end = [None] * 3
    if registration_tables != []:
        table = registration_tables[0]
        date_texts = [f.get_text().strip() for f in table.find_all("td")]

        def safe_parse_date(date_str, fmt="%d.%m.%Y %H:%M"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                return None

        registration_start, registration_end, deregistration_end = [
            safe_parse_date(t) for t in date_texts
        ]

    return Course(
        id=course_number,
        name=name,
        tiss_url=course_url,
        tuwel_url=tuwel_url,
        registration_start=registration_start,
        registration_end=registration_end,
        deregistration_end=deregistration_end,
    )


async def main():
    parser = argparse.ArgumentParser(
        prog="generate_courses.py",
        description="Gather information about all courses from TISS.",
    )
    parser.add_argument(
        "--debug-small",
        action="store_true",
        help="Only download a small set for debuggin purposes, since the full"
        + " set can take minutes.",
    )
    args = parser.parse_args()

    # setup the session
    global session
    session = CustomSession()

    # 1) Download programs list
    print("Downloading program list ...")
    programs_url = "https://tiss.tuwien.ac.at/curriculum/studyCodes.xhtml"

    programs_html = await (await session.get(programs_url)).text()
    programs = re.findall(
        r"/curriculum/public/curriculum\.xhtml\?key=\d+", programs_html
    )
    programs = ["https://tiss.tuwien.ac.at" + p for p in set(programs)]

    if args.debug_small:
        programs = programs[:10]

    print(f"Found {len(programs)} programs")

    # 2) Download all courses
    global total_programs
    total_programs = len(programs)
    print("Downloading courses list ...")
    courses = set().union(
        *await asyncio.gather(*[fetch_program_courses(p) for p in programs])
    )
    courses = ["https://tiss.tuwien.ac.at" + c for c in set(courses)]

    if args.debug_small:
        courses = courses[:100]

    print(f"Found {len(courses)} courses")

    # 3) Download all the course info
    global total_courses
    total_courses = len(courses)
    course_infos: Iterable[Course] = await asyncio.gather(
        *[fetch_course_info(c) for c in courses]
    )

    print("Writing to file courses.csv")
    course_infos = sorted(course_infos, key=lambda c: c.tiss_url)
    with open("courses.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Number",
                "Name",
                "TISS",
                "TUWEL",
                "Registration Start",
                "Registration End",
                "Deregistration End",
            ]
        )
        for course in course_infos:
            writer.writerow(
                [
                    course.id,
                    course.name,
                    course.tiss_url,
                    course.tuwel_url,
                    course.registration_start.isoformat()
                    if course.registration_start
                    else None,
                    course.registration_end.isoformat()
                    if course.registration_end
                    else None,
                    course.deregistration_end.isoformat()
                    if course.deregistration_end
                    else None,
                ]
            )

    await session.close()
    print("Done ✨")


asyncio.run(main())
