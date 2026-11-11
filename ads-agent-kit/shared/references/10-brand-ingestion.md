# 10 — Brand ingestion: the agent writes its own brand playbook

Goal: for any brand on Foresite, produce a **brand playbook** and **client file** as specific as the Linda's
operation — who the customer is, what sells, what the economics allow, which channels and creative work, what
the rules are — and then run the daily operation from it.

Output files (created by `scripts/adsctl.py scaffold --slug <slug> --model b2c|b2b`, then filled in):
- `clients/<slug>/brand-playbook.md` — from `templates/brand-playbook-template.md`
- `clients/<slug>/ads-account.yaml` — from `templates/client-account.yaml`
- `clients/<slug>/decisions.jsonl` — decision log (starts empty)

## Step 1 — Gather (read-only; cite every source)

Pull from every source available; skip what isn't connected and list it under **Gaps** in the playbook.

| Source | Tool | What to extract |
|---|---|---|
| Foresite Marketing Profile | `marketing-profile` (tenant) — `business`, `personas`, `audience_segments`, `keywords`, `competitors`, `recommendations`, `preferences`, `questionnaire` | ICP/personas, positioning, keywords, competitors, stated goals |
| Brand identity | `analyze-branding` (saves colors, fonts, tagline, voice, logo) | Voice and visual rules for creative |
| Website | WebFetch the home, top category, top product/service, pricing, about, reviews/testimonials pages | Offer, value props, proof, objections handled, CTAs, price points |
| Store data (B2C) | Shopify `run-analytics-query`: sales by month (24 mo), by product (top 100 by net sales 90d), AOV, repeat rate, new vs returning, discount rate; sessions & CVR by source | What sells, seasonality curve, economics, channel CVR |
| Lifecycle | Klaviyo flows/campaigns/lists (or Foresite `instant-*`) | Owned-audience sizes, flow coverage, email revenue share |
| CRM (B2B) | HubSpot/Salesforce (if connected) or uploaded export | Deal size, cycle length, win rates by stage/source/segment, ICP firmographics of best customers |
| Ad accounts | Ads Gateway / connectors / exports: 12–24 months by campaign, ad, audience, placement, geo, age/gender (B2C) or job function/seniority/industry/company size (B2B) | What worked historically, waste, saturation, creative winners |
| Foresite AI Ads | `roas-report breakdown=true compare=true`, `ai_ads_metrics` | Channel ROAS trends |
| Competitors | Konvert (`find_competitor_brands`, `get_brand_top_ads`, `search_ads`), ad libraries, competitor sites | Their angles, offers, price points, longest-running ads |
| Customer voice | Reviews, support tickets (Gorgias/Zendesk), sales-call notes (B2B), survey answers | Language customers use, objections, desired outcomes — fuel for copy |
| Owner/team | Uploaded docs, brand books, prior strategy decks, the **intake questionnaire** (`templates/brand-intake-questionnaire.md`) | Goals, constraints, non-negotiables, what's been tried |

Rules: hashes/aggregates only for customer data; no raw PII in the playbook. Quote numbers with window + source.

## Step 2 — Analyze (turn data into decisions)

1. **Business model & economics:** AOV/ACV, gross margin, contribution margin after fulfillment/fees,
   break-even ROAS/CPA, LTV (90/180/365d or contract value × retention), payback target.
   `adsctl.py breakeven --aov … --margin …`.
2. **Customer:** 2–5 personas with demographics/firmographics, jobs-to-be-done, triggers, objections, the words
   they use (from reviews/calls). Identify the **standard targeting** (e.g. Linda's: women 55+). Validate with
   ad-account breakdowns (who actually converts) — data beats assumptions.
3. **Product/offer:** hero products/services (Pareto: what drives 80% of revenue), entry offers, bundles,
   lead magnets (B2B), price position vs competitors, stock/capacity constraints.
4. **Demand map:** search volume themes (keywords from Marketing Profile + search terms), seasonality curve
   (monthly index from 24 months of sales/leads), day-of-week curve.
5. **Channel fit:** score each platform 1–5 on audience presence, intent, creative fit, measurability, past
   performance, minimum viable budget. Choose primary / secondary / test channels.
6. **Creative history:** winning concepts/angles/hooks/formats and losers; competitor gaps.
7. **Measurement maturity:** tracking audit result; choose source of record per metric.
8. **Risks/compliance:** regulated category? special ad category? claims restrictions? brand-safety sensitivities?

## Step 3 — Synthesize the brand playbook

Fill `templates/brand-playbook-template.md` completely. Every section must be specific to the brand (numbers,
names, products, personas) — if a section would be generic, it means data is missing: put it in **Gaps** with
the question to ask. Model it on the Linda's documents in this repo (`docs/00-BASELINE-2026-09.md`,
`docs/01-GROWTH-PLAN-10PCT.md`, `docs/03…05` playbooks, `docs/06-AUTOMATION-MATRIX.md`,
`docs/11-TRAFFIC-PAID-ORGANIC.md`).

Proposed — not active until ratified:
- Targets (monthly ladder) and budget by platform
- Decision-rule thresholds (scale/hold/cut/fatigue) tuned to this brand's economics
- **Standing Orders** (targeting standards, disclosure settings, auto-send rules, emergency brake)
- Autonomy placement for each workstream (0–5 ladder)

## Step 4 — Ratify (human in the loop)

Send the Approver a short summary: the 10 most important findings, the proposed targets/budget, the proposed
Standing Orders and guardrails, and the top 5 first-week cards. **Standing Orders and targets are decisions —
nothing in them is active until the Approver approves them** (playbook card, category `playbook`). Record the
ratification (who, when) in the playbook header and client file.

## Step 5 — Operate and learn
- Daily update runs from the brand playbook's thresholds and Standing Orders.
- Every test result, rejected card reason and QA correction appends to the playbook's **Learnings log**.
- Every executed card reviewed after 7 days feeds the "what works here" section.

## Refresh
- **Monthly:** update baseline numbers, Learnings log → rules; propose threshold changes as playbook cards.
- **Quarterly** (or after a major change — new product line, pricing, market, paused media relaunch): re-run
  Steps 1–4 as a diff against the current playbook; show what changed and why.

## Quality bar (the agent checks before presenting a playbook)
- [ ] Every number has a window and a source.
- [ ] Break-even and target ROAS/CPA (or cost/SQL) computed and shown.
- [ ] Personas grounded in data (ad breakdowns / CRM / reviews), not only the questionnaire.
- [ ] Channel plan has primary/secondary/test with budgets that meet platform minimums.
- [ ] At least 6 creative concepts with angles mapped to personas.
- [ ] Seasonality calendar for the next 12 months.
- [ ] Standing Orders and guardrails explicit, bounded, and marked "proposed".
- [ ] Gaps section lists every missing source and the question to close it.
