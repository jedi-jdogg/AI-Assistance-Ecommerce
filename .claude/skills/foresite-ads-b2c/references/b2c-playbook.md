# B2C playbook — ecommerce / DTC advertising

Built from the Linda's Electric Quilters operation (Shopify Plus, ~130k purchasers, Meta + Google + OpenAI Ads,
FPX attribution) and generalized. Overrides `09-generic-playbook.md` where they differ.

## 1. The B2C workstreams (Linda's pattern → any store)

| Workstream | What the agent does | Default level |
|---|---|---|
| **Daily ads management** (Meta + Google + others) | Morning report per platform: spend, results, proposed moves | 1 report · 2 changes |
| **Revenue pacing** | Monthly pacing every day; intraday determinations (e.g. 10/12/14/16 local) against a daily revenue target for large spenders; pooled same-weekday curve, backtested monthly | 4 (with QA) |
| **Anomaly & ROAS watch** | Tripwires: spend pace vs plan, CPM/CTR drift vs prior week, EMQ, attributed purchases, delivery anomalies (e.g. catalog ad set delivering to a narrow audience 3 runs in a row → escalate) | 1 (alerts only) |
| **Channel efficiency** | Daily blended ROAS/MER, net profit, new-customer CPA, top channels from the source of record | 1 |
| **Competitor-informed recommendations** | Price watch vs competitors (top products), competitor ads → ads recommendations section | 1 recs · 2 changes |
| **Audience pipeline** | Purchaser/subscriber/category segments from Shopify/Klaviyo → hashed refresh into Meta, Google (and others); exclusion lists kept current | 3 (membership only, size-delta guard) |
| **Feeds & Merchant Center** | Disapprovals, store rating, GTINs, titles, custom labels, availability/pre-order, satellite-store feeds mirroring the primary | 2 |
| **Creative lanes** | Drafts ads (and adjacent email/SMS), independent check passes/fails, owner approves anything customer-facing at scale | 2 |
| **Promotions** | Promo calendar, promo-day pacing, offer consistency between ad, feed and site | 2 |

## 2. Metrics (B2C hierarchy)
1. **Net profit after ads** / contribution margin — named field (e.g. FPX `/api/profit` net profit).
2. **MER** = total revenue ÷ total ad spend; **aMER** (new-customer revenue ÷ ad spend).
3. **nCAC** vs first-order profit and LTV (90/180/365d); **payback**.
4. Platform ROAS/CPA (windowed), AOV, CVR, new vs returning mix.
5. Leading: CPM, CTR, hook/hold rate, ATC rate, checkout completion.

Break-even ROAS = 1 ÷ contribution margin. Example: 35% CM → 2.86× break-even; with a 25% buffer → 3.57× target.

## 3. Channel playbook (in order of priority for most stores)
1. **Google Shopping / PMax on hero products.** Feed quality first: titles (brand + product type + key attribute
   + size/color), GTINs, high-quality images, custom labels (margin bucket, bestseller rank, seasonal, stock
   status), availability incl. **preorder** where the store supports it, sale price annotations. Split PMax by
   margin tier or hero vs long-tail; brand exclusions to measure non-brand honestly.
2. **Brand & product exact-match search** — cheap, defends against resellers/marketplaces; test incrementality.
3. **Meta retargeting + catalog (DPA / Advantage+ catalog)** — ATC non-buyers 7d, product viewers 14d,
   excluding purchasers 30–180d (by purchase cycle).
4. **Meta prospecting** — broad + strong creative, or Advantage+ Shopping where Standing Orders allow; respect
   targeting standards (Linda's: women 55+, Advantage+ Audience **off**). Customer-list lookalikes as seeds.
5. **YouTube / Demand Gen, TikTok, Pinterest** — when creative supply exists and audience fits (Pinterest for
   planning-heavy categories: crafts, home, wedding, recipes).
6. **CTV (Vibe)** — awareness/prospecting for brands past ~$100k/mo spend or with broad audiences; measure by
   post-view + geo-lift + promo code.
7. **Emerging (OpenAI/ChatGPT Ads, retail media)** — test budget only, own Standing Order.

Owned-channel interplay: paid feeds email/SMS (capture rate on paid landings); email/SMS retargets for free —
check lifecycle flows are live before scaling paid (Linda's lever mix: lifecycle 35% vs paid 5% of growth).

## 4. Audience architecture
- **Seeds:** purchasers (all, top LTV decile, category buyers — e.g. batting, thread, fabric), subscribers,
  high-AOV buyers, repeat buyers.
- **Exclusions:** recent purchasers from prospecting (window = purchase cycle), employees, wholesale accounts.
- **Retargeting pools:** site visitors 30d, product viewers 14d, ATC 7d, checkout starters 3d, engagers 60d.
- **Refresh cadence:** daily or weekly hashed sync; guard holds big deltas (Linda's: held ~91,600 removals).
- **Standards:** demographic standards from the brand playbook enforced daily (drift → 🟠 alert; correction
  only if the Standing Order says the agent may correct).

## 5. Creative for B2C
- Formats that win in ecommerce: UGC/testimonial video, demo/how-to, product-in-use lifestyle, comparison
  ("roll vs package cost per yard"), founder/expert, offer-led statics, catalog with overlays (price, rating,
  free-shipping threshold), carousel of bestsellers.
- Persona-matched casting and language (older audiences: larger type, clear value, real people, phone-friendly
  but not trend-jargon).
- Offer discipline: discount rate ceiling from the brand playbook (Linda's ≤ 12% of gross); prefer bundles,
  free-shipping thresholds and gifts-with-purchase over blanket discounts.
- Adjacent lanes (email/SMS/social) follow the same build → independent check → owner approves at scale
  (Linda's: 349,711-recipient campaign scheduled only after the owner approved the actual designs).

## 6. Seasonality & peaks (B2C)
- Build a 12-month calendar: BFCM, holidays, category seasons (Linda's: fall quilting season, Jan new-year
  projects), product launches, vendor promos.
- **BFCM 2026:** Thanksgiving Thu Nov 26 · Black Friday Nov 27 · Cyber Monday Nov 30. CPMs rise sharply from
  mid-November; warm retargeting pools in the 2–3 weeks before; pre-approve a peak budget Standing Order with a
  hard cap and day-by-day pacing curve; creative and feed promotions loaded by ~Nov 20; stock cover confirmed on
  hero SKUs; cut back quickly after Cyber Monday; exclude peak days from baselines.
- **Relaunch from paused** (Linda's posture Nov 2026): restart in this order — tracking verified → brand/
  Shopping on hero SKUs → retargeting/catalog → prospecting; small budgets, 7-day read, then scale by rule.
  Each step is a card.

## 7. Ecommerce-specific tripwires (in addition to `05-guardrails.md`)
- Hero SKU out of stock while advertised (feed or ad) → 🟠; top product OOS without pre-order → 🔴.
- Checkout completion rate below brand floor (Linda's 22%) → 🔴 — treat as outage before judging ads.
- Bot-traffic day (sessions z > 3 and ATC/sessions < 3%) → exclude from CVR/ROAS judgment.
- Discount rate above ceiling (7d) → 🟠 (promo creep erodes margin even when ROAS looks fine).
- Merchant Center account warnings / suspension risk → 🔴.

## 8. Daily update — B2C scoreboard columns
Spend · Purchases · Revenue (source of record) · MER · Platform ROAS (window) · nCAC · AOV · CVR · Δ vs 7d ·
MTD vs cap. Plus pacing to revenue target and net profit when the attribution tool provides it.

## 9. Example Standing Orders (Linda's, as ratified)
- Meta: all ads target women 55+, Advantage+ Audience off. Google: same demographic standard.
- Meta AI-generated content disclosure: opt-out.
- Board pacing emails/texts send automatically in the fixed short-table format; "Needs your call" lists only
  levers that need the owner's tap.
- Audience pipeline: membership refresh only; hashes only; size-delta guard.
- Satellite-store feeds must mirror the approved primary store exactly.
- Attribution: FPX only for blended MER, paid split, email/SMS flows and net profit.
