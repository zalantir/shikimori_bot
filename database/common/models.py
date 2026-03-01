from playhouse.sqlite_ext import JSONField
import time
import peewee as pw

# ─────────────────────────────────────────────────────────────────────────────
# DatabaseProxy — «заглушка» вместо реальной БД.
# Мы инициализируем её позже (init_db), чтобы не прибивать путь к файлу «насмерть»
# и удобно подменять БД на тестовую.
db_proxy = pw.DatabaseProxy()
# ─────────────────────────────────────────────────────────────────────────────


class BaseModel(pw.Model):
    """Базовая модель, чтобы всем наследникам автоматически подставлялась БД."""

    class Meta:  # class Meta - интерпретируется самим ORM как контейнер для настроек
        database = db_proxy  # <- сюда init_db подставит настоящий SqliteDatabase
        legacy_table_names = False  # автоматически конвертирует CamelCase → snake_case.


class History(BaseModel):
    """
    История. Сейчас:
    - сохранять исходный текст запроса пользователя
    """

    created_at = pw.IntegerField(default=time.time)
    chat_id = pw.IntegerField(index=True)  # id пользователя
    message = pw.TextField(null=False)  # сообщение пользователя

    class Meta:
        """индексирование для запросов «история по чату в хронологическом порядке»"""

        indexes = (
            (("chat_id", "created_at"), False),  # ← именно двойные скобки вокруг полей
        )


class ShikiToken(BaseModel):
    tg_user_id = pw.IntegerField(unique=True)  # ID чата/пользователя Telegram
    shiki_user_id = pw.IntegerField(null=True)  # ID пользователя Shikimori (из /whoami)
    access_token = pw.TextField()
    refresh_token = pw.TextField()
    expires_at = pw.IntegerField()  # unix-время истечения access_token


class UserAnime(BaseModel):
    """
    Список аниме конкретного пользователя Telegram.
    Уникальная пара: (chat_id, anime_id).
    """

    # --- Ключи ---
    chat_id = pw.BigIntegerField()  # ID пользователя (из Telegram)
    anime_id = pw.IntegerField()  # ID аниме (из Shikimori)

    # --- Основная информация ---
    anime_data = JSONField(default=dict)  # Список видео {name,url,kind}

    # --- Время добавления/обновления ---
    seen_at = pw.IntegerField(default=lambda: int(time.time()))
    """
    Unix timestamp (int), когда запись была создана/обновлена.
    Используем для сортировки: последние сверху.
    """

    class Meta:
        indexes = (
            (("chat_id", "anime_id"), True),  # уникальный составной
            (("chat_id", "seen_at"), False),  # для быстрой истории по пользователю
        )
