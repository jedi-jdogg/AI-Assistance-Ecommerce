# Purchasing recommendations

## Method (per variant in the top 500 with velocity)
- Demand d = 30-day daily velocity × 1.10 (plan for the growth target, not for flat).
- Horizon H = vendor lead time + 7-day review period.
- Safety stock = 1.65 × σ_daily × √H (≈95% service). σ from the 14d vs prior-14d swing, floored at Poisson.
- **Reorder point** ROP = d × H + safety.
- **Order quantity** = d × 45 days − (on-hand + on-order), rounded up to MOQ / case pack.
- Urgency: **now** if cover ≤ lead time; **this_week** if cover ≤ H; **plan** otherwise.
- Lines are grouped into one PO draft per vendor with estimated cost from `inventoryItem.unitCost`.

## Vendor notes (from `config/vendors.yaml`)
| Vendor | Lead | Notes |
|---|---|---|
| Hobbs Bonded Fibers | 28d | 34% of revenue; run 60-day cover Oct–Dec and Mar–May |
| Quilters Dream | 42d | Queen rolls ~8 weeks; keep permanent pre-order option |
| Pellon | 21d | Fix negative feed; December closure |
| Warm Company | 21d | December closure |
| Checker | 7d | Fastest; use for fill-ins |
| Famore | 14d | Overstocked; no POs until cover < 120d |

## Seasonality
Quilting demand peaks Oct–Dec (holiday gifting, retreats) and Mar–May (guild shows). Increase target cover to
60 days for batting six weeks before each peak; the monthly playbook triggers the vendor calls.

## Inputs the agent cannot see
- Open POs (Stocky) — pass `on_order` as `{variant_id: qty}` (CSV import planned) so ROP does not double-order.
- Vendor promos/closures — put them in `vendors.yaml notes`; the weekly review prints them.
