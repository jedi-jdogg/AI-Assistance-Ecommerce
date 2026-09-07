"""Command line entry point.

  lindas-agent daily            # brief + stock/pre-order alerts (dry-run actions)
  lindas-agent daily --apply    # also flip top-100 OOS to pre-order
  lindas-agent alerts           # stock alerts only (run every 2h)
  lindas-agent weekly [--apply] # purchasing + pricing + lifecycle audit
  lindas-agent monthly          # scorecard + targets
  lindas-agent forecast         # pace only
  lindas-agent targets          # 12-month ladder
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .config import load_settings
from .connectors.notify import deliver
from .forecast.revenue import month_pace, twelve_month_targets
from .inventory.alerts import stock_alerts
from .report import render_alerts, render_pace


def _write(report: str, name: str) -> Path:
    out = Path("reports")
    out.mkdir(exist_ok=True)
    p = out / f"{date.today().isoformat()}-{name}.md"
    p.write_text(report, encoding="utf-8")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lindas-agent")
    ap.add_argument("command", choices=["daily", "alerts", "weekly", "monthly", "forecast", "targets"])
    ap.add_argument("--apply", action="store_true", help="execute automated Shopify actions (default dry-run)")
    ap.add_argument("--no-send", action="store_true", help="print only, do not deliver to Slack/email")
    args = ap.parse_args(argv)
    settings = load_settings()

    if args.command == "targets":
        print("\n".join(f"{m}: ${v:,.0f}" for m, v in twelve_month_targets(settings)))
        return 0

    from .playbooks.context import build_context  # imported lazily: needs credentials

    if args.command == "forecast":
        ctx = build_context(settings, need_catalog=False, need_funnel=False)
        print(render_pace(month_pace(ctx.sales, settings, ctx.today)))
        return 0

    if args.command == "alerts":
        ctx = build_context(settings, need_catalog=True, need_funnel=False, history_days=1)
        alerts = stock_alerts(ctx.ranked, settings)
        dedupe = int(settings.get("inventory.alert_dedupe_hours", 24))
        fresh = [a for a in alerts if ctx.store.should_send(a.key, dedupe)]
        for a in fresh:
            ctx.store.mark_sent(a.key, a.severity.value)
        if fresh:
            body = render_alerts(fresh, 60)
            if args.no_send:
                print(body)
            else:
                deliver(f"Linda's stock alerts ({len(fresh)})", body)
        return 0

    ctx = build_context(settings)
    if args.command == "daily":
        from .playbooks.daily import run_daily
        report = run_daily(ctx, apply=args.apply)
    elif args.command == "weekly":
        from .playbooks.weekly import run_weekly
        report = run_weekly(ctx, apply=args.apply)
    else:
        from .playbooks.monthly import run_monthly
        report = run_monthly(ctx)

    path = _write(report, args.command)
    if args.no_send:
        print(report)
    else:
        deliver(f"Linda's {args.command} — {date.today().isoformat()}", report)
    print(f"report written to {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
