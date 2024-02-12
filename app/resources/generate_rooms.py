# This script creates the files rooms.csv.
# It does this automatically by the room UI from tiss and extracting the information from there.
# To run this you first need to: pip install selenium
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    TISS_ROOM_LINK = "https://tiss.tuwien.ac.at/events/selectRoom.xhtml"
    NAVIGATION_BUTTON_SELECTOR = ".ui-paginator-pages > *"
    TABLE_ROW_SELECTOR = "#tableForm\\:roomTbl_data > *"

    data = []

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
