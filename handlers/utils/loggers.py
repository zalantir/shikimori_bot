from database.utils.helpers import context_connection
from database.common.models import History


@context_connection
def log_message(chat_id: int, text: str):
    """Сохраняет сообщение пользователя в истории (таблица History)."""
    History.create(chat_id=chat_id, message=text)
