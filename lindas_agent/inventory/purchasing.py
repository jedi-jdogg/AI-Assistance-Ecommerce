"""Purchasing recommendations: reorder point + order-up-to quantity, planned for growth.

reorder_point = demand_per_day * (lead_time + review_period) + safety_stock
safety_stock  = z * sigma_daily * sqrt(lead_time + review_period)
order_qty     = max(0, demand_per_day * growth * target_cover_days - on_hand - on_order)
                rounded up to vendor MOQ / case pack.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..config import Settings
from ..models import Recommendation, Variant


@dataclass
class PurchaseLine:
    variant: Variant
    reorder_point: float
    order_qty: int
    est_cost: float
    days_cover_after: float
    urgency: str  # now | this_week | plan

    def as_row(self) -> str:
        return (
            f"| #{self.variant.rank} | {self.variant.display[:60]} | {self.variant.vendor} | "
            f"{self.variant.inventory_quantity} | {self.variant.daily_velocity:.1f} | {self.reorder_point:.0f} | "
            f"{self.order_qty} | ${self.est_cost:,.0f} | {self.urgency} |"
        )


def _sigma_daily(v: Variant) -> float:
    """Approximate daily demand std-dev from 14d vs prev 14d windows; floor at Poisson."""
    d30 = v.daily_velocity
    a = v.units_14d / 14.0
    b = v.units_prev_14d / 14.0
    spread = abs(a - b) / 2.0
    return max(spread, math.sqrt(max(d30, 0.01)))


def purchase_plan(ranked: list[Variant], settings: Settings, on_order: dict[str, int] | None = None, top_n: int = 500) -> list[PurchaseLine]:
    on_order = on_order or {}
    z = float(settings.get("purchasing.service_level_z", 1.65))
    review = int(settings.get("purchasing.review_period_days", 7))
    cover_target = int(settings.get("purchasing.target_cover_days", 45))
    growth = float(settings.get("purchasing.growth_factor", 1.10))
    lines: list[PurchaseLine] = []

    for v in ranked:
        if v.rank is None or v.rank > top_n or v.daily_velocity <= 0:
            continue
        if v.inventory_quantity < 0:
            continue  # untracked feed; purchasing is a vendor conversation, not a formula
        rule = settings.vendor(v.vendor)
        horizon = rule.lead_time_days + review
        d = v.daily_velocity * growth
        safety = z * _sigma_daily(v) * math.sqrt(horizon)
        rop = d * horizon + safety
        position = v.inventory_quantity + on_order.get(v.variant_id, 0)
        if position > rop:
            continue
        qty = d * cover_target - position
        qty = max(qty, rule.moq_units)
        if rule.case_pack > 1:
            qty = math.ceil(qty / rule.case_pack) * rule.case_pack
        qty_int = int(math.ceil(qty))
        cost = (v.unit_cost or v.price * 0.6) * qty_int
        if cost < float(settings.get("purchasing.min_order_value", 0)) and v.rank > 100:
            continue
        cover_now = v.days_of_cover or 0
        urgency = "now" if cover_now <= rule.lead_time_days else ("this_week" if cover_now <= horizon else "plan")
        lines.append(
            PurchaseLine(
                variant=v,
                reorder_point=rop,
                order_qty=qty_int,
                est_cost=cost,
                days_cover_after=(position + qty_int) / d if d else 0,
                urgency=urgency,
            )
        )
    order = {"now": 0, "this_week": 1, "plan": 2}
    lines.sort(key=lambda ln: (order[ln.urgency], ln.variant.rank or 9999))
    return lines


def purchase_recommendations(lines: list[PurchaseLine]) -> list[Recommendation]:
    by_vendor: dict[str, list[PurchaseLine]] = {}
    for ln in lines:
        by_vendor.setdefault(ln.variant.vendor, []).append(ln)
    recs: list[Recommendation] = []
    for vendor, ls in sorted(by_vendor.items(), key=lambda kv: -sum(x.est_cost for x in kv[1])):
        total = sum(x.est_cost for x in ls)
        now = [x for x in ls if x.urgency == "now"]
        recs.append(
            Recommendation(
                category="purchasing",
                title=f"PO to {vendor}: {len(ls)} SKUs, ~${total:,.0f}",
                rationale=f"{len(now)} SKUs are at/below lead-time cover; top item {ls[0].variant.display[:50]}",
                expected_impact="Protects revenue on ranked sellers; every stock-out day on a top-100 SKU is lost sales",
                automation="semi",
                payload={"vendor": vendor, "lines": [(x.variant.sku or x.variant.variant_id, x.order_qty) for x in ls]},
            )
        )
    return recs
