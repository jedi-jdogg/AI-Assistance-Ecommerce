# Monthly playbook (1st business day, half day)

`lindas-agent monthly` produces the scorecard, new target, lever mix and 12-month ladder.

1. **Scorecard**: total sales vs target, orders, AOV, GM%, discount rate, return rate, CVR engaged, email share, new vs returning.
2. **Re-base**: if last month beat target, next target chains from the actual. If it missed by >10%, decide whether the shortfall was demand (traffic) or execution (stock, flows) — the lever tracker tells you.
3. **Vendor calls**: Hobbs, Quilters Dream, Pellon, Warm Company, Checker. Confirm 60-day supply of top-100, pre-order ETAs, price changes, MAP updates, holiday closures.
4. **Pricing re-base**: margin by vendor; pass through vendor increases within 30 days; refresh MAP list in tags.
5. **Assortment**: top-10 concentration (currently ~30% of net sales). Add adjacent SKUs to spread risk (Hobbs 80/20 in 108"/120"/black, Quilters Dream Select, Warm & Natural rolls). Delist zero-velocity SKUs > 365d.
6. **Cohorts**: 60-day second-order rate of last month's new customers; tune post-purchase + Crafter Club offer.
7. **Paid budget**: budget = (target − organic/lifecycle forecast) ÷ blended ROAS target (4×). Allocate: Shopping/PMax 60%, brand search 10%, Meta retargeting 20%, prospecting tests 10%.
8. **SEO plan**: 8 articles, 4 collection refreshes, technical fixes (schema, pre-order availability, canonical on variants).
9. **Automation review**: what fired, what humans overrode, false positives. Tune thresholds in `config/agent.yaml`.
10. **Promo calendar**: one hero event, two category pushes, Crafter Club perk, marketplace promo.
