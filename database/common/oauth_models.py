from .models import BaseModel
from peewee import *

# 1) Подключаемся к той же базе, что у тебя в корне: test.db
db = SqliteDatabase("test.db")


class ShikiToken(BaseModel):
    tg_user_id = IntegerField(unique=True)  # ID чата/пользователя Telegram
    shiki_user_id = IntegerField(null=True)  # ID пользователя Shikimori (из /whoami)
    access_token = TextField()
    refresh_token = TextField()
    expires_at = IntegerField()  # unix-время истечения access_token
