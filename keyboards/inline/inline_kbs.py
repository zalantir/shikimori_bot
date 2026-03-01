from math import ceil
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_list(
    lines: list[tuple[str, str]], scrollable: bool = False
) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру со списком тайтлов"""
    kb = InlineKeyboardMarkup()
    for text, ref in lines:
        kb.add(InlineKeyboardButton(text=text, callback_data=f"browse:ref:{ref}"))
    if scrollable:
        kb.row(
            InlineKeyboardButton("⬅️", callback_data="scroll:prev"),
            InlineKeyboardButton("➡️", callback_data="scroll:next"),
        )
    return kb


def info_add_kb_row(anime_id: int, total_ep: int) -> InlineKeyboardMarkup:
    """Возвращает инлайн-клавиатуру с кнопками Инфо и Статус для указанного тайтла."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("🔍 Инфо", callback_data=f"info:{anime_id}:{total_ep}"),
        InlineKeyboardButton("✅ Статус", callback_data=f"edit:{anime_id}:{total_ep}"),
    )
    return kb


def title_info_kb(anime_id: int, total_ep: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для подробной информации о тайтле (кадры, описание, трейлер, похожее)."""
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📷 Кадры", callback_data=f"title:frames:{anime_id}"),
        InlineKeyboardButton(
            "📖 Описание", callback_data=f"title:description:{anime_id}"
        ),
    )
    kb.row(
        InlineKeyboardButton(
            "Назад", callback_data=f"title:back:{anime_id}:{total_ep}"
        ),
        InlineKeyboardButton("🎬 Трейлер", callback_data=f"title:trailer:{anime_id}"),
        InlineKeyboardButton("🔗 Похожее", callback_data=f"title:similar:{anime_id}"),
    )
    return kb


def title_edit_kb(
    anime_id: int | str, total_ep: int, status: str, rate_id: str
) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для редактирования статуса тайтла в списке пользователя на Shikimori."""
    anime_id = str(anime_id)

    # заготовки кнопок статусов
    btn_planned = InlineKeyboardButton(
        "📅 Запланировано",
        callback_data=f"set:planned:{anime_id}:{total_ep}:{rate_id}",
    )
    btn_watched = InlineKeyboardButton(
        "👀 Просмотрено",
        callback_data=f"set:completed:{anime_id}:{total_ep}:{rate_id}",
    )
    btn_watching = InlineKeyboardButton(
        "▶️ Смотрю",
        callback_data=f"set:watching:{anime_id}:{total_ep}:{rate_id}",
    )

    # список в фиксированном порядке
    status_btns = [
        ("planned", btn_planned),
        ("completed", btn_watched),
        ("watching", btn_watching),
    ]

    # убираем кнопку текущего статуса, если он есть среди трёх
    status_btns = [b for key, b in status_btns if key != status]

    kb = InlineKeyboardMarkup()
    # 1-й ряд: первые две кнопки статуса
    kb.row(*status_btns[:2])

    # 2-й ряд
    episodes_btn = InlineKeyboardButton(
        "#️⃣ Серий",
        callback_data=f"acc:episodes:{anime_id}:{total_ep}:{rate_id}",
    )
    delete_btn = InlineKeyboardButton(
        "🗑 Удалить",
        callback_data=f"set:delete:{anime_id}:{total_ep}:{rate_id}",
    )
    rest = status_btns[2:]
    # выбираем текст кнопки в зависимости от того, остался ли ещё один статус в этой строке
    if rest:
        # есть ещё один статус -> статус + серий
        kb.row(*(rest + [episodes_btn]))
    else:
        # статусов больше нет -> серий + удалить
        kb.row(delete_btn, episodes_btn)

    # 3-й ряд
    kb.row(
        InlineKeyboardButton(
            "Назад", callback_data=f"title:back:{anime_id}:{total_ep}"
        ),
        InlineKeyboardButton(
            "⭐ Оценка",
            callback_data=f"acc:score:{anime_id}:{total_ep}:{rate_id}",
        ),
        InlineKeyboardButton(
            "✚ серия",
            callback_data=f"acc:plus_ep:{anime_id}:{total_ep}:{rate_id}",
        ),
    )
    return kb


def episodes_kb(
    anime_id: int, total_episodes: int, rate_id: str, page: int = 0
) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора количества эпизодов (по 16 на страницу)."""
    kb = InlineKeyboardMarkup()

    total_pages = max(1, ceil(total_episodes / 16))

    # Нормализуем номер страничцы (зацикливание)
    page = page % total_pages

    # Диапазон эпизодов для этой страницы (1..total_episodes)
    start = page * 16
    end = min(start + 16, total_episodes)

    # Собираем список номеров для текущей страницы (макс 16)
    items = list(range(start + 1, end + 1))
    n = len(items)

    # Делим на два ряда:
    # - если n чётное — поровну
    # - если n нечётное — верхний ряд на 1 больше, нижний на 1 меньше
    top_cnt = min(8, (n + 1) // 2)  # ceil(n/2), но не более 8
    bot_cnt = min(8, n - top_cnt)  # floor(n/2), но не более 8

    top = items[:top_cnt]
    bot = items[top_cnt : top_cnt + bot_cnt]

    if n > 0 and top:
        kb.row(
            *[
                InlineKeyboardButton(
                    str(x),
                    callback_data=f"ep_count:{x}:{anime_id}:{total_episodes}:{rate_id}",
                )
                for x in top
            ]
        )
    if n > 0 and bot:
        kb.row(
            *[
                InlineKeyboardButton(
                    str(x),
                    callback_data=f"ep_count:{x}:{anime_id}:{total_episodes}:{rate_id}",
                )
                for x in bot
            ]
        )
        # Навигация (зациклена) + выход
    prev_page = (page - 1) % total_pages
    next_page = (page + 1) % total_pages
    kb.row(
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"acc:episodes:{anime_id}:{total_episodes}:{rate_id}:{prev_page}",
        ),
        InlineKeyboardButton(
            "Вперёд ➡️",
            callback_data=f"acc:episodes:{anime_id}:{total_episodes}:{rate_id}:{next_page}",
        ),
    )

    return kb


def inline_kb_pult(id_list: list) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура пульта (нумерованные кнопки с прокруткой)."""
    kb = InlineKeyboardMarkup()

    row_1 = []
    for num, anime_id in enumerate(id_list[:7], start=1):
        row_1.append(InlineKeyboardButton(str(num), callback_data=str(anime_id)))
    kb.row(*row_1)

    row_2 = [InlineKeyboardButton("<", callback_data="scroll:prev")]
    for num, anime_id in enumerate(id_list[7:], start=8):
        row_2.append(InlineKeyboardButton(str(num), callback_data=str(anime_id)))
    row_2.append(InlineKeyboardButton(">", callback_data="scroll:next"))
    kb.row(*row_2)
    return kb


def shikimori_user_rates_kb() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора списка аниме пользователя Shikimori по статусу."""
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("Запланировано", callback_data="shiki:planned"))
    kb.row(InlineKeyboardButton("Смотрю", callback_data="shiki:watching"))
    kb.row(InlineKeyboardButton("Просмотрено", callback_data="shiki:completed"))
    kb.row(InlineKeyboardButton("Отложено", callback_data="shiki:on_hold"))
    return kb


def continue_kb(ns="") -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с кнопкой 'Дальше' для продолжения вывода списка."""
    kb = InlineKeyboardMarkup()
    if ns:
        ns += ":"
    kb.row(InlineKeyboardButton("Дальше", callback_data=f"{ns}continue"))
    return kb


def extended_search_kb(page: int = 1):
    """Инлайн-клавиатура основного меню расширенного поиска (две страницы)."""
    kb = InlineKeyboardMarkup()
    if page == 1:
        # каждая кнопка отдельной строкой
        kb.row(
            InlineKeyboardButton("Жанры", callback_data="genre"),
            InlineKeyboardButton("Темы", callback_data="theme"),
        )
        kb.row(InlineKeyboardButton("Статус", callback_data="status"))
        kb.row(InlineKeyboardButton("Сортировка", callback_data="order"))
        kb.row(InlineKeyboardButton("Оценка", callback_data="score"))

        # нижние кнопки
        kb.row(
            InlineKeyboardButton("Выйти", callback_data="exit"),
            InlineKeyboardButton("Поиск", callback_data="search"),
            InlineKeyboardButton("Дальше ▶", callback_data="page:2"),
        )

    elif page == 2:
        kb.row(InlineKeyboardButton("Сезоны", callback_data="seasons"))
        kb.row(InlineKeyboardButton("Тип аниме", callback_data="kind"))
        kb.row(InlineKeyboardButton("Аудитория", callback_data="demographic"))
        kb.row(
            InlineKeyboardButton("Сбросить настройки", callback_data="reset_settings")
        )

        # нижние кнопки
        kb.row(
            InlineKeyboardButton("Выйти", callback_data="cancel"),
            InlineKeyboardButton("Поиск", callback_data="search"),
            InlineKeyboardButton("◀ Назад", callback_data="page:1"),
        )

    return kb


def settings_kb_with_mark(
    items, selected, page: int = 1, rows: int = 5, cols: int = 2, ns=""
) -> InlineKeyboardMarkup:
    """
    :param items список [(id, название), ...]
    :param selected множество выбранных ключей
    :param page текущая страница
    :param rows строки
    :param cols колонки
    :param ns префикс для callback_data
    """
    # приводи всё к итерабельному виде
    if isinstance(selected, (int, str, float)):
        selected = {selected}
    elif selected is None:
        selected = set()
    # сколько всего страниц
    per_page = rows * cols
    total = len(items)
    pages = ceil(total / per_page)
    # ограничения для номера страницы
    page = max(1, min(page, pages))
    # формируем список на одну страницу
    start = (page - 1) * per_page
    end = start + per_page
    one_page = items[start:end]

    kb = InlineKeyboardMarkup(row_width=cols)

    # Создаём кнопки
    btns = []
    for item_id, label in one_page:
        mark = "[x]" if item_id in selected else "[]"
        btns.append(
            InlineKeyboardButton(
                text=f"{label} {mark}",
                callback_data=f"{ns}:toggle:{item_id}:{page}",
            )
        )
    kb.add(*btns)

    # нижняя строка: навигация + действия
    bottom = []
    if page > 1:
        bottom.append(
            InlineKeyboardButton("◀ Назад", callback_data=f"{ns}:page:{page-1}")
        )
    if page < pages:
        bottom.append(
            InlineKeyboardButton("Дальше ▶", callback_data=f"{ns}:page:{page+1}")
        )

    bottom.append(InlineKeyboardButton("Поиск", callback_data=f"search"))
    bottom.append(InlineKeyboardButton("Выйти", callback_data=f"cancel"))

    kb.row(*bottom)

    return kb


def anime_score_set_kb(anime_id, total_ep, rate_id) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура: оценки 1–10 (два ряда по 5 кнопок)."""
    kb = InlineKeyboardMarkup()
    for row_start in (1, 6):  # 1–5 и 6–10
        kb.row(
            *[
                InlineKeyboardButton(
                    str(x),
                    callback_data=f"set_score:{x}:{anime_id}:{total_ep}:{rate_id}",
                )
                for x in range(row_start, row_start + 5)
            ]
        )
    return kb
