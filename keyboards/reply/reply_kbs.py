from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def home_menu() -> ReplyKeyboardMarkup:
    """Reply-клавиатура главного меню."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📺 Аниме сезона"), KeyboardButton("🎲 Мне повезёт"))
    kb.row(
        KeyboardButton("🔥 Недавно вышедшее"), KeyboardButton("🔎 Расширенный поиск")
    )
    kb.row(KeyboardButton("🕓 История"), KeyboardButton("🌐 Shikimori"))
    return kb


def kb_status_pult():
    """Reply-клавиатура для редактирования статуса тайтла (Устаревшее)."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📅 Запланировано"), KeyboardButton("👀 Просмотрено"))
    kb.row(KeyboardButton("▶️ Смотрю"), KeyboardButton("#️⃣ Просмотрено серий"))
    kb.row(
        KeyboardButton("Выйти"),
        KeyboardButton("📌 сохранить"),
        KeyboardButton("➕ серия"),
    )
    return kb


def title_info_menu():
    """Reply-клавиатура с дополнительной информацией по выбранному тайтлу (Устаревшее)."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📷 Кадры"), KeyboardButton("📖 Описание"))
    kb.row(KeyboardButton("🎬 Трейлер"), KeyboardButton("🔗 Похожее"))
    return kb
