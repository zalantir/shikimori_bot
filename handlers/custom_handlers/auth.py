from telebot.states.sync import StateContext
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from loader import bot
from api.shiki_auth import build_auth_url
from states.browse_states import MenuStates


@bot.message_handler(state=MenuStates.default, commands=["login"])
def login(msg: Message, state: StateContext):
    """Обработчик команды /login. Отправляет пользователю кнопку для OAuth2-авторизации на Shikimori."""
    auth_url = build_auth_url(str(msg.chat.id))

    kb = InlineKeyboardMarkup()  # инлайн-клавиатура
    kb.add(InlineKeyboardButton("🔑 Войти через Shikimori", url=auth_url))

    login_msg = bot.send_message(
        msg.chat.id,
        f"Чтобы связать ваш аккаунт Shikimori с ботом, Нажмите кнопку ниже(или перейдите по <a href='{auth_url}'>ссылке</a>) и дайте разрешение",
        reply_markup=kb,
        parse_mode="HTML",
    )
    with state.data() as data:
        login_msg_prev = data.setdefault("login_msg", [])
        login_command_msg_prev = data.get("login_command_msg")
        if login_msg_prev:
            bot.delete_message(msg.chat.id, login_msg_prev)
            bot.delete_message(msg.chat.id, login_command_msg_prev)
    state.add_data(login_msg=login_msg.message_id, login_command_msg=msg.message_id)


"""Для работы с вашим аккаунтом Shikimori нужна авторизация.
Нажмите кнопку ниже, чтобы войти и разрешить доступ."""
