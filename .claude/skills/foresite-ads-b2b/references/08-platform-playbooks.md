# 08 — Platform playbooks: the levers on each platform

What the agent inspects and what it can recommend, per platform. Every write is still a Decision Card.

## Meta (Facebook / Instagram)
**Structure:** consolidate — fewer campaigns, fewer ad sets, more conversions per ad set (to exit learning).
Typical: Prospecting (broad or Advantage+ where Standing Orders allow) · Retargeting (site visitors / ATC /
engagers, excluding purchasers) · Retention/cross-sell (purchasers) · Catalog (Advantage+ catalog / DPA).
**Levers:** CBO vs ABO, budget, bid strategy (highest volume, cost cap, bid cap, ROAS goal), optimization event,
attribution setting, audience (broad, interest, lookalike, custom, Advantage+ audience on/off), placements
(Advantage+ placements vs manual), creative mix, dynamic creative, catalog sets, exclusions, frequency
(reach & frequency buys).
**Inspect daily:** spend pace, CPM, CTR (link), CPC, CVR, CPA, ROAS, frequency, learning status, delivery
(“Learning limited”), breakdowns by age/gender/placement/device, EMQ, disapprovals.
**Watch-outs:** significant edits reset learning; Advantage+ Audience may override age/gender unless set as
hard controls — check against Standing Orders daily; don't run overlapping ad sets that self-compete.

## Google Ads
**Campaign types:** Search (brand, non-brand, competitor), Shopping (standard), Performance Max, Demand Gen,
YouTube/Video, Display.
**Levers:** budgets, bid strategy and targets (tCPA/tROAS/Max conv value), keywords & match types, negative
lists, ad assets (RSA, sitelinks, callouts, structured snippets, images, promotions), audience signals (PMax),
listing groups / product partitions, feed custom labels, geo/device/schedule adjustments (where supported),
brand exclusions / brand inclusion, final URL expansion (PMax).
**Inspect daily:** spend, conv, conv value, CPA/ROAS by campaign; search impression share and IS lost to
budget vs rank; search terms (new waste); disapprovals; Merchant Center item issues.
**Weekly:** search-term mining → negatives + new exacts; auction insights; Quality Score components; PMax
insights (search categories, asset performance); brand vs non-brand split (and PMax brand cannibalization).
**Watch-outs:** separate brand from non-brand in reporting; budget-limited high-ROAS campaigns are the cheapest
scale; Smart Bidding learning ≈ 1–2 weeks after big changes.

## LinkedIn
**Objectives:** brand awareness, website visits, engagement, video views, lead generation (Lead Gen Forms),
website conversions, talent (not used for ads ops).
**Formats:** single image, carousel, video, document ads, Thought Leader Ads, conversation ads, text/spotlight/
follower ads, event ads, CTV/LinkedIn Audience Network (opt-in/out).
**Targeting:** company (list upload / name / industry / size / growth), job title / function / seniority /
skills / years of experience, groups, member interests, matched audiences (contact lists, company lists,
website retargeting, Lead Gen Form openers, video viewers, page visitors), lookalikes/predictive audiences,
audience expansion (default **off** for precision), LinkedIn Audience Network (default **off** for B2B quality
unless tested).
**Levers:** bidding (maximum delivery, cost cap, manual CPC/CPM), budget (daily/lifetime; platform minimums
apply), schedule, frequency, creative rotation, form questions/hidden fields, exclusions (customers,
competitors, employees, students/entry-level when irrelevant).
**Inspect daily:** spend pace, CTR, CPC, CPM, leads, form completion rate, cost/lead, and — via CRM — lead→MQL/SQL;
demographics report (job function/seniority/company who actually saw/clicked) vs intended ICP.
**Watch-outs:** high CPCs make waste expensive — demographics report drift is the #1 check; audience too
narrow underdelivers, too broad dilutes ICP; Lead Gen Forms convert well but need qualification questions.

## Microsoft Advertising
Mirrors Google Search/Shopping/PMax, usually lower CPCs and older/more desktop audience. LinkedIn profile
targeting (company, industry, job function) as bid adjustments — strong for B2B. If using Google Import, review
what the import changed (counts as a write).

## TikTok / Pinterest / Reddit / Snap
TikTok: creative volume and native UGC style matter most; Spark Ads; Smart+ campaigns. Pinterest: planning-
stage intent, catalogs/shopping, seasonal lead time (users plan 1–3 months ahead). Reddit: community/subreddit
targeting and conversation-native creative. Same guardrails and card process.

## CTV (Vibe — connected)
Use for awareness and prospecting reach; measure with post-view conversions via pixel, promo codes, and
geo-lift — not last click. Vibe tools: `list_campaigns`, `query_metrics`, `get_strategy_details`,
`list_creatives`, `create_or_update_campaign` (write → card), `publish_campaign` (write → card).

## Foresite AI Ads (Instant)
Foresite-run channels report daily into `ai_ads_metrics` per tenant (Facebook Acquisition, Facebook
Retargeting, Google Search/Shopping/Display, YouTube, Bing, Other) with cost, revenue, ROAS 7/30-day. Monthly
budget override via `tenant-budget` (write → card; changing it is a money decision). Use `roas-report
breakdown=true compare=true` for channel splits and period-over-period.

## Cross-platform budget allocation
1. Fund measurement-proven, non-saturated channels first (marginal ROAS/CPA above target).
2. Estimate marginal returns from spend-vs-outcome curves (last 8–12 weeks by campaign); never reallocate on
   average ROAS alone.
3. Keep 10–20% of budget for tests (new platforms, audiences, concepts).
4. Respect each platform's minimum viable budget (enough for ~50 optimization events/week on Meta; LinkedIn
   needs enough daily budget to deliver against the audience).
5. Reallocations are batch cards (money out of A and into B move together).
