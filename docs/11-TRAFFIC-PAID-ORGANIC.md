# Traffic: converting paid and growing organic

## Facts (90 days)
| Source | Sessions | CVR | Read |
|---|---|---|---|
| direct | 1.48M | 0.96% | mostly bots + untagged links |
| search | 232K | **3.44%** | best channel; grow it |
| social | 157K | 1.35% | includes untagged Meta ads |
| email | 22.6K | 2.29% | tiny because flows are off |
| paid | 700 | 0.29% | ads off, or untagged |

74% of orders have no referrer. Fix attribution first, otherwise every budget decision is blind.

## Step 0 — attribution (AUTO, one-time)
- Klaviyo: enable UTM tracking on all flows and campaigns.
- Every ad, QR, YouTube description, guild newsletter link gets utm_source/medium/campaign.
- TripleWhale (installed) becomes the source of truth for channel ROAS; Shopify referrer is the sanity check.

## Paid — how to convert it
1. **Google Shopping / PMax on the top 100** (batting rolls, Pellon bolts, packages). High intent, brand-searched products. Feed rules: Pre-Order tag → availability=preorder; exclude MAP violations; include GTINs.
2. **Brand + product exact match** ("hobbs 80/20 batting roll", "pellon sf101 bolt"): cheap, 5–10× ROAS, defends against Amazon/Missouri Star.
3. **Meta retargeting only** at first: ATC non-buyers 7d, viewed-roll 14d, email list lookalikes. Prospecting after retargeting proves ROAS > 4×.
4. **Landing pages**: send roll ads to the roll PDP with ETA badge and bundle offer, not to the home page. Paid CVR today (0.29%) says landings are wrong.
5. **Rules**: 14-day ROAS < 2× pause; > 4× scale +20%/week. Budget = (target − organic forecast) ÷ 4.
6. **CTV (Vibe)**: brand awareness for Crafter Club; measure with promo code + post-view lift, not last click.

## Organic — how to bring more
1. **Buying guides** that match how quilters search: 80/20 vs 100% cotton vs wool vs bamboo; how much batting for queen/king; interfacing chooser (SF101 vs 911FF vs 987F vs Flex-Foam); roll vs package cost per yard calculator.
2. **Collection pages** for every brand × width × fiber with real copy + FAQ schema; canonical pre-order pages that stay indexable (never 404 an OOS top-500 PDP).
3. **Product schema** with price, availability (preorder), reviews (Klaviyo Reviews) → rich results.
4. **Video**: "Morning with Corey" emails → blog posts (the `mwc-blog-pipeline` skill) → YouTube shorts linking back.
5. **Links**: vendor "where to buy" pages (Hobbs, Pellon, Quilters Dream, Warm), guild sites, longarm forums.
6. **Marketplaces as discovery**: Amazon/eBay/Etsy listings via LitCommerce for top-100 where MAP allows; insert a Crafter Club card in every marketplace shipment.
7. **KPIs**: search sessions MoM, non-brand clicks (GSC), pages with rich results, articles published (8/month).
