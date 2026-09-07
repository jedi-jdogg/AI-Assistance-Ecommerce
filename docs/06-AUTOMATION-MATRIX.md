# Automation matrix — what runs itself, what needs a click, what stays human

Legend: **AUTO** = agent/Flow executes and logs. **SEMI** = agent drafts, human approves (one click / reply).
**MANUAL** = human judgment; agent supplies the data. "Tool" = where the automation lives.

## Inventory & availability

| Task | Mode | Tool | Rule |
|---|---|---|---|
| Rank top 100 / top 500 daily | AUTO | agent | 90-day net sales, exclusions for non-physical items |
| Alert top-500 out of stock | AUTO | agent (2h job) → Slack | de-duped 24h |
| Flip top-100 OOS to pre-order (policy CONTINUE + tag + ETA) | **AUTO** | agent `--apply` / Shopify Flow | vendor on allowed list; else SEMI |
| Clear pre-order when restocked > 14d cover | AUTO | agent | |
| Low-cover warnings vs vendor lead time | AUTO | agent | |
| Draft POs to 45-day cover at +10% | SEMI | agent → Stocky | human sends |
| Expedite / vendor negotiation | MANUAL | phone/email | agent supplies qty + cover |
| Fix negative/untracked dropship feeds | MANUAL | Stocky, Matrixify | agent lists SKUs |
| Back-in-stock capture on OOS PDPs | AUTO | Klaviyo BIS / Wishlist Plus | |
| Pre-order order tagging + customer ETA email | AUTO | Shopify Flow + Klaviyo | |

## Pricing & margin

| Task | Mode | Tool | Rule |
|---|---|---|---|
| +3% on scarce, accelerating SKUs rank 101–500 | AUTO | agent `--apply` | ≤5%/wk, not MAP, compare-at respected |
| Any change on rank 1–100 | SEMI | agent → approval | |
| −10% on overstock with falling demand | SEMI | agent | margin floor 25% |
| Bundle instead of markdown when margin thin | SEMI | agent → Shopify Bundles / Rebuy | |
| Vendor cost pass-through | MANUAL | monthly | agent flags margin < floor |
| Discount-rate ceiling alert | AUTO | agent | > 12% of gross (7d) |

## Conversion

| Task | Mode | Tool | Rule |
|---|---|---|---|
| Bot-day detection and clean CVR reporting | AUTO | agent | z>3 & ATC<3% |
| Bot blocking rules | SEMI | Negate Bot Protection / Cloudflare | agent names the days/devices |
| Checkout-completion outage alert | AUTO | agent | < 22% 7d → critical |
| Zero-result search fixes | SEMI | Search & Discovery | weekly list |
| Cart cross-sell rules | SEMI | Rebuy | roll → thread/scissors/mat |
| CRO tests | MANUAL | theme / Checkout Blocks | one live at all times |

## Marketing & traffic

| Task | Mode | Tool | Rule |
|---|---|---|---|
| Abandoned checkout / cart / browse flows | **AUTO once live** | Klaviyo | publish drafts (SEMI, one time) |
| Welcome, post-purchase, winback, review, BIS | AUTO once live | Klaviyo | |
| Campaign cadence alert (< 3/wk) | AUTO | agent | |
| Campaign drafting (copy + product picks) | SEMI | agent / Claude + Klaviyo MCP | human schedules |
| UTM enforcement | AUTO | Klaviyo tracking settings | one-time toggle |
| Paid pause/scale by ROAS | SEMI | TripleWhale + ad platforms | < 2× pause, > 4× +20% |
| Shopping feed availability for pre-order | AUTO | Data Feed Watch rule | tag Pre-Order → availability=preorder |
| SEO content production | SEMI | Claude drafts, human publishes (see `mwc-blog-pipeline` skill) | 2/wk |
| Marketplace stock sync | AUTO | LitCommerce | |

## Reporting

| Task | Mode | Tool |
|---|---|---|
| Daily brief 07:00 CT | AUTO | GitHub Actions → Slack/email, or Claude Routine using the skill |
| Weekly review Monday | AUTO | same |
| Monthly plan on the 1st | AUTO | same |
| Ad-hoc questions ("how are we pacing?") | AUTO | `/lindas-growth-agent` skill in Claude Code |

## Kill switches
- `pricing.enabled: false` in `config/agent.yaml` stops all price proposals.
- Omit `--apply` and every Shopify write becomes a dry-run line in the brief.
- Remove a vendor from `inventory.preorder.allowed_vendors` and its pre-order flips become SEMI.
