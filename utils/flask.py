from threading import Thread
from api.flask_callback import app  # сам Flask-приложение


def start_flask() -> None:
    """Запускает Flask-сервер в отдельном потоке."""

    def run():
        # Flask слушает локально, ngrok пробрасывает наружу
        app.run(host="127.0.0.1", port=5000)

    Thread(
        target=run, daemon=True
    ).start()  # передаём функцию как объект для запуска в потоке
