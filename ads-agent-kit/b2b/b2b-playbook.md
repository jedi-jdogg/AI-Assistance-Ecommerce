# B2B playbook — lead generation, pipeline and ABM advertising

The B2C operating model (human approves money, one approval = one write, daily update, QA) carries over
unchanged. What changes is **what success means, which platforms lead, how targeting works, and how slowly
truth arrives**. Overrides `09-generic-playbook.md` where they differ.

## 1. What changes from B2C

| Dimension | B2C (Linda's) | B2B |
|---|---|---|
| Outcome | Revenue / net profit same day | Pipeline and closed-won weeks–months later |
| Source of record | Shopify + attribution tool | **CRM** (HubSpot/Salesforce) opportunity stages and amounts |
| Optimization signal | Purchase + value | Lead → **offline-imported MQL/SQL/Opp/Won** with values |
| Primary platforms | Google Shopping/PMax, Meta | **LinkedIn**, Google Search, Microsoft (LinkedIn profile targeting), Meta for retargeting |
| Targeting | Demographics/interests/lookalikes | Firmographics, job function/seniority/title, **account lists (ABM)**, intent |
| Key cost metric | nCAC / ROAS | **Cost per SQL / opportunity**, CAC payback, LTV:CAC |
| Decision speed | Daily | Daily for hygiene; **weekly** for money (lagging signal) |
| Budget cadence | Daily pacing | **Monthly/quarterly** pacing; fiscal calendars |
| Creative | Product, UGC, offer | Insight/POV, proof (case studies), gated & ungated content, Thought Leader Ads |
| Buying unit | Individual | **Buying committee** (5–10 people per account) |
| Lead quality risk | Low | High — spam/junk leads, students, competitors, job seekers |

## 2. Metrics (B2B hierarchy)
1. **Pipeline $ sourced** (and influenced) by paid, **closed-won $**, **CAC payback**, LTV:CAC (target ≥ 3:1).
2. **Cost per SQL** and **cost per opportunity** — the primary efficiency metrics for money decisions.
3. Stage conversion rates by channel/campaign/audience: lead→MQL, MQL→SQL, SQL→Opp, Opp→Won; velocity
   (days per stage).
4. CPL and lead volume — **directional only**; never scale on CPL alone.
5. ABM: target-account reach %, engaged accounts, accounts with ≥ 2 engaged contacts, account → opp rate.

Reverse funnel (`adsctl.py b2b-budget`): closed-won target ÷ deal size ÷ win rate ÷ SQL→Opp ÷ MQL→SQL ÷
lead→MQL = leads needed; × CPL = budget. Report cost/SQL, cost/opp and CAC it implies; compare to payback target.

**Lag handling:** judge money decisions on the stage that has matured. Use lead→MQL (days) as the early read,
SQL (weeks) for budget moves, opp/won (months) for channel strategy. Always show "matured cohort" vs "immature".

## 3. Measurement setup (must be done before scaling)
- CRM fields: original source, latest source, campaign, UTM fields, **GCLID/LI fat ID/FBCLID** captured on forms.
- **Offline conversions** sent back to every platform with stage values: Google (offline conversion import /
  enhanced conversions for leads), LinkedIn (Conversions API / CRM integration), Meta (CAPI CRM events),
  Microsoft (offline conversions). Optimize campaigns toward SQL/Opp where volume allows.
- Lead Gen Forms (LinkedIn/Meta) synced to CRM natively with hidden fields (campaign, ad, form).
- Lead-quality filters: block free-email domains where relevant, honeypots, enrichment (company, size, title)
  and routing; mark junk leads so they are excluded from CPL math and fed back as negative signals.
- Agreed MQL and SQL definitions written into the client file (`metrics.source_of_record.sql`).

## 4. Platform playbook (B2B emphasis)

### LinkedIn (primary for most B2B)
- **Campaign groups by funnel stage and ABM tier**: Awareness (video/Thought Leader/document, broad ICP) →
  Consideration (website visits, document ads, events) → Conversion (Lead Gen Forms, website conversions,
  conversation ads) → Retargeting (video viewers 50%+, LGF openers, page visitors, website visitors).
- **Targeting standard** per ICP: company size × industry × job function × seniority (or titles), geo;
  **audience expansion OFF**, **LinkedIn Audience Network OFF** unless a test card turns it on.
- **ABM:** upload Tier 1/2/3 company lists (from CRM/intent tool); Tier 1 gets higher bids and personalized
  creative; measure account-level engagement.
- **Exclusions:** current customers (unless expansion campaign), competitors, own employees, students/entry
  level, irrelevant functions (e.g. HR for a finance product).
- **Daily check — Demographics report:** job function/seniority/company size/industry who actually clicked/
  converted vs ICP. Drift → targeting card.
- **Bidding:** start with maximum delivery or cost cap; manual CPC on narrow ABM lists; watch frequency.
- **Lead Gen Form:** 3–5 fields + 1 qualifying question; pre-filled; thank-you page with next step (book a demo
  link — Calendly is connected in this workspace).
- **Thought Leader Ads:** promote executive/employee posts — usually the best CTR/CPC in B2B.

### Google Search (high intent)
- Non-brand problem/solution keywords, category keywords, "software/agency/service for X", competitor terms
  (separate campaign, careful copy), brand defense.
- Ruthless negatives: jobs, salary, free, template, course, definition, student, login (unless brand), DIY.
- Optimize to offline SQL/Opp values once volume ≥ ~30/month; until then to qualified lead with value rules.
- Landing pages per intent cluster; demo/consult CTA plus a lower-commitment offer (guide, ROI calculator).

### Microsoft Advertising
Import top Google Search campaigns; add **LinkedIn profile targeting** bid adjustments (company, industry, job
function). Often lower CPCs and strong desktop/enterprise audience.

### Meta (supporting role)
Retargeting site visitors/engagers with proof content; lookalikes of closed-won customers (CRM upload, hashed);
Lead Ads with qualifying questions — watch quality closely. Special Ad Category if employment/credit/housing.

### YouTube / CTV / podcasts
Category awareness for larger budgets; measure with brand search lift, direct traffic, ABM account engagement.

## 5. Creative for B2B
- **Insight/POV** (a sharp opinion about the buyer's problem), **proof** (named customer, number, timeframe),
  **product demo** (30–60s), **document ads** (checklists, benchmarks, playbooks), **events/webinars**,
  **ROI/cost calculators**, **comparison** pages vs alternatives.
- Message by role in the buying committee: economic buyer (ROI, risk), champion (ease, career win), user
  (workflow), IT/security (compliance), procurement (terms).
- Gated vs ungated: ungated for reach and retargeting pools; gate only high-value assets; Lead Gen Forms for
  mid-funnel offers.
- Refresh cadence slower than B2C (smaller audiences fatigue at higher frequency — watch LinkedIn frequency).

## 6. B2B decision rules (defaults; brand playbook tunes them)
- Scale: cost/SQL ≤ 0.8× target with ≥ 10 SQLs in matured cohort and stable SQL rate → +15–20%.
- Cut: cost/SQL > 1.5× target after 2× target cost/SQL spent, or lead→MQL < 50% of account average.
- Lead-quality alarm: junk/spam rate > 20% of leads (7d) → 🟠, review form/targeting/placements (often Audience
  Network or Meta lead ads).
- ABM coverage: Tier-1 account reach < 60% after 30 days → budget/bid card on the ABM campaign.
- Search: any search term with spend ≥ target CPL and 0 qualified leads → negative-keyword card (or Level 3 if
  a Standing Order allows adding negatives from an approved pattern list).

## 7. B2B tripwires (in addition to `05-guardrails.md`)
- Lead volume up > 50% with no spend change → 🟠 likely spam/bot or form abuse.
- CRM sync failure (leads in platform ≠ leads in CRM ±10%) → 🔴 known gap.
- Offline conversion upload stale > 3 days → 🟠.
- LinkedIn demographics drift: > 30% of clicks outside target seniority/function → 🟠 targeting card.

## 8. Daily update — B2B scoreboard columns
Spend · Leads · Junk % · MQL · SQL · Cost/Lead · **Cost/SQL** · Opps · Pipeline $ · Δ vs 7d · MTD vs cap.
Add a weekly **cohort table** (leads by week → MQL/SQL/Opp to date) and, monthly, **pipeline & closed-won by
channel**, CAC payback and LTV:CAC.

## 9. Example Standing Orders for a B2B client
- LinkedIn: ICP targeting standard (e.g. US/CA, 51–1,000 employees, industries X/Y, Director+ in Finance/Ops);
  audience expansion OFF; Audience Network OFF.
- Exclude current customers, competitors and employees on every acquisition campaign.
- Google: agent may add negative keywords matching the approved negative pattern list (Level 3), reported daily.
- Lead Gen Form leads: daily reconciliation platform vs CRM; mismatches reported.
- Daily update to #client-ads at 08:00 local; weekly pipeline cohort report every Monday.
