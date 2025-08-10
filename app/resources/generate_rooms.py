# /// script
# dependencies = [
# "attrs==23.2.0",
# "certifi==2024.7.4",
# "h11==0.14.0",
# "idna==3.7",
# "outcome==1.3.0.post0",
# "PySocks==1.7.1",
# "selenium==4.19.0",
# "sniffio==1.3.1",
# "sortedcontainers==2.4.0",
# "trio==0.25.0",
# "trio-websocket==0.11.1",
# "typing_extensions==4.11.0",
# "urllib3==2.2.2",
# "wsproto==1.2.0",
# ]
# ///

# This script creates the files rooms.csv.
# It does this automatically by the room UI from tiss and extracting the
# information from there.
# To run this enter the following:
# uv run generate_rooms.py

import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    TISS_ROOM_LINK = "https://tiss.tuwien.ac.at/events/selectRoom.xhtml"
    NAVIGATION_BUTTON_SELECTOR = ".ui-paginator-pages > *"
    TABLE_ROW_SELECTOR = "#tableForm\\:roomTbl_data > *"

    data: list[list[str]] = []

    with webdriver.Firefox() as driver:
        driver.get(TISS_ROOM_LINK)
        navigation_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, NAVIGATION_BUTTON_SELECTOR)
            )
        )

        for i in range(0, len(navigation_buttons)):
            navigation_buttons = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, NAVIGATION_BUTTON_SELECTOR)
                )
            )
            navigation_buttons[i].click()
            table_rows = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, TABLE_ROW_SELECTOR)
                )
            )
            for row in table_rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                room = [cell.text for cell in cells]
                room.append(
                    cells[0]
                    .find_elements(By.CSS_SELECTOR, "a")[0]
                    .get_attribute("href")
                )
                data.append(room)

    data.sort(key=lambda i: i[0])

    with open("rooms.csv", "w", newline="", encoding="utf-8") as f:
        csvwriter = csv.writer(f)
        csvwriter.writerows(data)


if __name__ == "__main__":
    main()
