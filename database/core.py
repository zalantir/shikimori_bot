from playhouse.sqlite_ext import (
    SqliteExtDatabase,
)  # У peewee-пакета нет нормальных .pyi-стабов для подмодуля playhouse.sqlite_ext.
from database.common.models import (
    db_proxy,
    History,
    ShikiToken,
    UserAnime,
)
from database.common.extended_search_models import (
    UserSearchPrefs,
    UserSearchGenre,
    UserSearchType,
    UserSeasonToken,
    UserSearchStatuses,
)


def init_db(path: str = "test.db"):
    """Подключает прокси к реальной базе и создаёт таблицы."""
    db = SqliteExtDatabase(
        path,
        pragmas={"journal_mode": "wal", "foreign_keys": 1},
        timeout=10,
        check_same_thread=False,
    )
    db_proxy.initialize(db)
    db.connect(reuse_if_open=True)
    db.create_tables(
        [
            History,
            ShikiToken,
            UserAnime,
            UserSearchPrefs,
            UserSearchGenre,
            UserSearchType,
            UserSeasonToken,
            UserSearchStatuses,
        ],
        safe=True,
    )
    return db
