from loader import bot
import handlers  # noqa
from utils.set_bot_commands import set_default_commands
from utils.ngrok import start_ngrok
from utils.flask import start_flask
from config_data.config import init_ngrok_and_shiki_client, IS_NGROK
from database.utils.token_refresher import start_token_refresher

import telebot
import logging

telebot.logger.setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)


if __name__ == "__main__":
    start_flask()
    if IS_NGROK:
        start_ngrok()
        init_ngrok_and_shiki_client()  # конфигурация для NGROK_REDIRECT_URI

    set_default_commands(bot)
    start_token_refresher()
    bot.infinity_polling()
