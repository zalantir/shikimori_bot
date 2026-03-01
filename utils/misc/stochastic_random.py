import random
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any

# -----------------------------
# Константы: эпохи и сезоны
# -----------------------------
EPOCHS = {
    1: (1960, 1999),  # Фундаментальная классика
    2: (2000, 2009),  # Телевизионный бум
    3: (2010, 2016),  # Цифровая глобализация
    4: (2017, 2021),  # Эра стримингов
    5: (2022, 2025),  # Современный пик
}

SEASONS = ["winter", "spring", "summer", "fall"]

# Сколько уникальных (год, сезон) берём у эпох 2..5:
BASE_COUNTS = {2: 2, 3: 2, 4: 2, 5: 2}  # потом одной из {4,5} добавим +1

# Параметры "непредсказуемости"
TEMPERATURE = 1.6  # для смягчения различий между годами (softmax-like)
NOISE_STD = 0.35  # шум для "дрожания" весов годов при каждом запуске


@dataclass(frozen=True)
class SeasonSlot:
    """Одна ячейка сезона"""

    epoch: int
    year: Optional[int] = None
    season: Optional[str] = None
    # epoch=1 используется без года/сезона (охват всей эпохи)


# Математические утилиты
def softmax(xs: List[float], tau: float = 1.0) -> List[float]:
    """softmax

    Сдвигаем все значения на самое большое значение в выборке, тогда максимальное значение exp(x-m)=exp(0) = 1. С помощью tau регулируем насколько остальные значения экспонент будут ближе/дальше к нулю

    Делим каждую экспоненту на сумму всех полученных экспонент, получая их конечные вероятности
    """
    # softmax
    m = max(xs)  # Берём максимум, это будет наш сдвиг для всех экспонент
    exps = [math.exp((x - m) / tau) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def gumbel() -> float:
    """формула генерации случайной величины для распределения Гумбеля"""
    u = random.random()  # получаем 0 или 1
    return -math.log(
        -math.log(u + 1e-12) + 1e-12
    )  # Маленькие 1e-12 нужны, чтобы не попасть в log(0) (численная защита)


def gumbel_top_k(items_with_scores: List[Tuple[Any, float]], k: int) -> List[Any]:
    """
    Распределение Гумбеля:
    Возвращает k элементов из списка[0] по их весам[1] (softmax-вероятностям).
    Добавляет дополнительный шуп в вероятности перед выбором добавляя к каждой величину Гумбеля.
    """
    keys = []
    for item, score in items_with_scores:
        keys.append((item, score + gumbel()))
    keys.sort(key=lambda t: t[1], reverse=True)
    return [item for item, _ in keys[:k]]


def pick_years_no_repeat(
    epoch: int, k: int, temperature: float, noise_std: float
) -> List[int]:
    """Выбирает k уникальных лет из заданной эпохи, с учётом softmax и шума."""
    # создаём лист из всех годов в эпохе
    y0, y1 = EPOCHS[epoch]
    years = list(range(y0, y1 + 1))
    # создаём базовые веса = 1, для всех лет в эпохе
    base = [1.0 for _ in years]
    noisy_scores = []
    """Формируем “сырые оценки” для каждого года: log(1)=0 +
    + Гауссов шум со средним в 0 и отклонением noise_std"""
    for b in base:
        noisy_scores.append(math.log(b) + random.gauss(0, noise_std))

    # Превращаем оценки в вероятности через softmax
    probs = softmax(noisy_scores, tau=temperature)
    # Берём логарифмы вероятностей для устойчивой работы трюка Гумбеля
    items_with_scores = list(zip(years, [math.log(p + 1e-12) for p in probs]))
    picked = gumbel_top_k(items_with_scores, k)

    return picked


def pick_unique_year_seasons(
    epoch: int, k: int, temperature: float, noise_std: float
) -> List[Tuple[int, str]]:
    """Вернёт k уникальных пар (год, сезон) для заданной эпохи."""
    # возвращаем k разных лет указанной эпохи, с учётом softmax и шумов
    years = pick_years_no_repeat(epoch, k, temperature, noise_std)
    result = []
    # присваиваем сезоны полученным годам
    for y in years:
        s = random.choice(SEASONS)
        result.append((y, s))
    return result


# Построение 10 исходных слотов
def build_10_slots():
    """Формирует 10 "слотов" (эпоха+год+сезон)"""
    # Копируем базовые квоты и случайно решаем, у кого 3 штуки — у эпохи 4 или 5
    counts = dict(BASE_COUNTS)
    boosted_epoch = random.choice([4, 5])
    counts[boosted_epoch] += 1  # теперь одна из (4/5) имеет 3, другая 2

    # Создаём пустой список слотов
    slots: List[SeasonSlot] = []

    # добавляем эпоху 1
    slots.append(SeasonSlot(epoch=1, year=None, season=None))

    # 2–5 эпохи: Собираем уникальные (год, сезон) по квотам
    for ep in [2, 3, 4, 5]:
        k = counts[ep]
        years_seasons = pick_unique_year_seasons(ep, k, TEMPERATURE, NOISE_STD)
        for year, season in years_seasons:
            slots.append(SeasonSlot(epoch=ep, year=year, season=season))

    return slots


# Парное перемешивание и отбор 5 слотов
def pair_and_pick(slots: List[SeasonSlot]) -> List[SeasonSlot]:
    """Перемешивает 10 слотов и случайным образом выбирает из каждой пары один слот (итого 5)."""
    # Тасуем 10 слотов как колоду карт
    random.shuffle(slots)
    # разбивает список на пары: [(slot0,slot1),(slot2,slot3)...]
    pairs = [slots[i : i + 2] for i in range(0, len(slots), 2)]
    # из каждой пары выбираем один случайный слот.
    winners = [random.choice(p) for p in pairs]
    return winners


# Пайплайн
def build_final_5_slots() -> List[SeasonSlot]:
    """Формирует итоговые 5 слотов: собирает 10, затем попарно сокращает до 5."""
    ten = build_10_slots()
    five = pair_and_pick(ten)
    return five
