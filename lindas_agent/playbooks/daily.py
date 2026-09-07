"""DAILY brief (07:00 CT): pace vs 10% target, funnel health, stock/pre-order alerts, today's actions."""
from __future__ import annotations

from ..actions.shopify_actions import ActionLog, clear_preorder_when_restocked, flip_to_preorder
from ..forecast.revenue import month_pace
from ..inventory.alerts import preorder_candidates, stock_alerts
from ..metrics.funnel import guardrail_alerts, summarize, week_over_week
from ..models import Severity
from ..report import render_alerts, render_funnel, render_pace, render_wow
from .context import Context


def run_daily(ctx: Context, apply: bool = False) -> str:
    s = ctx.settings
    sections: list[str] = [f"# Linda's Daily Brief — {ctx.today.isoformat()}"]

    pace = month_pace(ctx.sales, s, ctx.today)
    sections.append(render_pace(pace))
    wow = week_over_week(ctx.sales)
    if wow:
        sections.append(render_wow(wow))

    if ctx.funnel:
        sections.append(render_funnel(summarize(ctx.funnel, s, 7)))

    alerts = []
    alerts += guardrail_alerts(ctx.sales, ctx.funnel, s)
    stock = stock_alerts(ctx.ranked, s)
    alerts += stock
    dedupe = int(s.get("inventory.alert_dedupe_hours", 24))
    fresh = [a for a in alerts if ctx.store.should_send(a.key, dedupe)]
    for a in fresh:
        ctx.store.mark_sent(a.key, a.severity.value)

    crit = [a for a in fresh if a.severity == Severity.CRITICAL]
    warn = [a for a in fresh if a.severity == Severity.WARNING]
    sections.append(f"## 🔴 Critical ({len(crit)})\n" + render_alerts(crit))
    sections.append(f"## 🟠 Warnings ({len(warn)})\n" + render_alerts(warn, 25))

    log = ActionLog()
    flip_to_preorder(preorder_candidates(ctx.ranked, s), ctx.client, s, apply, log)
    clear_preorder_when_restocked(ctx.ranked, ctx.client, s, apply, log)
    sections.append("## ⚙️ Automated actions" + (" (APPLIED)" if apply else " (dry-run)") + "\n" + log.render())

    sections.append(
        "## ✅ Today's operator checklist\n"
        "1. Clear every 🔴 above (pre-order flips + expedite POs).\n"
        "2. Confirm yesterday's revenue vs required daily rate; if behind 2 days running, trigger a promo/email send.\n"
        "3. Send today's email/SMS (cadence ≥3/week); confirm UTMs present.\n"
        "4. Skim Gorgias for shipping-damage / stock-ETA tickets → feed ETA text on pre-order pages.\n"
        "5. Check bot spikes: if flagged, tighten Negate rules before ad budgets shift."
    )
    return "\n\n".join(sections)
