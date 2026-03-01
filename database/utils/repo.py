import time
from peewee import ModelSelect
from database.common.models import (
    History,
    ShikiToken,
    UserAnime,
    db_proxy as db,
)
from api.shiki_auth import refresh_access_token


def save_history(chat_id: int, message: str) -> History:
    """Сохраняет одну запись истории (сообщение пользователя)."""
    # для одиночной вставки транзакция не обязательна, но так привычнее и безопаснее
    with db.atomic():
        return History.create(chat_id=chat_id, message=message)


def list_history(chat_id: int, limit: int = 20, offset: int = 0) -> ModelSelect:
    """Возвращает ленивый SELECT последних записей истории для чата."""
    return (
        History.select(
            History.id,
            History.message,
            History.created_at,
        )
        .where(History.chat_id == chat_id)
        .order_by(History.id.desc())
        .limit(limit)
        .offset(offset)
    )


def shiki_token_save(
    tg_user_id: int,
    shiki_user_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: int,
) -> None:
    """Сохраняет токены Shikimori в базу (с обновлением по tg_user_id при конфликте)."""
    # 4) сохраняем в таблицу (upsert по tg_user_id)
    ShikiToken.insert(
        tg_user_id=tg_user_id,
        shiki_user_id=shiki_user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    ).on_conflict(
        conflict_target=[ShikiToken.tg_user_id],
        update={
            ShikiToken.shiki_user_id: shiki_user_id,
            ShikiToken.access_token: access_token,
            ShikiToken.refresh_token: refresh_token,
            ShikiToken.expires_at: expires_at,
        },
    ).execute()


def get_all_tg_user_ids() -> list[int]:
    """Возвращает список всех tg_user_id из таблицы ShikiToken."""
    query = ShikiToken.select(ShikiToken.tg_user_id)
    return [record.tg_user_id for record in query]


class NotAuthorizedError(Exception):
    pass


async def get_token(tg_user_id: int, without_timer: bool = False) -> tuple[str, int]:
    """Получает действующий access_token для пользователя (обновляет с помощью refresh_token при необходимости)."""
    row = ShikiToken.get_or_none(ShikiToken.tg_user_id == tg_user_id)
    if row is None:
        raise NotAuthorizedError
    now = int(time.time())
    if not without_timer and row.expires_at and row.expires_at - now > 1 * 60 * 60:
        return row.access_token, row.shiki_user_id
    fresh = await refresh_access_token(row.refresh_token)
    expires_at = now + int(fresh["expires_in"])
    shiki_token_save(
        tg_user_id,
        row.shiki_user_id,
        fresh["access_token"],
        fresh["refresh_token"],
        expires_at,
    )
    return fresh["access_token"], row.shiki_user_id


def save_anime_search(chat_id: int, anime_id: int, anime_dict: dict) -> None:
    """Сохраняет информацию о тайтле (результат поиска) в истории пользователя."""
    now = int(time.time())
    (
        UserAnime.insert(
            chat_id=chat_id,
            anime_id=anime_id,
            anime_data=anime_dict,
            seen_at=now,
        )
        .on_conflict(
            conflict_target=[UserAnime.chat_id, UserAnime.anime_id],
            update={
                UserAnime.anime_data: anime_dict,  # можно заменить на pw.fn.json_set(...) если нужно менять точечно
                UserAnime.seen_at: now,
            },
        )
        .execute()
    )


def get_anime_search(chat_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    """Извлекает из БД список сохраненных тайтлов пользователя (как в ответе Shikimori API)."""
    rows = (
        UserAnime.select(UserAnime.anime_id, UserAnime.anime_data)
        .where(UserAnime.chat_id == chat_id)
        .order_by(UserAnime.seen_at.desc())
        .limit(limit)
        .offset(offset)
    )
    titles_list = []
    for r in rows:
        data = r.anime_data or {}
        # если вдруг в anime_data есть свой 'id', гарантированно перезатираем на корректный
        titles_list.append({"id": r.anime_id, **data})
    return titles_list


def get_anime_by_id(chat_id: int, anime_id: int) -> dict:
    """Извлекает из БД информацию о конкретном тайтле пользователя по ID."""
    row = UserAnime.get(
        (UserAnime.chat_id == chat_id) & (UserAnime.anime_id == anime_id)
    )
    data = row.anime_data or {}
    return {"id": row.anime_id, **data}
