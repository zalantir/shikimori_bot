from functools import wraps
from database.common.models import db_proxy as db
from typing import Callable


def context_connection(func: Callable) -> Callable:
    """Открывает контекстное подключение на время вызова функции"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with db.connection_context():
            return func(*args, **kwargs)

    return wrapper
