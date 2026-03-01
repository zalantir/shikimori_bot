from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS
from loader import bot

from ..utils.loggers import log_message
from telebot.states.sync.context import StateContext


@bot.message_handler(state=None, commands=["help"])
def bot_help(msg: Message, state: StateContext):
    """Обработчик команды /help. Выводит список доступных команд и их описание."""

    text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    help_msg = bot.reply_to(msg, "\n".join(text))

    with state.data() as data:
        help_msg_prev = data.setdefault("help_msg", [])
        help_command_msg_prev = data.get("help_command_msg")
        if help_msg_prev:
            bot.delete_message(msg.chat.id, help_msg_prev)
            bot.delete_message(msg.chat.id, help_command_msg_prev)
    state.add_data(help_msg=help_msg.message_id, help_command_msg=msg.message_id)
    log_message(msg.chat.id, msg.text)
