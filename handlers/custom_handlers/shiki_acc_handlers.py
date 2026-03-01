from telebot.types import CallbackQuery
import asyncio
from loader import bot
from states.browse_states import MenuStates
import api.shiki_acc_interaction as acc

from telebot.states.sync.context import StateContext
from keyboards.inline.inline_kbs import (
    title_edit_kb,
    episodes_kb,
    anime_score_set_kb,
)
from handlers.utils.format_for_handlers import (
    user_edit_one_title_view,
    posters_messages_menu,
)
from database.utils.repo import NotAuthorizedError


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("edit"),
)
def edit_rate(call: CallbackQuery, state: StateContext):
    """Обрабатывает нажатие кнопки ✅ (Статус) под аниме.

    Отправляет reply-клавиатуру с вариантами действий (смена статуса, изменение оценки, кол-ва эпизодов).
    """
    chat_id = call.message.chat.id
    anime_id = int(call.data.split(":")[1])
    total_ep = int(call.data.split(":")[2])
    try:
        status, episodes, score, rate_id = asyncio.run(
            acc.user_anime_info(chat_id, anime_id)
        )
    except NotAuthorizedError:
        bot.answer_callback_query(
            call.id,
            "⚠️ Вы не авторизованы.",
        )
        return
    old_caption = call.message.caption

    new_caption = user_edit_one_title_view(
        old_caption, status, episodes, total_ep, score
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        caption_entities=call.message.caption_entities,
    )
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=title_edit_kb(anime_id, total_ep, status, rate_id),
    )

    with state.data() as data:
        # исключения id сообщения из списка для /clear
        poster_msg_ids = data.get("poster_msg_ids")
        if poster_msg_ids:
            poster_msg_ids.remove(call.message.message_id)


def _set_status_and_notify(
    call: CallbackQuery, anime_id: str, status_str: str, total_ep: int, rate_id: str
):
    """Вспомогательная функция для смены статуса аниме в списке и обновления сообщения.

    Вызывает API для изменения статуса (или удаления, если status_str=="delete"), затем обновляет сообщение с новым статусом.
    """
    _, status, episodes, score, rate_id = asyncio.run(
        acc.anime_status_set(
            chat_id=call.message.chat.id,
            anime_id=anime_id,
            status=status_str,
            rate_id=rate_id,
        )
    )
    old_caption = call.message.caption
    new_caption = user_edit_one_title_view(
        old_caption, status, episodes, total_ep, score
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        caption_entities=call.message.caption_entities,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=title_edit_kb(anime_id, total_ep, status, rate_id),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("set:"),
)
def status_set(call: CallbackQuery, state: StateContext):
    """Обрабатывает выбор нового статуса для аниме.

    Парсит из call.data статус, anime_id, total_ep, rate_id и обновляет статус записи на Shikimori.
    """
    status = call.data.split(":")[1]
    anime_id = int(call.data.split(":")[2])
    total_ep = int(call.data.split(":")[3])
    rate_id = call.data.split(":")[4]
    _set_status_and_notify(call, anime_id, status, total_ep, rate_id)


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("acc:score:"),
)
def score_menu(call: CallbackQuery, state: StateContext):
    """Обрабатывает нажатие кнопки ⭐ (Оценка).

    Показывает inline-клавиатуру с вариантами оценки 1-10 для выбранного тайтла.
    """
    anime_id = int(call.data.split(":")[2])
    total_ep = int(call.data.split(":")[3])
    rate_id = call.data.split(":")[4]
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=anime_score_set_kb(anime_id, total_ep, rate_id),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("set_score"),
)
def score_set(call: CallbackQuery, state: StateContext):
    """Обрабатывает выбор конкретной оценки из клавиатуры.

    Парсит выбранную оценку и обновляет её через API, затем обновляет сообщение с новой оценкой.
    """
    chat_id = call.message.chat.id
    score = int(call.data.split(":")[1])
    anime_id = int(call.data.split(":")[2])
    total_ep = int(call.data.split(":")[3])
    rate_id = call.data.split(":")[4]
    status, episodes, score, rate_id = asyncio.run(
        acc.set_anime_score(chat_id, anime_id, score, rate_id)
    )
    old_caption = call.message.caption
    new_caption = user_edit_one_title_view(
        old_caption, status, episodes, total_ep, score
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        caption_entities=call.message.caption_entities,
    )
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=title_edit_kb(anime_id, total_ep, status, rate_id),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("acc:episodes:"),
)
def episodes_watched(call: CallbackQuery, state: StateContext):
    """Обрабатывает нажатие кнопки #️⃣ (Серий).

    Отображает клавиатуру для выбора количества эпизодов (постранично, если их много).
    """
    parts = call.data.split(":")
    print(parts)
    anime_id = parts[2]
    total_ep = int(parts[3])
    rate_id = parts[4]
    page = int(parts[5]) if len(parts) > 5 else 0
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=episodes_kb(anime_id, total_ep, rate_id, page),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("ep_count:"),
)
def episodes_watched_menu(call: CallbackQuery, state: StateContext):
    """Обрабатывает выбор конкретного числа эпизодов.

    Парсит число эпизодов из call.data, обновляет записанное количество через API и обновляет сообщение.
    """
    chat_id = call.message.chat.id
    count = call.data.split(":")[1]
    anime_id = int(call.data.split(":")[2])
    total_ep = int(call.data.split(":")[3])
    rate_id = call.data.split(":")[4]
    status, episodes, score = asyncio.run(
        acc.episodes_watched(chat_id, anime_id, count, rate_id)
    )
    old_caption = call.message.caption
    new_caption = user_edit_one_title_view(
        old_caption, status, episodes, total_ep, score
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        caption_entities=call.message.caption_entities,
    )
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=title_edit_kb(anime_id, total_ep, status, rate_id),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("acc:plus_ep:"),
)
def plus_episode(call: CallbackQuery, state: StateContext):
    """Обрабатывает нажатие кнопки ✚ (серия).

    Увеличивает число просмотренных эпизодов на 1 через API и обновляет информацию в сообщении.
    """
    chat_id = call.message.chat.id
    anime_id = int(call.data.split(":")[2])
    total_ep = int(call.data.split(":")[3])
    rate_id = call.data.split(":")[4]
    status, episodes, score, rate_id = asyncio.run(
        acc.another_one_episode(chat_id, anime_id, rate_id)
    )
    old_caption = call.message.caption
    new_caption = user_edit_one_title_view(
        old_caption, status, episodes, total_ep, score
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        caption_entities=call.message.caption_entities,
    )
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=title_edit_kb(anime_id, total_ep, status, rate_id),
    )


@bot.callback_query_handler(
    state=MenuStates.default, func=lambda call: call.data.startswith("shiki")
)
def shikimori_lists_show(call: CallbackQuery, state: StateContext):
    """Обрабатывает выбор конкретного списка (watching/completed/planned/on_hold) из меню Shikimori.

    Загружает соответствующий список пользователя через API и выводит его (постранично с кнопкой "Далее").
    """

    action = call.data.split(":")[1]  # watching, completed, planned, on_hold
    titles_list = asyncio.run(acc.user_anime_list(call.message.chat.id, action))
    posters_messages_menu(
        call.message.chat.id,
        state,
        "shikimori_lists",
        titles_list,
        call.message.message_id,
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("shikimori_lists:continue"),
)
def shikimori_lists_show_continue(call: CallbackQuery, state: StateContext):
    """Продолжает вывод списка аниме пользователя (Shikimori) на следующей странице."""

    posters_messages_menu(call.message.chat.id, state, "shikimori_lists")
