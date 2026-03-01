import asyncio
import json
import re

# порядок сезонов внутри года
SEASON_ORDER = {"winter": 1, "spring": 2, "summer": 3, "fall": 4}


def parse_season_key(s: str):
    """
    'fall_2023' -> (2023, 4).
    Невалидные строки отправляем в конец.
    """
    m = re.fullmatch(r"(winter|spring|summer|fall)_(\d{4})", s)
    if not m:
        return 10**9, 9
    name, year = m.group(1), int(m.group(2))
    return year, SEASON_ORDER[name]


async def fetch_all_seasons(client, limit: int = 50, max_pages: int = 1000):
    """
    Идём по страницам GraphQL-запроса animes и вытаскиваем поле season.
    limit по доке максимум 50. Останавливаемся, когда пришла пустая страница
    или вернулось меньше limit.
    """
    seen = set()
    page = 1
    while page <= max_pages:
        # В fields достаточно указать нужные поля Selection Set'а.
        resp = await client.graphql.animes(
            fields="{ season }",
            page=page,
            limit=limit,
            kind="!special",  # исключим спешлы, чтобы меньше мусора
        )
        data = resp.get("data") or {}
        batch = data.get("animes") or []
        if not batch:
            break

        for item in batch:
            s = item.get("season")
            if s:
                seen.add(s)

        if len(batch) < limit:
            break
        await asyncio.sleep(1)
        page += 1

    return sorted(seen, key=parse_season_key)


import config_data.config as cfg


async def main():
    seasons = await fetch_all_seasons(cfg.SHIKI_CLIENT, limit=50, max_pages=400)
    with open("seasons.json", "w", encoding="utf-8") as f:
        json.dump(seasons, f, ensure_ascii=False, indent=2)
    print(f"Сезоны сохранены в seasons.json (всего: {len(seasons)})")


if __name__ == "__main__":
    asyncio.run(main())
