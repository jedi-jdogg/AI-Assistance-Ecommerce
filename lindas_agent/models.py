"""Plain data models shared across the agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Variant:
    variant_id: str
    product_id: str
    product_title: str
    variant_title: str
    sku: str
    vendor: str
    price: float
    compare_at_price: Optional[float]
    unit_cost: Optional[float]
    inventory_quantity: int          # summed across locations
    inventory_policy: str            # DENY | CONTINUE
    tracked: bool
    tags: list[str] = field(default_factory=list)
    status: str = "ACTIVE"
    # trailing-window performance (filled by ranking)
    net_sales_90d: float = 0.0
    units_90d: int = 0
    units_30d: int = 0
    units_14d: int = 0
    units_prev_14d: int = 0
    rank: Optional[int] = None

    @property
    def display(self) -> str:
        vt = "" if self.variant_title in ("", "Default Title") else f" / {self.variant_title}"
        return f"{self.product_title}{vt}"

    @property
    def daily_velocity(self) -> float:
        return self.units_30d / 30.0

    @property
    def days_of_cover(self) -> Optional[float]:
        if self.inventory_quantity < 0:
            return None
        if self.daily_velocity <= 0:
            return float("inf")
        return self.inventory_quantity / self.daily_velocity

    @property
    def gross_margin_pct(self) -> Optional[float]:
        if self.unit_cost is None or self.price <= 0:
            return None
        return (self.price - self.unit_cost) / self.price

    @property
    def is_preorder(self) -> bool:
        return self.inventory_policy.upper() == "CONTINUE" or any(t.lower() in ("pre-order", "preorder") for t in self.tags)


@dataclass
class DailySales:
    day: date
    orders: int
    total_sales: float
    net_sales: float
    gross_sales: float = 0.0
    discounts: float = 0.0
    reversals: float = 0.0
    cogs: Optional[float] = None
    aov: float = 0.0


@dataclass
class DailyFunnel:
    day: date
    sessions: int
    atc_sessions: int
    checkout_sessions: int
    completed_sessions: int

    @property
    def cvr(self) -> float:
        return self.completed_sessions / self.sessions if self.sessions else 0.0

    @property
    def atc_rate(self) -> float:
        return self.atc_sessions / self.sessions if self.sessions else 0.0

    @property
    def checkout_completion(self) -> float:
        return self.completed_sessions / self.checkout_sessions if self.checkout_sessions else 0.0


@dataclass
class Alert:
    key: str                      # stable id for de-duplication
    severity: Severity
    category: str                 # stock | preorder | funnel | pricing | marketing | forecast
    title: str
    detail: str
    action: str                   # what a human or automation should do
    automation: str = "manual"    # auto | semi | manual
    entity: Optional[str] = None  # variant id / product id / metric name

    def as_line(self) -> str:
        icon = {"critical": "🔴", "warning": "🟠", "info": "🔵"}[self.severity.value]
        return f"{icon} [{self.category}] {self.title} — {self.detail} → {self.action}"


@dataclass
class Recommendation:
    category: str                 # purchasing | pricing | marketing | traffic | conversion
    title: str
    rationale: str
    expected_impact: str
    automation: str = "semi"
    payload: dict = field(default_factory=dict)
