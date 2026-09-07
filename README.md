# Linda's Growth Agent

An autonomous ecommerce operator for **lindas.com** (Linda's Electric Quilters, Shopify Plus) with one goal:
**grow total sales 10% month-over-month while protecting gross profit.**

It watches the store the way an expert owner would, tells you what to do daily / weekly / monthly, alerts on
stock-outs across the top 500 sellers, flips the top 100 to pre-order automatically, drafts purchase orders,
proposes price moves from supply and demand, forecasts revenue against the target, audits lifecycle marketing,
and says which of those jobs can run without a human.

Start with **[docs/00-BASELINE-2026-09.md](docs/00-BASELINE-2026-09.md)** — the live audit that this plan is built on.

## Two ways to run it

**1. Interactive, in Claude Code (no keys needed).** The `/lindas-growth-agent` skill uses the Shopify, Klaviyo,
Slack and Gmail connectors already attached to this workspace:

```
/lindas-growth-agent daily brief
/lindas-growth-agent weekly review
/lindas-growth-agent are we pacing to target?
```

Schedule it as a Claude Routine (daily 07:00 CT) and the brief lands in Slack without anyone typing.

**2. Headless, on a schedule (GitHub Actions).**

```bash
pip install -e .
cp .env.example .env      # Shopify custom-app token, Klaviyo key, Slack webhook
lindas-agent daily        # brief + alerts, actions dry-run
lindas-agent daily --apply   # also flips top-100 OOS SKUs to pre-order
lindas-agent alerts       # stock/pre-order alerts only (runs every 2h)
lindas-agent weekly [--apply]  # purchasing plan, pricing, lifecycle audit
lindas-agent monthly      # scorecard, targets, lever mix
lindas-agent targets      # 12-month 10% ladder
```

Workflows in `.github/workflows/` run daily 07:00 CT, alerts every 2h, weekly Monday, monthly on the 1st.
Add repository secrets `SHOPIFY_SHOP`, `SHOPIFY_ACCESS_TOKEN`, `KLAVIYO_API_KEY`, `SLACK_WEBHOOK_URL`.

## What it does

| Area | What the agent does | Doc |
|---|---|---|
| Pace | MTD vs 10% target, month-end projection, required daily rate | [10-FORECASTING](docs/10-FORECASTING.md) |
| Funnel | Bot-day detection, CVR on clean data, guardrails (checkout completion, AOV, discount, returns) | [02-METRICS](docs/02-METRICS.md) |
| Stock | Top-500 out-of-stock alerts, low-cover vs vendor lead time, **top-100 → pre-order automatically** | [07-INVENTORY-ALERTS](docs/07-INVENTORY-ALERTS.md) |
| Purchasing | Reorder point + order-up-to 45 days at +10% demand, PO drafts per vendor | [09-PURCHASING](docs/09-PURCHASING.md) |
| Pricing | +3% when scarce & accelerating, −10% on overstock, margin floor, MAP guard | [08-PRICING-ENGINE](docs/08-PRICING-ENGINE.md) |
| Marketing | Klaviyo flow audit, campaign cadence, abandoned-checkout upside | [11-TRAFFIC](docs/11-TRAFFIC-PAID-ORGANIC.md) |
| Traffic | Attribution health, paid conversion plan, organic growth plan | [11-TRAFFIC](docs/11-TRAFFIC-PAID-ORGANIC.md) |
| Routine | Daily / weekly / monthly playbooks and checklists | [03](docs/03-PLAYBOOK-DAILY.md) · [04](docs/04-PLAYBOOK-WEEKLY.md) · [05](docs/05-PLAYBOOK-MONTHLY.md) |
| Automation | Full / semi / manual matrix, kill switches | [06-AUTOMATION-MATRIX](docs/06-AUTOMATION-MATRIX.md) |
| Flow | Event-driven recipes for Shopify Flow | [12-SHOPIFY-FLOW-RECIPES](docs/12-SHOPIFY-FLOW-RECIPES.md) |

## Configuration

All thresholds live in [`config/agent.yaml`](config/agent.yaml) (tiers, cover days, pricing steps, guardrails,
lever mix) and [`config/vendors.yaml`](config/vendors.yaml) (lead times, MOQ, pre-order permission).
Nothing writes to Shopify unless `--apply` is passed; even then only rule-bound, reversible actions run
(pre-order flips, ≤5% price moves on ranks 101–500). Everything else is a proposal in the brief.

## Layout

```
lindas_agent/
  connectors/   shopify.py (GraphQL + ShopifyQL), klaviyo.py, notify.py (Slack/email)
  inventory/    ranking.py, alerts.py, purchasing.py
  pricing/      engine.py
  forecast/     revenue.py
  metrics/      funnel.py (KPIs, bot detection, guardrails)
  marketing/    lifecycle.py (Klaviyo audit), traffic.py
  actions/      shopify_actions.py (dry-run by default)
  playbooks/    daily.py, weekly.py, monthly.py, context.py
  report.py, store.py (SQLite), config.py, cli.py
config/         agent.yaml, vendors.yaml
docs/           baseline, plan, metrics, playbooks, automation matrix, methods
.claude/skills/lindas-growth-agent/   interactive skill for Claude Code
.github/workflows/                    schedules + CI
tests/                                pytest (rules, forecast, actions)
```

## Development

```bash
pip install -e .[dev]
ruff check lindas_agent tests
pytest -q
```
