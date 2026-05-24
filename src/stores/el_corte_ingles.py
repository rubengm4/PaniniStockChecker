from __future__ import annotations

import re

from src.models import CheckResult, StockStatus
from src.stores.base import fetch_html_with_fallback


def check_el_corte_ingles(url: str, html: str | None = None) -> CheckResult:
    page_html, note = fetch_html_with_fallback(url, html=html)
    if page_html is None:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Failed to fetch page ({note})",
        )

    lower = page_html.lower()
    if "access denied" in lower or len(page_html) < 1000:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason="ECI blocked request — checks may work from your Mac, not all cloud IPs",
        )

    if re.search(r"\bAGOTADO\b", page_html):
        if not re.search(r"añadir a la cesta", page_html, re.I):
            return CheckResult(StockStatus.UNAVAILABLE, "AGOTADO")
        return CheckResult(StockStatus.UNAVAILABLE, "AGOTADO")

    if re.search(r"no disponible online|sin stock online", page_html, re.I):
        return CheckResult(StockStatus.UNAVAILABLE, "no disponible online")

    if re.search(r"añadir a la cesta", page_html, re.I):
        if re.search(
            r'<button[^>]*(disabled|aria-disabled=["\']true["\'])',
            page_html,
            re.I,
        ):
            return CheckResult(StockStatus.UNAVAILABLE, "add button disabled")
        return CheckResult(StockStatus.BUYABLE, "añadir a la cesta")

    unavailable_phrases = ["agotado", "no disponible", "sin stock"]
    for phrase in unavailable_phrases:
        if phrase in lower:
            return CheckResult(StockStatus.UNAVAILABLE, phrase)

    return CheckResult(StockStatus.UNKNOWN, f"could not parse ECI page [{note}]")
