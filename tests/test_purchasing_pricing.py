from lindas_agent.inventory.purchasing import purchase_plan
from lindas_agent.inventory.ranking import rank_variants
from lindas_agent.pricing.engine import propose_prices


def test_purchase_plan_flags_number_one(settings, catalog):
    ranked = rank_variants(catalog, settings)
    lines = purchase_plan(ranked, settings)
    top = [ln for ln in lines if ln.variant.rank == 1]
    assert top and top[0].urgency == "now"
    # 45-day cover at +10%: ~1301/30*1.1*45 ≈ 2147 minus 225 on hand
    assert 1800 <= top[0].order_qty <= 2300
    assert top[0].est_cost > 0


def test_purchase_plan_skips_negative_feed(settings, catalog):
    ranked = rank_variants(catalog, settings)
    lines = purchase_plan(ranked, settings)
    assert not any("SF101" in ln.variant.product_title for ln in lines)


def test_pricing_rules(settings, catalog):
    ranked = rank_variants(catalog, settings)
    props = propose_prices(ranked, settings)
    by = {p.variant.product_title: p for p in props}
    assert "Scarce Thread" in by and by["Scarce Thread"].direction == "up"
    assert 0 < by["Scarce Thread"].change_pct <= 0.05
    assert "460RT Rotary Handle" in by and by["460RT Rotary Handle"].direction in ("down", "bundle")
    if by["460RT Rotary Handle"].direction == "down":
        p = by["460RT Rotary Handle"]
        assert p.new_price >= p.variant.unit_cost / (1 - 0.25) - 0.01


def test_map_products_untouched(settings, catalog):
    for v in catalog:
        if v.product_title == "Scarce Thread":
            v.tags.append("MAP Pricing")
    ranked = rank_variants(catalog, settings)
    assert not any(p.variant.product_title == "Scarce Thread" for p in propose_prices(ranked, settings))
