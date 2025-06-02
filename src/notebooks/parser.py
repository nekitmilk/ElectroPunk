import requests
import pandas as pd 
import time
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

# Инициализация драйвера один раз (вне функции)
def init_driver_Chrome():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Для автоматического определения архитектуры M1
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
        firefox_options.set_preference("layout.css.devPixelsPerPx", "1")  # Фиксируем масштаб
        
    # Настройки для ускорения и stealth
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference("useAutomationExtension", False)
    firefox_options.set_preference("browser.cache.disk.enable", True)
    firefox_options.set_preference("browser.cache.memory.enable", True)
    firefox_options.set_preference("browser.cache.offline.enable", True)
    firefox_options.set_preference("network.http.use-cache", True)
    firefox_options.set_preference("permissions.default.image", 2)  # Блокировка изображений
    
    # Случайный User-Agent из реальных браузеров
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
    ]
    firefox_options.set_preference("general.useragent.override", random.choice(user_agents))
    
    # Дополнительные настройки для незаметности
    firefox_options.set_preference("privacy.resistFingerprinting", True)
    firefox_options.set_preference("privacy.trackingprotection.enabled", True)
    firefox_options.set_preference("dom.event.clipboardevents.enabled", False)
    firefox_options.set_preference("media.volume_scale", "0.0")
    
    # Настройки для производительности
    firefox_options.set_preference("gfx.webrender.all", True)
    firefox_options.set_preference("layers.acceleration.force-enabled", True)
    
    # Создаем сервис и драйвер
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    
    # Устанавливаем размер окна как у реального пользователя
    driver.set_window_size(random.randint(1200, 1400), random.randint(800, 1000))
    
    # Эмулируем человеческое поведение
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("window.chrome = undefined;")
    
    return driver

# Передаём драйвер как аргумент
def get_product_details(driver, product_id):
    driver.get(f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx")
    details = {
        "description": "",
        "specifications": {},  # Словарь для всех характеристик
        "power_type": None,
        "zones": None
    }
    
    # Умное ожидание вместо фиксированного sleep
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "main__container"))
    )
    
    # Проверка и клик по кнопке подтверждения возраста
    try:
        button_confirm_age = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/button[1]"))
        )
        button_confirm_age.click()
        print("Подтверждение возраста выполнено")
    except Exception:
        print("Кнопка подтверждения возраста не найдена")
    
    # Прокрутка с ожиданием
    driver.execute_script("window.scrollBy(0, 800)")

    # Нажатие на характеристики с улучшенным ожиданием
    try:
        button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.product-page__btn-detail.hide-mobile.j-details-btn-desktop"))
        )
        driver.execute_script("arguments[0].click();", button)
        
        # Ожидание загрузки контента характеристик
        try:
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".product-params, .option__text"))
            )
            print("Характеристики успешно открыты")
        except:
            print("Характеристики не найдены")
        
        # Сбор данных
        try:
            time.sleep(2)
            details["description"] = driver.find_element(By.CSS_SELECTOR, ".option__text").text
            print("Описание успешно записано")
        except Exception:
            print("Описание 1 не найдено")
            try:
                descriptions = driver.find_elements(By.CSS_SELECTOR, ".option__text--md")
                for description in descriptions:
                    details["description"] = details["description"] + description.text
                print("Описание успешно записано")
            except Exception:
                print("Описание 2 не найдено")
            
        # Парсинг характеристик
        try:
            # Находим все таблицы с характеристиками
            tables = driver.find_elements(By.CSS_SELECTOR, "table.product-params__table")
            for table in tables:
                # Извлекаем название группы характеристик
                try:
                    group_name = table.find_element(By.CSS_SELECTOR, "caption.product-params__caption").text

                    # Создаем подраздел для этой группы
                    details["specifications"][group_name] = {}
                    
                    # Обрабатываем строки таблицы
                    rows = table.find_elements(By.CSS_SELECTOR, "tr.product-params__row")
                    for row in rows:
                        try:
                            name = row.find_element(By.CSS_SELECTOR, "th.product-params__cell").text.strip()
                            value = row.find_element(By.CSS_SELECTOR, "td.product-params__cell").text.strip()
                            
                            # Сохраняем характеристику в соответствующей группе
                            details["specifications"][group_name][name] = value
                            
                            # Для совместимости сохраняем особые поля
                            if any(word in name.lower() for word in ['питани', 'питание', 'электропитание']):
                                details["power_type"] = value
                            elif any(word in name.lower() for word in ['зон', 'област', 'воздейств']):
                                details["zones"] = value
                            
                                
                        except Exception as e:
                            print(f"Ошибка обработки строки: {str(e)}")
                            continue
                except:
                    continue
                        
        except Exception as e:
            print(f"Ошибка парсинга характеристик: {str(e)}")
            
    except Exception as e:
        print(f"Ошибка открытия характеристик: {str(e)}")
    
    return details


def parse_product_data(product_data, product_id):
    """
    Преобразует сырые данные товара в два DataFrame:
    1. Основная информация (main_info)
    2. Характеристики (specifications)
    """
    # Создаем первый DataFrame с основной информацией
    main_info = pd.DataFrame({
        'id': [product_id],
        'power_type': [product_data['power_type']],
        'zones': [product_data['zones']],
        'description': [product_data['description']]
    })
    
    # Создаем второй DataFrame с характеристиками
    specs_list = []
    for group_name, group_items in product_data['specifications'].items():
        for name, value in group_items.items():
            specs_list.append({
                'good_id': product_id,  # foreign key (дублирует id)
                'group_name': group_name,
                'name': name,
                'value': value
            })
    
    specifications = pd.DataFrame(specs_list)
    
    return main_info, specifications
