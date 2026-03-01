import os
from dotenv import load_dotenv, find_dotenv
from shikimori.client import Shikimori

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

# конфиги бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "FastShikimoriBot"

DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("help", "Вывести справку"),
    ("menu", "Главное меню"),
    ("clear", "Очистить"),
    ("login", "Авторизация"),
)

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
NGROK_REDIRECT_URI = os.getenv("NGROK_REDIRECT_URI") or None
SHIKI_REDIRECT_URI = os.getenv("SHIKI_REDIRECT_URI") or NGROK_REDIRECT_URI

SHIKI_AUTH_BASE = "https://shikimori.one/oauth/authorize"


def redirect_uri() -> str:
    """ленивая дёргалка SHIKI_REDIRECT_URI (сейчас не используется)"""
    return os.getenv("SHIKI_REDIRECT_URI") or os.getenv("NGROK_REDIRECT_URI")


SHIKI_CLIENT_NAME = "MyShikiTestApp/1.0"
SHIKI_CLIENT_ID = os.getenv("SHIKI_CLIENT_ID")
SHIKI_CLIENT_SECRET = os.getenv("SHIKI_CLIENT_SECRET")

SHIKI_CLIENT = Shikimori(
    user_agent=SHIKI_CLIENT_NAME,
    client_id=SHIKI_CLIENT_ID,
    client_secret=SHIKI_CLIENT_SECRET,
    redirect_uri=SHIKI_REDIRECT_URI,
    raise_on_error=True,
    logging=True,
)

IS_NGROK = False  # Флаг запуска NGROK


def init_ngrok_and_shiki_client() -> None:
    """Инициализирует OAuth-клиент Shikimori с актуальным redirect_uri после запуска ngrok.
    :raises RuntimeError: если переменная окружения NGROK_REDIRECT_URI не установлена.
    """
    global SHIKI_CLIENT
    global NGROK_REDIRECT_URI
    global SHIKI_REDIRECT_URI
    NGROK_REDIRECT_URI = os.getenv("NGROK_REDIRECT_URI")
    if not NGROK_REDIRECT_URI:
        raise RuntimeError("Сначала вызови start_ngrok()")
    SHIKI_REDIRECT_URI = NGROK_REDIRECT_URI
    SHIKI_CLIENT = Shikimori(
        user_agent=SHIKI_CLIENT_NAME,
        client_id=SHIKI_CLIENT_ID,
        client_secret=SHIKI_CLIENT_SECRET,
        redirect_uri=SHIKI_REDIRECT_URI,
        raise_on_error=True,
        logging=True,
    )


# Постер на случай отсутствия постера у тайтла
DEFAULT_POSTER = r"C:\Users\Pupa_i_Lupa\PycharmProjects\shikimori\utils\misc\main.png"
# Перевод статусов для пользователя
STATUS_RU = {
    "watching": "Смотрю",
    "planned": "В планах",
    "completed": "Просмотрено",
    "on_hold": "Отложено",
    "dropped": "Брошено",
}
# ====== ЖАНРЫ ======
GENRES = [
    # популярные сверху
    ("1", "Экшен"),
    ("10", "Фэнтези"),
    ("22", "Романтика"),
    ("4", "Комедия"),
    ("8", "Драма"),
    ("24", "Фантастика"),
    ("2", "Приключения"),
    ("36", "Повседневность"),
    ("117", "Триллер"),
    ("7", "Тайна"),
    ("14", "Ужасы"),
    ("37", "Сверхъестественное"),
    ("30", "Спорт"),
    # остальные
    ("133", "Сёнен-ай"),
    ("129", "Сёдзё-ай"),
    ("9", "Этти"),
    ("543", "Гурман"),
    ("5", "Авангард"),
]

# ====== ТЕМЫ ======
THEMES = [
    ("198", "Злодейка"),
    ("197", "Городское фэнтези"),
    ("134", "Забота о детях"),
    ("20", "Пародия"),
    ("142", "Исполнительское искусство"),
    ("148", "Питомцы"),
    ("135", "Магическая смена пола"),
    ("143", "Антропоморфизм"),
    ("102", "Командный спорт"),
    ("107", "Любовный многоугольник"),
    ("38", "Военное"),
    ("32", "Вампиры"),
    ("145", "Идолы (Жен.)"),
    ("150", "Идолы (Муж.)"),
    ("40", "Психологическое"),
    ("141", "Выживание"),
    ("106", "Реинкарнация"),
    ("144", "Кроссдрессинг"),
    ("119", "CGDCT"),
    ("147", "Медицина"),
    ("17", "Боевые искусства"),
    ("18", "Меха"),
    ("21", "Самураи"),
    ("23", "Школа"),
    ("29", "Космос"),
    ("35", "Гарем"),
    ("125", "Реверс-гарем"),
    ("151", "Романтический подтекст"),
    ("31", "Супер сила"),
    ("13", "Исторический"),
    ("3", "Гонки"),
    ("124", "Махо-сёдзё"),
    ("103", "Видеоигры"),
    ("149", "Образовательное"),
    ("139", "Работа"),
    ("136", "Шоу-бизнес"),
    ("114", "Удостоено наград"),
    ("105", "Жестокость"),
    ("140", "Иясикэй"),
    ("19", "Музыка"),
    ("112", "Гэг-юмор"),
    ("146", "Игра с высокими ставками"),
    ("6", "Мифология"),
    ("118", "Спортивные единоборства"),
    ("137", "Культура отаку"),
    ("111", "Путешествие во времени"),
    ("104", "Взрослые персонажи"),
    ("39", "Детектив"),
    ("11", "Стратегические игры"),
    ("108", "Изобразительное искусство"),
    ("138", "Организованная преступность"),
    ("131", "Хулиганы"),
    ("130", "Исэкай"),
]

# ====== АУДИТОРИЯ ======
DEMOGRAPHICS = [
    ("27", "Сёнен"),
    ("25", "Сёдзё"),
    ("42", "Сэйнэн"),
    ("43", "Дзёсей"),
    ("15", "Детское"),
]

# ====== Сортировка ======
SORT = [
    ("RANKED", "По рейтингу"),
    ("POPULARITY", "По популярности"),
    ("AIRED_ON", "По дате выхода"),
    ("RANDOM", "Случайно"),
    ("NAME", "По алфавиту"),
]

# ====== Оценка ======
SCORE = [
    (8, "8+"),
    (7, "7+"),
    (6, "6+"),
]

# ====== Тип аниме ======
KIND = [
    ("tv", "Сериал"),
    ("tv_13", "Короткий сериал"),
    ("tv_24", "Средний сериал"),
    ("tv_48", "Длинный сериал"),
    ("movie", "Фильм"),
    ("ova", "OVA"),
    ("ona", "ONA"),
]

# ====== Статус аниме ======
ANIME_STATUS = [
    ("anons", "Анонсировано"),
    ("ongoing", "Сейчас выходит"),
    ("released", "Вышедшее"),
]
