from __future__ import annotations

import re

from src.models import CheckResult, StockStatus
from src.stores.base import fetch_html_with_fallback


def check_amazon_es(url: str, html: str | None = None) -> CheckResult:
    page_html, note = fetch_html_with_fallback(url, html=html)
    if page_html is None:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Failed to fetch page ({note})",
        )

    # Block / captcha detection
    if "captcha" in page_html.lower() or "robot check" in page_html.lower():
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason="Amazon blocked or CAPTCHA — try from home IP",
        )

    lower = page_html.lower()

    unavailable_phrases = [
        "no disponible",
        "temporalmente agotado",
        "actualmente no disponible",
        "no se puede enviar",
    ]
    for phrase in unavailable_phrases:
        if phrase in lower:
            return CheckResult(StockStatus.UNAVAILABLE, phrase)

    # Pre-order without buy now
    if "pedido anticipado" in lower or "pre-order" in lower:
        if not _amazon_buyable(page_html):
            return CheckResult(StockStatus.UNAVAILABLE, "pre-order only")

    if _amazon_buyable(page_html):
        return CheckResult(StockStatus.BUYABLE, "buy box available")

    if re.search(r"id=['\"]availability['\"]", page_html, re.I):
        return CheckResult(StockStatus.UNAVAILABLE, "availability indicates no stock")

    return CheckResult(StockStatus.UNKNOWN, f"could not parse Amazon page [{note}]")


def _amazon_buyable(html: str) -> bool:
    if re.search(r'id=["\']add-to-cart-button["\']', html, re.I):
        if re.search(r"añadir a la cesta|add to cart|comprar ya", html, re.I):
            if not re.search(r"disabled", html[:50000], re.I):
                return True
    if re.search(
        r"availability.*?(en stock|disponible)",
        html,
        re.I | re.DOTALL,
    ):
        return True
    return False
