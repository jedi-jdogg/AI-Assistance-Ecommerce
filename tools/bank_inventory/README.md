# Bank inventory projection

Builds `reports/Lindas_Projected_Inventory_Nov2026-Oct2027.xlsx`: a SKU-level 12-month projected
inventory purchase list, summarized by product category, with reconciliations for lender review.

- `prep.py` — cleans ShopifyQL sales (TTM + last 91 days), owned-location inventory (GraphQL),
  and Bill.com bills into one dataset; maps ~160 Shopify product types to 10 categories; applies
  exclusion rules (non-inventory, returns-only, archived, retired SKUs).
- `build.py` — writes the workbook with live formulas (Assumptions drive every projection).

Source extracts are pulled interactively via the Shopify / Bill.com connectors and are not committed
(they contain full order-level financials). Paths at the top of each script point to the session scratchpad.
