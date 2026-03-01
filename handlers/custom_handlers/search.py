import asyncio
from telebot.types import Message
from telebot.states.sync.context import StateContext

from loader import bot

from api.shiki import search_by_title
from keyboards.inline.inline_kbs import kb_list
from ..utils.format_for_handlers import list_of_titles
from ..utils.loggers import log_message
from ..utils.sorting import sort_in_chunks
from states.browse_states import MenuStates


@bot.message_handler(
    state=MenuStates.default,
    content_types=["text"],
    func=lambda m: not m.text.startswith("/"),
)
def default_search(msg: Message, state: StateContext):
    """Поиск по умолчанию. Любой введенный текст (не команда) в главном меню трактуется как поисковой запрос.

    Бот выполняет поиск аниме по введенному тексту и выводит результаты списком с кнопками.
    Предыдущие результаты (если были) очищаются из чата для удобства.
    """

    form_msg = msg.text.strip()  # Удалить пробелы в начале и конце
    titles_by_id = {}
    titles = []
    titles_list = asyncio.run(search_by_title(form_msg, quality=True))
    if not titles_list:
        sent = bot.send_message(
            msg.chat.id,
            f"По запросу '{form_msg}' ничего не найдено",
        )
    else:
        titles_list = sort_in_chunks(titles_list)
        titles_by_id = {t["id"]: t for t in titles_list}
        titles = list_of_titles(titles_list)
        sent = bot.send_message(
            msg.chat.id,
            text=form_msg,
            reply_markup=kb_list(titles[:5], scrollable=True),
        )

    """Удаляем старую клавиатуру если пользователь запросил новую"""
    with state.data() as data:
        last_kb_list = data.get("last_kb_list")
        if last_kb_list:
            bot.delete_message(msg.chat.id, last_kb_list)
    """Удаляем сообщение запроса, чтобы не засорять чат"""
    bot.delete_message(msg.chat.id, msg.message_id)

    # Сохраняем в FSM
    state.add_data(
        titles_by_id=titles_by_id,
        titles=titles,
        offset=0,
        query=form_msg,
        last_kb_list=sent.message_id,
    )

    log_message(msg.chat.id, msg.text)
