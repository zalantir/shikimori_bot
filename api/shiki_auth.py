from urllib.parse import urlencode
import asyncio
from config_data import config as cfg
from shikimori import Shikimori


def build_auth_url(state: str) -> str:
    """Формирует URL для OAuth-авторизации на Shikimori.

    :param state: Произвольная строка состояния (в данном проекте это Telegram chat_id).
    :return: Полный URL для перенаправления пользователя на страницу авторизации Shikimori.
    """

    params = {
        "client_id": cfg.SHIKI_CLIENT_ID,
        "redirect_uri": cfg.SHIKI_REDIRECT_URI,
        "response_type": "code",
        "scope": "user_rates",
        "state": state,
    }

    return cfg.SHIKI_AUTH_BASE + "?" + urlencode(params)


def exchange_code_for_token(code: str) -> dict:
    """Обменивает код подтверждения на токен доступа и обновления.

    :param code: Authorization code, полученный от Shikimori после OAuth.
    :return: Словарь с 'access_token', 'refresh_token' и 'expires_in' (в секундах).
    """
    client = cfg.SHIKI_CLIENT  # создаём клиента с нашими параметрами
    token = asyncio.run(client.auth.get_access_token(code))
    return {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "expires_in": int(token.expires_in),
    }


async def refresh_access_token(refresh_token: str) -> dict:
    """Обновляет токен доступа по refresh-токену.

    :param refresh_token: Действующий refresh-токен.
    :return: Новый словарь с 'access_token', 'refresh_token' и 'expires_in'.
    """
    client: Shikimori = cfg.SHIKI_CLIENT  # новый клиент с той же конфигурацией
    fresh = await client.auth.refresh(refresh_token)
    return {
        "access_token": fresh.access_token,
        "refresh_token": fresh.refresh_token,
        "expires_in": int(fresh.expires_in),
    }


def whoami(access_token: str) -> dict:
    """Получает информацию о текущем пользователе Shikimori по токену.

    :param access_token: Токен доступа пользователя.
    :return: Словарь с id и nickname пользователя на Shikimori.
    """
    client = cfg.SHIKI_CLIENT  # берём базовый клиент
    # подставляем access_token (после этого запросы защищённых эндпоинтов разрешены
    client.set_token(access_token)
    me = asyncio.run(client.user.whoami())  # вызываем whoami (async → sync)
    # Возвращаем компактный словарь:
    return {"id": int(me.id), "nickname": me.nickname}
