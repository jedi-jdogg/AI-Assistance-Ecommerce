# 04 — The daily update (and weekly / monthly rhythms)

## Daily update — every morning, every client

Default time: 07:00 in the client's timezone (`client.timezone`). Delivered to `reporting.daily.channels`
(Slack channel, email draft via Gmail, Foresite). Length target: readable in 3 minutes; detail below the fold.

### Format (fixed order — do not reorder, do not skip sections; write "none" when empty)

```
# <Client> — Ads daily update — <Day, Mon DD>
Posture: <LIVE | PARTIAL | PAUSED | MONITOR-ONLY>  ·  Yesterday spend $X (plan $Y)  ·  MTD $X of $Y cap (Z% at D% of month)

## 1. Headline (3 bullets max)
- The one number that matters (B2C: blended MER / net profit vs target; B2B: pipeline $ and SQLs vs target)
- The biggest change since yesterday and why
- The single most important decision waiting on you

## 2. Scoreboard  (yesterday · 7d · MTD · vs prior period)
| Platform | Spend | Results | CPA/CPL | ROAS or Pipeline | Δ vs 7d | Pacing |
(B2C cols: purchases, revenue, ROAS (platform), new-cust CPA; B2B cols: leads, MQL, SQL, cost/SQL, pipeline $)
Blended row from the source of record — never the sum of platform-reported conversions.

## 3. Alerts  🔴 critical · 🟠 warning · 🔵 info
Tripwires fired (05-guardrails.md §Tripwires), tracking health, disapprovals, policy, account health,
budget runaway, landing-page failures, token expiry.

## 4. Needs your call  (Decision Cards, grouped)
### Money — budgets & platform reallocation
### Targeting & audiences
### Creative
### Bids, keywords & structure
### Feeds / landing pages / tracking
### Playbook changes (Standing Order proposals, new tests, rule changes)
Each card: ID · platform · entity · before → after · why (one line) · risk · rollback.
End with: "Reply `approve <IDs>` / `reject <ID> <reason>`."

## 5. Executed since last update
Card ID · what changed · approved by · verified ✅/❌ (read-back) · early read vs expected impact.
Standing-Order actions taken (Level 3) listed separately.

## 6. Watching (no action yet)
Tests in flight with day N of M and current read; learning-phase entities; items held by a guard.

## 7. Known gaps
Every broken connection / missing data source, with days open. Example: "Google Ads OAuth expired — day 7 —
Google numbers below are from yesterday's Foresite sync, not live."

## 8. QA
"Numbers checked against source of record: ✅" or the list of corrections made and their system-level fix.
```

### Recommendation coverage the update must consider every day

| Category | Look for |
|---|---|
| **Money / platform budget** | Pacing vs monthly cap; marginal (not average) ROAS/CPA by campaign & platform; budget-limited winners; losers past kill threshold; cross-platform reallocation |
| **Targeting** | Demographic/geo/device/placement breakdown skews; audience saturation (frequency, reach growth); Standing-Order drift (e.g. Advantage+ turned back on); exclusions missing (purchasers, employees, competitors) |
| **Audiences** | Seed freshness, list match rates, membership refresh results, held guard actions, new segments worth building |
| **Creative** | Fatigue (CTR decay, frequency), winners to iterate, losers to pause, concept gaps vs competitors, disapprovals, new test proposals |
| **Bids / keywords** | Search-term negatives, match-type expansion, impression-share lost to budget vs rank, bid-strategy target changes |
| **Feeds / landing pages** | Disapproved products, out-of-stock items still advertised, final-URL 4xx/5xx, slow pages, LP CVR outliers |
| **Tracking** | Event volume drops, EMQ, enhanced conversions, offline import lag, attribution gaps |
| **Playbook** | Rules that should change because evidence says so (thresholds, cadences, Standing Orders) |

Rules:
- Max **7 cards** per day unless something is on fire — rank by expected $ impact × confidence. Put the rest in
  a "backlog" line count.
- Each recommendation states the **decision rule** it came from (e.g. "scale rule: 14d ROAS > 4× and freq < 3").
- Never recommend what a Standing Order already forbids; never re-propose a rejected card within 7 days without
  new evidence.

## Intraday pacing (optional, for high spenders — Linda's "$50k/day" pattern)

Determinations at fixed times (Linda's: 10:00, 12:00, 14:00, 16:00 PT). Projection = actual-so-far ÷
pooled day-of-week cumulative curve (last 4 completed same-weekday days); backtest the curve monthly and
report its mean absolute error. Output a short fixed table + "Needs your call" levers only.
`adsctl.py pace-intraday` implements the projection.

## Weekly review (Monday)
1. Week scoreboard vs plan and vs same week last year.
2. Impact review of every executed card from last week (keep / roll back).
3. Creative report: top/bottom 5 by hook rate, CTR, CPA/ROAS; fatigue list; next week's test plan.
4. Search: search-term mining (negatives + new exact keywords), auction insights, impression share.
5. Audience health; feed health; landing-page leaderboard.
6. Competitor ad watch (new angles/offers seen, via Konvert / ad libraries).
7. Budget plan for the next 7 days per platform.

## Monthly business review (1st business day)
Scorecard vs target, blended efficiency (MER / CAC / payback / pipeline), incrementality evidence, what we
learned (test log), next month's budget by platform with the reasoning, Standing Orders to add/retire,
playbook revisions. This is the moment to re-base the brand playbook (`10-brand-ingestion.md` §Refresh).

## Scheduling it
- **Claude routine / scheduled task:** ask the agent to "schedule the <client> ads daily update at 07:00
  <timezone> on weekdays" — it creates a recurring scheduled task that runs this skill with `daily update
  <client>` and posts to the configured channel.
- **Delivery rules:** Slack → the client's channel from `reporting.daily.channels` (read the channel topic first);
  email → Gmail **draft** unless a Standing Order says auto-send. Verify the post/draft exists before saying it was sent.
