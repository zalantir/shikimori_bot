from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from telebot.states.sync.middleware import StateMiddleware
from telebot import custom_filters

from config_data import config
from database.core import init_db

init_db("test.db")


storage = StateMemoryStorage()
bot = TeleBot(token=config.BOT_TOKEN, state_storage=storage, use_class_middlewares=True)

bot.setup_middleware(StateMiddleware(bot))
bot.add_custom_filter(custom_filters.StateFilter(bot))
