"""Load everything the playbooks need in one place (so daily/weekly/monthly share one data pull)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..config import Settings, load_settings
from ..connectors.klaviyo import KlaviyoClient
from ..connectors.shopify import ShopifyClient, attach_sales_to_variants
from ..inventory.ranking import rank_variants
from ..models import DailyFunnel, DailySales, Variant
from ..store import StateStore


@dataclass
class Context:
    settings: Settings
    store: StateStore
    client: ShopifyClient | None
    klaviyo: KlaviyoClient | None
    sales: list[DailySales] = field(default_factory=list)
    funnel: list[DailyFunnel] = field(default_factory=list)
    ranked: list[Variant] = field(default_factory=list)
    flows: list[dict] = field(default_factory=list)
    campaigns_7d: int = 0
    today: date = field(default_factory=date.today)


def build_context(settings: Settings | None = None, need_catalog: bool = True, need_funnel: bool = True, history_days: int | None = None) -> Context:
    settings = settings or load_settings()
    store = StateStore(settings.db_path)
    client = ShopifyClient(settings.shopify_shop, settings.shopify_token, settings.shopify_api_version)
    klav = KlaviyoClient(settings.klaviyo_key)
    ctx = Context(settings=settings, store=store, client=client, klaviyo=klav)
    days = history_days or int(settings.get("forecast.history_days", 120))

    ctx.sales = client.daily_sales(days)
    if need_funnel:
        try:
            ctx.funnel = client.daily_funnel(min(days, 60))
        except Exception:  # ShopifyQL sessions unavailable → funnel sections are skipped
            ctx.funnel = []
    if need_catalog:
        variants = list(client.iter_variants())
        window = int(settings.get("ranking.window_days", 90))
        s90 = client.variant_sales(window)
        s30 = client.variant_sales(30)
        s14 = client.variant_sales(14)
        # previous 14 = 28d window minus 14d window
        s28 = client.variant_sales(28)
        sprev = {k: {"net_sales": v["net_sales"] - s14.get(k, {}).get("net_sales", 0), "units": v["units"] - s14.get(k, {}).get("units", 0), "sku": v.get("sku"), "title": v.get("title")} for k, v in s28.items()}
        attach_sales_to_variants(variants, s90, s30, s14, sprev)
        ctx.ranked = rank_variants(variants, settings)
        ctx.store.save_variant_daily(
            ctx.today.isoformat(),
            [(ctx.today.isoformat(), v.variant_id, v.inventory_quantity, v.units_30d, v.net_sales_90d, v.rank) for v in ctx.ranked[:1000]],
        )
    if klav.enabled:
        try:
            ctx.flows = klav.flows()
            ctx.campaigns_7d = len(klav.campaigns_sent(7))
        except Exception:
            pass
    return ctx
