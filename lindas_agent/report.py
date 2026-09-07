"""Markdown rendering for briefs."""
from __future__ import annotations

from .forecast.revenue import Pace
from .metrics.funnel import FunnelSummary
from .models import Alert, Recommendation


def money(x: float) -> str:
    return f"${x:,.0f}"


def render_pace(p: Pace) -> str:
    icon = {"ahead": "🟢", "on_track": "🟡", "behind": "🔴"}[p.status]
    return (
        f"{icon} **{p.month} pace: {p.status.replace('_', ' ')}**\n"
        f"- Target (10% MoM): {money(p.target)}  ·  MTD: {money(p.mtd_actual)} (day {p.days_elapsed}/{p.days_in_month})\n"
        f"- Projected month-end: {money(p.projected_month_end)} ({p.gap:+,.0f} vs target)\n"
        f"- Need {money(p.required_daily_rate)}/day for the rest of the month; forecast run-rate {money(p.forecast_daily_rate)}/day"
    )


def render_funnel(s: FunnelSummary, label: str = "7-day") -> str:
    bots = f"  · bot-suspect days excluded: {', '.join(s.suspect_bot_days)}" if s.suspect_bot_days else ""
    return (
        f"**Funnel ({label}, {s.days} clean days)**{bots}\n"
        f"- Sessions {s.sessions:,} → ATC {s.atc_sessions:,} ({s.atc_rate:.1%}) → Checkout {s.checkout_sessions:,} "
        f"({s.atc_to_checkout:.0%}) → Orders {s.completed:,} ({s.checkout_completion:.0%})\n"
        f"- CVR raw {s.cvr_raw:.2%} · CVR engaged (orders / ATC sessions) {s.cvr_engaged:.1%}"
    )


def render_alerts(alerts: list[Alert], max_lines: int = 40) -> str:
    if not alerts:
        return "_No alerts._"
    lines = [a.as_line() for a in alerts[:max_lines]]
    if len(alerts) > max_lines:
        lines.append(f"… and {len(alerts) - max_lines} more")
    return "\n".join(lines)


def render_recs(recs: list[Recommendation]) -> str:
    if not recs:
        return "_None._"
    out = []
    for r in recs:
        out.append(f"- **[{r.category}] {r.title}** ({r.automation})\n  - Why: {r.rationale}\n  - Impact: {r.expected_impact}")
        for k, v in r.payload.items():
            if isinstance(v, str):
                out.append(f"  - {k}: {v}")
    return "\n".join(out)


def render_wow(wow: dict[str, float]) -> str:
    if not wow:
        return ""
    def f(k): return f"{wow[k]:+.1%}"
    return f"**Week over week**: sales {f('total_sales')} · orders {f('orders')} · AOV {f('aov')}"
