"""MONTHLY plan (1st business day): scorecard vs 10%, lever attribution, next-month targets, purchasing budget."""
from __future__ import annotations

from datetime import timedelta

from ..forecast.revenue import month_target, twelve_month_targets
from ..report import money
from .context import Context


def run_monthly(ctx: Context) -> str:
    s = ctx.settings
    out = [f"# Linda's Monthly Growth Plan — {ctx.today.strftime('%B %Y')}"]

    monthly: dict[str, dict[str, float]] = {}
    for d in ctx.sales:
        m = monthly.setdefault(d.day.strftime("%Y-%m"), {"total": 0.0, "net": 0.0, "orders": 0, "gross": 0.0, "disc": 0.0, "rev": 0.0})
        m["total"] += d.total_sales
        m["net"] += d.net_sales
        m["orders"] += d.orders
        m["gross"] += d.gross_sales
        m["disc"] += d.discounts
        m["rev"] += d.reversals
    totals = {k: v["total"] for k, v in monthly.items()}

    last_month = (ctx.today.replace(day=1) - timedelta(days=1)).replace(day=1)
    lm_key = last_month.strftime("%Y-%m")
    if lm_key in monthly:
        m = monthly[lm_key]
        tgt = month_target(s, last_month, totals)
        hit = m["total"] / tgt - 1 if tgt else 0
        out.append(
            f"## Scorecard {lm_key}\n"
            f"- Total sales {money(m['total'])} vs target {money(tgt)} ({hit:+.1%})\n"
            f"- Orders {m['orders']:,} · AOV ${m['total']/max(1,m['orders']):.2f}\n"
            f"- Discount rate {m['disc']/m['gross'] if m['gross'] else 0:.1%} · Return rate {m['rev']/m['gross'] if m['gross'] else 0:.1%}"
        )

    this_tgt = month_target(s, ctx.today, totals)
    out.append(f"## Target {ctx.today.strftime('%Y-%m')}: {money(this_tgt)}  ({money(this_tgt/30.4)}/day)")

    mix = s.get("growth.lever_mix", {})
    inc = this_tgt - totals.get(lm_key, this_tgt / 1.1)
    out.append("## Where the +10% comes from\n" + "\n".join(f"- {k.replace('_',' ')}: {v:.0%} → {money(inc*v)}" for k, v in mix.items()))

    out.append("## 12-month ladder\n" + "\n".join(f"- {m}: {money(v)}" for m, v in twelve_month_targets(s)))

    top = ctx.ranked[:20]
    if top:
        conc = sum(v.net_sales_90d for v in top[:10]) / max(1, sum(v.net_sales_90d for v in ctx.ranked))
        out.append(
            f"## Assortment\n- Top-10 SKUs = {conc:.0%} of 90-day net sales (concentration risk → protect stock first).\n"
            + "\n".join(f"- #{v.rank} {v.display[:60]} — {money(v.net_sales_90d)} / 90d, {v.inventory_quantity} on hand" for v in top[:10])
        )

    out.append(
        "## Monthly operator checklist\n"
        "1. Lock next month's promo calendar (1 hero event, 2 category pushes, Crafter Club perk).\n"
        "2. Vendor calls: Hobbs, Quilters Dream, Pellon — confirm 60-day supply + pre-order ETAs.\n"
        "3. Re-baseline pricing: margin by vendor, MAP list refresh, shipping-cost pass-through.\n"
        "4. Cohort check: 2nd-order rate of last month's new customers; tune post-purchase flow.\n"
        "5. Paid budget: set month budget to (target − organic forecast) ÷ blended ROAS.\n"
        "6. SEO: refresh top-20 landing pages, publish 8 articles, prune thin pages.\n"
        "7. Review automation log: what fired, what was overridden → adjust thresholds in config/agent.yaml."
    )
    return "\n\n".join(out)
