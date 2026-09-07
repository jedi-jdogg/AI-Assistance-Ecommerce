"""Stock alerts.

Tier rules (from config/agent.yaml):
  * top 500 (watch)     : out of stock -> WARNING alert. Low cover (<14d) -> WARNING.
  * top 100 (critical)  : out of stock -> CRITICAL + pre-order recommendation
                          (auto-flip to CONTINUE if vendor allows). Cover < 7d -> CRITICAL.
Negative on-hand on dropship feeds is treated as "unknown", never "out".
"""
from __future__ import annotations

from ..config import Settings
from ..models import Alert, Severity, Variant
from .ranking import title_says_preorder


def _cover_str(v: Variant) -> str:
    c = v.days_of_cover
    if c is None:
        return "cover unknown (negative on-hand)"
    if c == float("inf"):
        return "no recent sales"
    return f"{c:.1f}d cover"


def stock_alerts(ranked: list[Variant], settings: Settings) -> list[Alert]:
    crit_n = int(settings.get("ranking.tiers.critical", 100))
    watch_n = int(settings.get("ranking.tiers.watch", 500))
    low_cover = float(settings.get("inventory.low_cover_days", 14))
    crit_cover = float(settings.get("inventory.critical_cover_days", 7))
    neg_unknown = bool(settings.get("inventory.treat_negative_as_unknown", True))
    alerts: list[Alert] = []

    for v in ranked:
        if v.rank is None or v.rank > watch_n:
            continue
        tier = "top100" if v.rank <= crit_n else "top500"
        vendor_rule = settings.vendor(v.vendor)
        qty = v.inventory_quantity

        if qty < 0 and neg_unknown:
            alerts.append(
                Alert(
                    key=f"stock:neg:{v.variant_id}",
                    severity=Severity.INFO,
                    category="stock",
                    title=f"#{v.rank} {v.display}",
                    detail=f"on-hand is {qty} (untracked dropship feed, vendor {v.vendor})",
                    action="Fix inventory tracking for this SKU so alerts are meaningful (Stocky/Matrixify sync).",
                    automation="manual",
                    entity=v.variant_id,
                )
            )
            continue

        if qty <= 0:
            if v.inventory_policy.upper() == "CONTINUE":
                # already sellable on backorder — informational only, but flag missing pre-order labeling
                if not title_says_preorder(v) and settings.get("inventory.preorder.tag") not in v.tags:
                    alerts.append(
                        Alert(
                            key=f"preorder:label:{v.variant_id}",
                            severity=Severity.INFO,
                            category="preorder",
                            title=f"#{v.rank} {v.display}",
                            detail="selling on backorder but not labeled Pre-Order",
                            action="Add 'Pre-Order' tag + ETA text so customers are not surprised.",
                            automation="auto",
                            entity=v.variant_id,
                        )
                    )
                continue
            if tier == "top100":
                can_auto = vendor_rule.preorder_ok and v.vendor in settings.get("inventory.preorder.allowed_vendors", [])
                alerts.append(
                    Alert(
                        key=f"stock:oos:{v.variant_id}",
                        severity=Severity.CRITICAL,
                        category="preorder",
                        title=f"#{v.rank} {v.display}",
                        detail=(
                            f"OUT OF STOCK, policy DENY, selling {v.daily_velocity:.1f}/day "
                            f"(${v.net_sales_90d:,.0f} net / 90d, vendor {v.vendor}, lead {vendor_rule.lead_time_days}d)"
                        ),
                        action=(
                            "Switch to PRE-ORDER now: inventoryPolicy=CONTINUE, add 'Pre-Order' tag and ETA; "
                            f"raise PO with {v.vendor}."
                        ),
                        automation="auto" if can_auto else "semi",
                        entity=v.variant_id,
                    )
                )
            else:
                alerts.append(
                    Alert(
                        key=f"stock:oos:{v.variant_id}",
                        severity=Severity.WARNING,
                        category="stock",
                        title=f"#{v.rank} {v.display}",
                        detail=f"OUT OF STOCK, selling {v.daily_velocity:.1f}/day (${v.net_sales_90d:,.0f} net / 90d, vendor {v.vendor})",
                        action=f"Reorder from {v.vendor} (lead {vendor_rule.lead_time_days}d) or enable Back-in-Stock capture.",
                        automation="semi",
                        entity=v.variant_id,
                    )
                )
            continue

        cover = v.days_of_cover
        if cover is None or cover == float("inf"):
            continue
        lead = vendor_rule.lead_time_days
        if tier == "top100" and cover < max(crit_cover, lead * 0.5):
            alerts.append(
                Alert(
                    key=f"stock:lowcover:{v.variant_id}:{int(cover)}",
                    severity=Severity.CRITICAL,
                    category="stock",
                    title=f"#{v.rank} {v.display}",
                    detail=f"{qty} on hand, {v.daily_velocity:.1f}/day → {cover:.1f} days left; vendor lead {lead}d",
                    action=f"Expedite PO with {v.vendor} today; pre-stage Pre-Order switch.",
                    automation="semi",
                    entity=v.variant_id,
                )
            )
        elif cover < max(low_cover, lead):
            alerts.append(
                Alert(
                    key=f"stock:lowcover:{v.variant_id}:{int(cover)}",
                    severity=Severity.WARNING,
                    category="stock",
                    title=f"#{v.rank} {v.display}",
                    detail=f"{qty} on hand, {v.daily_velocity:.1f}/day → {cover:.1f} days left; vendor lead {lead}d",
                    action=f"Place replenishment PO with {v.vendor} this week.",
                    automation="semi",
                    entity=v.variant_id,
                )
            )
    # critical first, then by rank
    order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    alerts.sort(key=lambda a: (order[a.severity], a.title))
    return alerts


def preorder_candidates(ranked: list[Variant], settings: Settings) -> list[Variant]:
    """Top-100 variants that are OOS with DENY policy — the exact set to flip to pre-order."""
    crit_n = int(settings.get("ranking.tiers.critical", 100))
    return [
        v for v in ranked
        if v.rank is not None and v.rank <= crit_n and 0 >= v.inventory_quantity >= 0 and v.inventory_policy.upper() == "DENY"
    ]
