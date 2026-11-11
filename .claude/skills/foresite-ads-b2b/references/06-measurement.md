# 06 — Measurement: one number, one source

## Source-of-record registry (required in every client file)

```yaml
metrics:
  source_of_record:
    revenue: shopify.total_sales            # B2C;  B2B: crm.closed_won_amount
    net_profit: fpx./api/profit.net_profit  # name the exact field — Linda's Nov 10 error came from the wrong field
    blended_roas: fpx.blended_mer           # = total revenue ÷ total ad spend (all platforms)
    new_customer_cpa: fpx.ncac
    platform_roas: platform_reported        # always labelled with attribution window
    pipeline: hubspot.deals.amount where stage>=SQL   # B2B
  attribution_windows:
    meta: 7d_click_1d_view
    google: data_driven
    linkedin: 30d_click_7d_view
```

If a metric has two plausible sources, **stop and ask** — then write the answer into the file. Definitions are
decisions.

## Metric hierarchy

**B2C (ecommerce / DTC)**
1. Contribution margin / net profit after ad spend (the business outcome)
2. MER (blended ROAS) = total revenue ÷ total ad spend; aMER = new-customer revenue ÷ ad spend
3. nCAC (new-customer CPA) vs first-order profit and 90/180-day LTV
4. Platform ROAS / CPA (directional, for in-platform optimization only)
5. Leading indicators: CPM, CTR, hook rate (3s views ÷ impressions), hold rate (ThruPlays ÷ 3s views), CVR, AOV

**B2B (lead gen / pipeline)**
1. Pipeline $ and Closed-won $ sourced/influenced by paid; CAC payback; LTV:CAC
2. Cost per SQL / opportunity (not cost per lead)
3. Lead → MQL → SQL → Opp → Won conversion rates by channel, campaign and audience
4. CPL and lead volume (directional only — cheap leads are often bad leads)
5. Leading indicators: target-account reach & engagement (ABM), CTR, form completion rate, cost per engaged account

## Tracking health checklist (weekly, and on every new client)
- Meta: Pixel + **Conversions API** with deduplication (event_id); EMQ ≥ 6 on key events; domain verified;
  AEM priorities set.
- Google: auto-tagging; primary vs secondary conversion actions correct; **enhanced conversions**; consent mode v2
  where required; GA4 linked; for B2B **offline conversion import** (GCLID/enhanced conversions for leads) of
  MQL/SQL/Opp/Won with values.
- LinkedIn: Insight Tag on all pages; conversion rules; **LinkedIn CAPI** or CRM sync for offline stages; Lead Gen
  Form → CRM sync with hidden fields (campaign, creative).
- UTMs on every ad (template in client file); landing pages preserve UTMs through forms/checkout.
- Server-side: Shopify customer events / CAPI gateway (B2C); CRM source fields locked (B2B).

## Incrementality (the "is this real?" layer)
- Prefer platform **conversion-lift** studies (Meta, Google) or **geo-holdouts** (matched-market tests) for big
  spend lines; run at least one per quarter on the largest channel.
- Brand search: test incrementality before scaling (pause in a few geos for 2–3 weeks).
- Retargeting: holdout 10% to measure true lift.
- Lightweight MMM / regression of revenue on spend by channel monthly once ≥ 12 months of data exist; use it to
  set the **marginal** ROAS curve that budget reallocation cards rely on.

## Testing discipline
- Pre-register: hypothesis, primary metric, minimum detectable effect, sample size / spend, stop date.
  `adsctl.py sig` checks significance for two-proportion tests (CTR, CVR).
- One variable per test where possible (concept vs angle vs hook vs format vs audience).
- Every test ends with a written learning in the brand playbook's **Learnings log**, win or lose.

## Reporting hygiene
- Show the window and the source on every number.
- Compare like with like (same weekday mix, promo vs non-promo, same attribution setting).
- When data is missing or stale, say so in **Known gaps** — never fill with an estimate dressed as fact.
