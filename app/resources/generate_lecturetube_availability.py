# /// script
# dependencies = [
# "selenium==4.40.0",
# ]
# ///

# This script creates the file lecturetube_availability.csv.
# It does this automatically by the room UI from colab.tuwien.ac.at
# and extracting the information from there
# To run this enter the following:
# uv run generate_lecturetube_availability.py

import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    COLAB_LECTURETUBE_LINK = "https://colab.tuwien.ac.at/lecturetube/"
    NAVIGATION_ELEMENTS_SELECTOR = "nav.ht-pages-nav > ul.ht-pages-nav-top > li"
    ANKOR_LECTUREHALL_LIST_IDENTIFIER_DE = "hoersaalliste"
    ANKOR_LECTUREHALL_LIST_IDENTIFIER_EN = "lecture-halls"
    LECTURETUBELIST_CONTENT_SELECTOR = "#main-content"
    LECTURETUBELIST_ROW_SELECTOR = "tbody > tr"

    data: list[list[str]] = []

    with webdriver.Firefox() as driver:
        driver.get(COLAB_LECTURETUBE_LINK)
        navigation_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, NAVIGATION_ELEMENTS_SELECTOR)
            )
        )

        for listelement in navigation_elements:
            ankor = listelement.find_element(By.TAG_NAME, "a")
            href = ankor.get_attribute("href")
            if href and (
                (ANKOR_LECTUREHALL_LIST_IDENTIFIER_DE in href)
                or (ANKOR_LECTUREHALL_LIST_IDENTIFIER_EN in href)
            ):
                ankor.click()
                break

        main_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, LECTURETUBELIST_CONTENT_SELECTOR)
            )
        )

        table_rows = main_content.find_elements(
            By.CSS_SELECTOR, LECTURETUBELIST_ROW_SELECTOR
        )
        for row in table_rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            room_details = [cell.text for cell in cells]
            roomcode = room_details[2]
            if room_details[4] == "JA" and verifyHasLectureTubeStreaming(
                driver, roomcode
            ):
                data.append([roomcode])

    data.sort(key=lambda i: i[0])

    with open("lecturetube_availability.csv", "w", newline="", encoding="utf-8") as f:
        csvwriter = csv.writer(f)
        csvwriter.writerows(data)


def verifyHasLectureTubeStreaming(driver, room_code):
    LECTURETUBE_ROOM_LINK = (
        f"https://live.video.tuwien.ac.at/room/{room_code}/player.html"
    )
    CONTENT_CARD_SELECTOR = "main#content > .card"

    previous_window = driver.current_window_handle
    driver.switch_to.new_window("tab")
    driver.get(LECTURETUBE_ROOM_LINK)
    content_card = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, CONTENT_CARD_SELECTOR))
    )
    video_tags = content_card.find_elements(By.TAG_NAME, "video")
    driver.close()
    driver.switch_to.window(previous_window)
    return len(video_tags) > 0


if __name__ == "__main__":
    main()
