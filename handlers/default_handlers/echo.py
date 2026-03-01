from telebot.types import Message

from loader import bot

from ..utils.loggers import log_message


# Эхо хендлер, куда летят текстовые сообщения без указанного состояния
@bot.message_handler(state=None)
def bot_echo(msg: Message):
    bot.reply_to(msg, "Эхо без состояния или фильтра.\n" f"Сообщение: {msg.text}")
    log_message(msg.chat.id, msg.text)
