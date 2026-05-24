from __future__ import annotations

import logging
import time

from dotenv import load_dotenv

from src.config import load_watchlist, state_db_path
from src.models import StockStatus
from src.notifier.telegram import TelegramNotifier
from src.state import StateStore
from src.stores import check_watch

logger = logging.getLogger(__name__)

REQUEST_DELAY_SEC = 2.5


def run_check(*, dry_run: bool = False) -> int:
    load_dotenv()
    watches = load_watchlist()
    if not watches:
        logger.warning("No watches configured in watchlist.yaml")
        return 0

    store = StateStore(state_db_path())
    notifier = TelegramNotifier()
    alerts_sent = 0

    try:
        for index, watch in enumerate(watches):
            if index > 0:
                time.sleep(REQUEST_DELAY_SEC)

            result = check_watch(watch)
            previous = store.get(watch.id)
            store.set(watch.id, result.status, result.reason)

            logger.info(
                "%s [%s] -> %s (%s)",
                watch.id,
                watch.store,
                result.status.value,
                result.reason,
            )

            if (
                not dry_run
                and result.status == StockStatus.BUYABLE
                and previous != StockStatus.BUYABLE
            ):
                if notifier.configured:
                    if notifier.send_buyable_alert(watch, result.reason):
                        alerts_sent += 1
                        logger.info("Telegram alert sent for %s", watch.id)
                    else:
                        logger.error("Failed to send Telegram alert for %s", watch.id)
                else:
                    logger.warning(
                        "BUYABLE %s but Telegram not configured (set TELEGRAM_* in .env)",
                        watch.id,
                    )
    finally:
        store.close()

    return alerts_sent


def test_telegram() -> bool:
    load_dotenv()
    notifier = TelegramNotifier()
    if not notifier.configured:
        logger.error(
            "Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
        return False
    if notifier.send_test_message():
        logger.info("Test message sent — check your Telegram chat")
        return True
    logger.error("Failed to send test message — check token, chat id, and that you /start the bot")
    return False


def list_status() -> None:
    load_dotenv()
    watches = load_watchlist()
    store = StateStore(state_db_path())
    try:
        for watch in watches:
            detail = store.get_detail(watch.id)
            if detail:
                print(
                    f"{watch.id:40} {detail['status']:12} {detail['checked_at']}  {watch.label}"
                )
            else:
                print(f"{watch.id:40} {'(never)':12} {'—':25}  {watch.label}")
            print(f"  {watch.url}")
    finally:
        store.close()
