# Metric dictionary — what to watch, when to act, who acts

Cadence: D = daily brief, W = weekly review, M = monthly plan, 2h = stock-alert job.
Mode: **auto** (agent acts), **semi** (agent proposes, human approves), **manual**.

## Revenue & pace

| Metric | Definition / source | Watch | Act when | Action | Mode |
|---|---|---|---|---|---|
| Total sales MTD | ShopifyQL `sales.total_sales` | D | — | Pace line in brief | auto |
| Projected month-end | MTD + DOW-median forecast × trend | D | < 97% of target 2 days running | Promo/email send, scale >4× ROAS ads, top-20 stock check | semi |
| Required daily rate | (target − MTD) ÷ days left | D | > forecast rate by 15% | Same as above | semi |
| Week-over-week sales | last 7d vs prior 7d | D | < −10% outside seasonality | Check bots, stock-outs on top-20, checkout errors | manual |
| AOV | total_sales ÷ orders | D | 7d < 28d by 12% | Free-ship threshold, bundle placement, roll vs package mix | manual |
| Gross profit | net_sales − Σ(units × unit_cost) | W/M | GM% down 2pts MoM | Vendor cost review, pricing engine, discount audit | semi |
| Discount rate | discounts ÷ gross_sales | D | > 12% (7d) | Cap stacked automatic discounts, review affiliate codes | manual |
| Return/refund rate | sales_reversals ÷ gross_sales | D | > 3.5% (7d) | Gorgias reasons; shipping damage on rolls | manual |

## Funnel & conversion

| Metric | Definition | Watch | Act when | Action | Mode |
|---|---|---|---|---|---|
| Sessions (clean) | sessions excluding bot-flagged days | D | z>3 spike with ATC flat | Negate/Cloudflare rules | semi |
| ATC rate | ATC sessions ÷ sessions | D | < 3% | Confirms bots; PDP issues | semi |
| ATC → checkout | checkout sessions ÷ ATC sessions | D | < 60% | Cart drawer, shipping messaging, protection default | manual |
| Checkout completion | completed ÷ reached checkout | D | < 22% | Payments (Bolt), discount errors, shipping rate shock; test order | manual |
| CVR engaged | orders ÷ ATC sessions | D | < 18% | Primary CVR KPI while bots persist | — |
| CVR raw | orders ÷ sessions | D | informational | — | — |
| Mobile vs desktop CVR | ShopifyQL GROUP BY device | W | desktop < 1/2 mobile | Bot or desktop UX issue | manual |
| Zero-result searches | Search & Discovery report | W | any top-20 term | Synonyms, redirects, create collection | semi |
| Site speed (LCP) | PageSpeed / Shopify web perf | W | LCP > 2.5s mobile | App bloat audit, image sizes | manual |

## Inventory & supply

| Metric | Definition | Watch | Act when | Action | Mode |
|---|---|---|---|---|---|
| Top-100 out of stock | rank ≤100, on-hand ≤0, policy DENY | 2h | immediately | Flip to pre-order (CONTINUE + tag + ETA); PO | **auto** |
| Top-500 out of stock | rank ≤500, on-hand ≤0 | 2h | immediately | Reorder; enable back-in-stock capture | semi |
| Days of cover | on-hand ÷ 30d daily velocity | D | top-100 < 7d; any < vendor lead time | Expedite / place PO | semi |
| Reorder point breach | position < d×(LT+7)+safety | W | breach | PO qty to 45-day cover at +10% demand | semi |
| Overstock | cover > 180d | W | with falling demand | Markdown (−10%, margin floor) or bundle | semi |
| Negative on-hand | dropship feed untracked | D | any top-500 | Fix Stocky/Matrixify sync | manual |
| Pre-order backlog | orders on CONTINUE SKUs | W | ETA slips | Update ETA text; email affected customers | semi |
| Vendor fill rate | received ÷ ordered (Stocky) | M | < 90% | Second-source or raise safety stock | manual |

## Pricing

| Metric | Definition | Watch | Act when | Action | Mode |
|---|---|---|---|---|---|
| Demand growth | 14d units ÷ prior 14d − 1 | W | ≥ +15% with cover ≤14d | +3% (rank>100 auto; rank≤100 approve) | auto/semi |
| Overstock + falling | cover ≥180d, growth ≤ −10% | W | — | −10% to margin floor, or bundle | semi |
| Margin vs floor | (price − cost) ÷ price | W | < 25% | Never mark down further; raise or delist | auto guard |
| MAP compliance | tag `MAP Pricing` | W | any proposal | Blocked | auto guard |
| Compare-at integrity | new price < compare_at | W | violation | Fix compare-at | auto guard |

## Marketing & traffic

| Metric | Definition | Watch | Act when | Action | Mode |
|---|---|---|---|---|---|
| Required flows live | 8 flows (see config) | W | any not live | Publish best draft, add UTMs | semi |
| Campaign cadence | email campaigns sent / 7d | W | < 3 | Schedule Mon/Wed/Fri/Sun sends | semi |
| Flow revenue share | Klaviyo attributed ÷ total | M | < 20% | Flow content/timing tests | manual |
| Abandoned checkouts | reached − completed | W | informational | Recovery upside = × 5% × AOV | — |
| Attribution blank share | orders with no referrer ÷ orders | W | > 50% | UTM everything; TripleWhale as truth | auto (config) |
| Paid share of sessions | paid ÷ sessions | W | < 2% | Ads off or untagged: fix tagging, then Shopping on top-100 | manual |
| Paid ROAS (14d) | TripleWhale / platform | W | < 2× pause; > 4× scale +20% | Budget moves | semi |
| Organic search CVR | ShopifyQL referrer_source=search | W | informational (3.4%) | Prioritise SEO content where CVR is highest | — |
| Organic sessions growth | MoM search sessions | M | < +5% | Content + collection SEO plan | manual |
| Returning-customer rate | returning ÷ customers | M | < 50% | Post-purchase + winback + Crafter Club | manual |
| List growth | Klaviyo new profiles / wk | W | < prior 4-wk avg | Pop-up offer, SMS Club push, quiz | manual |
