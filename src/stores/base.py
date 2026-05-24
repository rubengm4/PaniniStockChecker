from __future__ import annotations

import json
import re
from typing import Any

import httpx

from src.models import CheckResult, StockStatus

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30.0


def fetch_html(url: str) -> tuple[str | None, str]:
    """Return (html, fetch_note). html is None on failure."""
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"},
        ) as client:
            response = client.get(url)
            if response.status_code >= 400:
                return None, f"HTTP {response.status_code}"
            return response.text, "httpx"
    except httpx.HTTPError as exc:
        return None, f"HTTP error: {exc}"


def fetch_html_playwright(url: str) -> tuple[str | None, str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "playwright not installed"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT, locale="es-ES")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
        return html, "playwright"
    except Exception as exc:  # noqa: BLE001
        return None, f"playwright error: {exc}"


def fetch_html_with_fallback(url: str, html: str | None = None) -> tuple[str | None, str]:
    if html is not None:
        return html, "provided"
    html, note = fetch_html(url)
    if html is not None and len(html) > 500:
        return html, note
    pw_html, pw_note = fetch_html_playwright(url)
    if pw_html is not None:
        return pw_html, pw_note
    return html, note if html is None else note


def extract_json_ld_products(html: str) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for match in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Product":
                products.append(item)
            elif isinstance(item, dict) and "@graph" in item:
                for node in item["@graph"]:
                    if isinstance(node, dict) and node.get("@type") == "Product":
                        products.append(node)
    return products


def schema_availability(product: dict[str, Any]) -> str | None:
    offers = product.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        return None
    avail = offers.get("availability", "")
    if isinstance(avail, str):
        return avail.rsplit("/", 1)[-1]
    return None


def availability_to_status(availability: str | None) -> StockStatus | None:
    if not availability:
        return None
    key = availability.lower()
    if key == "instock":
        return StockStatus.BUYABLE
    if key in {"outofstock", "soldout", "discontinued"}:
        return StockStatus.UNAVAILABLE
    if key in {"preorder", "presale", "backorder"}:
        return StockStatus.UNAVAILABLE
    return None


def parse_product_availability_datalayer(html: str) -> str | None:
    match = re.search(
        r'"dataLayerProductDetail"\s*:\s*(\{[^}]+\})',
        html,
    )
    if not match:
        return None
    try:
        detail = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return detail.get("product_availability")


def main_product_stock_block(html: str) -> str | None:
    """Extract stock markup near the main product add-to-cart form."""
    form_match = re.search(
        r'id=["\']product_addtocart_form["\'][^>]*>(.*?)(?=<div[^>]+class=["\'][^"\']*block related)',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if form_match:
        return form_match.group(1)
    box_match = re.search(
        r'<div class="box-tocart">(.*?)</div>\s*</div>\s*</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    return box_match.group(1) if box_match else None


def _has_enabled_add_to_cart(block: str) -> bool:
    match = re.search(
        r'<button[^>]*id=["\']product-addtocart-button["\'][^>]*>',
        block,
        re.I,
    )
    if match:
        return "disabled" not in match.group(0).lower()
    for btn in re.finditer(
        r'<button[^>]*class=["\'][^"\']*action tocart primary[^"\']*["\'][^>]*>',
        block,
        re.I,
    ):
        if "disabled" not in btn.group(0).lower():
            return True
    return False


def _main_block_buyable(block: str) -> bool:
    if _is_preorder_block(block):
        return False
    if re.search(r'class=["\']stock unavailable["\']', block, re.I):
        return False
    return _has_enabled_add_to_cart(block)


def magento_main_product_check(html: str, store_label: str) -> CheckResult:
    block = main_product_stock_block(html) or html
    products = extract_json_ld_products(html)
    datalayer_avail = parse_product_availability_datalayer(html)

    if products:
        avail = schema_availability(products[0])
        mapped = availability_to_status(avail)
        if mapped == StockStatus.BUYABLE:
            if _main_block_buyable(block):
                return CheckResult(StockStatus.BUYABLE, f"In stock ({store_label})")
            return CheckResult(
                StockStatus.UNAVAILABLE,
                "Listed in catalog but add-to-cart disabled",
            )

        if mapped == StockStatus.UNAVAILABLE:
            reason = avail or "unavailable"
            if avail and "PreOrder" in avail:
                reason = "pre-order only"
            return CheckResult(StockStatus.UNAVAILABLE, reason)

    if datalayer_avail == "available":
        if _main_block_buyable(block):
            return CheckResult(StockStatus.BUYABLE, "Purchasable (dataLayer)")
        return CheckResult(
            StockStatus.UNAVAILABLE,
            "dataLayer available but add-to-cart disabled",
        )
    if datalayer_avail == "not_purchasable":
        return CheckResult(StockStatus.UNAVAILABLE, "not_purchasable")

    if re.search(r'class=["\']stock available["\']', block, re.I):
        if _main_block_buyable(block):
            return CheckResult(StockStatus.BUYABLE, "Add to cart available")

    if re.search(r'class=["\']stock unavailable["\']', block, re.I):
        return CheckResult(StockStatus.UNAVAILABLE, "out of stock")

    if _is_preorder_block(block):
        return CheckResult(StockStatus.UNAVAILABLE, "pre-order only")

    if re.search(r'action tocart primary', block, re.I):
        return CheckResult(
            StockStatus.UNAVAILABLE,
            "add-to-cart present but disabled",
        )

    return CheckResult(StockStatus.UNKNOWN, "could not determine stock")


def _is_preorder_block(block: str) -> bool:
    patterns = [
        r"pre-order",
        r"preorder",
        r"preventa",
        r"pre\s*order",
        r"pedido anticipado",
    ]
    lower = block.lower()
    if any(re.search(p, lower) for p in patterns):
        if re.search(r"action tocart primary", block, re.I):
            if re.search(r">\s*pre[- ]?order\s*<", block, re.I):
                return True
            if re.search(r">\s*preventa\s*<", block, re.I):
                return True
    return bool(
        re.search(r'class=["\'][^"\']*preorder', block, re.I)
        or re.search(r"button-preorder", block, re.I)
    )
