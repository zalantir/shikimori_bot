import re
from telebot.types import InputFile

from telebot.states.sync.context import StateContext
from loader import bot
from keyboards.inline.inline_kbs import continue_kb, info_add_kb_row
from config_data.config import DEFAULT_POSTER, STATUS_RU


def title_head(title: dict) -> str:
    """Форматирование базового заголовка аниме."""
    ru = title.get("russian")
    en = title.get("name")
    total = int(title.get("episodes"))
    status = title.get("status")
    head = f"{ru}/{en}"
    if status == "released":
        head += f" [{total} из {total}]"
    elif status == "ongoing":
        aired = int(title.get("episodesAired"))
        if total == 0:
            total = "?" * len(str(aired))
        head += f" [{aired} из {total}]"
    elif status == "anons":
        head += " [Анонс]"
    return head


def list_of_titles(titles: list[dict] | dict) -> list[tuple[str, str]]:
    """Формирует список кортежей (текст, id) для передачи клавиатуре."""
    if isinstance(titles, dict):
        titles = [titles]
    return [(title_head(title), title.get("id")) for title in titles]


def one_title_view(title: dict, is_date: bool = True) -> tuple[InputFile | str, str]:
    """Форматирование краткой справочной информации по одному аниме."""
    head = title_head(title)
    link = title.get("url")
    status = title.get("status")
    release_str = None
    if is_date:
        # Дата выхода
        aired = title.get("airedOn") or ""
        released = title.get("releasedOn") or ""
        if not released:
            released = aired
        if status == "released":
            release_str = f"Вышло: в {released.partition("-")[0]} году"
        elif status == "ongoing":
            release_str = f"Выходит: с {aired.partition("-")[0]} года"
        elif status == "anons":
            release_str = f"Выйдет: в {aired.partition("-")[0]} году"

    # Рейтинг
    score = title.get("score")
    score_str = f"Рейтинг: {score}" if float(score) != 0 else None

    # Жанры
    genres = title.get("genres")
    genres_str = None
    if genres:
        genres_str = f"Жанры: {", ".join(genres)}"

    # Сборщик строк - отсеивает пустые строки
    parts = [
        f'<a href="{link}">{head}</a>',
        score_str,
        release_str,
        genres_str,
    ]
    caption = "\n".join(p for p in parts if p)

    poster = title.get("poster") or InputFile(DEFAULT_POSTER)
    return poster, caption


def user_edit_one_title_view(
    old_caption: str,
    status: str | None,
    episodes: int | None,
    total_ep: int,
    score: int | None,
) -> str:
    """Обновляет информацию о тайтле с учетом статуса, прогресса и оценки пользователя."""
    divide = "\n━━━ 📜 В СПИСКЕ ━━━"
    pos = old_caption.find(divide)
    if pos != -1:
        old_caption = old_caption[:pos].rstrip()

    if status:
        status_txt = STATUS_RU.get(str(status), str(status))
        status = f"📌 Статус: {status_txt}"
    else:
        parts = [old_caption, divide, "Отсутствует"]
        caption = "\n".join(p for p in parts if p)
        return caption

    if episodes:
        episodes = f"🎞️ Серий просмотрено: {episodes} из {total_ep}"
    if score:
        score = f"⭐ Ваша оценка: {score}"
    parts = [old_caption, divide, status, episodes, score]
    caption = "\n".join(p for p in parts if p)
    return caption


def user_info_one_title_view(old_caption: str, title: dict) -> str:
    """Добавляет к краткому описанию информацию о тайтле из списка пользователя (если есть)."""
    _, caption = one_title_view(title)
    divide = "\n━━━ 📜 В СПИСКЕ ━━━"
    pos = old_caption.find(divide)
    if pos == -1:
        return caption
    old_caption = old_caption[pos:].rstrip()
    parts = [caption, old_caption]
    caption = "\n".join(p for p in parts if p)
    return caption


def get_description(description: str) -> str:
    """Форматирование описания (очистка от тегов и обрезка по длине)."""
    # [[...]] -> ... (сохраняем текст внутри двойных скобок)
    clean_description = re.sub(r"\[\[([^\[\]]+)]]", r"\1", description)
    # чистим внутренние теги [character=89], [デンジ] и т.д.
    clean_description = re.sub(r"\[/?[^]]+]", "", clean_description)
    if len(clean_description) > 4096:
        sents = re.split(r"(?<=[.!?…])(?!\n\n)\s+", clean_description)
        tail = []
        while len(" ".join(sents)) > 4093:  # -3 запас на троеточие.
            tail.insert(0, sents.pop())
        clean_description = " ".join(sents)
        if not clean_description.endswith(("…", "...")):
            clean_description += "..."
    return clean_description


def one_title_details(title: dict) -> tuple[list[str] | None, str]:
    """Компоновка кадров и описания (устаревшее)."""
    description = title.get("description") or ""

    # [[...]] -> ... (сохраняем текст внутри двойных скобок)
    clean_description = re.sub(r"\[\[([^\[\]]+)]]", r"\1", description)
    # чистим внутренние теги [character=89], [デンジ] и т.д.
    clean_description = re.sub(r"\[/?[^]]+]", "", clean_description)

    if len(clean_description) > 1024:
        sents = re.split(r"(?<=[.!?…])(?!\n\n)\s+", clean_description)
        tail = []
        while len(" ".join(sents)) > 1021:  # -3 запас на троеточие.
            tail.insert(0, sents.pop())
        clean_description = " ".join(sents)
        if not clean_description.endswith(("…", "...")):
            clean_description += "..."

    # Скриншоты
    screenshots = title.get("screenshots")

    return screenshots, clean_description


def posters_messages_menu(
    chat_id: int,
    state: StateContext,
    key: str | None = None,
    titles_lst: list[dict] | None = None,
    reply_kb_msg_id: int | None = None,
) -> None:
    """Логика меню вывода списка аниме с постерами (10 за раз)."""
    if not titles_lst:
        with state.data() as data:
            titles_lst = data.get(key)
    poster_msg_ids = []
    if reply_kb_msg_id:
        poster_msg_ids.append(reply_kb_msg_id)
    for title in titles_lst[:10]:
        poster, head = one_title_view(title)
        anime_id = title.get("id")
        status = title.get("status")
        if status == "released":
            total_ep = int(title.get("episodes"))
        else:
            total_ep = int(title.get("episodesAired"))
        m = bot.send_photo(
            chat_id=chat_id,
            photo=poster,
            caption=head,
            reply_markup=info_add_kb_row(anime_id, total_ep),
            parse_mode="HTML",
        )
        poster_msg_ids.append(m.message_id)

    if key and titles_lst[10:]:
        bot_msg = bot.send_message(
            chat_id,
            "Выберите действие",
            reply_markup=continue_kb(key),
            reply_to_message_id=poster_msg_ids[0],
        )
        state.add_data(**{key: titles_lst[10:]})
    else:
        bot_msg = bot.send_message(
            chat_id, "Конец списка", reply_to_message_id=poster_msg_ids[0]
        )
    poster_msg_ids.append(bot_msg.message_id)

    with state.data() as data:
        ids = data.setdefault("poster_msg_ids", [])
        ids.extend(poster_msg_ids)
