# /// script
# dependencies = [
#   "requests==2.32.5",
# ]
# ///


import random
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import csv

import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "nl-NL,nl;q=0.9,en-AT;q=0.8,en-US;q=0.7,en;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

req_id = str(random.randint(0, 999))
window_id = str(random.randint(1000, 9999))


class CustomSession(requests.Session):
    def __init__(self):
        super().__init__()

    def get(self, url, **kwargs):
        new_url = url + (
            ("&" if "?" in url else "?") + f"dswid={window_id}&dsrid={req_id}"
        )

        return super().get(new_url, **kwargs)


session = CustomSession()
session.headers.update(headers)
session.cookies.set(f"dsrwid-{req_id}", f"{window_id}", domain="tiss.tuwien.ac.at")
session.cookies.set("TISS_LANG", "en", domain="tiss.tuwien.ac.at")
session.cookies.set(f"dsrwid-{req_id}", f"{window_id}", domain="tiss.tuwien.ac.at")
session.cookies.set("TISS_LANG", "en", domain="tiss.tuwien.ac.at")


def fetch_program_courses(program_url):
    html = session.get(program_url).text
    courses = re.findall(r"/course/courseDetails\.xhtml\?courseNr=\d+", html)
    return set(courses)


@dataclass(frozen=True)
class Course:
    id: str | None
    tiss_url: str
    tuwel_url: str | None


def fetch_course_info(course_url):
    html = session.get(course_url).text
    course_match = re.search(r'<span class="light">([\d\.]+)', html)
    course_number = course_match.group(1) if course_match else "unknown"
    tuwel_match = re.search(
        r"https://tuwel\.tuwien\.ac\.at/course/view\.php\?id=\d+",
        html,
    )
    tuwel_url = tuwel_match.group(0) if tuwel_match else None
    return Course(id=course_number, tiss_url=course_url, tuwel_url=tuwel_url)


def main():
    # 1) Download programs list
    print("Downloading program list ...")
    programs_url = "https://tiss.tuwien.ac.at/curriculum/studyCodes.xhtml"

    programs_html = session.get(programs_url).text
    programs = re.findall(
        r"/curriculum/public/curriculum\.xhtml\?key=\d+", programs_html
    )
    programs = ["https://tiss.tuwien.ac.at" + p for p in set(programs)]
    print(f"Found {len(programs)} programs")

    # 2) Download all courses
    print("Downloading courses list ...")
    with ThreadPoolExecutor(max_workers=100) as executor:
        # Map fetch_program_courses over all programs
        results = executor.map(fetch_program_courses, programs)

        # Combine all course sets
        courses = set().union(*results)
    courses = ["https://tiss.tuwien.ac.at" + c for c in set(courses)]

    print(f"Found {len(courses)} courses")

    # 3) Download all the course info
    course_infos = set()
    with ThreadPoolExecutor(max_workers=100) as executor:
        # Map fetch_program_courses over all programs
        results = executor.map(fetch_course_info, courses)
        # Combine all course sets
        course_infos.update(results)

    with open("courses.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for course in course_infos:
            writer.writerow([course.id, course.tiss_url, course.tuwel_url])


main()
