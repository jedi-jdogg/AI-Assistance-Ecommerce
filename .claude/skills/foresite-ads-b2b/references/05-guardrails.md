# 05 — Guardrails, tripwires and compliance

Defaults below apply unless the client file overrides them under `guardrails:`. Overrides can only be
**tighter** unless an Approver signs a Standing Order loosening them. `adsctl.py guard` checks cards against
these mechanically; the agent still applies judgment.

## Money guardrails (checked on every card)

| Rule | Default | Why |
|---|---|---|
| Monthly cap | Never project MTD spend above `budgets.monthly_cap_usd` | Over = **new money** → escalation lane 1 |
| Per-platform cap | `budgets.platforms.<p>.monthly_cap_usd` if set | Client-approved split |
| Budget step size | ≤ **20%** up / ≤ 30% down per entity per change | Larger edits reset learning (Meta/LinkedIn) and destabilize Smart Bidding |
| Budget edit frequency | ≥ **72h** between budget edits on the same entity | Let the algorithm re-stabilize; judge on ≥ 3 days data |
| Bid/target step | tROAS / tCPA moves ≤ 15% per change, ≥ 7 days apart | Smart Bidding needs a cycle (≈ conversion lag + 7d) |
| Daily account ceiling | Yesterday spend ≤ 1.3× planned daily (B2C promo days: per promo plan) | Runaway detection |
| Minimum data | No scale/kill on < `min_conversions_for_decision` (default 30 conversions, or 14 days and ≥ 2× target CPA spent) | Avoid deciding on noise |
| Learning phase | Don't edit entities in learning except to fix errors; Meta exits learning ~50 optimization events/7d | Edits restart learning |

## Decision rules (defaults — the brand playbook tunes them)

| Rule | B2C default | B2B default |
|---|---|---|
| Scale | 14d ROAS ≥ 1.25× target ROAS **and** frequency < 3 (prospecting) → +15–20% | Cost/SQL ≤ 0.8× target **and** SQL rate stable → +15–20% |
| Hold | Within ±20% of target | Within ±20% of target CPL with acceptable lead quality |
| Cut | 14d ROAS < 0.7× break-even ROAS after min data → −30% or pause card | Cost/SQL > 1.5× target after min data, or lead→MQL < half of account average |
| Creative fatigue | CTR down ≥ 30% vs its first 7 days **or** frequency > 3.5 (7d) prospecting / > 8 retargeting | Same, LinkedIn frequency per member > 4/week on a 30d window |
| Kill a test | After pre-registered sample size or 2× target CPA spent with 0 conversions | After 2× target CPL with 0 qualified leads |

Break-even ROAS = 1 ÷ contribution margin %. Target ROAS = break-even × (1 + required profit buffer).
`adsctl.py breakeven` computes them; record them in the client file.

## Tripwires (Level 1 alerts; optional emergency brake)

| Tripwire | Threshold | Severity |
|---|---|---|
| Spend runaway | Entity spend today > 2× its daily budget, or account > 1.5× plan by 2 PM local | 🔴 |
| Zero conversions with spend | Entity spent ≥ 2× target CPA today with 0 conversions while account has conversions | 🟠 |
| Tracking break | Conversion events down ≥ 50% vs same weekday avg while clicks within ±20% | 🔴 |
| CPM / CPC spike | +40% vs prior 7d | 🟠 |
| CTR collapse | −40% vs prior 7d | 🟠 |
| EMQ drop (Meta) | Event Match Quality < 6 on purchase/lead | 🟠 |
| Delivery anomaly | Active ad set delivering to an audience far narrower/wider than defined; Advantage+/expansion re-enabled against a Standing Order | 🟠 (🔴 if Standing Order) |
| Disapprovals | Any active ad or > 5% of feed items disapproved | 🟠 |
| Landing page | Final URL returns 4xx/5xx or redirects off-domain | 🔴 |
| Out of stock advertised | Ad/feed item for an OOS SKU without pre-order | 🟠 |
| Account health | Payment failed, spending limit within 10%, account restricted, policy strike | 🔴 |
| Token expiry | < 14 days 🟠, expired 🔴 (count days open) | |
| Off-agent edits | Platform change history shows edits not from a card or Standing Order | 🔵 (report who/what) |

**Emergency brake (opt-in Standing Order only).** If `standing_orders.emergency_brake.enabled: true`, the agent
may pause a *single entity* (ad, ad set/ad group, or campaign up to `max_daily_budget_usd`) when one of the
listed tripwires fires (default: spend runaway, landing page down, tracking break with spend > $X). It reports
within the hour with a rollback card. Never account-wide. Default **off**.

## Audience guardrails
- Hashes only; never print raw identifiers.
- Membership changes only — never campaign, budget or bid changes from the audience pipeline.
- **Size-delta guard:** hold any refresh that removes > 10% or adds > 25% of a list in one run, or removes
  > 10,000 members, pending a card. (Linda's guard held ~91,600 questionable removals — correct behavior.)
- Exclusion lists (purchasers in prospecting, customers in B2B acquisition, employees, competitors) must exist
  before scaling prospecting.

## Creative & policy compliance (checked before any creative card)
- **Platform policy:** no personal-attribute assertions ("Are you over 55?", "Struggling with debt?") on Meta;
  no before/after for health/weight; no misleading claims, fake urgency or fake UI buttons; trademark use only
  with rights; prices/offers must match the landing page.
- **Special Ad Categories** (Meta: credit/financial products, employment, housing, social issues/politics):
  required declaration; age/gender/ZIP targeting restricted. Google personalized-ads restrictions for the same.
  The agent flags; a human declares.
- **Regulated verticals** (health, alcohol, gambling, finance, cannabis/CBD, firearms, pharma): escalate lane 2.
- **AI disclosure:** follow the client's Standing Order and platform requirements for AI-generated/altered
  imagery and realistic people.
- **Brand voice / claims:** must pass the brand playbook's voice rules and claims list (`claims_allowed`,
  `claims_forbidden`). Reviews/testimonials must be real and permitted.
- **Privacy:** consent mode honored; no sensitive-category audiences (health conditions, etc.).

## Data hygiene
- Never sum platform-reported conversions across platforms; blended numbers come only from the source of record.
- State the attribution window whenever quoting a platform number (e.g. "Meta 7d-click/1d-view").
- Exclude bot-traffic days (client playbook defines detection) before judging CVR.
- Currency and timezone from the account, not assumed.
