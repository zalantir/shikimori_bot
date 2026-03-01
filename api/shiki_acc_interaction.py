from shikimori import Shikimori
from shikimori.enums import (
    UserRateStatusEnum,
    UserRateTargetTypeEnum,
    UserRateOrderFieldEnum,
    UserRateOrderInputType,
    SortOrderEnum,
)

import config_data.config as cfg
from database.utils.repo import get_token, NotAuthorizedError
from shikimori.exceptions import RequestError


async def user_anime_info(
    chat_id: int, anime_id: int
) -> tuple[None | str, None | int, None | int, None | int]:
    """Получает информацию о статусе данного аниме в списке пользователя.

    :param chat_id: Telegram ID пользователя (используется для получения токена доступа).
    :param anime_id: ID аниме на Shikimori.
    :return: Кортеж (status, episodes, score, rate_id) если запись найдена, либо (None, None, None, None) если у пользователя это аниме отсутствует в списке.
    """
    client: Shikimori = cfg.SHIKI_CLIENT
    try:
        access_token, user_id = await get_token(chat_id)
    except NotAuthorizedError:
        raise
    client.set_token(access_token)
    titles = await client.userRate.list(
        user_id=user_id, target_id=anime_id, target_type="Anime", limit=1
    )
    if not titles:
        return None, None, None, None
    title = titles[0]
    status = getattr(title, "status", None)
    episodes = getattr(title, "episodes", None)
    score = getattr(title, "score", None)
    rate_id = getattr(title, "id", None)
    return status, episodes, score, rate_id


async def _delete_user_rate_safely(client: Shikimori, rate_id: int) -> bool:
    """Удаляет запись о тайтле из списка пользователя.
     Игнорирует попытку обёртки вернуть json вместе с 204.

    Возвращает True, если удаление прошло успешно.
    :param client: Клиент Shikimori с установленным токеном.
    :param rate_id: ID записи (userRate.id) в списке, которую нужно удалить.
    :return: True если удалено, исключение при других ошибках.
    """
    try:
        await client.userRate.delete(rate_id)
        return True
    except RequestError as e:
        # 204 без JSON, который обёртка трактует как ошибку
        msg = str(e)
        if "Attempt to decode JSON with unexpected mimetype" in msg:
            return True
        raise  # другие ошибки не скрываем


async def anime_status_set(
    chat_id: int, anime_id: int, status: int, rate_id: int
) -> tuple[None | str, str, int, int, int]:
    """Добавляет или изменяет статус аниме в списке пользователя.

    :param chat_id: Telegram ID пользователя.
    :param anime_id: ID аниме.
    :param status: Новый статус ("planned", "watching", "completed", "on_hold", "dropped", либо "delete" для удаления).
    :param rate_id: Идентификатор существующей записи списка (строка или "None"). Если "None", будет создана новая запись.
    :return: Кортеж из 5 элементов: (flag, status, episodes, score, rate_id). Первый элемент пока всегда None (зарезервировано под разные флаги).
             Остальные: статус, количество эпизодов, оценка, ID записи списка.
    """
    client: Shikimori = cfg.SHIKI_CLIENT
    access_token, user_id = await get_token(chat_id)
    client.set_token(access_token)

    if rate_id != "None":
        if status == "delete":
            await _delete_user_rate_safely(client, int(rate_id))
            return None, None, None, None, None

        title = await client.userRate.update(rate_id, status=status)
        return None, title.status, title.episodes, title.score, title.id

    title = await client.userRate.create(
        user_id=user_id, target_id=anime_id, target_type="Anime", status=status
    )
    return None, title.status, title.episodes, title.score, title.id


async def set_anime_score(
    chat_id: int, anime_id: int, score: int, rate_id: str
) -> tuple[str, int, int, int]:
    """Устанавливает или обновляет оценку пользователя для указанного аниме.

    :param chat_id: Telegram ID пользователя.
    :param anime_id: ID аниме.
    :param score: Оценка (целое число от 1 до 10).
    :param rate_id: ID записи списка (строка или "None"). Если "None", будет создана новая запись с этой оценкой.
    :return: Кортеж (status, episodes, score, rate_id) после обновления/создания записи:
             статус в списке, количество эпизодов, новая оценка, ID записи.
    """
    client: Shikimori = cfg.SHIKI_CLIENT
    access_token, user_id = await get_token(chat_id)
    client.set_token(access_token)

    if rate_id != "None":
        # запись есть — обновляем оценку
        title = await client.userRate.update(rate_id, score=score)
    else:
        # записи нет — создаём новую с оценкой
        title = await client.userRate.create(
            user_id=user_id,
            target_id=anime_id,
            target_type="Anime",
            score=score,
        )
    return title.status, title.episodes, title.score, title.id


async def episodes_watched(
    chat_id: int, anime_id: int, count: int, rate_id: str
) -> tuple[str, int, int]:
    """Обновляет количество просмотренных эпизодов для аниме (статус "watching").

    :param chat_id: Telegram ID пользователя.
    :param anime_id: ID аниме.
    :param count: Число эпизодов, которое пользователь отметил просмотренным.
    :param rate_id: ID записи списка (строка или "None"). Если "None", создается новая запись со статусом "watching".
    :return: Кортеж (status, episodes, score) после обновления:
             статус, обновленное число эпизодов, текущая оценка.
    """
    client = cfg.SHIKI_CLIENT
    access_token, user_id = await get_token(chat_id)
    client.set_token(access_token)

    if rate_id != "None":
        updated = await client.userRate.update(
            user_rate_id=int(rate_id),
            status="watching",
            episodes=count,
        )
        return updated.status, updated.episodes, updated.score

    updated = await client.userRate.create(
        user_id=user_id,
        target_id=anime_id,
        target_type="Anime",
        status="watching",
        episodes=count,
    )
    return updated.status, updated.episodes, updated.score


async def another_one_episode(
    chat_id: int, anime_id: int, rate_id: str
) -> tuple[str, int, int, int]:
    """Помечает просмотр еще одного эпизода (инкремент на +1).

    :param chat_id: Telegram ID пользователя.
    :param anime_id: ID аниме.
    :param rate_id: ID записи списка (строка или "None").
    :return: Кортеж (status, episodes, score, rate_id) после обновления:
             статус, новое число эпизодов, оценка, ID записи.
    """
    client = cfg.SHIKI_CLIENT
    access_token, user_id = await get_token(chat_id)
    client.set_token(access_token)

    if rate_id != "None":
        updated = await client.userRate.increment(rate_id)
        return updated.status, updated.episodes, updated.score, updated.id

    updated = await client.userRate.create(
        user_id=user_id,
        target_id=anime_id,
        target_type="Anime",
        status="watching",
        episodes=1,
    )
    return updated.status, updated.episodes, updated.score, updated.id


async def user_anime_list(
    chat_id: int, status: str, page: int = 1, limit: int = 50, quality: bool = False
) -> list[dict]:
    """Получает список аниме пользователя по категории статуса.

    :param chat_id: Telegram ID пользователя.
    :param status: Категория списка ("planned", "watching", "completed", "on_hold" или "dropped").
    :param page: Номер страницы (пагинация результатов с Shikimori).
    :param limit: Сколько элементов получать за раз (максимум 50).
    :param quality: True – постеры в оригинале, False – стандартные.
    :return: Список словарей с информацией об аниме этой категории, включающий поля аниме и вложенный словарь user (содержит информацию о статусе/оценке/эпизодах пользователя).
    """
    poster_size = "originalUrl" if quality else "mainUrl"
    fields = f"""
    {{
      id
      status
      score
      episodes
      createdAt
      updatedAt
      anime {{
        id name russian score status episodes episodesAired duration
        airedOn {{ date }} releasedOn {{ date }}
        url
        poster {{ {poster_size} }}
        genres {{ russian }}
      }}
    }}
    """

    client = cfg.SHIKI_CLIENT
    access_token, user_id = await get_token(chat_id)
    client.set_token(access_token)

    if status == "completed":
        status = UserRateStatusEnum.COMPLETED
    elif status == "watching":
        status = UserRateStatusEnum.WATCHING
    elif status == "planned":
        status = UserRateStatusEnum.PLANNED
    else:
        status = UserRateStatusEnum.ON_HOLD

    user_rates = await client.graphql.userRates(
        fields,
        userId=user_id,
        page=page,
        limit=limit,
        targetType=UserRateTargetTypeEnum.ANIME,
        status=status,
        order=UserRateOrderInputType(
            field=UserRateOrderFieldEnum.UPDATED_AT,
            order=SortOrderEnum.DESC,
        ),
    )
    rates = user_rates.get("data").get("userRates")

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
            "poster": (a.get("poster") or {}).get(poster_size),
            "genres": [g.get("russian") for g in (a.get("genres") or [])],
            "user": {
                "rateId": r.get("id"),
                "status": r.get("status"),  # watching/completed/...
                "score": r.get("score"),  # твоя оценка
                "episodes": r.get("episodes"),  # сколько отметил
                "createdAt": r.get("createdAt"),
                "updatedAt": r.get("updatedAt"),
            },
        }
        for r in rates
        for a in [r.get("anime") or {}]
        if a
    ]
