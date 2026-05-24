from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from src.models import ProductWatch

logger = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self._token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    @property
    def configured(self) -> bool:
        return bool(self._token and self._chat_id)

    def send_test_message(self) -> bool:
        if not self.configured:
            return False
        now = datetime.now(MADRID).strftime("%Y-%m-%d %H:%M %Z")
        text = (
            "✅ <b>Panini monitor — test message</b>\n"
            "Telegram is configured correctly.\n"
            f"Checked: {now}"
        )
        return self._send(text)

    def send_buyable_alert(self, watch: ProductWatch, reason: str) -> bool:
        if not self.configured:
            return False
        now = datetime.now(MADRID).strftime("%Y-%m-%d %H:%M %Z")
        text = (
            "🟢 <b>Panini alert — BUYABLE</b>\n"
            f"<b>{_escape(watch.label)}</b>\n"
            f"Store: {_escape(watch.store)}\n"
            f"{_escape(reason)}\n"
            f'<a href="{watch.url}">{_escape(watch.url)}</a>\n'
            f"Checked: {now}"
        )
        return self._send(text)

    def _send(self, text: str) -> bool:
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            logger.debug("Telegram API error: %s", exc.response.text)
            return False
        except httpx.HTTPError:
            return False


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
