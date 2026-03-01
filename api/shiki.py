from shikimori.enums import OrderEnum
import asyncio
import config_data.config as cfg
from api.utils.seasons_clock import what_seasons
from utils.misc.stochastic_random import build_final_5_slots, EPOCHS


async def search_by_title(
    query: str, limit: int = 50, quality: bool = False
) -> list[dict]:
    """Ищет аниме по названию через GraphQL API Shikimori.

    :param query: Поисковый запрос (название аниме или ключевые слова).
    :param limit: Максимальное число результатов (по умолчанию 50).
    :param quality: Если True – загружать постеры в высоком качестве (оригинал), иначе стандартное.
    :return: Список словарей с информацией об аниме (поля: id, name, russian, score, статус и др.).
    """
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """

    anime_list = await client.graphql.animes(
        fields=fields, search=query, limit=limit, censored=True
    )

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for a in anime_list.get("data").get("animes")
    ]


async def expanded_search_api(
    order: str = "RANKED",
    kind: str | None = None,
    status: str | None = None,
    season: str | None = None,
    score: int | None = None,
    genre: str | None = None,
    limit: int = 50,
    quality: bool = False,
) -> list[dict]:
    """Выполняет расширенный поиск аниме по различным фильтрам.

    Возможные фильтры передаются параметрами (order, kind, status, season, score, genre).
    :param order: Критерий сортировки (например, "RANKED", "POPULARITY" и т.д.).
    :param kind: Тип сериала (tv, movie, ova и т.п.).
    :param status: Статус аниме ("ongoing", "released", "anons").
    :param season: Сезон/год в формате "season_year".
    :param score: Минимальный рейтинг (целое число).
    :param genre: ID жанра (строка, может начинаться с '!' для исключения жанра).
    :param limit: Максимум результатов.
    :param quality: Если True – загружать постеры в высоком качестве (оригинал), иначе стандартное.
    :return: Список словарей с аниме, соответствующих фильтрам.
    """

    params = dict(
        order=OrderEnum[order],
        kind=kind,
        status=status,
        season=season,
        score=score,
        genre=genre,
    )
    # убираем ключи где значение None
    params = {key: v for key, v in params.items() if v is not None}

    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """
    anime_list = await client.graphql.animes(
        **params,
        fields=fields,
        limit=limit,
        censored=True,
    )
    # for url in [a.get("poster") for a in anime_list.get("data").get("animes")]:
    #     print(url)

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for a in anime_list.get("data").get("animes")
    ]


async def title_info(anime_id: int, quality=False) -> dict:
    """Получает подробную информацию об аниме по его ID.

    Включает описание, скриншоты, трейлеры, жанры и другую информацию.
    :param anime_id: ID аниме на Shikimori.
    :param quality: True для получения изображений в оригинальном размере (постер, скриншоты), False – в стандартном.
    :return: Словарь с подробной информацией об аниме (ключи: description, screenshots, videos, name, russian, score, status, episodes, и т.д.).
    """
    if quality:
        screenshots_size = "originalUrl"
        poster_size = "originalUrl"
    else:
        screenshots_size = "x332Url"
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ description
          screenshots {{ {screenshots_size} }}
          videos {{ url name kind }}
          poster {{ {poster_size} }}
          name russian score status episodes episodesAired
          airedOn {{ date }} releasedOn {{ date }}
          url
          genres {{ russian }}
        }}
        """

    anime = await client.graphql.animes(fields=fields, ids=str(anime_id), limit=1)
    anime = anime.get("data").get("animes")[0]
    return {
        "description": anime.get("description"),
        "screenshots": [
            screenshot.get(screenshots_size) for screenshot in anime.get("screenshots")
        ],
        "videos": [
            {
                "name": video.get("name"),
                "url": video.get("url"),
                "kind": video.get("kind"),
            }
            for video in anime.get("videos")
            if "youtu" in video.get("url")
        ],
        "name": anime.get("name"),
        "russian": anime.get("russian"),
        "score": anime.get("score"),
        "status": anime.get("status"),
        "episodes": anime.get("episodes"),
        "episodesAired": anime.get("episodesAired"),
        "airedOn": (anime.get("airedOn") or {}).get("date"),
        "releasedOn": (anime.get("releasedOn") or {}).get("date"),
        "url": anime.get("url"),
        "genres": [g.get("russian") for g in anime.get("genres", [])],
        "poster": (anime.get("poster") or {}).get(f"{poster_size}"),
    }


async def seasons_ongoing(limit: int = 50, quality=False) -> list[dict]:
    """Возвращает список онгоингов текущего или последнего сезонов.

    Формирует запрос на Shikimori для аниме со статусом 'ongoing' (онгоинг) в двух последних сезонах.
    :param limit: Максимальное число аниме для вывода.
    :param quality: True – загрузить постеры в оригинале, False – стандартное качество.
    :return: Список словарей с информацией об онгоингах.
    """
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """
    seasons = what_seasons()
    anime_list = await client.graphql.animes(
        fields=fields,
        kind="tv,tv_13,tv_24,tv_48,ova,ona",
        status="ongoing",
        season=seasons,
        limit=limit,
        censored=True,
        order=OrderEnum.RANKED,
    )

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for a in anime_list.get("data").get("animes")
    ]


async def latest_anime(limit: int = 50, quality: bool = False) -> list[dict]:
    """Возвращает список новейших вышедших аниме.

    Запрашивает у Shikimori аниме со статусом 'latest' (новые релизы).
    :param limit: Максимум результатов.
    :param quality: True – постеры высокого качества, False – обычные.
    :return: Список словарей с информацией о последних вышедших аниме.
    """
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """

    anime_list = await client.graphql.animes(
        fields=fields,
        status="latest",
        limit=limit,
        censored=True,
        order=OrderEnum.RANKED,
    )

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for a in anime_list.get("data").get("animes")
    ]


async def anime_by_id(anime_id: int, quality: bool = False) -> dict:
    """Получает краткую информацию об аниме по ID (сейчас не используется).

    :param anime_id: ID тайтла.
    :param quality: True – постер оригинал, False – постер стандартный.
    :return: Словарь с основными данными об аниме (id, name, russian, score, статус, эпизоды, постер и т.д.).
    """
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """
    anime_list = await client.graphql.animes(
        fields=fields, ids=str(anime_id), limit=1, censored=True
    )
    a = anime_list.get("data").get("animes")[0]
    return {
        "id": a.get("id"),
        "name": a.get("name"),
        "russian": a.get("russian"),
        "score": a.get("score"),
        "status": a.get("status"),
        "episodes": a.get("episodes"),
        "episodesAired": a.get("episodesAired"),
        "duration": a.get("duration"),
        "airedOn": (a.get("airedOn") or {}).get("date"),
        "releasedOn": (a.get("releasedOn") or {}).get("date"),
        "url": a.get("url"),
        "poster": (a.get("poster") or {}).get(f"{poster_size}"),
        "genres": [g.get("russian") for g in a.get("genres", [])],
    }


async def random_anime_list(limit: int = 10, quality: bool = False):
    """Получает случайный список аниме(сейчас не используется)"""
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """

    anime_list = await client.graphql.animes(
        fields=fields,
        kind="tv,tv_13,tv_24,tv_48,ova,ona",  # только сериалы
        order=OrderEnum.RANDOM,  # или: order=OrderEnum.random
        limit=limit,  # максимум 50
        censored=True,
    )

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for a in anime_list.get("data").get("animes")
    ]


async def controlled_random_anime_list(quality: bool = False) -> list[dict]:
    """Подбирает список случайных аниме с контролем по эпохам и параметрам.

    Генерирует 5 случайных "слотов" сезонов из разных эпох и для каждого выбирает 2 аниме с фильтрами
    :param quality: True – постеры оригиналы, False – обычные.
    :return: Список словарей с информацией об отобранных случайных аниме.
    """
    if quality:
        poster_size = "originalUrl"
    else:
        poster_size = "mainUrl"

    client = cfg.SHIKI_CLIENT
    fields = f"""
        {{ 
        id name russian score status episodes episodesAired duration
          airedOn {{ date }} releasedOn {{ date }}
          url poster {{ {poster_size} }}
          genres {{ russian }}
        }}
        """

    random_seasons = build_final_5_slots()

    def season_str(slot) -> str:
        return (
            f"{EPOCHS[slot.epoch][0]}_{EPOCHS[slot.epoch][1]}"
            if slot.year is None
            else f"{slot.season}_{slot.year}"
        )

    anime_list = [
        client.graphql.animes(
            fields=fields,
            season=season_str(season),
            kind="tv,tv_13,tv_24,tv_48,ova,ona,!special,!tv_special,!music,!pv,!cm",
            score=7,
            duration="D,!S",
            genre="!15",
            studio="!1768,!2528,!1827,!2396!1667!2065,!2471",  # Китайские 3d студии
            order=OrderEnum.RANDOM,
            limit=2,
            censored=True,
        )
        for season in random_seasons
    ]

    responses = await asyncio.gather(*anime_list)

    return [
        {
            "id": a.get("id"),
            "name": a.get("name"),
            "russian": a.get("russian"),
            "score": a.get("score"),
            "status": a.get("status"),
            "episodes": a.get("episodes"),
            "episodesAired": a.get("episodesAired"),
            "duration": a.get("duration"),
            "airedOn": (a.get("airedOn") or {}).get("date"),
            "releasedOn": (a.get("releasedOn") or {}).get("date"),
            "url": a.get("url"),
            "poster": (a.get("poster") or {}).get(f"{poster_size}"),
            "genres": [g.get("russian") for g in a.get("genres", [])],
        }
        for resp in responses
        for a in resp.get("data").get("animes")
    ]


async def get_similar_anime(anime_id: int, quality: bool = False) -> list[dict]:
    """Получает список похожих аниме для заданного тайтла.

    :param anime_id: ID исходного аниме.
    :param quality: True – постеры оригиналы, False – обычные
    :return: Список словарей с данными по похожим аниме (id, name, russian, score, статус, эпизоды и др.). Может быть пустым, если похожих нет.
    """
    poster_attr = "original" if quality else "preview"
    print(poster_attr)

    def _abs_url(path: str | None) -> str | None:
        if not path:
            return None
        return path if path.startswith("http") else f"https://shikimori.one{path}"

    client = cfg.SHIKI_CLIENT
    # shiki.py оборачивает /api/animes/{id}/similar в метод .similar()
    similar = await client.anime.similar(anime_id)
    if not similar:
        return []

    return [
        {
            "id": a.id,
            "name": a.name,
            "russian": a.russian,
            "score": a.score,
            "status": a.status,
            "episodes": a.episodes,
            "episodesAired": getattr(a, "episodes_aired", None),
            "duration": getattr(a, "duration", None),
            "airedOn": getattr(a, "aired_on", None),
            "releasedOn": getattr(a, "released_on", None),
            "url": _abs_url(a.url),
            "poster": _abs_url(getattr(a.image, poster_attr, None)),
            "kind": a.kind,
        }
        for a in similar
    ]
