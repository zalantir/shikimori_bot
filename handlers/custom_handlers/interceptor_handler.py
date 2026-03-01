from loader import bot
from telebot.types import Message, CallbackQuery
from telebot.states.sync.context import StateContext
from states.browse_states import MenuStates


@bot.message_handler(state=[None], content_types=["text"])
def catch_any_text(msg: Message, state: StateContext):
    """
    Перехватывает любые текстовые сообщения без состояния.
    Можно определить, куда их дальше отправить.
    """

    state.set(MenuStates.default)
    bot.process_new_messages([msg])


@bot.callback_query_handler(state=[None], func=lambda c: True)
def catch_any_callback(call: CallbackQuery, state: StateContext):
    """
    Перехватывает любые callback'и без состояния.
    Ставит состояние и переотправляет событие, чтобы сработали
    обычные хендлеры для MenuStates.default.
    """
    state.set(MenuStates.default)
    # Не отвечаем здесь на callback, чтобы это сделал целевой хендлер.
    bot.process_new_callback_query([call])
