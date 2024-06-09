import time

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
                'transmission': car_specs[2].text.rstrip(", "),
                'wd': car_specs[3].text.rstrip(","),
                'price': int(card.find_element(By.CSS_SELECTOR, 'span[data-ftid="bull_price"]').text.replace(" ", "")),
                'year': int(year)
            }
            if len(car_specs) == 5:
                card_info['mileage'] = int(car_specs[4].text.rstrip(" км").replace(" ", ""))
            else:
                card_info['mileage'] = 0
            cards_info.append(card_info)
        return cards_info


if __name__ == "__main__":
    driver = webdriver.Chrome()
    page = DromPage(driver)
    page.open()
    print(page.get_cards())
    time.sleep(100)
