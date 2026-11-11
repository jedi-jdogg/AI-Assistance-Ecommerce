# 09 — The generic advertising playbook

The default playbook every brand starts from. It tells the agent **how to market and advertise well**, in what
order, and what to do every day / week / month / quarter. The brand-ingestion procedure
(`10-brand-ingestion.md`) specializes this into a **brand playbook** for one client, the same way the Linda's
operation was specialized for an older-female quilting audience on Shopify Plus.

Where B2C and B2B differ, the model-specific playbook (`b2c-playbook.md` / `b2b-playbook.md`) overrides this file.

---

## Part A — Principles (how great advertisers think)

1. **Start from the business outcome, work backwards.** Revenue/profit target (B2C) or pipeline/closed-won
   target (B2B) → required conversions → required traffic → budget. Never start from "what budget do we have".
2. **Unit economics decide the ceiling.** Know contribution margin, break-even ROAS/CPA, LTV and payback before
   scaling anything. Spend that is profitable at the margin scales; spend that is not, doesn't.
3. **Measure blended, optimize in-platform, prove with incrementality.** Platforms over-credit themselves.
4. **Fix the leaks before buying more water.** Tracking, landing pages, offer, checkout/forms and lifecycle
   follow-up first; then scale traffic.
5. **Capture demand before you create it.** Order: brand search & shopping/high-intent search → retargeting →
   lookalikes/similar-to-buyers → broad prospecting → awareness/CTV. Each layer must prove itself before the next
   gets meaningful budget.
6. **Creative is the targeting.** Allocate as much effort to creative testing as to media buying.
7. **Consolidate for the algorithm.** Fewer, bigger campaigns with enough conversions to learn beat many tiny ones.
8. **Change slowly, judge on enough data.** Small steps, waiting periods, minimum sample sizes.
9. **Write down every definition, rule and learning.** The playbook is the memory; the agent is the operator.
10. **Humans own money and standards; the agent owns diligence.** (See `01-operating-model.md`.)

## Part B — The full-funnel model

| Stage | Goal | B2C channels / formats | B2B channels / formats | KPI |
|---|---|---|---|---|
| Awareness | Reach the right people cheaply | Meta/TikTok video, YouTube, CTV, Pinterest | LinkedIn video/Thought Leader, YouTube, CTV, podcasts | Reach in target, CPM, hook rate, brand search lift |
| Consideration | Educate and earn the click | Carousels, UGC, comparison, quizzes, Demand Gen | Document ads, webinars, guides, conversation ads | CTR, engaged visits, content consumption |
| Conversion | Capture the purchase/lead | Shopping/PMax, brand & non-brand search, catalog retargeting | Search (high intent), LinkedIn Lead Gen Forms, retargeting with demo/trial offer | CPA, ROAS, CVR / CPL, cost/SQL |
| Retention / expansion | Repeat and grow | Purchaser cross-sell, winback, lifecycle email/SMS | Customer upsell, ABM expansion, advocacy | Repeat rate, LTV, NRR |

## Part C — Launch sequence for a new account (first 30 days)

**Week 0 — Foundation (no spend changes)**
1. Connections verified (`02-connections.md` checklist) and Connection Report sent.
2. Brand ingestion run → draft brand playbook + client file (`10-brand-ingestion.md`); Approver ratifies
   targets, guardrails, Standing Orders.
3. Tracking audit and fixes (pixel/CAPI/enhanced conversions/offline imports/UTMs).
4. Account audit: structure, wasted spend (search terms, placements, audiences), overlap, exclusions, naming,
   learning-limited entities, creative inventory and fatigue, feed health, landing pages.
5. Baseline: last 90 days (and same period last year) by platform/campaign — the "before" picture.

**Week 1 — Quick wins (cards)**
- Negative keywords, broken URLs, disapprovals, exclusion lists, Standing-Order violations, budget-limited
  winners, obvious losers past kill threshold.

**Weeks 2–4 — Structure and tests**
- Consolidate structure; launch the first creative test cycle; set up retargeting and exclusions properly;
  pre-register one incrementality test on the largest channel; set the budget plan for next month.

## Part D — Operating rhythm

| Cadence | Agent does | Human does |
|---|---|---|
| **Intraday** (optional) | Pacing determinations; tripwire checks | Acts on 🔴 only |
| **Daily** | Daily update (`04-daily-update.md`), ≤ 7 Decision Cards, execute & verify approved cards, QA | Approve/reject cards (5–10 min) |
| **Weekly** | Impact review of last week's changes, creative report & briefs, search-term mining, audience/feed/LP health, competitor watch, next-7-day budget | Approve creative + budget plan |
| **Monthly** | Business review, budget by platform, test learnings, playbook revisions, Standing-Order review | Approve next month's budget and standing orders |
| **Quarterly** | Re-run brand ingestion refresh; incrementality read-out; channel-mix strategy; seasonal plan for next quarter | Approve strategy |

## Part E — Budgeting

**Reverse funnel (top-down):**
- B2C: `budget = (revenue target − non-paid revenue forecast) ÷ target MER`, sanity-checked against new-customer
  targets: `new customers needed × target nCAC`.
- B2B: `closed-won target ÷ win rate ÷ SQL→Opp rate ÷ MQL→SQL rate ÷ lead→MQL rate = leads needed`;
  `budget = leads needed × target CPL` (and check `cost/SQL` against CAC payback).
  `adsctl.py b2b-budget` does this math.

**Allocation:** proven high-intent first, then retargeting, then prospecting; 10–20% test budget; respect
minimum viable budgets per platform; reallocate monthly on marginal returns, weekly only for clear outliers.

**Pacing:** monthly cap ÷ days, weighted by the brand's day-of-week and seasonal curve; daily update reports
MTD % vs month-elapsed %; intraday pacing only for large daily budgets.

## Part F — Optimization decision tree (run per campaign/ad set, daily)

```
Is tracking healthy? ── no → fix tracking first (alert); freeze scale decisions on that entity
   │ yes
Enough data? (min conversions / spend) ── no → wait; check delivery & creative health only
   │ yes
Performance vs target (14d, source of record + platform):
   ├─ ≥ 1.25× target & not saturated (freq, IS lost to budget) → SCALE card (+15–20%)
   ├─ within ±20% → HOLD; look for creative/LP/audience improvements
   ├─ 0.7–0.8× → FIX card: creative refresh, audience/keyword pruning, bid target adjust
   └─ < 0.7× break-even after min data → CUT card (−30% or pause), budget to winners (batch card)
Creative fatigue? → refresh card. Learning-limited? → consolidation card.
```

## Part G — Seasonality & promotions
- Maintain a 12-month promo/seasonal calendar in the brand playbook (holidays, industry events, product launches,
  fiscal-year ends for B2B, peak buying seasons).
- 2–4 weeks before peaks: build creative, raise audiences warm (retargeting pools), confirm stock/capacity,
  set seasonality adjustments (Google) only with a card, pre-approve the peak budget as a Standing Order with a
  hard cap so the agent can pace within it.
- After peaks: cut back quickly; mark the period in reporting so it isn't used as a baseline.

## Part H — Account hygiene standards
- **Naming:** `<OBJ>_<AUDIENCE>_<GEO>_<OFFER>_<YYMM>` campaigns; ads as in `07-creative-and-competitive.md`.
- **UTMs:** `utm_source={platform}&utm_medium=paid_{type}&utm_campaign={campaign_name}&utm_content={ad_name}`.
- **Exclusions:** purchasers/customers from acquisition, employees, job seekers (B2B), competitors (B2B).
- **No overlap:** one audience → one ad set per objective.
- **Documentation:** every change via card or Standing Order; off-agent edits get reported.

## Part I — The agent's daily checklist (generic)
1. Pull yesterday/7d/MTD from every connected platform + source of record. Note any gaps.
2. Run tripwires. 🔴s go to the top and to the Approver directly.
3. Check Standing-Order compliance (targeting standards, exclusions, disclosures).
4. Review last 7 days of executed cards vs expected impact.
5. Run the decision tree across active entities; draft cards (≤ 7, ranked by $ impact × confidence).
6. Creative fatigue and disapproval sweep.
7. Landing-page and feed sweep.
8. QA pass on every number and every "done" claim.
9. Publish the daily update; verify it landed.
10. Execute approved cards as they arrive; verify; log.
