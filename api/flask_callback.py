import time
import asyncio
from flask import Flask, request, abort, redirect, Response
from database.utils.repo import shiki_token_save, get_token, NotAuthorizedError
from api.shiki_auth import exchange_code_for_token, whoami
from config_data.config import BOT_USERNAME


app = Flask(__name__)

# простой кэш с TTL
_processed = {}  # key: (tg_user_id, code)


def mark_processed(key, ttl=300):
    """Отметить ключ как обработанный на ttl секунд."""
    _processed[key] = int(time.time()) + ttl


def already_processed(key):
    """Проверить, не истёк ли TTL и есть ли ключ."""
    now = int(time.time())
    exp = _processed.get(key)
    if exp and exp > now:
        return True
    # удаляем просроченные записи
    for k, v in list(_processed.items()):
        if v < now:
            _processed.pop(k, None)
    return False


@app.get("/shiki/callback")
def shiki_callback() -> Response:
    """Обрабатывает OAuth-callback Shikimori: обменивает код на токены и сохраняет их в БД."""
    # получаем code,state
    code = request.args.get("code")
    tg_user_id = request.args.get("state")

    if not code:
        return abort(400)
    try:
        tg_user_id_int = int(tg_user_id)
    except ValueError:
        return abort(400)
    key = (tg_user_id_int, code)
    # если уже обрабатывали этот (пользователь, code) — просто редиректим
    if already_processed(key):
        return redirect(f"tg://resolve?domain={BOT_USERNAME}", code=302)
        # если уже есть рабочий токен — не обмениваем code повторно
    try:
        asyncio.run(get_token(tg_user_id_int))
        mark_processed(key)
        return redirect(f"tg://resolve?domain={BOT_USERNAME}", code=302)
    except NotAuthorizedError:
        pass  # токена нет — будем обменивать
    except Exception:
        pass  # хз, пока работает
    # меняем code -> токены
    token = exchange_code_for_token(code)
    access_token = token["access_token"]
    refresh_token = token["refresh_token"]
    expires_at = int(time.time()) + int(token.get("expires_in", 3600)) - 30

    # получаем id пользователя Shikimori
    me = whoami(access_token)
    shiki_user_id = int(me["id"])
    shiki_user_name = me["nickname"]
    # делаем запись в БД
    shiki_token_save(tg_user_id, shiki_user_id, access_token, refresh_token, expires_at)

    print(f"Получен запрос от {shiki_user_name}")

    return redirect(f"tg://resolve?domain={BOT_USERNAME}", code=302)
