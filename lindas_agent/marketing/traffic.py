"""Traffic mix analysis: channel CVR, attribution health, paid/organic recommendations."""
from __future__ import annotations

from ..models import Recommendation


def channel_recommendations(channel_rows: list[dict], attribution_blank_share: float) -> list[Recommendation]:
    """channel_rows: [{source, sessions, cvr}] from ShopifyQL sessions GROUP BY referrer_source."""
    recs: list[Recommendation] = []
    by = {r["source"]: r for r in channel_rows}
    total = sum(r["sessions"] for r in channel_rows) or 1

    if attribution_blank_share > 0.5:
        recs.append(Recommendation(
            category="traffic", title="Fix order attribution (UTMs everywhere)",
            rationale=f"{attribution_blank_share:.0%} of orders have no referrer source; email shows near-zero attributed orders",
            expected_impact="Makes every channel decision below measurable; prerequisite for scaling paid",
            automation="auto",
            payload={"klaviyo": "enable UTM tracking on all flows + campaigns", "ads": "utm_source/medium/campaign on every ad"},
        ))
    paid = by.get("paid", {"sessions": 0, "cvr": 0})
    if paid["sessions"] / total < 0.02:
        recs.append(Recommendation(
            category="traffic", title="Paid traffic is <2% of sessions (or untagged)",
            rationale="Either paid is off, or ads land as 'direct/social'. Tagged paid sessions convert at 0.3% — landing pages are wrong",
            expected_impact="A disciplined Google Shopping + PMax program on batting rolls typically runs 4-6x ROAS in this category",
            automation="manual",
            payload={"start": "Shopping on top-100 SKUs, brand + 'hobbs 80/20 batting roll' exact; Meta retargeting of ATC non-buyers"},
        ))
    search = by.get("search")
    if search and search["cvr"] > 0.025:
        recs.append(Recommendation(
            category="traffic", title="Double down on organic search (highest-CVR channel)",
            rationale=f"Search sessions convert at {search['cvr']:.1%}, 2-3x other channels",
            expected_impact="+10% organic sessions ≈ +2-3% total revenue at current mix",
            automation="semi",
            payload={
                "content": "Buying guides: batting comparison (80/20 vs cotton vs wool vs bamboo), 'how much batting for a queen quilt', interfacing chooser (SF101 vs 911FF vs 987F)",
                "technical": "Collection pages for every brand/width combo with FAQ schema; product schema with price/availability; fix pre-order availability schema",
                "links": "Vendor 'where to buy' listings (Hobbs, Pellon, Quilters Dream), guild newsletters, YouTube tutorials linking to lindas.com",
            },
        ))
    direct = by.get("direct")
    if direct and direct["sessions"] / total > 0.6:
        recs.append(Recommendation(
            category="traffic", title="'Direct' is >60% of sessions — mostly bots + untagged links",
            rationale=f"Direct CVR {direct['cvr']:.1%} vs mobile human CVR ~2%",
            expected_impact="Cleaner denominators for CVR; lower app/CDN costs; honest channel ROI",
            automation="semi",
            payload={"do": "Negate Bot Protection rules on desktop US/other spikes; UTM on SMS, email, QR, YouTube, guild links"},
        ))
    return recs
