from database.common.extended_search_models import (
    UserSearchPrefs,
    UserSearchGenre,
    UserSearchType,
    UserSeasonToken,
    UserSearchStatuses,
)

from database.common.models import db_proxy as db


def ensure_prefs(chat_id: int):
    """Создает запись настроек поиска, если ее нет, и возвращает объект UserSearchPrefs."""
    return UserSearchPrefs.get_or_create(chat_id=chat_id)[0]


# -------- жанры --------
def get_selected_ids(chat_id: int) -> set:
    """Возвращает set[int] id жанров для быстрой проверки наличия жанра в списке пользователя"""
    q = UserSearchGenre.select(UserSearchGenre.genre_id).where(
        UserSearchGenre.chat_id == chat_id
    )
    return {row.genre_id for row in q}


def toggle_genre(chat_id: int, genre_id) -> bool:
    """Возвращает True, если жанр стал выбранным; False — если сняли выбор."""
    exists = UserSearchGenre.get_or_none(chat_id=chat_id, genre_id=genre_id)
    if exists:
        exists.delete_instance()
        return False
    UserSearchGenre.create(chat_id=chat_id, genre_id=genre_id)
    return True


def clear_genre(chat_id: int) -> None:
    """Сбрасывает жанры, темы, аудитории"""
    UserSearchGenre.delete().where(UserSearchGenre.chat_id == chat_id).execute()


# -------- сезоны --------
def get_selected_seasons(chat_id: int) -> set[str]:
    """Возвращает множество выбранных сезонов (id фильтра сезона)."""
    q = UserSeasonToken.select(UserSeasonToken.season).where(
        UserSeasonToken.chat_id == chat_id
    )
    return {row.season for row in q}


def toggle_season(chat_id: int, season_token: int) -> bool:
    """Переключает выбор сезона: возвращает True, если добавлен, False — если снят."""
    ensure_prefs(chat_id)
    exists = UserSeasonToken.get_or_none(chat_id=chat_id, season=season_token)
    if exists:
        exists.delete_instance()
        return False
    UserSeasonToken.create(chat_id=chat_id, season=season_token)
    return True


def clear_seasons(chat_id: int) -> None:
    """Сбрасывает выбранные сезоны пользователя."""
    UserSeasonToken.delete().where(UserSeasonToken.chat_id == chat_id).execute()


# -------- типы --------
def get_selected_types(chat_id: int) -> set[str]:
    """Возвращает множество выбранных типов аниме ('tv', 'movie', ...)."""
    q = UserSearchType.select(UserSearchType.kind).where(
        UserSearchType.chat_id == chat_id
    )
    return {r.kind for r in q}


def toggle_type(chat_id: int, kind: str) -> bool:
    """Переключает выбор типа: возвращает True, если тип добавлен, False — если снят."""
    row = UserSearchType.get_or_none(chat_id=chat_id, kind=kind)
    if row:
        row.delete_instance()
        return False
    UserSearchType.create(chat_id=chat_id, kind=kind)
    return True


def clear_types(chat_id: int) -> None:
    """Сбрасывает выбранные типы аниме пользователя."""
    UserSearchType.delete().where(UserSearchType.chat_id == chat_id).execute()


# -------- оценка (min_score) --------
def get_min_score(chat_id: int):
    """Текущий минимальный рейтинг пользователя (min_score)."""
    row = UserSearchPrefs.get_or_none(UserSearchPrefs.chat_id == chat_id)
    return row.min_score


def set_min_score(chat_id: int, score) -> bool:
    """Устанавливает новое значение минимального рейтинга (повторное значение снимает выбор). Возвращает True, если значение установлено, False если сброшено."""
    with db.atomic():
        row, _ = UserSearchPrefs.get_or_create(chat_id=chat_id)
        if row.min_score == score:
            row.min_score = None  # сняли выбор
            is_selected = False
        else:
            row.min_score = score  # установили новое
            is_selected = True
        row.save()
        return is_selected


def reset_min_score(chat_id: int) -> None:
    """Сбрасывает min_score (ставит 1)."""
    set_min_score(chat_id, 1)


# -------- Статус аниме --------
def get_selected_statuses(chat_id: int) -> set[str]:
    """Возвращает множество выбранных статусов аниме пользователя."""
    q = UserSearchStatuses.select(UserSearchStatuses.status).where(
        UserSearchStatuses.chat_id == chat_id
    )
    return {row.status for row in q}


def toggle_statuses(chat_id: int, status: str) -> bool:
    """Переключает выбор статуса: возвращает True, если статус добавлен, False — если снят."""
    exists = UserSearchStatuses.get_or_none(chat_id=chat_id, status=status)
    if exists:
        exists.delete_instance()
        return False
    UserSearchStatuses.create(chat_id=chat_id, status=status)
    return True


def clear_statuses(chat_id):
    """Сбрасывает выбранные статусы аниме пользователя."""
    UserSearchStatuses.delete().where(UserSearchStatuses.chat_id == chat_id).execute()


# -------- сортировка --------
def get_sort(chat_id: int):
    """Текущая сортировка пользователя."""
    row = UserSearchPrefs.get_or_none(UserSearchPrefs.chat_id == chat_id)
    return row.sort


def toggle_sort(chat_id: int, sort_key: str) -> str:
    """Переключает сортировку (если такая уже выбрана, сбрасывает на дефолт 'RANKED').
    Возвращает актуальное значение сортировки.
    """
    row = UserSearchPrefs.get_or_none(UserSearchPrefs.chat_id == chat_id)
    current = row.sort
    if current == sort_key:
        row.sort = "RANKED"
        row.save()
        return row.sort
    row.sort = sort_key
    row.save()
    return row.sort


def reset_sort(chat_id: int) -> None:
    """Сбрасывает сортировку на значение по умолчанию."""
    toggle_sort(chat_id, "RANKED")


def reset_user_search_prefs(chat_id: int) -> None:
    """Сбрасывает расширенный поиск пользователя к значениям по умолчанию.
    Поля с default -> default, поля без default -> None (или 0), списки очищаются.
    """

    with db.atomic():  # работает прозрачно с прокси
        clear_types(chat_id)
        clear_genre(chat_id)
        clear_seasons(chat_id)
        clear_statuses(chat_id)
        reset_min_score(chat_id)
        reset_sort(chat_id)
