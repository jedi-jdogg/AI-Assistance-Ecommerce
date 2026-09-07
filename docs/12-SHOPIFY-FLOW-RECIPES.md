# Shopify Flow recipes (Flow is installed)

These run inside Shopify with no code. The agent covers the analytics; Flow covers the event-driven bits.

1. **Top-100 stock-out → pre-order**
   Trigger: Inventory quantity changed. Condition: available ≤ 0 AND product tag `top-100` (agent maintains the tag daily). Actions: add product tag `Pre-Order`; send Slack message; (app action) set variant policy Continue if your pre-order app supports it — otherwise the agent does it.
2. **Restock → clear pre-order**
   Trigger: Inventory quantity changed. Condition: available > 20 AND tag `Pre-Order`. Actions: remove tag; Slack.
3. **Pre-order order handling**
   Trigger: Order created. Condition: any line item product tag = `Pre-Order`. Actions: add order tag `preorder`; hold fulfillment; Klaviyo event `Placed Pre-Order` (ETA email).
4. **Top-500 tag maintenance**
   Agent writes `top-100` / `top-500` tags nightly (`tagsAdd`/`tagsRemove`) so Flow, Rebuy, Klaviyo and Data Feed Watch can all key off rank.
5. **High-value order alert**: Order created, total > $500 → Slack (VIP handling, Crafter Club invite).
6. **Discount abuse guard**: Order created with discount > 25% of subtotal → tag `review-discount`, Slack.
7. **Negative inventory**: Inventory quantity changed, available < 0 → tag `inventory-fix`, Slack (feeds the agent's INFO list).
8. **Low-stock vendor ping**: available < 14-day cover threshold (agent-set metafield `custom.reorder_point`) → email buyer.
9. **Review request**: Order fulfilled + 10 days → Klaviyo event (if not using Klaviyo Reviews' native trigger).
10. **Bot signal**: Not available in Flow; the agent's daily bot flag + Negate rules cover it.
