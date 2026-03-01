from datetime import date
from typing import List, Tuple

seasons_order = ["winter", "spring", "summer", "fall"]
ru_season_name = {
    "winter": "Зима",
    "spring": "Весна",
    "summer": "Лето",
    "fall": "Осень",
}


def _current_season(today: date) -> tuple[str, int]:
    """Вернёт (сезон, год) по дате. Сезоны: зима(12–2), весна(3–5), лето(6–8), осень(9–11)."""
    year, month = today.year, today.month
    if month in (12, 1, 2):
        return "winter", year
    if month in (3, 4, 5):
        return "spring", year
    if month in (6, 7, 8):
        return "summer", year
    return "fall", year  # 9–11


def _shift_season(season: str, year: int, step: int) -> tuple[str, int]:
    """Сдвиг сезона на step (±1, ±2) с учётом смены года."""
    idx = seasons_order.index(season) + step
    year_shift, idx_in_year = divmod(idx, 4)
    return seasons_order[idx_in_year], year + year_shift


def _build_four_seasons(today: date) -> list[tuple[str, int]]:
    """Ровно 4 сезона: следующий, текущий, предыдущий, предыдущий-2."""
    cur_season, cur_year = _current_season(today)
    next1 = _shift_season(cur_season, cur_year, +1)
    prev1 = _shift_season(cur_season, cur_year, -1)
    prev2 = _shift_season(cur_season, cur_year, -2)
    return [next1, (cur_season, cur_year), prev1, prev2]


def _pick_anchor_year(four_seasons: list[tuple[str, int]]) -> int:
    """Год с максимальным числом сезонов; при равенстве — меньший год."""
    count_by_year: dict[int, int] = {}
    for _, y in four_seasons:
        count_by_year[y] = count_by_year.get(y, 0) + 1
    max_count = max(count_by_year.values())
    return min(y for y, c in count_by_year.items() if c == max_count)


def _season_label_ru(season: str, year: int) -> str:
    return f"{ru_season_name[season]} {year}"


def _decade_label_ru(start_year: int) -> str:
    return f"{start_year}-е годы"


def build_time_filters(
    today: date | None = None,
    bottom_decade_start: int = 1980,
) -> List[Tuple[str, str]]:
    """
    Возвращает список (gql_value, label_ru) в порядке:
      1) 4 сезона (следующий, текущий, предыдущий, предыдущий-2)
      2) якорный год, год-1
      3) двухлетний блок [Y-3..Y-2]
      4) переходный блок через десятилетие [L..U], где U=Y-4, L=max(D-3, D-10)
      5) добивка предыдущего десятилетия [D-10..L-1]
      6) десятилетия назад до bottom_decade_start (включая его): 200x, 199x, 198x
      7) «Более старые»: 0_(bottom_decade_start-1)
    """
    if today is None:
        today = date.today()

    items: list[tuple[str, str]] = []

    # 1) четыре сезона
    four = _build_four_seasons(today)
    for s, y in four:
        items.append((f"{s}_{y}", _season_label_ru(s, y)))

    # 2) якорный год и предыдущий
    anchor_year = _pick_anchor_year(four)
    items.append((f"{anchor_year}", f"{anchor_year} год"))
    items.append((f"{anchor_year - 1}", f"{anchor_year - 1} год"))

    # 3) блок [Y-3..Y-2]
    items.append(
        (f"{anchor_year - 3}_{anchor_year - 2}", f"{anchor_year - 3}–{anchor_year - 2}")
    )

    # 4) переходный блок через десятилетие
    decade_start = (anchor_year // 10) * 10  # начало текущего десятилетия
    prev_decade_start = decade_start - 10
    upper_bound = anchor_year - 4
    lower_bound = max(decade_start - 3, prev_decade_start)
    if lower_bound <= upper_bound:
        items.append((f"{lower_bound}_{upper_bound}", f"{lower_bound}–{upper_bound}"))

    # 5) добивка предыдущего десятилетия
    if prev_decade_start <= lower_bound - 1:
        items.append(
            (
                f"{prev_decade_start}_{lower_bound - 1}",
                f"{prev_decade_start}–{lower_bound - 1}",
            )
        )

    # 6) десятилетия назад до bottom_decade_start
    # для GraphQL используем маски '200x', '199x', '198x'
    for decade in range(prev_decade_start - 10, bottom_decade_start - 10, -10):
        mask = f"{str(decade)[:3]}x"
        items.append((mask, _decade_label_ru(decade)))
        if decade == bottom_decade_start:
            break

    # 7) более старые
    items.append((f"0_{bottom_decade_start - 1}", "Более старые"))

    return items


# пример
if __name__ == "__main__":
    filters = build_time_filters(today=date.today())
    print(filters)
