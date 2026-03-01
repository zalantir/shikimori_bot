from telebot.types import Message
from telebot.states.sync.context import StateContext
from loader import bot
from handlers.custom_handlers.menu_interaction import show_default_menu
from database.common.extended_search_models import UserSearchPrefs

welcome_msg = """
Добро пожаловать в ShikimoriBot – бота для поиска аниме и ведения списка просмотров.

📋 Введите название аниме для поиска или нажмите одну из кнопок меню ниже.

🔑 Если хотите связать свой аккаунт Shikimori и управлять списками через бота – используйте команду /login.

ℹ️ Для справки и списка команд введите /help."""


@bot.message_handler(state=None, commands=["start"])
def bot_start(msg: Message, state: StateContext):
    """Обработчик команды /start. Приветствует пользователя и отображает главное меню.

    Также инициализирует записи пользователя в базе (создает пустые настройки поиска) и удаляет предыдущие приветствия для чистоты чата.
    """
    bot_start_msg = bot.send_message(
        msg.chat.id, f"Привет, {msg.from_user.full_name}! {welcome_msg}"
    )
    show_default_menu(msg, state)
    # Нужно для корректной работы всех параметров через ForeignKeyField в моделях для расширенного поиска
    UserSearchPrefs.get_or_create(chat_id=msg.chat.id)
    with state.data() as data:
        bot_start_msg_prev = data.get("bot_start_msg")
        start_command_msg_prev = data.get("start_command_msg")
        if bot_start_msg_prev:
            bot.delete_message(msg.chat.id, bot_start_msg_prev)
            bot.delete_message(msg.chat.id, start_command_msg_prev)
    state.add_data(
        bot_start_msg=bot_start_msg.message_id, start_command_msg=msg.message_id
    )
