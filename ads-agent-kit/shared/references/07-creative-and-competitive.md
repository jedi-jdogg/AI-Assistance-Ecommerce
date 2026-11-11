# 07 — Creative engine and competitive intelligence

Creative is the biggest performance lever on modern auction platforms (targeting is increasingly automated;
the creative *is* the targeting). The agent runs a continuous creative system, not one-off ads.

## Creative taxonomy (tag every ad with these — put them in the ad name)

`<concept>_<angle>_<hook>_<format>_<persona>_<version>`

- **Concept** — the big idea (e.g. "roll vs package cost-per-yard", "the 10-minute setup").
- **Angle** — why it should matter: price/value, quality, social proof, problem/solution, identity, urgency,
  authority/expert, comparison, education, founder story, UGC testimonial.
- **Hook** — first 1–3 seconds / headline.
- **Format** — static, carousel, video (short/long), UGC, catalog/DPA, collection, document (LinkedIn),
  Thought Leader post, conversation ad, lead form, CTV.
- **Persona** — from the brand playbook persona list.

## Weekly creative loop
1. **Read**: performance by concept/angle/hook/format (not just by ad). Video: hook rate (3s ÷ impressions),
   hold rate, CTR, CVR, CPA/ROAS. Static: CTR, CVR, CPA/ROAS. B2B: CTR, form-completion rate, cost/SQL.
2. **Diagnose** fatigue (rules in `05-guardrails.md`) and winners worth iterating.
3. **Research** competitors and category (below) for gaps.
4. **Brief** 3–6 new variants: iterate winners (new hooks on winning concept) + 1–2 net-new concepts.
5. **Produce** drafts: copy written by the agent; images via Foresite `generate-creative` (on-brand, uses the
   tenant's saved branding from `analyze-branding`) or Konvert `generate_ad_image`; video scripts/storyboards
   for the client's team or UGC creators.
6. **QA** each draft against brand voice, claims list, platform specs and policy (`05-guardrails.md`).
7. **Card** the launch (category `creative`): which ad set/ad group, budget source, test design, stop rule.
8. **Learn**: winning and losing concepts go into the brand playbook Learnings log.

Creative mix targets (default): 70% iterations of proven concepts · 20% new concepts · 10% wild cards.
Keep ≥ 3–6 active ads per ad set (Meta), ≥ 4 per campaign (LinkedIn), full asset coverage in PMax/RSAs
(15 headlines / 4 descriptions, all image ratios, a video).

## Copy frameworks the agent uses
PAS (problem–agitate–solve), AIDA, Before–After–Bridge, "4 U's" headlines (useful, urgent, unique,
ultra-specific), FAB (feature–advantage–benefit), objection-first, number-led, question-led (avoiding
personal-attribute phrasing on Meta). B2B: insight-led ("Most CFOs underestimate…"), proof-led (named customer
result), POV/thought-leadership, ROI-calculator offers.

## Platform spec checklist (verify specs at production time)
- Meta: 1:1, 4:5 and 9:16 versions; text in safe zones for Reels/Stories; primary text front-loads the hook.
- Google: RSA 15 headlines (≤ 30 chars) / 4 descriptions (≤ 90 chars), pin sparingly; PMax asset groups per
  theme with audience signals; YouTube 16:9 + vertical Shorts.
- LinkedIn: single image 1.91:1 or 1:1 (or 4:5 mobile); intro text front-load in first ~150 chars; document ads
  (PDF) for gated content; Thought Leader Ads from employee posts.
- CTV (Vibe): 15s/30s, sound-on, brand in first 3 seconds, QR/URL end card.

## Competitive intelligence (weekly)
Sources: **Konvert MCP** (connected: `find_competitor_brands`, `get_brand_top_ads`, `search_ads`,
`browse_ads`, `get_top_ads_across_brands`, `scout_new_brand`, collections), Meta Ad Library, Google Ads
Transparency Center, LinkedIn Ad Library, competitor sites/pricing (Linda's runs a daily top-1,000-product price
watch against seven competitors), Foresite `marketing-profile` competitors section.

Report: new competitor ads/concepts this week, longest-running ads (proxy for winners), offers and price
moves, messaging gaps we can own, and any competitor bidding on our brand terms. Output becomes creative
briefs and, where relevant, bid/budget cards (recommendations only — no automatic execution).

## Landing pages (creative's other half)
- Message match: ad promise = headline of the landing page.
- Send product ads to the product/collection page, not the home page.
- Track LP CVR per ad concept; recommend LP tests when CTR is strong but CVR is weak.
- Health check final URLs daily (status code, redirect target, load time).
