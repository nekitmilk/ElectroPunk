import requests
import pandas as pd 
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType 

# Инициализация драйвера один раз (вне функции)
def init_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Для автоматического определения архитектуры M1
    service = Service(ChromeDriverManager().install())
    
    return webdriver.Chrome(service=service, options=chrome_options)


# Передаём драйвер как аргумент
def get_product_details(driver, product_id):
    
    driver.get(f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx")
    details = {"description": "", "power_type": "", "zones": ""}
    time.sleep(40)  # Ожидаем загрузки
    
    try:
        button_confirm_age = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/button[1]")
        button_confirm_age.click()
        time.sleep(3)
        driver.execute_script("window.scrollBy(0, 800)")
        time.sleep(20)

        # Нажатие на Характеристики
        button_characteristics_and_description = driver.find_element(By.CSS_SELECTOR, "button.product-page__btn-detail.hide-mobile.j-details-btn-desktop")
        button_characteristics_and_description.click()
        time.sleep(10)

        # Описание товара
        details["description"] = driver.find_element(By.CLASS_NAME, "option__text").text

    except Exception as e:
        print(f"Ошибка для {product_id}: {str(e)}")
    
    return details

driver = init_driver()
product_id = 192582931
details = get_product_details(driver, product_id)
print(details)
driver.quit()