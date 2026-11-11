# Foresite Ads Agent kit — human-in-the-loop advertising for any brand

Two Claude skills that run paid media for Foresite clients the way the Linda's Electric Quilters operation runs:
**the AI does measurement, monitoring, reporting, recommendations and verified execution; the human owns the
money.** Every platform change is a Decision Card that a named approver approves; one approval = one write.

| Skill | For | Lead platforms | Success metric |
|---|---|---|---|
| `foresite-ads-b2c` | Ecommerce / DTC / consumer brands | Google Shopping/PMax/Search, Meta, Microsoft, TikTok, Pinterest, CTV | Net profit, MER, nCAC |
| `foresite-ads-b2b` | Lead-gen / SaaS / services / sales-led brands | LinkedIn, Google Search, Microsoft (LinkedIn profile targeting), Meta retargeting | Pipeline $, cost per SQL, CAC payback |

## What the agent does

- **Connects** to the right Meta / Google / LinkedIn / Microsoft / CTV accounts per client, pins account IDs
  and names, and verifies read/write/tracking before any change (`shared/references/02-connections.md`).
- **Onboards a brand by itself**: ingests the Foresite Marketing Profile, website, Shopify/CRM data, ad-account
  history, competitors and reviews, and writes a brand-specific playbook + client file modeled on Linda's
  (`shared/references/10-brand-ingestion.md`). Targets and standing orders stay *proposed* until ratified.
- **Daily update** every morning: scoreboard, alerts, ≤ 7 Decision Cards (money, platform reallocation,
  targeting, audiences, creative, bids/keywords, feeds/landing pages, tracking, playbook changes), what was
  executed and verified, known gaps, QA (`shared/references/04-daily-update.md`).
- **Executes approved cards** with pre-flight (right account, unchanged state, guardrails), a single write,
  read-back verification and a decision log (`shared/references/03-decision-cards.md`).
- Weekly creative/search/audience reviews, monthly business review, intraday pacing for big spenders,
  competitor watch (Konvert), creative drafts (Foresite `generate-creative`), incrementality plans.

## Install / use (team members)

**1. Claude Code in this repo (works now).** Clone the repo; the skills load automatically.
```
/foresite-ads-b2c daily update lindas
/foresite-ads-b2c onboard <brand>
/foresite-ads-b2b connect <client>
approve DC-20261111-03
```

**2. claude.ai organization skills.** Build the zips and upload each in claude.ai (Settings → Capabilities /
Skills → upload), or have an org owner add them for everyone:
```bash
python3 ads-agent-kit/build.py --zip     # writes dist/foresite-ads-b2c.zip and dist/foresite-ads-b2b.zip
```

**3. Personal Claude Code (any repo).** Copy `.claude/skills/foresite-ads-b2c/` and `…-b2b/` into
`~/.claude/skills/`.

**Schedule the daily update:** in a session, ask "schedule the <client> ads daily update at 07:00 Central on
weekdays" — it becomes a recurring scheduled task.

## What has to be connected

| Need | Status in this workspace | Action |
|---|---|---|
| Foresite (tenant data, marketing profile, AI Ads metrics, budgets) | ✅ connected | — |
| Shopify, Klaviyo, Slack, Gmail, Drive, Calendly, Konvert, Vibe (CTV) | ✅ connected | — |
| **Meta / Google Ads / LinkedIn / Microsoft write access** | ❌ not connected | Build the **Foresite Ads Gateway** MCP (contract in `02-connections.md` §3) or install vetted third-party ad connectors as org custom connectors; add `ask` permission rules for write tools |
| CRM (HubSpot / Salesforce) for B2B | ❌ | Connect, or provide weekly exports |
| Attribution tool (FPX, TripleWhale, ThoughtMetric) | per client | ThoughtMetric connector needs re-authorization in claude.ai |

Without ad-platform connectors the agent still runs: it reports from Foresite data and exports, and its cards
carry click-path instructions for a human to execute.

## Layout

```
ads-agent-kit/                       ← edit here (source of truth)
  shared/references/01…10-*.md       operating model, connections, decision cards, daily update, guardrails,
                                     measurement, creative & competitive, platform playbooks,
                                     generic playbook, brand ingestion
  shared/templates/                  client-account.yaml, brand-playbook-template.md, brand-intake-questionnaire.md
  shared/scripts/adsctl.py           scaffold · guard · log · breakeven · pace · pace-intraday · sig · b2b-budget
  b2c/SKILL.md, b2c-playbook.md
  b2b/SKILL.md, b2b-playbook.md
  examples/                          sample Decision Card
  build.py                           assembles the skills (+ --zip, --check)
.claude/skills/foresite-ads-b2c/     ← built, self-contained (do not hand-edit)
.claude/skills/foresite-ads-b2b/     ← built, self-contained (do not hand-edit)
clients/<slug>/                      ads-account.yaml · brand-playbook.md · decisions.jsonl per client
```

After editing anything under `ads-agent-kit/`, run `python3 ads-agent-kit/build.py` (CI's test suite fails if
the built skills are stale).

## Design principles (from the Linda's operation)
1. A workstream's autonomy level is set by the **cost of being wrong**, not by what the AI can do. Spend sits at
   Level 2 (approve each change); measurement at 3–4; nothing at 5.
2. **Definitions are decisions** — every metric has one named source of record.
3. **Verify the deliverable, not the report.**
4. **Autonomy must be explicit** — standing orders are written into the client file and obeyed, not re-asked.
5. **A guard that holds is a feature** — the loop includes the right to not act.
