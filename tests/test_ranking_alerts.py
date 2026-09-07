from lindas_agent.inventory.alerts import preorder_candidates, stock_alerts
from lindas_agent.inventory.ranking import is_excluded, rank_variants, top_n
from lindas_agent.models import Severity


def test_exclusions(settings, catalog):
    titles = {v.product_title for v in catalog if is_excluded(v, settings)}
    assert "Free Returns + Package Protection" in titles
    assert "Linda's Gift Card" in titles
    assert "Hobbs 80/20 96in Roll" not in titles


def test_ranking_order(settings, catalog):
    ranked = rank_variants(catalog, settings)
    assert ranked[0].product_title == "Hobbs 80/20 96in Roll"
    assert ranked[0].rank == 1
    assert len(top_n(ranked, 100)) == 100
    assert all(v.rank <= 500 for v in top_n(ranked, 500))


def test_top100_oos_is_critical_preorder(settings, catalog):
    ranked = rank_variants(catalog, settings)
    alerts = stock_alerts(ranked, settings)
    queen = [a for a in alerts if "Queen" in a.title]
    assert queen and queen[0].severity == Severity.CRITICAL
    assert queen[0].category == "preorder"
    assert queen[0].automation == "auto"  # Hobbs on allowed list
    cands = preorder_candidates(ranked, settings)
    assert any(v.product_title == "Hobbs Heirloom Package Queen" for v in cands)


def test_number_one_low_cover_is_critical(settings, catalog):
    ranked = rank_variants(catalog, settings)
    alerts = stock_alerts(ranked, settings)
    roll = [a for a in alerts if "96in Roll" in a.title]
    assert roll and roll[0].severity == Severity.CRITICAL
    assert "days left" in roll[0].detail


def test_dropship_skus_never_alert(settings, catalog):
    ranked = rank_variants(catalog, settings)
    alerts = stock_alerts(ranked, settings)
    assert not [a for a in alerts if "SF101" in a.title or "Queen Roll" in a.title]


def test_negative_non_dropship_is_info(settings, catalog):
    for v in catalog:
        if "SF101" in v.product_title:
            v.sku = "SF101-LOCAL"
    ranked = rank_variants(catalog, settings)
    alerts = stock_alerts(ranked, settings)
    sf = [a for a in alerts if "SF101" in a.title]
    assert sf and sf[0].severity == Severity.INFO


def test_top500_oos_is_warning(settings, catalog):
    ranked = rank_variants(catalog, settings)
    alerts = stock_alerts(ranked, settings)
    fabric_oos = [a for a in alerts if a.title.startswith("#") and "Fabric" in a.title and "OUT OF STOCK" in a.detail]
    assert fabric_oos
    assert all(a.severity == Severity.WARNING for a in fabric_oos if int(a.title.split()[0][1:]) > 100)
