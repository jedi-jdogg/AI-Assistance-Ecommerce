"""Klaviyo lifecycle audit: which revenue-critical flows are live, campaign cadence."""
from __future__ import annotations

from ..config import Settings
from ..models import Alert, Recommendation, Severity

FLOW_KEYWORDS = {
    "Abandoned Checkout": ["abandoned checkout", "checkout abandon"],
    "Abandoned Cart": ["abandoned cart", "cart abandon", "add to cart abandon"],
    "Browse Abandonment": ["browse abandon", "product abandon", "viewed product abandon"],
    "Welcome Series": ["welcome"],
    "Post-Purchase": ["post-purchase", "post purchase", "thank you", "customer thank"],
    "Winback": ["winback", "win-back", "lapsed"],
    "Back in Stock": ["back in stock", "restock"],
    "Review Request": ["review"],
}


def audit_flows(flows: list[dict], settings: Settings) -> tuple[list[Alert], dict[str, str]]:
    """Return alerts for required flows that are not live, plus a status map."""
    required = settings.get("marketing.email.required_live_flows", list(FLOW_KEYWORDS))
    status: dict[str, str] = {}
    alerts: list[Alert] = []
    for req in required:
        kws = FLOW_KEYWORDS.get(req, [req.lower()])
        matches = [f for f in flows if any(k in (f.get("name") or "").lower() for k in kws)]
        live = [f for f in matches if (f.get("status") or "").lower() == "live"]
        if live:
            status[req] = f"live ({live[0]['name']})"
            continue
        status[req] = f"NOT LIVE ({len(matches)} draft/manual variants)" if matches else "MISSING"
        alerts.append(Alert(
            key=f"marketing:flow:{req}", severity=Severity.CRITICAL if req in ("Abandoned Checkout", "Welcome Series") else Severity.WARNING,
            category="marketing", title=f"{req} flow not live",
            detail=status[req],
            action=f"Pick the best existing draft of '{req}', QA, set Live. Add UTM params so orders attribute.",
            automation="semi",
        ))
    return alerts, status


def campaign_cadence_alert(sent_last_7: int, settings: Settings) -> Alert | None:
    minimum = int(settings.get("marketing.email.min_campaigns_per_week", 3))
    if sent_last_7 >= minimum:
        return None
    return Alert(
        key=f"marketing:cadence:{sent_last_7}", severity=Severity.WARNING, category="marketing",
        title="Email campaign cadence below minimum",
        detail=f"{sent_last_7} email campaigns sent in the last 7 days (minimum {minimum})",
        action="Schedule this week's sends: new arrivals, batting restock/pre-order, Crafter Club, education/tutorial.",
        automation="semi",
    )


def lifecycle_revenue_opportunity(abandoned_checkouts_month: int, aov: float, recovery_rate: float = 0.05) -> Recommendation:
    est = abandoned_checkouts_month * recovery_rate * aov
    return Recommendation(
        category="marketing",
        title="Turn on abandoned-checkout + cart flows",
        rationale=f"{abandoned_checkouts_month:,} checkouts abandoned last month; a live 3-touch flow recovers ~{recovery_rate:.0%}",
        expected_impact=f"≈ ${est:,.0f}/month incremental at ${aov:.0f} AOV",
        automation="semi",
    )
