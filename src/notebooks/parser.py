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

from config_parser import *


import logging
logging.basicConfig(level=logging.INFO, filename="parser.log", filemode="w",
                format="%(asctime)s %(levelname)s %(message)s")

from dotenv import load_dotenv
load_dotenv()
token = os.getenv('GH_TOKEN')

import undetected_chromedriver as uc 
from selenium.webdriver.common.keys import Keys

class Parser:
    def __init__(self):
        self.driver = None
    
    def _init_driver(self, browser="firefox"):
        if browser == "firefox":
            self.driver = self._init_driver_firefox(BROWSER_HEADLESS)
        elif browser == "chrome":
            self.driver = self._init_driver_chrome()
        elif browser == "undetected_chrome":
            self.driver = self._init_driver_undetected_chrome(CHROME_HEADLESS)
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
    def _init_driver_firefox(self, headless = False):
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
        firefox_options.set_preference("intl.accept_languages", "ru")
        firefox_options.set_preference("browser.shell.checkDefaultBrowser", False)
        firefox_options.set_preference("dom.disable_beforeunload", True)
        firefox_options.set_preference("browser.tabs.warnOnClose", False)

        firefox_options.set_preference("dom.disable_open_during_load", True)
        firefox_options.set_preference("alerts.showFadeIn", False)
        firefox_options.set_preference("alerts.slideIncrement", 0)
        firefox_options.set_preference("alerts.slideIncrementTime", 0)
        
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        driver.set_window_size(random.randint(1200, 1400), random.randint(800, 1000))
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("window.chrome = undefined;")

        try:
            driver.get(f"https://www.wildberries.ru")
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.dismiss()
        except:
            logging.info("Диалоговое окно смены языка не найдено")
            pass
        
        return driver
    
    def _init_driver_chrome(self):
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
    
    def _init_driver_undetected_chrome(self, headless = False):
        options = uc.ChromeOptions()
        # Отключаем загрузку изображений и CSS (если они не нужны)
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Блокировка картинок
            "profile.managed_default_content_settings.javascript": 1,  # JS включен (иначе Ozon не работает)
            "profile.managed_default_content_settings.stylesheets": 2,  # Блокировка CSS (опционально)
            "profile.default_content_setting_values.notifications": 2,  # Блокировка уведомлений
        }
        options.add_experimental_option("prefs", prefs)
        driver = uc.Chrome(
            options=options,
            headless=headless, 
            use_subprocess=True)
        # driver.implicitly_wait(5)
        return driver

    def restart_driver(self):
        if self.driver:
            self.driver.quit()
        self._init_driver()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.safe_close()

    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logging.warning(f"Error closing driver: {e}")
    
    def safe_close(self):
        self.__del__()

    @staticmethod
    def _scroll_page_down(driver):
        # Прокрутка страницы для загрузки ВСЕХ отзывов
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10 # Максимум попыток прокрутки для защиты от бесконечного цикла

        while scroll_attempts < max_scroll_attempts:
            prev_count = 0
            new_items = len(driver.find_elements(By.CSS_SELECTOR, "li.comments__item"))
            if new_items > prev_count:
                prev_count = new_items
                scroll_attempts = 0  # Сброс при нахождении новых
            else:
                scroll_attempts += 1
                logging.info("Не получилось прокрутить страницу")
            # Прокрутка вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # Ожидание подгрузки контента
            
            # Проверка изменения высоты страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    @staticmethod
    def _scroll_page_mid(driver):
        # Прокрутка страницы для загрузки ВСЕХ отзывов
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10 # Максимум попыток прокрутки для защиты от бесконечного цикла

        while scroll_attempts < max_scroll_attempts:
            prev_count = 0
            new_items = len(driver.find_elements(By.CSS_SELECTOR, "div.tile-root"))
            if new_items > prev_count:
                prev_count = new_items
                scroll_attempts = 0  # Сброс при нахождении новых
            else:
                scroll_attempts += 1
                logging.info("Не получилось прокрутить страницу")
            # Прокрутка вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5);")
            time.sleep(3)  # Ожидание подгрузки контента
            
            # Проверка изменения высоты страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    @staticmethod
    def _page_down_slowly(driver):
        # Прокрутка страницы для загрузки ВСЕХ отзывов
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 100 # Максимум попыток прокрутки для защиты от бесконечного цикла

        while scroll_attempts < max_scroll_attempts:
            prev_count = 0
            new_items = len(driver.find_elements(By.CSS_SELECTOR, "div.tile-root"))
            if new_items > prev_count:
                prev_count = new_items
                scroll_attempts = 0  # Сброс при нахождении новых
            else:
                scroll_attempts += 1
                logging.info("Не получилось прокрутить страницу")
            # Прокрутка вниз
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script('''
                                const scrollStep = 200; // Размер шага прокрутки (в пикселях)
                                const scrollInterval = 100; // Интервал между шагами (в миллисекундах)

                                const scrollHeight = document.documentElement.scrollHeight;
                                let currentPosition = 0;
                                const interval = setInterval(() => {
                                    window.scrollBy(0, scrollStep);
                                    currentPosition += scrollStep;

                                    if (currentPosition >= scrollHeight) {
                                        clearInterval(interval);
                                    }
                                }, scrollInterval);
                            ''')
            time.sleep(2)  # Ожидание подгрузки контента
            
            # Проверка изменения высоты страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    @staticmethod
    def _page_down_slowly_2(driver):
        # Прокрутка страницы для загрузки ВСЕХ карточек товаров
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 30  # Уменьшено для оптимизации
        prev_count = 0
        stability_counter = 0
        required_stability = 3  # Требуемое количество стабильных проверок
        
        while scroll_attempts < max_scroll_attempts and stability_counter < required_stability:
            # Прокрутка плавным скриптом
            driver.execute_script('''
                window.scrollBy({
                    top: 800,
                    behavior: 'smooth'
                });
            ''')
            
            # Динамическое ожидание вместо фиксированного
            time.sleep(3 + random.uniform(0.2, 0.5))  # Случайная задержка
            
            # Обновляем высоту страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # Проверяем появление новых карточек
            current_items = driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
            current_count = len(current_items)
            
            if current_count > prev_count:
                # Нашли новые элементы - сбрасываем счетчики
                prev_count = current_count
                stability_counter = 0
                scroll_attempts = 0
            elif new_height == last_height:
                # Высота не изменилась - увеличиваем счетчик стабильности
                stability_counter += 1
            else:
                # Высота изменилась, но новых карточек нет
                last_height = new_height
                stability_counter = 0
            
            scroll_attempts += 1
            
            # Ранний выход если достигли конца
            current_position = driver.execute_script("return window.pageYOffset + window.innerHeight")
            if current_position >= new_height:
                break

        logging.info(f"Завершение прокрутки. Найдено элементов: {prev_count}, Попыток: {scroll_attempts}")

class WB_Parser(Parser):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_wb_products(query="электростимулятор", pages=3) -> pd.DataFrame:
        all_products = []
        for page in range(1, pages + 1):
            try:
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
                response.raise_for_status()

                data = response.json()
                products = data.get("data", {}).get("products", [])
                if not products:
                    logging.info(f"Нет товаров на странице {page}. Прекращаем парсинг.")
                    break

                for product in products:
                    all_products.append({
                        "id": product["id"],
                        "name": product["name"],
                        "price": product["salePriceU"] / 100,
                        "rating": product.get("reviewRating", 0),
                        "feedbacks": product.get("feedbacks", 0),
                        "brand": product["brand"]
                    })
                
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
                logging.debug(f"Страница {page} получена")
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка при запросе страницы {page}: {e}")
                continue
                
        return pd.DataFrame(all_products)
    
    # Сделать так, чтобы он возвращал один df со всеми характеристиками, делить на main и other_specs нужно потом
    def get_product_details(self, product_id, driver=None) -> dict: 
        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="firefox")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver

        details = {
                "id" : product_id,
                "description": "",
                "specifications": {},
        }
        try:
            driver.get(f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx")
            
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "main__container"))
            )
            
            try:
                button_confirm_age = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/button[1]"))
                )
                button_confirm_age.click()
                logging.debug(f"{product_id} Подтверждение возраста выполнено")
            except Exception:
                logging.info(f"{product_id} Кнопка подтверждения возраста не найдена")
            
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
                    logging.debug(f"{product_id} Характеристики успешно открыты")
                except:
                    logging.warning(f"{product_id} Характеристики не найдены")
                
                try:
                    time.sleep(2)
                    details["description"] = driver.find_element(By.CSS_SELECTOR, ".option__text").text
                    logging.debug(f"{product_id} Описание успешно записано")
                except Exception:
                    logging.debug(f"{product_id} Описание 1 не найдено")
                    try:
                        descriptions = driver.find_elements(By.CSS_SELECTOR, ".option__text--md")
                        for description in descriptions:
                            details["description"] = details["description"] + description.text
                        logging.debug(f"{product_id} Описание успешно записано")
                    except Exception:
                        logging.warning(f"{product_id} Описание 2 не найдено")
                    
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
                                except Exception as e:
                                    logging.error(f"{product_id} Ошибка обработки строки: {str(e)}")
                                    continue
                        except:
                            continue
                except Exception as e:
                    logging.error(f"{product_id} Ошибка парсинга характеристик: {str(e)}")
            except Exception as e:
                logging.error(f"{product_id} Ошибка открытия характеристик: {str(e)}")
        except Exception as e:
            logging.error(f"Ошибка при парсинге товара {product_id}: {str(e)}")
        return details
    
    def get_product_feedbacks(self, product_id, driver = None) -> pd.DataFrame:
        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="firefox")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver

        feedbacks = pd.DataFrame(columns=['product_id', 'rating', 'advantage', 'disadvantage', 'comment'])
        try:
            driver.get(f"https://www.wildberries.ru/catalog/{product_id}/feedbacks")

            # Ожидание загрузки основного контейнера с отзывами
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "comments__list, .non-comments"))
            )
            
            try:
                driver.find_element(By.CLASS_NAME, ".non-comments")
                logging.info(f"{product_id} - нет отзывов")
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
                logging.info(f"{product_id} - не удалось найти кнопку \"Этот вариант\"")
                pass

            # Прокрутка страницы для загрузки ВСЕХ отзывов
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10 # Максимум попыток прокрутки для защиты от бесконечного цикла

            while scroll_attempts < max_scroll_attempts:
                prev_count = 0
                new_items = len(driver.find_elements(By.CSS_SELECTOR, "li.comments__item"))
                if new_items > prev_count:
                    prev_count = new_items
                    scroll_attempts = 0  # Сброс при нахождении новых
                else:
                    scroll_attempts += 1
                # Прокрутка вниз
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)  # Ожидание подгрузки контента
                
                # Проверка изменения высоты страницы
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Сбор всех отзывов
            feedback_items = driver.find_elements(By.CSS_SELECTOR, "li.comments__item.feedback")
            feedbacks_list = []

            for item in feedback_items:
                try:
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
            logging.info(f"{product_id} Отзывы успешно собраны. Количество отзывов: {len(feedbacks)}")
        except Exception as e:
            logging.error(f"Ошибка при парсинге отзывов товара {product_id}: {str(e)}")
            
        return feedbacks

    def __del__(self):
        return super().__del__()
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)
    
class Ozon_Parser(Parser):
    def __init__(self):
        super().__init__()
    
    def get_products_links(self, query="миостимулятор", driver=None, max_products=200):
        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="undetected_chrome")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver
        
        try:
            self.driver.get(url='https://ozon.ru')
            time.sleep(2)
    
            find_input = driver.find_element(By.NAME, 'text')
            find_input.clear()
            find_input.send_keys(query)
            time.sleep(2)
            find_input.send_keys(Keys.ENTER)
            time.sleep(2)
            
            logging.info("Начало прокрутки страницы")
            # self._page_down_slowly_2(driver)
            seen_links = set()
            products_data = []
            scroll_attempts = 0
            max_attempts = 10
            while scroll_attempts < max_attempts and len(products_data) < max_products:
                driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
                time.sleep(1.5)
                current_cards = driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
                new_items = 0

                for card in current_cards:
                    try:
                        link_elem = card.find_element(By.CSS_SELECTOR, "a.tile-clickable-element[href*='/product/']")
                        link = link_elem.get_attribute("href")
                        
                        if link not in seen_links:
                            seen_links.add(link)
                            title = card.find_element(By.CSS_SELECTOR, "span.tsBody500Medium").text

                            # Цена (актуальная)
                            try:
                                price_elem = card.find_element(By.CSS_SELECTOR, "span.tsHeadline500Medium")
                                price = price_elem.text
                            except:
                                # Если нет скидки, ищем обычную цену
                                price_elem = card.find_element(By.CSS_SELECTOR, "span[class*='tsHeadline']")
                                price = price_elem.text
                            
                            try:
                                bottom_elem = WebDriverWait(card, 0.5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.tsBodyMBold"))
                                )
                                rating = bottom_elem.text[:3]
                                reviews = re.sub(r'[^\d]', '', bottom_elem.text[3:])
                            except:
                                logging.info(f"Отзывы и рейтинг не найдены для товара: {title}")
                                rating = 0
                                reviews = 0

                            products_data.append({
                                "link": link,
                                "title": title,
                                "price": price,
                                "rating": rating,
                                "reviews": reviews
                            })
                            new_items += 1
                    except Exception as e:
                        logging.debug(f"Пропуск карточки: {str(e)}")
                        continue
                    
                if new_items == 0:
                    scroll_attempts += 1
                    logging.info(f"Новых товаров нет ({scroll_attempts}/{max_attempts})")
                else:
                    scroll_attempts = 0  # Сброс счетчика
                    logging.info(f"Найдено новых: {new_items} | Всего: {len(products_data)}")
                
                # Выход при достижении лимита
                if len(products_data) >= max_products:
                    break
            logging.info("Конец прокрутки страницы")
            logging.info(f"Завершено. Собрано товаров: {len(products_data)}")
            return pd.DataFrame(products_data)
            # time.sleep(2)
            # product_cards = driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
            
            # for card in product_cards:
            #     try:
            #         # Ссылка на товар
            #         # link_elem = card.find_element(By.CSS_SELECTOR, "a.tile-clickable-element")
            #         link_elem = card.find_element(By.CSS_SELECTOR, "a.tile-clickable-element[href*='/product/']")
            #         link = link_elem.get_attribute("href")
                    
            #         # Название товара
            #         title_elem = card.find_element(By.CSS_SELECTOR, "span.tsBody500Medium")
            #         title = title_elem.text
                    
            #         # Цена (актуальная)
            #         try:
            #             price_elem = card.find_element(By.CSS_SELECTOR, "span.tsHeadline500Medium")
            #             price = price_elem.text
            #         except:
            #             # Если нет скидки, ищем обычную цену
            #             price_elem = card.find_element(By.CSS_SELECTOR, "span[class*='tsHeadline']")
            #             price = price_elem.text
                    

            #         try:
            #             bottom_elem = WebDriverWait(card, 0.5).until(
            #                 EC.presence_of_element_located((By.CSS_SELECTOR, "div.tsBodyMBold"))
            #             )
            #             rating = bottom_elem.text[:3]
            #             reviews = re.sub(r'[^\d]', '', bottom_elem.text[3:])
            #         except:
            #             logging.info(f"Отзывы и рейтинг не найдены для товара: {title}")
            #             rating = 0
            #             reviews = 0
                    
            #         products_data.append({
            #             "link": link,
            #             "title": title,
            #             # "price": price,
            #             # "rating": rating,
            #             # "reviews": reviews
            #         })
            #         logging.info(f"Завершен парсинг товара: {title}")
                    
            #     except Exception as e:
            #         logging.warning(f"Ошибка при парсинге карточки товара: {str(e)}")
            #         continue

            # logging.info(f'[+] Собрано данных о {len(products_data)} товарах!')
            # return pd.DataFrame(products_data)

        except Exception as e:
            logging.error(f"Произошла ошибка при получении товаров с Ozon: {e}")

    def __del__(self):
        return super().__del__()
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)

def parse_product_data(product_data):
    """
    Преобразует сырые данные товара в два DataFrame:
    1. Основная информация (main_info)
    2. Характеристики (specifications)
    """
    product_id = product_data['id']
    description = product_data['description']
    details = {
        "id" : product_id,
        "description": description,
        "power_type": None,
        "zones": None,
        "type": None
    }
    specs_mapping = {
        'power_type': ['питани', 'питание', 'электропитание'],
        'zones': ['зон', 'област', 'воздейств'],
        'type': ['тип']
    }
    
    specs_list = []
    for group_name, group_items in product_data['specifications'].items():
        for name, value in group_items.items():
            specs_list.append({
                'good_id': product_id,
                'group_name': group_name,
                'name': name,
                'value': value
            })
            for key, keywords in specs_mapping.items():
                if any(kw in name.lower() for kw in keywords):
                    details[key] = value
    

    main_info = pd.DataFrame({
        'id': [product_id],
        'power_type': [details['power_type']],
        'zones': [details['zones']],
        'type': [details['type']],
        'description': [details['description']]
    })
    specifications = pd.DataFrame(specs_list)
    
    return main_info, specifications
