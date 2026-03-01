import peewee as pw
from database.common.models import BaseModel


class UserSearchPrefs(BaseModel):
    """Одиночные настройки пользователя для расширенного поиска"""

    chat_id = pw.IntegerField(primary_key=True)  # уникальный id пользователя
    min_score = pw.IntegerField(null=True)  # оценка 1..10, либо None
    sort = pw.CharField(default="RANKED")  # строка сортировки


class UserSearchGenre(BaseModel):
    """Выбранные жанры для поиска, ссылается на UserSearchPrefs"""

    chat_id = pw.ForeignKeyField(
        UserSearchPrefs, to_field="chat_id", backref="genres", on_delete="CASCADE"
    )
    genre_id = pw.CharField()

    class Meta:
        primary_key = pw.CompositeKey("chat_id", "genre_id")


class UserSearchType(BaseModel):
    """Выбранные типы аниме ('tv', 'movie', ...)."""

    chat_id = pw.ForeignKeyField(
        UserSearchPrefs, to_field="chat_id", backref="types", on_delete="CASCADE"
    )
    kind = pw.CharField()  # текстовое значение типа

    class Meta:
        primary_key = pw.CompositeKey("chat_id", "kind")


class UserSeasonToken(BaseModel):
    chat_id = pw.ForeignKeyField(
        UserSearchPrefs, to_field="chat_id", backref="seasons", on_delete="CASCADE"
    )
    season = pw.CharField()

    class Meta:
        primary_key = pw.CompositeKey("chat_id", "season")


class UserSearchStatuses(BaseModel):
    chat_id = pw.ForeignKeyField(
        UserSearchPrefs, to_field="chat_id", backref="statuses", on_delete="CASCADE"
    )
    status = pw.CharField(null=True)

    class Meta:
        primary_key = pw.CompositeKey("chat_id", "status")
