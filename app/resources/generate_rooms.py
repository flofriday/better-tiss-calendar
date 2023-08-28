import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    TISS_ROOM_LINK = "https://tiss.tuwien.ac.at/events/selectRoom.xhtml"
    NAVIGATION_BUTTON_SELECTOR = ".ui-paginator-pages > *"
    TABLE_ROW_SELECTOR = "#tableForm\:roomTbl_data > *"

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
                    "https://tiss.tuwien.ac.at/events/roomSchedule.xhtml?roomCode="
                    + room[7]
                )
                data.append(room)

    data.sort(key=lambda i: i[0])

    with open("rooms.csv", "w", newline="", encoding="utf-8") as f:
        csvwriter = csv.writer(f, delimiter=";")
        csvwriter.writerows(data)


if __name__ == "__main__":
    main()
