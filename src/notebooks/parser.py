import requests
import pandas as pd 
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType 

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from threading import Lock
import os
from concurrent.futures import ThreadPoolExecutor

# class parser:
    
#     pass

def get_wb_products(query="электростимулятор", pages=3):
    all_products = []
    
    for page in range(1, pages + 1):
        url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        params = {
            "query": query,
            "resultset": "catalog",
            "limit": 100,
            "page": page,
            "appType": 1,
            "curr": "rub",
            "dest": -1257786  # Регион доставки: Москва
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Ошибка на странице {page}")
            continue
            
        data = response.json()
        products = data.get("data", {}).get("products", [])
        
        for product in products:
            all_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["salePriceU"] / 100,
                "rating": product.get("reviewRating", 0),
                "feedbacks": product.get("feedbacks", 0),
                "brand": product["brand"]
            })
        
        # Поправить задержку на моменте, когда API уже ничего не возвращает
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
        print(f"Страница {page} получена")
            
    return pd.DataFrame(all_products)

def init_driver_Chrome():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    stealth(driver, 
            platform="macOS",
            languages=["en-US", "en"],
            webgl_vendor="Intel Inc.")
    
    return driver


def init_driver_firefox(headless = False):
    firefox_options = Options()

    if headless:
        firefox_options.add_argument("--headless")
        firefox_options.set_preference("layout.css.devPixelsPerPx", "1")
        
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference("useAutomationExtension", False)
    firefox_options.set_preference("browser.cache.disk.enable", True)
    firefox_options.set_preference("browser.cache.memory.enable", True)
    firefox_options.set_preference("browser.cache.offline.enable", True)
    firefox_options.set_preference("network.http.use-cache", True)
    firefox_options.set_preference("permissions.default.image", 2)
    
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
    ]
    firefox_options.set_preference("general.useragent.override", random.choice(user_agents))
    
    firefox_options.set_preference("privacy.resistFingerprinting", True)
    firefox_options.set_preference("privacy.trackingprotection.enabled", True)
    firefox_options.set_preference("dom.event.clipboardevents.enabled", False)
    firefox_options.set_preference("media.volume_scale", "0.0")
    firefox_options.set_preference("gfx.webrender.all", True)
    firefox_options.set_preference("layers.acceleration.force-enabled", True)
    
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    
    driver.set_window_size(random.randint(1200, 1400), random.randint(800, 1000))
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("window.chrome = undefined;")
    
    return driver

def get_product_details(driver, product_id):
    driver.get(f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx")
    details = {
        "description": "",
        "specifications": {},
        "power_type": None,
        "zones": None,
        "type": None
    }
    
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "main__container"))
    )
    
    try:
        button_confirm_age = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/button[1]"))
        )
        button_confirm_age.click()
        print(f"{product_id} Подтверждение возраста выполнено")
    except Exception:
        print(f"{product_id} Кнопка подтверждения возраста не найдена")
    
    driver.execute_script("window.scrollBy(0, 800)")

    try:
        button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.product-page__btn-detail.hide-mobile.j-details-btn-desktop"))
        )
        driver.execute_script("arguments[0].click();", button)
        
        try:
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".product-params, .option__text"))
            )
            print(f"{product_id} Характеристики успешно открыты")
        except:
            print(f"{product_id} Характеристики не найдены")
        
        try:
            time.sleep(2)
            details["description"] = driver.find_element(By.CSS_SELECTOR, ".option__text").text
            print(f"{product_id} Описание успешно записано")
        except Exception:
            print(f"{product_id} Описание 1 не найдено")
            try:
                descriptions = driver.find_elements(By.CSS_SELECTOR, ".option__text--md")
                for description in descriptions:
                    details["description"] = details["description"] + description.text
                print(f"{product_id} Описание успешно записано")
            except Exception:
                print(f"{product_id} Описание 2 не найдено")
            
        # Парсинг характеристик
        try:
            tables = driver.find_elements(By.CSS_SELECTOR, "table.product-params__table")
            for table in tables:
                try:
                    group_name = table.find_element(By.CSS_SELECTOR, "caption.product-params__caption").text
                    details["specifications"][group_name] = {}
                    
                    rows = table.find_elements(By.CSS_SELECTOR, "tr.product-params__row")
                    for row in rows:
                        try:
                            name = row.find_element(By.CSS_SELECTOR, "th.product-params__cell").text.strip()
                            value = row.find_element(By.CSS_SELECTOR, "td.product-params__cell").text.strip()
                            details["specifications"][group_name][name] = value
                            
                            if any(word in name.lower() for word in ['питани', 'питание', 'электропитание']):
                                details["power_type"] = value
                            elif any(word in name.lower() for word in ['зон', 'област', 'воздейств']):
                                details["zones"] = value 
                            elif any(word in name.lower() for word in ['тип']):
                                details["type"] = value 
                        except Exception as e:
                            print(f"{product_id} Ошибка обработки строки: {str(e)}")
                            continue
                except:
                    continue
        except Exception as e:
            print(f"{product_id} Ошибка парсинга характеристик: {str(e)}")
            
    except Exception as e:
        print(f"{product_id} Ошибка открытия характеристик: {str(e)}")
    
    return details


def parse_product_data(product_data, product_id):
    """
    Преобразует сырые данные товара в два DataFrame:
    1. Основная информация (main_info)
    2. Характеристики (specifications)
    """
    main_info = pd.DataFrame({
        'id': [product_id],
        'power_type': [product_data['power_type']],
        'zones': [product_data['zones']],
        'type': [product_data['type']],
        'description': [product_data['description']]
    })
    
    specs_list = []
    for group_name, group_items in product_data['specifications'].items():
        for name, value in group_items.items():
            specs_list.append({
                'good_id': product_id,
                'group_name': group_name,
                'name': name,
                'value': value
            })
    
    specifications = pd.DataFrame(specs_list)
    
    return main_info, specifications

def get_product_feedbacks(driver, product_id):
    driver.get(f"https://www.wildberries.ru/catalog/{product_id}/feedbacks")

    # Ожидание загрузки основного контейнера с отзывами
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "comments__list, .non-comments"))
    )
    
    try:
        no_feedback = driver.find_element(By.CLASS_NAME, ".non-comments")
        print(f"{product_id} - нет отзывов")
        return pd.DataFrame(columns=['product_id', 'rating', 'advantage', 'disadvantage', 'comment'])
    except:
        pass

    # Проверка и переключение на вкладку "Этот вариант" если доступна
    try:
        # Ожидаем появления переключателя вариантов
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-feedbacks__tabs"))
        )
        
        # Ищем кнопку "Этот вариант"
        variant_button = driver.find_element(
            By.CSS_SELECTOR, "li.product-feedbacks__tab:nth-child(2) > button:nth-child(1)"
        )
        variant_button.click()
        time.sleep(1.5)
    except:
        # Если нет переключателя или кнопки, продолжаем как обычно
        print(f"{product_id} - не удалось найти кнопку \"Этот вариант\"")
        pass

    # Прокрутка страницы для загрузки ВСЕХ отзывов
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 100 # Максимум попыток прокрутки для защиты от бесконечного цикла

    while scroll_attempts < max_scroll_attempts:
        # Прокрутка вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)  # Ожидание подгрузки контента
        
        # Проверка изменения высоты страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1

    # Сбор всех отзывов
    feedback_items = driver.find_elements(By.CSS_SELECTOR, "li.comments__item.feedback")
    feedbacks_list = []

    for item in feedback_items:
        try:
            # Парсинг рейтинга
            rating_elem = item.find_element(By.CLASS_NAME, "feedback__rating")
            rating_class = rating_elem.get_attribute("class")
            rating = int(re.search(r'star(\d+)', rating_class).group(1))
        except:
            rating = None

        advantage = None
        disadvantage = None
        comment = None
        
        # Парсинг текста отзыва
        try:
            text_block = item.find_element(By.CSS_SELECTOR, ".feedback__text.j-feedback__text")
            
            # Обработка структурированных отзывов (с разделами)
            sections = text_block.find_elements(By.CLASS_NAME, "feedback__text--item")
            if sections:
                for section in sections:
                    text = section.text.strip()
                    if not text:
                        continue
                        
                    if "feedback__text--item-pro" in section.get_attribute("class"):
                        advantage = text
                    elif "feedback__text--item-con" in section.get_attribute("class"):
                        disadvantage = text
                    else:
                        comment = text
            # Обработка неструктурированных отзывов
            else:
                comment = text_block.text.strip()
        except:
            pass  # Если текста нет, оставляем поля пустыми

        feedbacks_list.append({
            'product_id': product_id,
            'rating': rating,
            'advantage': advantage,
            'disadvantage': disadvantage,
            'comment': comment
        })

    feedbacks = pd.DataFrame(feedbacks_list)
    print(f"{product_id} Отзывы успешно собраны. Количество отзывов: {len(feedbacks)}")
    return feedbacks