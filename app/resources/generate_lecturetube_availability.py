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
import time

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
            ankor = listelement.find_element(By.TAG_NAME, 'a')
            href = ankor.get_attribute('href')
            if href and ((ANKOR_LECTUREHALL_LIST_IDENTIFIER in href) or (ANKOR_LECTUREHALL_LIST_IDENTIFIER_EN in href)):
                ankor.click()
                break
        
        main_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, LECTURETUBELIST_CONTENT_SELECTOR)
            )
        )

        table_rows = main_content.find_elements(By.CSS_SELECTOR, LECTURETUBELIST_ROW_SELECTOR)
        for row in table_rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            room_details = [cell.text for cell in cells]
            roomcode = room_details[2]
            if (room_details[4] == "JA" and verifyHasLectureTubeStreaming(driver, roomcode)):
                data.append([roomcode])

    data.sort(key=lambda i: i[0])
    
    with open("lecturetube_availability.csv", "w", newline="", encoding="utf-8") as f:
        csvwriter = csv.writer(f)
        csvwriter.writerows(data)

def verifyHasLectureTubeStreaming(driver, room_code):
    LECTURETUBE_ROOM_LINK = f"https://live.video.tuwien.ac.at/room/{room_code}/player.html"
    CONTENT_CARD_SELECTOR = "main#content > .card"

    previous_window = driver.current_window_handle
    driver.switch_to.new_window('tab')
    driver.get(LECTURETUBE_ROOM_LINK)
    content_card = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CONTENT_CARD_SELECTOR)
            )
        )
    video_tags = content_card.find_elements(By.TAG_NAME, 'video')
    driver.close()
    driver.switch_to.window(previous_window)
    return len(video_tags) > 0

if __name__ == "__main__":
    main()
