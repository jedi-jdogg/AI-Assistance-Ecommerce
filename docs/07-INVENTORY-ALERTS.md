# Inventory alerts: top-500 out-of-stock and top-100 pre-order

## Ranking
- Universe: active, inventory-tracked variants. Excluded: package protection (re:do), gift cards, memberships,
  digital items (patterns in `ranking.exclude_*`).
- Metric: trailing 90-day **net sales** per variant (`ranking.rank_by`, alternative `units`).
- Recomputed on every run; rank is stored daily in SQLite so movement can be reviewed.

## Tiers and rules

| Condition | Rank ≤ 100 (critical tier) | Rank 101–500 (watch tier) |
|---|---|---|
| On-hand ≤ 0, policy DENY | 🔴 CRITICAL, category `preorder` → flip to pre-order (AUTO if vendor allowed) + PO | 🟠 WARNING → reorder, enable BIS capture |
| On-hand ≤ 0, policy CONTINUE, no Pre-Order label | 🔵 INFO → add tag/ETA (AUTO) | same |
| Cover < max(7d, ½ lead time) | 🔴 CRITICAL → expedite PO | — |
| Cover < max(14d, lead time) | 🟠 WARNING → PO this week | 🟠 WARNING |
| On-hand negative | 🔵 INFO → fix tracking (untracked dropship feed) | same |

Cover = on-hand ÷ (30-day units ÷ 30). Lead times come from `config/vendors.yaml`.

## Pre-order mechanics (no pre-order app installed)
1. `productVariantsBulkUpdate` → `inventoryPolicy: CONTINUE` so the PDP stays buyable.
2. `tagsAdd` → `Pre-Order` (drives theme badge, Flow rules, Data Feed Watch availability, Klaviyo segment).
3. ETA text: theme block reads a product metafield `custom.preorder_eta` (set by hand or by Flow; default 6 weeks).
4. Shopify Flow: order contains Pre-Order item → tag order `preorder`, send Klaviyo event `Placed Pre-Order`.
5. Reversal: on-hand > 0 and cover ≥ 14 days → policy DENY, remove tag (agent AUTO).

Recommended upgrade: install a selling-plan-based pre-order app (e.g. PreProduct, Purple Dot) so partial payment,
per-variant ETAs and Shop Pay compatibility are handled natively. The agent's rules stay the same; only the
action changes from policy flip to selling-plan assignment.

## Today's live examples (7 Sep 2026)
- #1 Hobbs 80/20 96" roll: 225 on hand, 43/day → **5 days**. CRITICAL low cover.
- #7 Hobbs Heirloom package Queen: 0 on hand, policy DENY, 197 sold/30d → CRITICAL pre-order flip.
- Hobbs 96" by the yard: 120 on hand, 18/day → 7 days.
- Hobbs Bleached 108" roll: 99 on hand → 20 days (lead 28d) → WARNING.
- Pellon SF101 / 911FF: negative on-hand → INFO, fix feed.

## Delivery
`lindas-agent alerts` every 2 hours (GitHub Actions) → Slack `#lindas-growth`. Same alert key is suppressed
for 24h. The daily brief repeats all open criticals.
