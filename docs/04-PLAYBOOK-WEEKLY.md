# Weekly playbook (Monday, ~2 hours)

`lindas-agent weekly` produces: purchasing plan, pricing proposals, lifecycle audit, traffic mix.

## 1. Purchasing (30 min)
- Review the PO table: urgency **now** = below lead-time cover; **this_week** = below ROP; **plan** = will breach within review period.
- Quantities target 45 days of cover at +10% demand, rounded to MOQ/case. Adjust for known vendor promos or holiday closures (Pellon / Warm Company / RNK closures were last December's problem).
- Send POs via Stocky. Record on-order quantities (optional CSV to the agent) so ROP accounts for them.
- Top-100 items with lead time > 21 days (Hobbs, Quilters Dream): keep 60 days in peak (Oct–Dec, Mar–May).

## 2. Pricing (20 min)
- Approve/decline rank 1–100 proposals. Ranks 101–500 within ±5% auto-apply if `--apply` is on.
- Overstock list: choose markdown vs bundle. Famore handles/blades: bundle with cutting mats and rulers rather than markdown (margin is fine, demand is the issue).
- Check compare-at integrity on anything changed.

## 3. Lifecycle & campaigns (30 min)
- Flow audit: every required flow live? If not, publish the best draft (pick the one with the newest edits, QA on a test profile).
- Cadence: schedule the week — Mon new arrivals / restock, Wed education (tutorial, batting guide), Fri offer or pre-order drop, Sun Crafter Club members.
- Segments to hit: batting buyers 60–120 days ago (re-order cycle), interfacing buyers, engaged non-buyers 30d.
- Check Klaviyo attributed revenue share; goal ≥ 20% within 90 days.

## 4. Conversion (20 min)
- Search & Discovery: fix top zero-result queries (synonyms: "wadding"→batting, "fusible fleece"→987F).
- Rebuy: review cart cross-sell performance; make sure roll pages offer thread/scissors bundles.
- One CRO test live at all times (PDP ETA badge, free-shipping bar, sticky ATC on mobile). Run 2 weeks min.
- Speed: mobile LCP under 2.5s; audit app scripts quarterly.

## 5. Traffic (20 min)
- Attribution health: blank-referrer share trending down? UTMs on everything.
- Paid: pause ad groups < 2× ROAS (14d), scale > 4× by 20%. Feed health in Data Feed Watch (pre-order items must show `preorder` availability, not out of stock).
- Organic: publish 2 pieces (buying guide, how-to). Update one collection page with copy + FAQ schema. Check GSC for pages losing clicks.
- Marketplaces (LitCommerce): sync stock; list top-100 on Amazon/eBay/Etsy where MAP allows.

## 6. Report back
- Update the promo calendar and the lever tracker in the monthly doc. Note anything the agent got wrong → adjust `config/agent.yaml`.
