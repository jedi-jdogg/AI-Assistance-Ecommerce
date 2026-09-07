# Daily playbook (07:00 CT, ~20 minutes of human time)

The agent (`lindas-agent daily` or the `/lindas-growth-agent` skill) produces the brief. The human clears it.

## What the agent does automatically
1. Pulls 60 days of sales, 14 days of funnel, full catalog with 90/30/14-day velocities.
2. Computes pace vs the 10% target and the required daily run-rate.
3. Flags bot-traffic days and reports CVR on clean data.
4. Ranks the top 500; raises stock alerts; **flips top-100 out-of-stock items to pre-order** (with `--apply`).
5. Clears pre-order flags when stock is back above 14 days cover.
6. Checks funnel guardrails (checkout completion, ATC→checkout, AOV, discount, returns).
7. De-duplicates alerts (24h) and posts to Slack / email.

## What the human does (checklist in the brief)
1. **Clear every 🔴**: approve pre-order flips for vendors not on the auto list; call/email the vendor for expedite.
2. **Pace**: if projected < 97% of target two days running → pick one lever today (email send with a
   product story, SMS Club offer, scale a >4× ROAS campaign).
3. **Send today's email/SMS** (min 3 email campaigns/week). Confirm UTM parameters are on.
4. **Customer signal**: 5 minutes in Gorgias — ETA questions become pre-order page copy; damage tickets become
   packaging/carrier tasks.
5. **Bots**: if flagged, tighten Negate rules before any ad-budget decision.

## Daily automations that run in Shopify Flow / Klaviyo without the agent
- Flow: "Inventory quantity changed → ≤0 and tag top-100 → add tag Pre-Order, set policy Continue (via app action), Slack notify".
- Flow: "Order created with Pre-Order item → tag order `preorder`, email customer ETA".
- Klaviyo: back-in-stock flow on Wishlist Plus / Klaviyo BIS trigger.
- Klaviyo: abandoned checkout 1h / 24h / 72h; abandoned cart 4h / 48h; browse abandon 24h.

## Escalation
- Checkout completion < 22% → treat as an outage: place a test order, check Bolt/Shop Pay, shipping rates.
- #1 SKU (Hobbs 96" roll) below 7 days cover → CEO-level: it is 16% of revenue.
