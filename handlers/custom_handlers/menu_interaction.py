from random import shuffle
import asyncio

from telebot.types import Message
from telebot.states.sync.context import StateContext

from loader import bot

from api.shiki import (
    seasons_ongoing,
    latest_anime,
    random_anime_list,
    controlled_random_anime_list,
)

from keyboards.inline.inline_kbs import (
    kb_list,
    info_add_kb_row,
    shikimori_user_rates_kb,
)

from keyboards.reply.reply_kbs import home_menu

from ..utils.format_for_handlers import (
    list_of_titles,
    one_title_view,
    posters_messages_menu,
)
from ..utils.loggers import log_message

from states.browse_states import MenuStates

from database.utils.repo import get_anime_search


def show_default_menu(msg: Message, state: StateContext):
    """Отправляет пользователю главное меню (Reply-клавиатура с основными разделами).

    Также удаляет предыдущее меню, если было, чтобы не дублировать.
    """
    default_menu_msg = bot.send_message(
        msg.chat.id, "Основное меню:", reply_markup=home_menu()
    )

    log_message(msg.chat.id, msg.text)

    with state.data() as data:
        default_menu_msg_prev = data.setdefault("default_menu_msg", [])
        if default_menu_msg_prev:
            bot.delete_message(msg.chat.id, default_menu_msg_prev)
    state.add_data(default_menu_msg=default_menu_msg.message_id)


@bot.message_handler(state=None, commands=["menu"])
def default_menu(msg: Message, state: StateContext):
    """Обработчик команды /menu. Отображает основное меню (как при /start)."""
    show_default_menu(msg, state)
    with state.data() as data:
        default_menu_command_msg_prev = data.get("default_menu_command_msg")
        if default_menu_command_msg_prev:
            bot.delete_message(msg.chat.id, default_menu_command_msg_prev)
    state.add_data(default_menu_command_msg=msg.message_id)


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("📺"),
)
def animes_of_season(msg: Message, state: StateContext):
    """Обрабатывает нажатие кнопки 📺 (Аниме сезона). Показывает список онгоингов текущего сезона."""
    anime_of_season_list = asyncio.run(seasons_ongoing(quality=True))
    posters_messages_menu(
        msg.chat.id, state, "seasons", anime_of_season_list, msg.message_id
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("seasons:continue"),
)
def animes_of_season_continue(call, state: StateContext):
    """Обрабатывает нажатие кнопки "Далее" для списка сезона, отправляет следующую страницу."""
    posters_messages_menu(call.message.chat.id, state, "seasons")


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("🔥"),
)
def latest_animes(msg: Message, state: StateContext):
    """Обрабатывает нажатие кнопки 🔥 (Недавно вышедшее). Показывает список новейших вышедших аниме."""
    latest_animes_list = asyncio.run(latest_anime(quality=True))
    posters_messages_menu(
        msg.chat.id, state, "latest", latest_animes_list, msg.message_id
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("latest:continue"),
)
def latest_animes_continue(call, state: StateContext):
    """Обрабатывает нажатие кнопки "Далее" для недавно вышедших, отправляет следующую страницу"""
    posters_messages_menu(call.message.chat.id, state, "latest")


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("🎲"),
)
def control_random(msg: Message, state: StateContext):
    """Обрабатывает нажатие кнопки 🎲 (Мне повезёт). Выдает сбалансированную подборку случайных аниме."""
    anime_random_lst = asyncio.run(controlled_random_anime_list(quality=True))
    shuffle(anime_random_lst)
    posters_messages_menu(
        msg.chat.id, state, "random", anime_random_lst, msg.message_id
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("random:continue"),
)
def control_random_continue(call, state: StateContext):
    """Обрабатывает нажатие кнопки "Далее" для случайной подборки, отправляет следующую страницу.

    p.s. Вывод спика случайного аниме ограничевается 10 тайтлами на запрос,
    по этому сейчас эта функция не применяется.
    """
    anime_random_lst: list = asyncio.run(controlled_random_anime_list(quality=True))
    shuffle(anime_random_lst)
    posters_messages_menu(call.message.chat.id, state, "random", anime_random_lst)


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("🕓"),
)
def search_history(msg: Message, state: StateContext):
    """Обрабатывает кнопку 🕓 (История). Отправляет список последних аниме с которым пользователь взаимодействовал."""
    anime_history_list = get_anime_search(msg.chat.id)

    titles = list_of_titles(anime_history_list)
    sent = bot.send_message(
        msg.chat.id,
        text=msg.text,
        reply_markup=kb_list(titles[:5], scrollable=True),
    )

    # Удаляем старую клавиатуру если пользователь запросил новую
    with state.data() as data:
        last_kb_list = data.get("last_kb_list")
        if last_kb_list:
            bot.delete_message(msg.chat.id, last_kb_list)
    # Удаляем сообщение запроса, чтобы не засорять чат
    bot.delete_message(msg.chat.id, msg.message_id)

    titles_by_id = {str(t["id"]): t for t in anime_history_list}
    # Сохраняем в FSM
    state.add_data(
        titles=titles,
        titles_by_id=titles_by_id,
        offset=0,
        last_kb_list=sent.message_id,
    )


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: m.text.startswith("🌐"),
)
def shikimori_lists(msg: Message, state: StateContext):
    """Обрабатывает кнопку 🌐 (Shikimori). Выводит меню выбора списка пользователя (смотрю/просмотрено/запланировано/отложено)."""
    bot.send_message(
        msg.chat.id, text="🌐 Shikimori:", reply_markup=shikimori_user_rates_kb()
    )
    bot.delete_message(msg.chat.id, msg.message_id)


def random_anime(msg: Message, state: StateContext):
    """Случайное аниме(сейчас не используется)"""
    anime_list = asyncio.run(random_anime_list())
    lucky_random = max(anime_list, key=lambda anime: anime["score"])
    anime_id = lucky_random.get("id")
    total_ep = int(lucky_random.get("episodesAired"))
    if total_ep == 0:
        total_ep = int(lucky_random.get("episodes"))

    poster, head = one_title_view(lucky_random)
    bot.send_photo(
        chat_id=msg.chat.id,
        photo=poster,
        caption=head,
        reply_markup=info_add_kb_row(anime_id, total_ep),
        parse_mode="HTML",
    )
