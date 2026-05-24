from __future__ import annotations

import re

from src.models import CheckResult, StockStatus
from src.stores.base import fetch_html_with_fallback


def check_juguettos(url: str, html: str | None = None) -> CheckResult:
    page_html, note = fetch_html_with_fallback(url, html=html)
    if page_html is None:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Failed to fetch page ({note})",
        )

    avail_match = re.search(
        r'<span class="availability">(instock|outofstock)</span>',
        page_html,
        re.I,
    )
    if avail_match:
        if avail_match.group(1).lower() == "outofstock":
            if re.search(r"Disponible solo en algunas", page_html, re.I):
                return CheckResult(
                    StockStatus.UNAVAILABLE,
                    "outofstock (solo en tienda física)",
                )
            return CheckResult(StockStatus.UNAVAILABLE, "outofstock")

        if "agotado-producto" in page_html:
            return CheckResult(StockStatus.UNAVAILABLE, "agotado")

        if "box-info-product unvisible" in page_html:
            return CheckResult(StockStatus.UNAVAILABLE, "add to cart hidden")

        if re.search(
            r'id="add_to_cart"[^>]*>.*?<button[^>]*type="submit"[^>]*class="exclusive"',
            page_html,
            re.DOTALL | re.I,
        ):
            return CheckResult(StockStatus.BUYABLE, "online add to cart")

        return CheckResult(StockStatus.UNAVAILABLE, "instock flag but cannot order online")

    if "agotado-producto" in page_html:
        return CheckResult(StockStatus.UNAVAILABLE, "agotado")

    return CheckResult(StockStatus.UNKNOWN, f"could not parse Juguettos page [{note}]")
