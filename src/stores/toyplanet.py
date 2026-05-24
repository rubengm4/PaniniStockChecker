from __future__ import annotations

import re

from src.models import CheckResult, StockStatus
from src.stores.base import fetch_html_with_fallback


def check_toyplanet(url: str, html: str | None = None) -> CheckResult:
    page_html, note = fetch_html_with_fallback(url, html=html)
    if page_html is None:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Failed to fetch page ({note})",
        )

    avail = re.search(r'"available"\s*:\s*(true|false)', page_html, re.I)
    if avail:
        if avail.group(1).lower() == "true":
            return CheckResult(StockStatus.BUYABLE, "available (Shopify)")
        return CheckResult(StockStatus.UNAVAILABLE, "sold out (Shopify)")

    if re.search(
        r'id="AddToCart"[^>]*class="[^"]*sold-out[^"]*"[^>]*disabled',
        page_html,
        re.I,
    ) or re.search(r"badge out-of-stock", page_html, re.I):
        return CheckResult(StockStatus.UNAVAILABLE, "agotado")

    if re.search(
        r'id="AddToCart"[^>]*class="[^"]*single-add-to-cart-button[^"]*"[^>]*>(?!.*disabled)',
        page_html,
        re.I,
    ):
        if "sold-out" not in page_html[page_html.find('id="AddToCart"'): page_html.find('id="AddToCart"') + 200]:
            return CheckResult(StockStatus.BUYABLE, "add to cart enabled")

    return CheckResult(StockStatus.UNKNOWN, f"could not parse Toy Planet page [{note}]")
