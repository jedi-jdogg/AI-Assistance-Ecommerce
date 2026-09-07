"""WEEKLY review (Monday): purchasing plan, pricing proposals, lifecycle audit, traffic mix."""
from __future__ import annotations

from ..actions.shopify_actions import ActionLog, apply_prices
from ..inventory.purchasing import purchase_plan, purchase_recommendations
from ..marketing.lifecycle import audit_flows, campaign_cadence_alert, lifecycle_revenue_opportunity
from ..metrics.funnel import summarize
from ..pricing.engine import propose_prices
from ..report import render_alerts, render_recs
from .context import Context


def run_weekly(ctx: Context, apply: bool = False) -> str:
    s = ctx.settings
    out = [f"# Linda's Weekly Review — week of {ctx.today.isoformat()}"]

    # ---- purchasing
    lines = purchase_plan(ctx.ranked, s)
    out.append("## 📦 Purchasing plan (top 500, 45-day cover, planned at +10%)")
    if lines:
        hdr = "| rank | item | vendor | on hand | /day | ROP | order qty | est. cost | urgency |\n|---|---|---|---|---|---|---|---|---|"
        out.append(hdr + "\n" + "\n".join(ln.as_row() for ln in lines[:60]))
        out.append(render_recs(purchase_recommendations(lines)))
    else:
        out.append("_All ranked SKUs above reorder point._")

    # ---- pricing
    props = propose_prices(ctx.ranked, s)
    out.append("## 💲 Pricing proposals (supply/demand)")
    if props:
        out.append("| rank | item | dir | old | new | Δ | reason | mode |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(p.as_row() for p in props[:40]))
        log = ActionLog()
        apply_prices(props, ctx.client, ctx.store, apply, log)
        out.append("### Applied\n" + log.render())
    else:
        out.append("_No price moves triggered this week._")

    # ---- lifecycle marketing
    flow_alerts, status = audit_flows(ctx.flows, s) if ctx.flows else ([], {})
    out.append("## ✉️ Lifecycle (Klaviyo)")
    if status:
        out.append("\n".join(f"- {k}: {v}" for k, v in status.items()))
    cad = campaign_cadence_alert(ctx.campaigns_7d, s)
    out.append(render_alerts(flow_alerts + ([cad] if cad else [])))
    if ctx.funnel:
        f30 = summarize(ctx.funnel, s, 30)
        abandoned = max(0, f30.checkout_sessions - f30.completed)
        aov = (sum(d.total_sales for d in ctx.sales[-30:]) / max(1, sum(d.orders for d in ctx.sales[-30:]))) if ctx.sales else 90
        out.append(render_recs([lifecycle_revenue_opportunity(abandoned, aov)]))

    out.append(
        "## 📋 Weekly operator checklist\n"
        "1. Approve/adjust POs above; send to vendors Monday.\n"
        "2. Approve rank 1-100 price moves; ranks 101-500 auto-applied if enabled.\n"
        "3. Publish 3-5 campaigns (Mon new-in, Wed education, Fri offer/restock, Sun Crafter Club).\n"
        "4. Review top-20 search terms in Search & Discovery → fix zero-result queries with synonyms.\n"
        "5. Review overstock (>180d cover) → bundle or clearance collection.\n"
        "6. Paid: pause ad groups <2x ROAS 14d; scale >5x by 20%.\n"
        "7. Publish 2 SEO articles / buying guides; update 1 collection page copy + FAQ."
    )
    return "\n\n".join(out)
