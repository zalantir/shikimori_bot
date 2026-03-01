def sort_in_chunks(items: list[dict], chunk_size: int = 10) -> list[dict]:
    """Сортирует список словарей по ключу 'score' внутри чанков заданного размера.

    Попытка лучше отсортировать результаты чем это делает сам Shikimori для компактного отображения
    """
    result = []
    for i in range(0, len(items), chunk_size):
        chunk = items[i : i + chunk_size]
        # сортируем внутри блока
        sorted_chunk = sorted(
            chunk,
            key=lambda t: (t["score"] is None, t["score"] or 0),  # None в конец
            reverse=True,  # убывание
        )
        result.extend(sorted_chunk)
    return result
