# The 10%/month growth plan

## Targets (total sales)

Baseline = August 2026 actual $1,120,197. Each month's target = max(prior target, prior actual) × 1.10, so
beating a month raises the bar rather than banking slack.

| Month | Target | YoY vs 2025 | Notes |
|---|---|---|---|
| 2026-09 | $1,232,217 | +45% | Pacing ahead after Labor Day; hold the run-rate |
| 2026-10 | $1,355,438 | +32% | Fall quilting season; batting demand rises |
| 2026-11 | $1,490,982 | +19% | Black Friday / Cyber week; pre-buy Hobbs 6–8 weeks ahead |
| 2026-12 | $1,640,080 | +86% | Dec 2025 was weak ($883K); gift cards + kits |
| 2027-01 | $1,804,088 | +60% | New-year projects; education content |
| 2027-02 | $1,984,497 | +59% | |
| 2027-03 | $2,182,947 | +42% | |
| 2027-04 | $2,401,241 | +59% | |
| 2027-05 | $2,641,365 | +46% | |
| 2027-06 | $2,905,502 | +78% | |
| 2027-07 | $3,196,052 | +121% | |
| 2027-08 | $3,515,657 | +214% | |

Twelve straight months of 10% is a 3.1× store. The first 3–4 months are credible from fixing what is broken
(lifecycle email, stock-outs, attribution, bots). After that, growth must come from new demand (paid, organic,
marketplaces, wholesale/B2B) and the plan should be re-based quarterly.

## Where the increment comes from (lever mix, config `growth.lever_mix`)

For September the increment is ~$112K. Expected contribution:

| Lever | Share | $ | How |
|---|---|---|---|
| Email/SMS lifecycle | 35% | $39K | Abandoned checkout/cart, welcome, post-purchase, winback live; 3–5 campaigns/wk |
| Conversion rate | 25% | $28K | Bot filtering, checkout errors, pre-order availability, PDP trust/ETA, Rebuy cart |
| AOV: bundles & upsell | 15% | $17K | Roll + thread/scissors bundles, free-ship threshold nudges, Crafter Club perks |
| Stock availability | 10% | $11K | Top-100 never un-buyable (pre-order), 45-day cover on top-500 |
| Organic traffic | 10% | $11K | Buying guides, collection SEO, schema, vendor links |
| Paid traffic | 5% | $6K | Shopping on top-100, brand exact, retargeting ATC non-buyers |

## Unit economics guardrails

- Gross margin floor on any markdown: 25%. MAP-tagged products: never touched.
- Discount rate ceiling: 12% of gross (Aug was 6.3%; do not let promos creep back to Feb's 13%).
- Returns/reversals ceiling: 3.5% of gross.
- Blended paid: scale only when 14-day ROAS > 4×; pause < 2×.

## Decision rhythm

- **Daily (07:00 CT)**: pace vs target, funnel guardrails, stock/pre-order criticals, actions taken.
- **Weekly (Mon)**: purchasing plan by vendor, pricing proposals, lifecycle audit, traffic mix, promo calendar.
- **Monthly (1st)**: scorecard, new target, lever attribution, vendor calls, paid budget, SEO plan.

If projected month-end is < 97% of target for two consecutive days, the daily brief escalates: promo/email send,
paid scale on >4× ROAS campaigns, and a stock check on the top-20.
