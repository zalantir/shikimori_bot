import asyncio

from telebot.states.sync import StateContext
from telebot.types import Message, InputMediaPhoto, CallbackQuery
from loader import bot
from api.shiki import title_info, get_similar_anime
from database.utils.repo import save_anime_search
from handlers.utils.format_for_handlers import (
    one_title_view,
    get_description,
    posters_messages_menu,
    user_info_one_title_view,
)
from keyboards.inline.inline_kbs import info_add_kb_row, title_info_kb
from states.browse_states import MenuStates


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("browse:ref:"),
)
def title_view(call: CallbackQuery, state: StateContext):
    """Справка по тайтлу (отображение информации о выбранном аниме)."""
    chat_id = call.message.chat.id
    anime_id = call.data.split(":")[2]
    print(anime_id)
    with state.data() as data:
        title_by_id = data["titles_by_id"].get(anime_id)
        print(title_by_id)
    status = title_by_id.get("status")
    if status == "released":
        total_ep = int(title_by_id.get("episodes"))
    else:
        total_ep = int(title_by_id.get("episodesAired"))
    poster, head = one_title_view(title_by_id)
    bot.send_photo(
        chat_id=chat_id,
        photo=poster,
        caption=head,
        reply_markup=info_add_kb_row(anime_id, total_ep),
        parse_mode="HTML",
    )
    state.add_data(anime_id=anime_id)
    # сохраняем в историю поиска
    save_anime_search(chat_id, anime_id, title_by_id)


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("info"),
)
def title_view_menu(call, state: StateContext):
    """Вызывает inline-клавиатуру для отображения подробностей о тайтле."""
    chat_id = call.message.chat.id
    anime_id = call.data.split(":")[1]
    total_ep = call.data.split(":")[2]
    title_by_id = asyncio.run(title_info(anime_id, quality=True))
    old_caption = call.message.caption
    new_caption = user_info_one_title_view(old_caption, title_by_id)
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=new_caption,
        parse_mode="HTML",
    )
    bot.edit_message_reply_markup(
        chat_id, call.message.message_id, reply_markup=title_info_kb(anime_id, total_ep)
    )

    with state.data() as data:
        poster_msg_ids = data.get("poster_msg_ids")
        if poster_msg_ids:
            poster_msg_ids.remove(call.message.message_id)

    state.add_data(
        frames_description_videos=title_by_id,
        anime_id=anime_id,
    )
    # сохраняем в историю поиска
    save_anime_search(chat_id, anime_id, title_by_id)


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("title:back:"),
)
def back_to_title_vew(call: CallbackQuery, state: StateContext):
    """Возвращается к исходному просмотру информации о тайтле."""
    anime_id = call.data.split(":")[2]
    total_ep = call.data.split(":")[3]
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=info_add_kb_row(anime_id, total_ep),
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("title:frames:"),
)
def view_frames(call: CallbackQuery, state: StateContext):
    """Отправляет кадры (скриншоты) пользователю."""
    with state.data() as data:
        title = data.get("frames_description_videos")
    screenshots = title.get("screenshots")

    media = []
    for screenshot in screenshots[:10]:
        media.append(InputMediaPhoto(screenshot))
    bot.send_media_group(
        chat_id=call.message.chat.id,
        media=media,
        reply_to_message_id=call.message.message_id,
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("title:description:"),
)
def view_description(call: CallbackQuery, state: StateContext):
    """Отправляет описание пользователю."""
    with state.data() as data:
        title = data.get("frames_description_videos")
    description = title.get("description")
    description = get_description(description)
    bot.send_message(
        chat_id=call.message.chat.id,
        text=description,
        reply_to_message_id=call.message.message_id,
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("title:trailer:"),
)
def view_trailer(call: CallbackQuery, state: StateContext):
    """Отправляет трейлер пользователю."""
    with state.data() as data:
        title = data.get("frames_description_videos")
    videos = title.get("videos")
    print(videos)
    trailer = "Трейлер отсутствует"
    for video in videos:
        if video.get("kind") == "pv":
            trailer = video.get("url")
            break
    bot.send_message(
        call.message.chat.id, text=trailer, reply_to_message_id=call.message.message_id
    )


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("title:similar:"),
)
def view_similar(call: CallbackQuery, state: StateContext):
    """Отправляет похожие тайтлы пользователю."""
    anime_id = call.data.split(":")[2]
    with state.data() as data:
        continue_msg_prev = data.get("continue_msg_prev")
        if continue_msg_prev:
            bot.delete_message(call.message.chat.id, continue_msg_prev)
    similar_anime = asyncio.run(get_similar_anime(anime_id, quality=True))

    posters_messages_menu(call.message.chat.id, state, "similar_anime", similar_anime)


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: call.data.startswith("similar_anime:continue"),
)
def view_similar_continue(call: CallbackQuery, state: StateContext):
    """Продолжает выводить список похожих тайтлов."""
    posters_messages_menu(call.message.chat.id, state, "similar_anime")


@bot.message_handler(state=MenuStates.default, commands=["clear"])
def clear(msg: Message, state: StateContext):
    """Очищает ранее отправленные ботом сообщения с постерами аниме(и связанными с ними меню), в которых пользователь не заинтересовался.

    p.s. В данный момент это все постеры, вызванные не callback_data == (ref, edit, info)
    """
    with state.data() as data:
        poster_msg_ids = data.setdefault("poster_msg_ids", [])
        if poster_msg_ids:
            bot.delete_messages(msg.chat.id, poster_msg_ids)
            poster_msg_ids.clear()

        clear_command_msg_prev = data.get("clear_command_msg")
        if clear_command_msg_prev:
            bot.delete_message(msg.chat.id, clear_command_msg_prev)
    state.add_data(clear_command_msg=msg.message_id)
