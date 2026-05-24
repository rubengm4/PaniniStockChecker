from __future__ import annotations

from src.models import CheckResult, ProductWatch, StockStatus
from src.stores.amazon_es import check_amazon_es
from src.stores.el_corte_ingles import check_el_corte_ingles
from src.stores.juguettos import check_juguettos
from src.stores.panini_magento import check_panini_magento
from src.stores.paninistore import check_paninistore
from src.stores.toyplanet import check_toyplanet

STORE_HANDLERS = {
    "panini_es": check_panini_magento,
    "paninistore": check_paninistore,
    "amazon_es": check_amazon_es,
    "eci": check_el_corte_ingles,
    "juguettos": check_juguettos,
    "toyplanet": check_toyplanet,
}


def check_watch(watch: ProductWatch, html: str | None = None) -> CheckResult:
    handler = STORE_HANDLERS.get(watch.store)
    if handler is None:
        return CheckResult(
            status=StockStatus.UNKNOWN,
            reason=f"Unknown store: {watch.store}",
        )
    return handler(watch.url, html=html)
