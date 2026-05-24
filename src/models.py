from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StockStatus(str, Enum):
    BUYABLE = "buyable"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProductWatch:
    id: str
    store: str
    label: str
    url: str
    enabled: bool = True


@dataclass(frozen=True)
class CheckResult:
    status: StockStatus
    reason: str
