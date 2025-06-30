import re 
import pandas as pd

# Фильтрация нерелевантных товаров
def is_relevant(name):
    # Первичный фильтр 
    exclude_patterns = [
        r"электрод", r"шнур", r"кабель", r"провод", 
        r"пластин", r"гель",
        r"крепеж", r"держатель", r"запчасть",
        r"аксессуар", r"led", #r"подставка",
        r"основание"
    ]
    if pd.isna(name):
        return False
    name = name.lower()
    if any(re.search(pattern, name) for pattern in exclude_patterns):
        return False
   
    # return any(re.search(kw, name) for kw in include_keywords)
    return True

def cleaner_products(dirty_df, percent_feedbacks=20, id_col="id"):
    mask = dirty_df['name'].apply(is_relevant)
    clear_df = dirty_df[mask].copy()

    # 1. Удалить товары без отзывов
    clear_df = clear_df[clear_df['feedbacks'] > 0]

    # 2. Рассчитать пороги для ценовых сегментов
    price_25 = clear_df['price'].quantile(0.25)
    price_75 = clear_df['price'].quantile(0.75)
    feedback_median = clear_df['feedbacks'].median()

    # 3. Отобрать топ-20% по отзывам?
    percentil = 1 - percent_feedbacks/100
    top_20_percent = clear_df[clear_df['feedbacks'] >= clear_df['feedbacks'].quantile(percentil)]

    # 4. Сбалансированные выборки по ценовым сегментам
    low_price = clear_df[clear_df['price'] < price_25].nlargest(30, 'feedbacks')
    mid_price = clear_df[(clear_df['price'] >= price_25) & (clear_df['price'] <= price_75)].nlargest(30, 'feedbacks')
    high_price = clear_df[clear_df['price'] > price_75].nlargest(30, 'feedbacks')

    # 5. Недооцененные товары с высоким рейтингом
    undervalued = clear_df[
        (clear_df['rating'] >= 4.8) & 
        (clear_df['price'] < clear_df['price'].median()) & 
        (clear_df['feedbacks'] < feedback_median)
    ].nlargest(20, 'rating')

    # Объединить все отобранные товары
    final_ids = pd.concat([
        top_20_percent,
        low_price,
        mid_price,
        high_price,
        undervalued
    ])[id_col].drop_duplicates()

    clear_df = dirty_df[dirty_df[id_col].isin(final_ids)]

    return clear_df