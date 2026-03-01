import asyncio
import time
import random
import logging
import threading
from database.utils.repo import get_all_tg_user_ids, get_token

log = logging.getLogger(__name__)
logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _token_refresher_loop(interval_hours: int = 12):
    """Фоновая задача: раз в interval_hours обновляет токены Shikimori."""
    base_interval = interval_hours * 3600  # 12 часов → 43200 секунд

    while True:
        ids = get_all_tg_user_ids()
        if ids:
            for tg_user_id in ids:
                time.sleep(random.uniform(0.0, 5.0))
                try:
                    asyncio.run(get_token(tg_user_id, without_timer=True))
                except Exception as e:
                    log.exception("Error refreshing token for %s: %s", tg_user_id, e)
            log.info("Shiki tokens refreshed for %d users", len(ids))
        else:
            log.info("No users to refresh")

        # ---- добавляем джиттер (±120 секунд) ----
        jitter = random.randint(-120, 120)  # от -2 до +2 минут
        sleep_time = base_interval + jitter
        log.info(
            "Next refresh in %.2f hours (jitter %+d sec)", sleep_time / 3600, jitter
        )

        time.sleep(sleep_time)


def start_token_refresher(interval_hours: int = 12) -> threading.Thread:
    """Стартует фоновую нить-рефрешер (daemon)."""
    t = threading.Thread(
        target=_token_refresher_loop, args=(interval_hours,), daemon=True
    )
    t.start()
    return t
