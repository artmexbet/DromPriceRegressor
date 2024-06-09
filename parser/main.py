from pprint import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait


class DromPage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        driver.maximize_window()

    def open(self, path=""):
        self.driver.get('https://auto.drom.ru/region24/' + path)

    def wait_many(self, selector):
        return Wait(self.driver, 50).until(EC.visibility_of_all_elements_located(selector))

    def wait_one(self, selector):
        return Wait(self.driver, 5).until(EC.visibility_of_element_located(selector))

    def get_cards(self):
        tmp = self.wait_many((By.CSS_SELECTOR, '.css-4zflqt.e1huvdhj1'))
        cards_info = []
        for card in tmp:
            car_specs = card.find_elements(By.CSS_SELECTOR, 'span[data-ftid="bull_description-item"]')
            name_span = card.find_element(By.CSS_SELECTOR, '.css-16kqa8y.e3f4v4l2').text
            name, year = name_span.split(', ')
            engine_capacity, engine_power = car_specs[0].text.rstrip(",").split(" (")
            brand, *model = name.split(" ")
            card_info = {
                'brand': brand,
                'model': " ".join(model),
                'engine_power': int(engine_power.strip(' л.с.)')),
                'engine_capacity': float(engine_capacity.rstrip(" л")),
                'fuel_type': car_specs[1].text.rstrip(","),
                'wd': car_specs[3].text.rstrip(","),
                'price': int(card.find_element(By.CSS_SELECTOR, 'span[data-ftid="bull_price"]').text.replace(" ", "")),
                'year': int(year)
            }

            if len(car_specs) == 5:
                card_info['mileage'] = int(car_specs[4].text.rstrip(" км").replace(" ", ""))
            else:
                card_info['mileage'] = 0

            self.driver.execute_script("arguments[0].click();", card)
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
            card_info['transmission'] = ad_car_specs.get("Коробка передач", "-")
            card_info['body'] = ad_car_specs.get("Тип кузова", "-")
            card_info['color'] = ad_car_specs.get("Цвет", "-")
            card_info['steering_wheel_pos'] = ad_car_specs.get("Руль", "-")
            card_info['generation'] = ad_car_specs.get("Поколение", "-")

            vin_specs = self.wait_many((By.CSS_SELECTOR, '.css-z05wok.eawu4md2'))
            if len(vin_specs) > 2:
                first = vin_specs[:2]
                card_info['documents_cond'] = first[0].find_element(By.CSS_SELECTOR, 'button').text
                card_info['drivers_count'] = int(first[1].find_element(By.CSS_SELECTOR, 'button').text.split()[0])
                card_info['was_driven_by_legal_person'] = vin_specs[3].text != "Был во владении у юр. лица"
                card_info['is_under_credit'] = vin_specs[6].text == "Ограничений не обнаружено"
            else:
                card_info['documents_cond'] = "-"
                card_info['drivers_count'] = -1
                card_info['was_driven_by_legal_person'] = False
                card_info['is_under_credit'] = False
            self.driver.back()

            cards_info.append(card_info)
        return cards_info


if __name__ == "__main__":
    driver = webdriver.Chrome()
    page = DromPage(driver)
    page.open()
    res = []
    for i in range(2, 3):
        res += page.get_cards()
        page.open(f'all/page{i}')
    pprint(res[:5])
    print(len(res))
