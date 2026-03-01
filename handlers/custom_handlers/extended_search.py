import asyncio
from telebot.types import Message, CallbackQuery
from telebot.states.sync.context import StateContext
from loader import bot
from states.browse_states import MenuStates
from keyboards.inline.inline_kbs import settings_kb_with_mark, extended_search_kb
from config_data.config import (
    GENRES,
    THEMES,
    DEMOGRAPHICS,
    SORT,
    SCORE,
    KIND,
    ANIME_STATUS,
)
from utils.misc.calendar import build_time_filters
from database.utils.extended_search_helpers import (
    get_selected_ids,
    get_sort,
    get_selected_types,
    get_min_score,
    get_selected_seasons,
    get_selected_statuses,
    toggle_genre,
    toggle_sort,
    toggle_type,
    toggle_season,
    toggle_statuses,
    set_min_score,
    reset_user_search_prefs,
)
from api.shiki import expanded_search_api
from handlers.utils.format_for_handlers import posters_messages_menu


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("🔎"),
)
def extended_search(msg: Message, state: StateContext):
    """Открывает меню расширенного поиска"""
    bot.send_message(
        msg.chat.id,
        "🔎 Расширенный поиск:",
        reply_markup=extended_search_kb(),
    )
    bot.delete_message(msg.chat.id, msg.message_id)


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("search")),
)
def search(call: CallbackQuery, state: StateContext):
    """Выполняет расширенный поиск и выводит результаты."""
    chat_id = call.message.chat.id

    order = get_sort(chat_id)
    kind = ",".join(get_selected_types(chat_id) or []) or None
    status = ",".join(get_selected_statuses(chat_id) or []) or None
    season = ",".join(get_selected_seasons(chat_id) or []) or None
    score = get_min_score(chat_id)
    genre = ",".join(get_selected_ids(chat_id) or []) or None
    anime_search = asyncio.run(
        expanded_search_api(order, kind, status, season, score, genre, quality=True)
    )

    posters_messages_menu(
        call.message.chat.id,
        state,
        "extend_search",
        anime_search,
        call.message.message_id,
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("extend_search:continue"),
)
def latest_animes_continue(call: CallbackQuery, state: StateContext):
    """Продолжает выводить список аниме по расширенному поиску."""
    posters_messages_menu(call.message.chat.id, state, "extend_search")


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("page:")),
)
def extended_search_page_turning(call: CallbackQuery, state: StateContext):
    """Переключает страницы меню расширенного поиска (1 и 2)."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[1])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=extended_search_kb(page)
    )


# -------- Жанры --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("genre"),
)
def genre_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки жанров."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=GENRES, selected=get_selected_ids(chat_id), ns="g"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("g:toggle"),
)
def genre_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет жанры в пользовательских настройках расширенного поиска"""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    genre_id = call.data.split(":")[2]
    toggle_genre(chat_id, genre_id)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=GENRES, selected=get_selected_ids(chat_id), page=page, ns="g"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("g:page"),
)
def genre_scroll(call: CallbackQuery, state: StateContext):
    """листает список жанров"""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=GENRES, selected=get_selected_ids(chat_id), page=page, ns="g"
        ),
    )


# -------- Темы --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("theme"),
)
def theme_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки тематик"""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=THEMES, selected=get_selected_ids(chat_id), ns="th"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("th:toggle"),
)
def theme_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет тематику в пользовательских настройках расширенного поиска."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    genre_id = int(call.data.split(":")[2])
    toggle_genre(chat_id, genre_id)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=THEMES, selected=get_selected_ids(chat_id), page=page, ns="th"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("th:page"),
)
def theme_scroll(call: CallbackQuery, state: StateContext):
    """Листает список тематик."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=THEMES, selected=get_selected_ids(chat_id), page=page, ns="th"
        ),
    )


# -------- сортировка --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("order"),
)
def sort_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки сортировки"""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=SORT, selected=get_sort(chat_id), ns="srt", rows=5, cols=1
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("srt:toggle"),
)
def sort_toggle_handler(call: CallbackQuery, state: StateContext):
    """Выбирает параметр сортировки для расширенного поиска."""
    chat_id = call.message.chat.id
    sort_key = call.data.split(":")[2]
    toggle_sort(chat_id, sort_key)
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=extended_search_kb()
    )


# -------- Оценка --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("score"),
)
def score_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки минимальной оценки."""
    chat_id = call.message.chat.id
    user_score = [get_min_score(chat_id)]
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=SCORE, selected=user_score, ns="sc", cols=1
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("sc:toggle"),
)
def score_toggle_handler(call: CallbackQuery, state: StateContext):
    """Устанавливает минимальную оценку для расширенного поиска."""
    chat_id = call.message.chat.id
    score = int(call.data.split(":")[2])
    set_min_score(chat_id, score)

    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=extended_search_kb()
    )


# -------- Сезоны --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("seasons"),
)
def seasons_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки сезонов."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=build_time_filters(), selected=get_selected_seasons(chat_id), ns="se"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("se:toggle"),
)
def seasons_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет сезон в пользовательских настройках расширенного поиска."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    season_token = call.data.split(":")[2]
    toggle_season(chat_id, season_token)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=build_time_filters(),
            selected=get_selected_seasons(chat_id),
            page=page,
            ns="se",
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("se:page"),
)
def seasons_scroll(call: CallbackQuery, state: StateContext):
    """Листает список сезонов."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=build_time_filters(),
            selected=get_selected_seasons(chat_id),
            page=page,
            ns="se",
        ),
    )


# -------- Типы аниме --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("kind"),
)
def kind_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки типов аниме."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=KIND, selected=get_selected_types(chat_id), ns="k", cols=1
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("k:toggle"),
)
def kind_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет тип аниме в пользовательских настройках расширенного поиска."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    kind_key = call.data.split(":")[2]
    toggle_type(chat_id, kind_key)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=KIND, selected=get_selected_types(chat_id), page=page, ns="k", cols=1
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("k:page"),
)
def kind_scroll(call: CallbackQuery, state: StateContext):
    """Листает список типов аниме."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=KIND,
            selected=get_selected_types(chat_id),
            page=page,
            ns="k",
            cols=1,
        ),
    )


# -------- Аудитория --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("demographic"),
)
def demographic_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки аудитории."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=DEMOGRAPHICS, selected=get_selected_ids(chat_id), ns="d"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("d:toggle"),
)
def demographic_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет аудиторию в пользовательских настройках расширенного поиска."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    genre_id = int(call.data.split(":")[2])
    toggle_genre(chat_id, genre_id)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=DEMOGRAPHICS, selected=get_selected_ids(chat_id), page=page, ns="d"
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("d:page"),
)
def demographic_scroll(call: CallbackQuery, state: StateContext):
    """Листает список аудиторий."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=DEMOGRAPHICS, selected=get_selected_ids(chat_id), page=page, ns="d"
        ),
    )


# -------- статусы аниме --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("status"),
)
def status_settings(call: CallbackQuery, state: StateContext):
    """Открывает меню настройки статусов аниме."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=ANIME_STATUS, selected=get_selected_statuses(chat_id), ns="st", cols=1
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("st:toggle"),
)
def status_toggle_handler(call: CallbackQuery, state: StateContext):
    """Добавляет/удаляет статус(ы) аниме в пользовательских настройках расширенного поиска."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[3])
    status = call.data.split(":")[2]
    toggle_statuses(chat_id, status)
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=ANIME_STATUS,
            selected=get_selected_statuses(chat_id),
            page=page,
            ns="st",
            cols=1,
        ),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("st:page"),
)
def status_scroll(call: CallbackQuery, state: StateContext):
    """Листает список статусов аниме."""
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[2])  # 1 или 2

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=settings_kb_with_mark(
            items=ANIME_STATUS,
            selected=get_selected_statuses(chat_id),
            page=page,
            ns="st",
            cols=1,
        ),
    )


# -------- Остальное --------
@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("reset_settings")),
)
def reset(call: CallbackQuery, state: StateContext):
    """Сбрасывает настройки расширенного поиска."""
    chat_id = call.message.chat.id
    reset_user_search_prefs(chat_id)
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=extended_search_kb()
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("cancel")),
)
def cancel(call: CallbackQuery, state: StateContext):
    """возвращается к меню расширенного поиска."""
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=extended_search_kb()
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("exit")),
)
def expanded_search_exit(call: CallbackQuery, state: StateContext):
    """Выходит из меню расширенного поиска."""
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, call.message.message_id)
