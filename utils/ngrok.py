import os
from pyngrok import ngrok, conf
from config_data.config import NGROK_AUTHTOKEN


def start_ngrok() -> None:
    """Запускает ngrok-туннель для локального Flask-сервера и устанавливает NGROK_REDIRECT_URI.

    Подключается к локальному порту 5000 и получает публичный URL от ngrok.
    Устанавливает переменную окружения NGROK_REDIRECT_URI вида "https://<id>.ngrok.io/shiki/callback".
    :raises SystemExit: если NGROK_AUTHTOKEN не указан или не удалось получить URL."""
    if not NGROK_AUTHTOKEN:
        raise SystemExit("Отсутствует NGROK_AUTHTOKEN. Проверь в .env")

    conf.get_default().region = "eu"
    conf.get_default().auth_token = NGROK_AUTHTOKEN
    # поднимаем туннель к локальному Flask на 5000
    ngrok.connect(5000, "http")
    public_url = None
    for t in ngrok.get_tunnels():
        if t.public_url.startswith("https://"):
            public_url = t.public_url
            break
    if not public_url:
        raise SystemExit("Не получили https-URL от ngrok")

    redirect_uri = f"{public_url}/shiki/callback"
    os.environ["NGROK_REDIRECT_URI"] = redirect_uri

    print("NGROK PUBLIC URL:", public_url)
    print("REDIRECT_URI:", redirect_uri)
    print("‼ Обнови redirect_uri в настройках приложения Shikimori на этот адрес.")
