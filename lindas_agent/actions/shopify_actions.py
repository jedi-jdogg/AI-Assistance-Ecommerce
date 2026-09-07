"""Automated Shopify actions. Everything is dry-run unless apply=True.

Fully automatable (safe, reversible, rule-bound):
  * flip top-100 OOS variants to pre-order (inventoryPolicy CONTINUE + 'Pre-Order' tag)
  * remove 'Pre-Order' tag when stock returns and policy is back to DENY
  * apply price changes <= 5% on ranks 101-500 (rank 1-100 requires approval)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Settings
from ..connectors.shopify import ShopifyClient
from ..models import Variant
from ..pricing.engine import PriceProposal
from ..store import StateStore


@dataclass
class ActionResult:
    action: str
    entity: str
    detail: str
    applied: bool
    error: str | None = None


@dataclass
class ActionLog:
    results: list[ActionResult] = field(default_factory=list)

    def add(self, *a, **kw) -> None:
        self.results.append(ActionResult(*a, **kw))

    def render(self) -> str:
        if not self.results:
            return "_no actions_"
        lines = ["| action | entity | detail | applied |", "|---|---|---|---|"]
        for r in self.results:
            status = "✅" if r.applied else ("❌ " + (r.error or "") if r.error else "dry-run")
            lines.append(f"| {r.action} | {r.entity[:60]} | {r.detail} | {status} |")
        return "\n".join(lines)


def flip_to_preorder(candidates: list[Variant], client: ShopifyClient | None, settings: Settings, apply: bool, log: ActionLog) -> None:
    tag = settings.get("inventory.preorder.tag", "Pre-Order")
    policy = settings.get("inventory.preorder.inventory_policy_when_preorder", "CONTINUE")
    allowed = set(settings.get("inventory.preorder.allowed_vendors", []))
    eta = settings.get("inventory.preorder.default_eta_weeks", 6)
    by_product: dict[str, list[Variant]] = {}
    for v in candidates:
        by_product.setdefault(v.product_id, []).append(v)
    for pid, vs in by_product.items():
        v0 = vs[0]
        auto_ok = v0.vendor in allowed and settings.vendor(v0.vendor).preorder_ok
        detail = f"policy→{policy}, +tag '{tag}', ETA ~{eta}w ({len(vs)} variant(s), vendor {v0.vendor})"
        if not auto_ok:
            log.add("preorder", v0.product_title, detail + " — vendor not on auto list; needs approval", applied=False)
            continue
        if not apply or client is None:
            log.add("preorder", v0.product_title, detail, applied=False)
            continue
        try:
            client.set_inventory_policy(pid, [v.variant_id for v in vs], policy)
            client.add_tags(pid, [tag])
            log.add("preorder", v0.product_title, detail, applied=True)
        except Exception as exc:  # noqa: BLE001
            log.add("preorder", v0.product_title, detail, applied=False, error=str(exc)[:120])


def clear_preorder_when_restocked(ranked: list[Variant], client: ShopifyClient | None, settings: Settings, apply: bool, log: ActionLog) -> None:
    tag = settings.get("inventory.preorder.tag", "Pre-Order")
    for v in ranked:
        if tag in v.tags and v.inventory_quantity > 0 and v.inventory_policy.upper() == "CONTINUE":
            cover = v.days_of_cover or 0
            if cover < 14:
                continue  # restocked but thin: leave pre-order safety net on
            detail = f"{v.inventory_quantity} on hand ({cover:.0f}d) → policy DENY, remove '{tag}'"
            if not apply or client is None:
                log.add("preorder-clear", v.product_title, detail, applied=False)
                continue
            try:
                client.set_inventory_policy(v.product_id, [v.variant_id], "DENY")
                client.remove_tags(v.product_id, [tag])
                log.add("preorder-clear", v.product_title, detail, applied=True)
            except Exception as exc:  # noqa: BLE001
                log.add("preorder-clear", v.product_title, detail, applied=False, error=str(exc)[:120])


def apply_prices(proposals: list[PriceProposal], client: ShopifyClient | None, store: StateStore | None, apply: bool, log: ActionLog) -> None:
    for p in proposals:
        if p.direction == "bundle":
            log.add("bundle", p.variant.display, p.reason, applied=False)
            continue
        detail = f"${p.old_price:.2f} → ${p.new_price:.2f} ({p.change_pct:+.1%}); {p.reason}"
        if p.automation != "auto" or not apply or client is None:
            log.add(f"price-{p.direction}", p.variant.display, detail + ("" if p.automation == "auto" else " — needs approval"), applied=False)
            if store:
                store.log_price_change(p.variant.variant_id, p.old_price, p.new_price, p.reason, applied=False)
            continue
        if store and (last := store.last_price_change(p.variant.variant_id)):
            from datetime import datetime, timedelta
            if datetime.utcnow() - last < timedelta(days=7):
                log.add(f"price-{p.direction}", p.variant.display, detail + " — skipped: changed <7d ago", applied=False)
                continue
        try:
            client.set_variant_price(p.variant.product_id, p.variant.variant_id, p.new_price, p.variant.compare_at_price)
            if store:
                store.log_price_change(p.variant.variant_id, p.old_price, p.new_price, p.reason, applied=True)
            log.add(f"price-{p.direction}", p.variant.display, detail, applied=True)
        except Exception as exc:  # noqa: BLE001
            log.add(f"price-{p.direction}", p.variant.display, detail, applied=False, error=str(exc)[:120])
