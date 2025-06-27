BROWSER_HEADLESS = True
CHROME_HEADLESS = False # В настоящий момент uc.Chrome не может работать в headless режиме для Ozone

RAW_DIRECTORY = '../data/raw_data/' # Директория для сырых данных 
CLEAR_DIRECTORY = '../data/clear_data/' # Директория для создания очищенного набора данных
GOODS_FILE = 'Goods.csv'
OTHER_CHARACTERISTICKS_FILE = 'Other_characteristicks.csv'
FEEDBACKS_FILE = 'Feedbacks.csv'

# Настройка сбора товаров с Wildberries
WB_PRODUCTS_FILE = 'wb_products.csv' # Файл для записи всех товаров с главной страницы
WB_CLEARED_PRODUCTS_FILE = 'wb_cleared_products.csv' # Содержит в себе товары после очистки, для них происходит остальной парсинг
WB_MAIN_DETAILS_FILE = 'wb_main_details.csv' # Файл, содержащий записи о товарах и их главных характеристиках
WB_OTHER_DETAILS_FILE = 'wb_specs_details.csv' # Файл содержащий все характеристики товаров
WB_GOODS_FILE = 'wb_merged_main_details.csv' # В этом файле объединяются WB_CLEARED_PRODUCTS_FILE и WB_MAIN_DETAILS_FILE
WB_FEEDBACKS_FILE = 'wb_feedbacks.csv' # Содержит отзывы на товары

WB_PAGES = 10_000 # Как много товаров собрать с главной страницы?


# Настройка сбора товаров с Ozon
OZON_PRODUCTS_FILE = 'ozon_products.csv'
OZON_CLEARED_PRODUCTS_FILE = 'ozon_cleared_products.csv'
OZON_MAIN_DETAILS_FILE = 'ozon_main_details.csv'
OZON_OTHER_DETAILS_FILE = 'ozon_specs_details.csv'
OZON_GOODS_FILE = 'ozon_merged_main_details.csv'
OZON_FEEDBACKS_FILE = 'ozon_feedbacks.csv'

OZON_PAGES = 10_000


# Настройка очистки товаров с главной страницы
PERCENT_FEEDBACKS = 50 # Какой топ товаров по отзывам брать? (%)

