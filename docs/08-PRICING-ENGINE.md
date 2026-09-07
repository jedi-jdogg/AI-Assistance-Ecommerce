# Pricing engine — supply and demand rules

## Signals (per variant, weekly)
- **Demand growth** g = units(last 14d) ÷ units(prior 14d) − 1
- **Days of cover** c = on-hand ÷ daily velocity (30d)
- **Gross margin** m = (price − unit cost) ÷ price

## Rules
| Situation | Condition | Move | Mode |
|---|---|---|---|
| Scarce & accelerating | c ≤ 14d and g ≥ +15% | +3% (charm-rounded, never above compare-at) | AUTO rank 101–500, SEMI rank 1–100 |
| Overstock & falling | c ≥ 180d and g ≤ −10% | −10%, floored at 25% margin | SEMI |
| Overstock but thin margin | as above and m < 40% | bundle instead of markdown | SEMI |
| MAP product | tag `MAP Pricing` | no change, ever | guard |
| Any | change > 5% in a week, or changed < 7 days ago | blocked | guard |

## Why these numbers
- Batting is a replenishment purchase with strong brand loyalty (Hobbs 80/20), so short-term price elasticity is
  low when scarce; +3% on a scarce roll protects margin and slows sell-out without hurting conversion.
- Long-tail notions with 400–1,400 days of cover (Famore handles/blades) are cash tied up; a −10% step every
  two weeks until velocity responds, floored at 25% margin, or a bundle when the margin is already thin.
- 5%/week cap keeps price history smooth for Google Shopping and avoids compare-at "was/now" whiplash.

## Elasticity learning (next step)
Every applied change is logged in SQLite (`price_changes`). After 4+ changes on a SKU, fit
Δunits/Δprice to estimate elasticity and let the step size adapt (raise more where |ε| < 1).

## Shipping and margin
Rolls are oversized freight; re:do package protection attaches on ~44% of orders. Review carrier cost per roll
monthly and pass through via price, not via surcharges that hit checkout completion.
