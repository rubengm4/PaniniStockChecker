from __future__ import annotations

from src.models import CheckResult
from src.stores.base import magento_main_product_check


def check_paninistore(url: str, html: str | None = None) -> CheckResult:
    from src.stores.base import fetch_html_with_fallback

    page_html, note = fetch_html_with_fallback(url, html=html)
    if page_html is None:
        from src.models import StockStatus

        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Failed to fetch page ({note})",
        )
    result = magento_main_product_check(page_html, "paninistore.com")
    if result.reason.startswith("could not"):
        return CheckResult(result.status, f"{result.reason} [{note}]")
    return result
