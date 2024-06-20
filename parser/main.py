import os.path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from typing import List, Iterable

import pandas as pd


class DromPage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        driver.maximize_window()

    def open(self, path=""):
        self.driver.get('https://auto.drom.ru/region24/' + path)

    def wait_many(self, selector):
        return Wait(self.driver, 15).until(EC.visibility_of_all_elements_located(selector))

    def wait_one(self, selector):
        return Wait(self.driver, 5).until(EC.visibility_of_element_located(selector))

    def get_cars_pages(self, n=20) -> List[str]:
        """
        Gets all cars pages from search
        :param n: count of pages, which will be processed
        :return: list of links to cars
        """
        links = []
        for i in range(1, n + 1):
            self.open(f"all/page{i}")
            cards = self.wait_many((By.CSS_SELECTOR, '.css-4zflqt.e1huvdhj1'))
            for card in cards:
                links.append(card.get_attribute("href"))
        return links

    def get_cars_info(self, links: Iterable[str], filepath) -> List[dict]:
        """
        Gets info about cars from links
        :param links: list of links to cars
        :param filepath: path to file to save info
        :return: list of dicts with info about cars
        """
        cars_info = []

        for i, link in enumerate(links, 1):
            self.driver.get(link)
            try:
                name_span = self.wait_one(
                    (By.CSS_SELECTOR, '.css-1kb7l9z.e162wx9x0')
                ).text.lstrip("Продажа")
            except:
                continue

            name, year = name_span.split(', ')
            # engine_capacity, engine_power = car_specs[0].text.rstrip(",").split(" (")
            print(name)
            brand, *model = name.strip().split(" ")
            try:
                card_info = {
                    'brand': brand,
                    'model': " ".join(model),
                    'price': int(self.wait_one((By.CSS_SELECTOR, '.wb9m8q0')).text.replace(" ", "").rstrip("₽")),
                    'year': int(year.split(" год")[0])
                }
            except:
                continue

            # Получаем дополнительные данные (АКПП может делиться на несколько типов и т.д.)
            ad_car_specs_table = (self.wait_one((By.CSS_SELECTOR, '.css-xalqz7.eppj3wm0')).
                                  find_element(By.CSS_SELECTOR, 'tbody'))
            ad_car_specs_rows = ad_car_specs_table.find_elements(By.CSS_SELECTOR, 'tr')
            ad_car_specs = {}
            for row in ad_car_specs_rows:
                try:
                    ad_car_specs[row.find_element(By.CSS_SELECTOR, 'th').text] = row.find_element(
                        By.CSS_SELECTOR, 'td'
                    ).text
                except Exception:
                    pass
            try:
                card_info['transmission'] = ad_car_specs.get("Коробка передач", "-")
                card_info['body'] = ad_car_specs.get("Тип кузова", "-")
                card_info['color'] = ad_car_specs.get("Цвет", "-")
                card_info['steering_wheel_pos'] = ad_car_specs.get("Руль", "-")
                card_info['generation'] = ad_car_specs.get("Поколение", "-")
                if ad_car_specs["Пробег"] == "новый автомобиль":
                    card_info['mileage'] = 0
                elif ad_car_specs["Пробег"].endswith("без пробега по РФ"):
                    card_info['mileage'] = int(ad_car_specs['Пробег'].split(", ")[0].rstrip(" км").replace(" ", ""))
                    card_info['without_mileage_in_RF'] = True
                else:
                    card_info['mileage'] = int(ad_car_specs['Пробег'].rstrip(" км").replace(" ", ""))
                card_info['engine_power'] = int(ad_car_specs["Мощность"].strip(" л.с., налог"))

                if "электро" == ad_car_specs["Двигатель"]:
                    card_info['fuel_type'] = "электро"
                else:
                    fuel_type, engine_capacity, *other = ad_car_specs["Двигатель"].split(", ")
                    card_info['fuel_type'] = fuel_type if len(other) == 0 else other[0]
                    card_info['engine_capacity'] = float(engine_capacity.rstrip(' л'))
                card_info['wd'] = ad_car_specs['Привод']
            except:
                continue

            try:
                has_vin_specs = self.wait_one((By.CSS_SELECTOR, ".css-tf8dm7.e162wx9x0")).text == "Отчет по VIN-коду"
            except Exception:
                has_vin_specs = False
            if has_vin_specs:
                try:
                    first_vin_specs = self.wait_many((By.CSS_SELECTOR, '.css-13qo6o5.eawu4md1'))
                    vin_specs = self.wait_many((By.CSS_SELECTOR, '.css-13qo6o5.e1mhp2ux0'))
                except:
                    continue
                if len(vin_specs) > 2:
                    card_info['documents_cond'] = first_vin_specs[0].find_element(By.CSS_SELECTOR, 'button').text
                    card_info['drivers_count'] = int(
                        first_vin_specs[1].find_element(By.CSS_SELECTOR, 'button').text.split()[0])
                    card_info['was_driven_by_legal_person'] = vin_specs[1].text != "Был во владении у юр. лица"
                    card_info['is_under_credit'] = vin_specs[4].text == "Ограничений не обнаружено"

            try:
                description = self.wait_one((By.CSS_SELECTOR, '.css-inmjwf.e162wx9x0')).find_elements(
                    By.CSS_SELECTOR, 'span')[1].text
                card_info["description_len"] = len(description)
            except:
                pass

            cars_info.append(card_info)
            if i % 10 == 0:
                tmp = pd.DataFrame(cars_info)
                tmp.to_csv(filepath)

        return cars_info


if __name__ == "__main__":
    if os.path.exists("cars.csv"):
        df = pd.read_csv("cars.csv")
    else:
        df = pd.DataFrame()
    driver = webdriver.Chrome()
    page = DromPage(driver)
    links = page.get_cars_pages()
    info = page.get_cars_info(set(links), "cars.csv")
    df.to_csv("cars.csv")
    print(df)
