# 02 — Connections: getting the agent onto the *right* accounts

The single most expensive mistake an ads agent can make is a correct change on the **wrong client's account**.
Everything in this file exists to make that impossible: every client has one registry entry, every account ID
is pinned, and every write re-confirms the account name and ID live before it runs.

## 1. The connection map

```
                ┌───────────────────────── Foresite platform ──────────────────────────┐
 Team member →  │ tenant_id ─ marketing-profile (business, personas, keywords, competitors)
 (Claude Code / │           ─ ai_ads_metrics (Instant AI Ads: FB Acq/Retargeting, Google  │
  claude.ai)    │             Search/Shopping/Display, YouTube, Bing — daily, per tenant)  │
                │           ─ roas-report / tenant-budget / integration-status            │
                │           ─ tenant_attributes  ← ads.client_config (this skill's file)  │
                │           ─ platform_accesses  ← one row per ad platform per tenant      │
                │           ─ mcp_servers        ← the Ads Gateway connector               │
                └───────────────┬──────────────────────────────────────────────────────────┘
                                │ OAuth tokens per tenant (Foresite secrets — never in chat)
         ┌──────────────┬───────┴──────┬───────────────┬──────────────┬───────────────┐
      Meta Ads      Google Ads     LinkedIn Ads   Microsoft Ads   TikTok/Pinterest/  Vibe CTV
   (Marketing API)  (Ads API, MCC)  (Marketing API) (Bing Ads API)  Reddit/Amazon…    (connected MCP)
         └──────── revenue/lead truth: Shopify · CRM (HubSpot/Salesforce) · FPX/ThoughtMetric/TripleWhale · GA4 ────────┘
```

## 2. Client registry (do this first for every client)

Each client gets **one** config, stored in this order of preference:
1. Foresite tenant attribute `ads.client_config` (shared by the whole team) — read with `tenant-attribute get`.
2. Repo file `clients/<slug>/ads-account.yaml` (created by `adsctl.py scaffold`).

Template: `templates/client-account.yaml`. Minimum fields before **any** write is allowed:
`client.slug`, `client.foresite_tenant_id`, `model` (b2c|b2b), each platform's `account_id` **and**
`account_name`, `approvals.approvers`, `budgets.monthly_cap_usd`, `metrics.source_of_record`.

Writing the registry to Foresite (`tenant-attribute set`, `database-write` on `platform_accesses`) is a shared
write: propose it as a Decision Card the first time, then it is maintenance.

### `platform_accesses` row per platform (Foresite DB)

| column | value |
|---|---|
| `tenant_id` | Foresite tenant |
| `platform_key` | `meta_ads`, `google_ads`, `linkedin_ads`, `microsoft_ads`, `tiktok_ads`, `pinterest_ads`, `reddit_ads`, `amazon_ads`, `vibe_ctv` |
| `status` | `ACCESS_PENDING` → `ACCESS_VERIFIED` (read OK) → `WRITE_VERIFIED` (a no-op/read-back write test passed) → `ACCESS_BROKEN` |
| `verification_method` | `oauth_gateway`, `mcp_thirdparty`, `manual_export` |
| `account_identifier` | e.g. `act_864074647303601`, `191-524-4603`, `urn:li:sponsoredAccount:5xxxxxxx` |
| `capabilities` | JSON: `{"read":true,"write":false,"conversions_api":true,"audiences":true,"token_expires":"2027-01-10"}` |
| `checked_at` | last verification time — the daily update flags anything > 24h stale |

## 3. Recommended architecture: the Foresite **Ads Gateway** connector

Build (or buy) **one** MCP server that fronts all ad platforms, register it in Foresite `mcp_servers` and add it
to claude.ai as an **organization custom connector** (Settings → Connectors → Add custom connector) so every
team member gets the same tools after signing in. Tokens stay server-side, keyed by tenant.

Why one gateway instead of a separate third-party MCP per platform:
- **The approval gate is enforced server-side**, not just by the model's good behavior: `execute_change`
  refuses any card that is not `approved` by a listed Approver, has expired, or whose `before` no longer
  matches live state.
- One audit log for every write across platforms (`mcp_tool_call_logs` already exists in Foresite).
- Per-tenant isolation: a session scoped to tenant A cannot even list tenant B's accounts.
- Uniform tool contract, so the skill does not care which platform it is talking to.

### Tool contract the skills expect

| Tool | Kind | Purpose |
|---|---|---|
| `ads_list_accounts(tenant_id)` | read | Accounts this tenant has connected, with name, ID, currency, timezone, token expiry, write capability |
| `ads_get_insights(account, level, date_range, fields, breakdowns)` | read | Spend, impressions, clicks, conversions, value, reach, frequency; breakdowns by age/gender/placement/device/geo |
| `ads_get_entities(account, level, filter)` | read | Campaigns/ad sets(ad groups)/ads with status, budget, bid strategy, targeting, creative IDs |
| `ads_get_change_history(account, since)` | read | Platform change log — catches edits made outside the agent |
| `ads_search_terms` / `ads_auction_insights` | read | Google/Microsoft search hygiene |
| `ads_list_audiences` / `ads_audience_membership_update` | read / L3 write | Hashed membership adds/removes with size-delta guard |
| `ads_propose_change(card)` | write (queue only) | Stores a Decision Card; returns `card_id` |
| `ads_approve(card_id, approver, channel)` | write (queue only) | Called by the approval surface (Slack button, Ops Console) — **not** by the agent on a human's behalf |
| `ads_execute_change(card_id)` | **platform write** | Executes exactly one approved card; returns before/after as read back from the platform |
| `ads_rollback(card_id)` | platform write | Applies the card's stored rollback (itself requires approval unless an emergency-brake order covers it) |

Until the gateway exists, use the interim options in §5 and keep the gate in the skill + Claude permissions.

## 4. Platform-by-platform setup

Verify current scopes/limits in each platform's developer docs at setup time; platforms change these often.

### Meta (Facebook / Instagram / Messenger / Audience Network)
- **Access path:** client adds Foresite's Business Manager as a **Partner** on the ad account (and Page, Pixel/
  Dataset, Catalog) with *Manage campaigns* (write) or *View performance* (read). Never use a personal login.
- **Token:** a **System User** token in Foresite's Business Manager (does not expire like 60-day user tokens).
  Permissions: `ads_read`, `ads_management`, `business_management`; `pages_read_engagement` /
  `pages_manage_ads` for Page-backed ads; `catalog_management` for Advantage+ catalog ads.
- **IDs to pin:** ad account `act_<id>`, Page ID, Instagram account ID, Pixel/Dataset ID, Catalog ID, Business ID.
- **Must also verify:** Conversions API live and **Event Match Quality** per key event; domain verified;
  Aggregated Event Measurement priorities; Special Ad Category set where required.
- Linda's example: ad account `864074647303601` (~370 campaigns).

### Google Ads (Search, Shopping, PMax, Demand Gen, YouTube, Display)
- **Access path:** client links their account under Foresite's **Manager (MCC) account**. Read = Read only,
  write = Standard access.
- **API:** Google Ads API **developer token** on the MCC (Basic or Standard access for production), an OAuth
  client, scope `https://www.googleapis.com/auth/adwords`, header `login-customer-id` = MCC ID.
- **Token trap (Linda's dead token):** an OAuth consent screen left in **"Testing"** issues refresh tokens that
  expire after **7 days**. Publish the OAuth app to **Production** (and complete verification) so refresh tokens
  persist. The daily update reports days-since-failure until it is fixed.
- **IDs to pin:** customer ID (10 digits), MCC ID, Merchant Center ID, GA4 property ID, conversion action IDs.
- **Must also verify:** enhanced conversions, consent mode v2 (EEA/UK traffic), offline/CRM conversion import
  (B2B), Merchant Center diagnostics (B2C), auto-tagging on.
- Linda's example: Google Ads `1915244603`.

### LinkedIn (Campaign Manager)
- **Access path:** client grants the Foresite user/app a role on the **Ad Account**: *Campaign Manager* or
  *Account Manager* (write), *Viewer* (read); plus Page admin/“Sponsored content poster” for the Company Page
  (needed for Sponsored Content and Thought Leader Ads).
- **API:** a LinkedIn developer app with the **Advertising API** product approved (application review
  required). Scopes typically `r_ads`, `rw_ads`, `r_ads_reporting`, `r_organization_social`,
  `rw_conversions` (Conversions API). Access tokens are short-lived (~60 days) with refresh tokens for approved
  apps (~1 year) — track both expiries.
- **IDs to pin:** `urn:li:sponsoredAccount:<id>`, Company Page `urn:li:organization:<id>`, Insight Tag partner ID,
  conversion rule IDs, Lead Gen Form IDs, Matched Audience (company/contact list) IDs.
- **Must also verify:** Insight Tag firing, LinkedIn CAPI or CRM sync for offline conversions, Lead Gen Form
  → CRM sync (HubSpot/Salesforce native integration), Revenue Attribution Report (if CRM connected).

### Microsoft Advertising
- MCC-equivalent **Manager account** link; API developer token + Microsoft identity OAuth; pin Customer ID and
  Account ID. B2B bonus: **LinkedIn profile targeting** (company, industry, job function) on Microsoft search.
  Google import scheduler can mirror Google campaigns — the agent must treat imported changes as writes.

### Others (same contract, add when the client runs them)
TikTok (Business Center partner + Marketing API app; `advertiser_id`), Pinterest (Business access +
`ad_account_id`), Reddit, Snap, X, Amazon Ads (DSP/Sponsored — profile ID per marketplace), **Vibe CTV**
(already connected as an MCP in this workspace: `list_advertisers`, `query_metrics`, `create_or_update_campaign`
— writes still need a card), OpenAI/ChatGPT Ads where available.

### Revenue / lead truth (connect before trusting any ROAS)
- **B2C:** Shopify (connected MCP), the client's attribution tool (FPX `/api/profit` for Linda's, TripleWhale,
  ThoughtMetric, Northbeam), GA4, Klaviyo.
- **B2B:** CRM (HubSpot / Salesforce) with opportunity stages and amounts, marketing automation, GA4, call
  tracking (CallRail), calendar booking (Calendly is connected in this workspace).

## 5. Interim options until the Ads Gateway ships

| Option | Read | Write | Gate | Notes |
|---|---|---|---|---|
| **A. Third-party ad MCP connectors** (Meta, Google Ads, LinkedIn) added as org custom connectors | ✅ | varies | Skill protocol **+ Claude permission `ask` rules** on every write tool | Vet vendor security, token custody and write coverage before use. Google's open-source Ads MCP is read-oriented. |
| **B. Foresite data only** (`ai_ads_metrics`, `roas-report`, `marketing-profile`) | ✅ (Foresite-run AI Ads channels) | ❌ | — | Good for daily reporting on Foresite-managed spend today |
| **C. Export mode** (CSV/Sheets exports from each platform, uploaded or in Drive) | ✅ | ❌ | Human executes | Cards include exact click-paths; the agent verifies from the next export |

### Make the approval button physical in Claude Code (belt and braces)
Add `ask` rules so every platform-write tool prompts, even in auto mode. In the repo's `.claude/settings.json`
(names depend on the connector you install — list tools first, then pin them):

```json
{
  "permissions": {
    "ask": [
      "mcp__ads-gateway__ads_execute_change",
      "mcp__ads-gateway__ads_rollback",
      "mcp__meta-ads__*update*", "mcp__meta-ads__*create*",
      "mcp__google-ads__*mutate*",
      "mcp__linkedin-ads__*create*", "mcp__linkedin-ads__*update*",
      "mcp__Vibe__create_or_update_campaign", "mcp__Vibe__publish_campaign",
      "mcp__Foresite__tenant-budget"
    ]
  }
}
```

The chat approval ("approve DC-…") authorizes the card; the permission prompt is the physical button that lets
that one write through. Both must happen.

## 6. Connection verification checklist (run with `connect` / on every new client)

For each platform the client runs:
1. List accessible accounts → find the one in the client file → **account ID and account name both match**.
   Mismatch or multiple candidates → stop; ask the Operator which one, never guess.
2. Read last 30 days of insights → totals within ±2% of the platform UI or the Foresite `ai_ads_metrics` row.
3. Read entity list → count matches; note campaigns not following the naming convention.
4. Token expiry known and > 14 days out (else a 🔴 known-gap line).
5. Write capability: confirm role/permission; **do not** make a test write on a live entity. Use the gateway's
   validate-only mode (Google `validate_only`, Meta/LinkedIn draft objects) if available.
6. Tracking: pixel/tag firing, CAPI/enhanced conversions, conversion actions marked primary as intended.
7. Record result in `platform_accesses` (status, capabilities, checked_at) and the client file.
8. Print a **Connection Report**: platform · account name · ID · read/write · token expiry · tracking health ·
   gaps. This report opens every new client's first daily update.

## 7. Security rules (non-negotiable)
- Never paste, echo, log or store tokens, secrets or raw customer PII in chat, Slack, files or cards.
- Customer lists are uploaded **hashed** (SHA-256, normalized) only; raw emails never appear in any output.
- Never move data between tenants. A session works one client at a time; switching clients re-reads the registry.
- Personal ad accounts and personal logins are not used for client work.
