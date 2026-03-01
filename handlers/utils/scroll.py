from telebot.types import CallbackQuery
from telebot.states.sync.context import StateContext

from loader import bot
from states.browse_states import MenuStates
from keyboards.inline.inline_kbs import kb_list


@bot.callback_query_handler(
    state=MenuStates.default,
    func=lambda call: (call.data.startswith("scroll:")),
)
def scroll_handler(call: CallbackQuery, state: StateContext):
    """Обрабатывает скроллинг списка (вперёд/назад) на клавиатуре."""
    chat_id = call.message.chat.id
    action = call.data.split(":")[1]  # "next" или "prev"
    with state.data() as data:
        titles = data.get("titles")
        offset = data.get("offset")
    if action == "next":
        if offset + 5 < len(titles):
            offset += 5
        else:
            bot.answer_callback_query(call.id, "Это конец списка.")
            return
    elif action == "prev":
        if offset - 5 >= 0:
            offset -= 5
        else:
            bot.answer_callback_query(call.id, "Это начало списка.")
            return

    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=kb_list(titles[offset : offset + 5], scrollable=True),
    )

    state.add_data(offset=offset)
