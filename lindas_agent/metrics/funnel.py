"""Funnel KPIs, bot-traffic detection and guardrail alerts."""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..config import Settings
from ..models import Alert, DailyFunnel, DailySales, Severity


@dataclass
class FunnelSummary:
    days: int
    sessions: int
    atc_sessions: int
    checkout_sessions: int
    completed: int
    suspect_bot_days: list[str]

    @property
    def cvr_raw(self) -> float:
        return self.completed / self.sessions if self.sessions else 0.0

    @property
    def atc_rate(self) -> float:
        return self.atc_sessions / self.sessions if self.sessions else 0.0

    @property
    def atc_to_checkout(self) -> float:
        return self.checkout_sessions / self.atc_sessions if self.atc_sessions else 0.0

    @property
    def checkout_completion(self) -> float:
        return self.completed / self.checkout_sessions if self.checkout_sessions else 0.0

    @property
    def cvr_engaged(self) -> float:
        """Conversion among sessions that added to cart — immune to bot session inflation."""
        return self.completed / self.atc_sessions if self.atc_sessions else 0.0


def detect_bot_days(funnel: list[DailyFunnel], settings: Settings) -> list[DailyFunnel]:
    """A day is suspect when sessions z-score > threshold AND ATC/sessions collapses below the floor."""
    if len(funnel) < 10:
        return []
    z_thr = float(settings.get("conversion.bot_session_zscore", 3.0))
    floor = float(settings.get("conversion.bot_atc_ratio_floor", 0.03))
    sessions = [f.sessions for f in funnel]
    med = statistics.median(sessions)
    mad = statistics.median([abs(s - med) for s in sessions]) or 1.0
    suspects = []
    for f in funnel:
        z = 0.6745 * (f.sessions - med) / mad
        if z > z_thr and f.atc_rate < floor:
            suspects.append(f)
    return suspects


def summarize(funnel: list[DailyFunnel], settings: Settings, days: int = 7) -> FunnelSummary:
    window = sorted(funnel, key=lambda f: f.day)[-days:]
    bots = {b.day for b in detect_bot_days(funnel, settings)}
    clean = [f for f in window if f.day not in bots]
    src = clean or window
    return FunnelSummary(
        days=len(src),
        sessions=sum(f.sessions for f in src),
        atc_sessions=sum(f.atc_sessions for f in src),
        checkout_sessions=sum(f.checkout_sessions for f in src),
        completed=sum(f.completed_sessions for f in src),
        suspect_bot_days=[b.isoformat() for b in sorted(bots) if any(f.day == b for f in window)],
    )


def guardrail_alerts(sales: list[DailySales], funnel: list[DailyFunnel], settings: Settings) -> list[Alert]:
    g = settings.get("conversion.guardrails", {})
    alerts: list[Alert] = []
    s7 = summarize(funnel, settings, 7)

    if s7.suspect_bot_days:
        alerts.append(Alert(
            key=f"funnel:bots:{s7.suspect_bot_days[-1]}", severity=Severity.WARNING, category="funnel",
            title="Bot traffic inflating sessions",
            detail=f"{len(s7.suspect_bot_days)} suspect day(s) in last 7: {', '.join(s7.suspect_bot_days)}",
            action="Tighten Negate Bot Protection / Cloudflare rules; report CVR on engaged sessions until clean.",
            automation="semi",
        ))
    if s7.checkout_sessions and s7.checkout_completion < float(g.get("checkout_completion_rate_min", 0.22)):
        alerts.append(Alert(
            key=f"funnel:checkout:{s7.checkout_completion:.2f}", severity=Severity.CRITICAL, category="funnel",
            title="Checkout completion below guardrail",
            detail=f"{s7.checkout_completion:.1%} of sessions reaching checkout complete (7d)",
            action="Check payment/shipping errors, Bolt, discount code failures, shipping-rate shock; run a test order.",
            automation="manual",
        ))
    if s7.atc_sessions and s7.atc_to_checkout < float(g.get("atc_to_checkout_min", 0.60)):
        alerts.append(Alert(
            key=f"funnel:atc2co:{s7.atc_to_checkout:.2f}", severity=Severity.WARNING, category="funnel",
            title="Cart → checkout drop-off high",
            detail=f"only {s7.atc_to_checkout:.0%} of cart sessions reach checkout (7d)",
            action="Audit cart drawer (Rebuy), shipping threshold messaging, package-protection default.",
            automation="manual",
        ))

    # AOV, discount and return-rate checks on sales data
    srt = sorted(sales, key=lambda d: d.day)
    if len(srt) >= 35:
        last7 = srt[-7:]
        prev28 = srt[-35:-7]
        aov7 = sum(d.total_sales for d in last7) / max(1, sum(d.orders for d in last7))
        aov28 = sum(d.total_sales for d in prev28) / max(1, sum(d.orders for d in prev28))
        chg = aov7 / aov28 - 1 if aov28 else 0
        if chg < float(g.get("aov_drop_pct_alert", -0.12)):
            alerts.append(Alert(
                key=f"funnel:aov:{last7[-1].day}", severity=Severity.WARNING, category="funnel",
                title="AOV dropping", detail=f"7d AOV ${aov7:.0f} vs 28d ${aov28:.0f} ({chg:+.0%})",
                action="Check free-shipping threshold, bundle placement, roll vs package mix.", automation="manual",
            ))
        gross7 = sum(d.gross_sales for d in last7)
        if gross7 > 0:
            disc_rate = sum(d.discounts for d in last7) / gross7
            if disc_rate > float(g.get("discount_rate_max", 0.12)):
                alerts.append(Alert(
                    key=f"funnel:discount:{last7[-1].day}", severity=Severity.WARNING, category="funnel",
                    title="Discount rate above ceiling", detail=f"{disc_rate:.1%} of gross sales discounted (7d)",
                    action="Review stacked automatic discounts + affiliate codes; cap to protect gross profit.",
                    automation="manual",
                ))
            ret_rate = sum(d.reversals for d in last7) / gross7
            if ret_rate > float(g.get("return_rate_max", 0.035)):
                alerts.append(Alert(
                    key=f"funnel:returns:{last7[-1].day}", severity=Severity.WARNING, category="funnel",
                    title="Returns/refunds above ceiling", detail=f"{ret_rate:.1%} of gross sales reversed (7d)",
                    action="Pull refund reasons from Gorgias; look for damaged-roll shipping issues.", automation="manual",
                ))
    return alerts


def week_over_week(sales: list[DailySales]) -> dict[str, float]:
    srt = sorted(sales, key=lambda d: d.day)
    if len(srt) < 14:
        return {}
    cur, prev = srt[-7:], srt[-14:-7]
    def tot(rows, f): return sum(getattr(r, f) for r in rows)
    out = {}
    for f in ("total_sales", "orders", "net_sales"):
        c, p = tot(cur, f), tot(prev, f)
        out[f] = (c / p - 1) if p else 0.0
    out["aov"] = ((tot(cur, "total_sales") / max(1, tot(cur, "orders"))) / (tot(prev, "total_sales") / max(1, tot(prev, "orders")))) - 1
    return out
