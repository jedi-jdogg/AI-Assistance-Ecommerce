"""Rank sellable variants so 'top 100' and 'top 500' are stable, defensible sets."""
from __future__ import annotations

import re

from ..config import Settings
from ..models import Variant


def is_excluded(v: Variant, settings: Settings) -> bool:
    title = v.product_title.lower()
    for pat in settings.get("ranking.exclude_title_patterns", []):
        if pat.lower() in title:
            return True
    if v.vendor in settings.get("ranking.exclude_vendors", []):
        return True
    tags = {t.lower() for t in v.tags}
    if tags & {t.lower() for t in settings.get("ranking.exclude_tags", [])}:
        return True
    if v.status.upper() != "ACTIVE":
        return True
    if not v.tracked:
        return True
    return False


def rank_variants(variants: list[Variant], settings: Settings) -> list[Variant]:
    """Return sellable variants sorted by the configured metric, with .rank set (1-based)."""
    key = settings.get("ranking.rank_by", "net_sales")
    sellable = [v for v in variants if not is_excluded(v, settings)]
    if key == "units":
        sellable.sort(key=lambda v: (v.units_90d, v.net_sales_90d), reverse=True)
    else:
        sellable.sort(key=lambda v: (v.net_sales_90d, v.units_90d), reverse=True)
    for i, v in enumerate(sellable, start=1):
        v.rank = i
    return sellable


def top_n(ranked: list[Variant], n: int) -> list[Variant]:
    return [v for v in ranked if v.rank is not None and v.rank <= n and (v.net_sales_90d > 0 or v.units_90d > 0)]


_PREORDER_TITLE = re.compile(r"pre-?order", re.IGNORECASE)


def title_says_preorder(v: Variant) -> bool:
    return bool(_PREORDER_TITLE.search(v.product_title))
