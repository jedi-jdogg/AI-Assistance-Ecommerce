from datetime import date, timedelta

import pytest

from lindas_agent.config import load_settings
from lindas_agent.models import DailyFunnel, DailySales, Variant


@pytest.fixture
def settings():
    return load_settings()


def mk(vid, title, net90, u30, qty, policy="DENY", vendor="Hobbs Bonded Fibers", price=100.0, cost=60.0, u14=None, up14=None, tags=None):
    return Variant(
        variant_id=f"gid://shopify/ProductVariant/{vid}", product_id=f"gid://shopify/Product/{vid}",
        product_title=title, variant_title="Default Title", sku=f"SKU{vid}", vendor=vendor, price=price,
        compare_at_price=None, unit_cost=cost, inventory_quantity=qty, inventory_policy=policy, tracked=True,
        tags=tags or [], net_sales_90d=net90, units_90d=u30 * 3, units_30d=u30,
        units_14d=u14 if u14 is not None else u30 // 2, units_prev_14d=up14 if up14 is not None else u30 // 2,
    )


@pytest.fixture
def catalog():
    vs = [mk(1, "Hobbs 80/20 96in Roll", 575000, 1301, 225)]          # #1, 5 days cover
    vs.append(mk(2, "Hobbs Heirloom Package Queen", 53000, 197, 0))    # top100 OOS DENY
    vs.append(mk(3, "Free Returns + Package Protection", 55000, 18000, 1999999, vendor="re:do"))
    vs.append(mk(4, "Linda's Gift Card", 20000, 1145, -9849))
    vs.append(mk(5, "Pellon SF101 Bolt", 113000, 632, -6657, vendor="Pellon"))  # negative feed
    vs.append(mk(6, "460RT Rotary Handle", 5000, 428, 15726, vendor="Famore", price=19.99, cost=8.0, u14=150, up14=280))  # overstock, falling
    for i in range(7, 700):
        vs.append(mk(i, f"Fabric {i}", max(1.0, 4000 - i * 5), 10, 5 if i % 3 else 0))
    # scarce + rising demand, rank > 100
    vs.append(mk(900, "Scarce Thread", 3500, 60, 20, vendor="Superior Threads", price=12.0, cost=6.0, u14=45, up14=15))
    return vs


@pytest.fixture
def sales_history():
    start = date(2026, 5, 1)
    rows = []
    for i in range(129):  # through 2026-09-06
        d = start + timedelta(days=i)
        base = 45000 if d.month < 8 else 36000
        if d.month == 9:
            base = 70000
        rows.append(DailySales(day=d, orders=int(base / 87), total_sales=base, net_sales=base * 0.87, gross_sales=base * 0.95, discounts=base * 0.05, reversals=base * 0.02))
    return rows


@pytest.fixture
def funnel_history():
    start = date(2026, 7, 23)
    rows = []
    for i in range(46):
        d = start + timedelta(days=i)
        sessions = 15000
        if date(2026, 8, 6) <= d <= date(2026, 8, 9):
            sessions = 70000  # bot spike, ATC flat
        rows.append(DailyFunnel(day=d, sessions=sessions, atc_sessions=1000, checkout_sessions=750, completed_sessions=220))
    return rows
