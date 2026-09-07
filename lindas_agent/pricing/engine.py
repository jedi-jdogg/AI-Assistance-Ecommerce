"""Supply/demand pricing engine.

Signals per variant:
  demand_growth = units_14d / units_prev_14d - 1
  days_cover    = on_hand / daily_velocity
Rules (config/agent.yaml -> pricing):
  RAISE  when scarce (cover < 14d) and demand rising (> +15%) and not MAP -> +3% (max 5%/week)
  LOWER  when overstocked (cover > 180d) and demand falling (< -10%)      -> -10%, respecting margin floor
  Bundles are preferred over markdown when margin is already thin.
Never touches products tagged 'MAP Pricing'. Never breaches min_gross_margin_pct.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config import Settings
from ..models import Variant


@dataclass
class PriceProposal:
    variant: Variant
    direction: str            # up | down | bundle
    old_price: float
    new_price: float
    reason: str
    automation: str           # auto | semi

    @property
    def change_pct(self) -> float:
        return (self.new_price - self.old_price) / self.old_price if self.old_price else 0.0

    def as_row(self) -> str:
        return (
            f"| #{self.variant.rank} | {self.variant.display[:55]} | {self.direction} | ${self.old_price:.2f} | "
            f"${self.new_price:.2f} | {self.change_pct:+.1%} | {self.reason} | {self.automation} |"
        )


def _charm(p: float) -> float:
    """Charm-price to x.99 like the catalog does (179.99); under $10 keep cents."""
    if p >= 10:
        return float(int(p)) + 0.99 if (p - int(p)) >= 0.5 else float(int(p)) - 0.01
    return round(p, 2)


def _round_price(p: float, old: float, direction: str) -> float:
    """Charm-round without undoing the direction of the move (a +3% on $12.00 must not land on $11.99)."""
    c = _charm(p)
    if direction == "up" and c <= old:
        return round(p, 2)
    if direction == "down" and c >= old:
        return round(p, 2)
    return c


def demand_growth(v: Variant) -> Optional[float]:
    if v.units_prev_14d <= 0:
        return None if v.units_14d <= 0 else 1.0
    return v.units_14d / v.units_prev_14d - 1.0


def propose_prices(ranked: list[Variant], settings: Settings, top_n: int = 500) -> list[PriceProposal]:
    if not settings.get("pricing.enabled", True):
        return []
    map_tag = settings.get("pricing.map_tag", "MAP Pricing")
    max_step = float(settings.get("pricing.max_change_pct_per_week", 0.05))
    min_margin = float(settings.get("pricing.min_gross_margin_pct", 0.25))
    r = settings.get("pricing.raise", {})
    lo = settings.get("pricing.lower", {})
    out: list[PriceProposal] = []

    for v in ranked:
        if v.rank is None or v.rank > top_n or v.price <= 0:
            continue
        if map_tag in v.tags:
            continue
        g = demand_growth(v)
        cover = v.days_of_cover
        if g is None or cover is None:
            continue

        # ---- raise: scarce + accelerating demand
        if cover != float("inf") and r.get("min_days_cover", 0) <= cover <= r.get("max_days_cover", 14) and g >= r.get("min_demand_growth", 0.15):
            step = min(float(r.get("step_pct", 0.03)), max_step)
            new = _round_price(v.price * (1 + step), v.price, "up")
            if new > v.price:
                # keep compare-at consistent: don't exceed compare-at
                if v.compare_at_price and new >= v.compare_at_price:
                    new = round(v.compare_at_price - 0.01, 2)
                if new > v.price:
                    out.append(
                        PriceProposal(
                            v, "up", v.price, new,
                            f"scarce ({cover:.0f}d cover) & demand {g:+.0%} vs prior 14d",
                            automation="auto" if v.rank > 100 else "semi",
                        )
                    )
            continue

        # ---- lower: overstock + falling demand
        if cover >= lo.get("min_days_cover", 180) and g <= lo.get("max_demand_growth", -0.10):
            margin = v.gross_margin_pct
            if margin is not None and margin < float(lo.get("prefer_bundle_over_markdown_if_margin_below", 0.40)):
                out.append(
                    PriceProposal(v, "bundle", v.price, v.price,
                                  f"overstock ({cover:.0f}d) but margin {margin:.0%}: bundle instead of markdown",
                                  automation="semi")
                )
                continue
            step = float(lo.get("step_pct", 0.10))
            new = _round_price(v.price * (1 - step), v.price, "down")
            if v.unit_cost is not None:
                floor = v.unit_cost / (1 - min_margin)
                new = max(new, round(floor, 2))
            if new < v.price:
                out.append(
                    PriceProposal(v, "down", v.price, new,
                                  f"overstock ({cover:.0f}d cover) & demand {g:+.0%}; margin floor {min_margin:.0%}",
                                  automation="semi")
                )
    return out
