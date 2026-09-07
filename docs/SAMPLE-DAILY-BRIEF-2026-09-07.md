# Linda's Daily Brief — 2026-09-07

_Produced from live Shopify + Klaviyo data on 7 Sep 2026 using the rules in `config/agent.yaml`. This is what the
07:00 CT Slack post looks like._

🟢 **2026-09 pace: ahead**
- Target (10% MoM): $1,232,217  ·  MTD: $419,851 (day 6/30)
- Projected month-end: $1,349,000 at a flat run-rate ($1,580,000 if the post-Labor-Day trend holds; trend capped +25%)
- Need $33,849/day for the rest of the month; forecast run-rate $38,700–48,400/day

**Week over week**: sales +56% · orders +35% · AOV +15% (Labor Day event Sep 1–6; expect reversion this week)

**Funnel (7-day, 7 clean days)**
- Sessions 140,260 → ATC 7,198 (5.1%) → Checkout 5,440 (76%) → Orders 1,924 (35%)
- CVR raw 1.37% · CVR engaged (orders / ATC sessions) 26.7%
- Note: orders (3,279) exceed completed web checkouts (1,924): Recharge renewals, B2B/draft orders and
  marketplace orders via LitCommerce are in sales but not in the web funnel.
- No bot-flagged days this window. Aug 6–9 (37K–73K sessions/day, flat ATC) were bots.

## 🔴 Critical (3)
🔴 [stock] #1 Hobbs 80/20 Heirloom Batting 96" Wide Batting Roll - 30 Yards — 225 on hand, 43.4/day → 5.2 days left; vendor lead 28d → Expedite PO with Hobbs Bonded Fibers today; pre-stage Pre-Order switch.
🔴 [preorder] #7 Hobbs Heirloom 80/20 Batting Package (Available for PRE-ORDER) / Queen (90"x108") — OUT OF STOCK, policy DENY, selling 6.6/day ($53,951 net / 90d, vendor Hobbs Bonded Fibers, lead 28d) → Switch to PRE-ORDER now: inventoryPolicy=CONTINUE, add 'Pre-Order' tag and ETA; raise PO with Hobbs. (auto)
🔴 [marketing] Abandoned Checkout flow not live — NOT LIVE (5 draft/manual variants) → Pick the best draft, QA, set Live. ~16,200 checkouts abandoned in August ≈ $70K/month recoverable at 5%.

## 🟠 Warnings (7)
🟠 [stock] #5 Hobbs Heirloom Bleached 80/20 108" Wide Batting Roll - 30 Yards — 99 on hand, 5.2/day → 19 days left; vendor lead 28d → Place replenishment PO with Hobbs this week.
🟠 [stock] Hobbs 80/20 Heirloom Batting 96" Wide Batting - By The Yard — 120 on hand, 18.4/day → 6.5 days left → PO with Hobbs this week (cuts come off the #1 roll; same supply risk).
🟠 [stock] Hobbs Heirloom 80/20 Fusible Batting Package / Crib — 129 on hand, 7.7/day → 17 days; lead 28d → PO this week.
🟠 [stock] Pellon Lightweight Nonwoven Fusible 20" By The Yard — 88 on hand, 5.1/day → 17 days; lead 21d → PO this week.
🟠 [marketing] Welcome Series / Abandoned Cart / Browse Abandonment / Post-Purchase / Winback flows not live — 0 live email flows; 2 live SMS flows → Publish best drafts; add UTMs.
🟠 [marketing] Email campaign cadence below minimum — 2 campaigns sent since Aug 1 (minimum 3/week) → Schedule Mon/Wed/Fri/Sun sends.
🟠 [traffic] Order attribution broken — 74% of orders have no referrer; email shows 11 attributed orders / 90d → UTM tracking on in Klaviyo; TripleWhale as source of truth.

## 🔵 Info
🔵 [stock] Pellon SF101 bolt (#3), Pellon 911FF (#16), Crafter Club — on-hand negative (untracked dropship feed) → Fix inventory tracking so alerts are meaningful.
🔵 [pricing] Overstock candidates for the weekly review: 460RT handle (15,726 units, 1,139d cover), 738T snips (1,459d), 428RT (660d), 45mm blades (418d) → bundle with mats/rulers rather than markdown.

## ⚙️ Automated actions (dry-run — enable with `--apply`)
| action | entity | detail | applied |
|---|---|---|---|
| preorder | Hobbs Heirloom 80/20 Batting Package (Available for PRE-ORDER) | policy→CONTINUE, +tag 'Pre-Order', ETA ~6w (2 variants: Queen, Twin 72"; vendor Hobbs Bonded Fibers) | dry-run |

## ✅ Today's operator checklist
1. Call Hobbs: expedite 96" rolls (order qty to 45-day cover ≈ 1,900 rolls, ~$300K at cost) and Queen packages; get ETAs for the pre-order page.
2. Approve the pre-order flip above (or run `lindas-agent daily --apply`).
3. Publish Abandoned Checkout + Welcome flows in Klaviyo today; turn on UTM tracking.
4. Send today's email (restock/pre-order story on Hobbs rolls; SMS Club offer holds the post-holiday run-rate).
5. Gorgias: pull ETA questions on Queen packages into the PDP pre-order copy.
