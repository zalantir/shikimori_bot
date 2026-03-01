from datetime import date


def what_seasons() -> str:
    """Определяет текущий и предыдущий сезоны для запроса Shikimori.
    Возвращает строку формата "season_year,season_year", например: "summer_2025,fall_2025
    """
    today = date.today()
    cur_year, month = today.year, today.month

    if 1 <= month <= 3:  # Январь–март → зима
        cur_season = "winter"
    elif 4 <= month <= 6:  # Апрель–июнь → весна
        cur_season = "spring"
    elif 7 <= month <= 9:  # Июль–сентябрь → лето
        cur_season = "summer"
    else:  # Октябрь–декабрь → осень
        cur_season = "fall"

    # предыдущий сезон
    seasons = ["winter", "spring", "summer", "fall"]
    i = seasons.index(cur_season)
    prev_season = seasons[i - 1]
    prev_season_year = cur_year - 1 if cur_season == "winter" else cur_year

    return f"{prev_season}_{prev_season_year},{cur_season}_{cur_year}"
