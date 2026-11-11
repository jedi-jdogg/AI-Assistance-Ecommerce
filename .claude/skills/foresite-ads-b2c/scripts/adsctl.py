#!/usr/bin/env python3
"""adsctl — deterministic helpers for the Foresite Ads Agent skills.

The agent uses this for the math and checks that must not depend on model judgment:

  scaffold      create clients/<slug>/ (client file, brand playbook, decision log) from the templates
  guard         check a Decision Card against the client file's guardrails  (exit 1 on FAIL)
  log           append a card event to clients/<slug>/decisions.jsonl
  breakeven     break-even / target ROAS and CPA from margin
  pace          month-to-date budget pacing
  pace-intraday project today's finish from a pooled same-weekday cumulative curve
  sig           two-proportion z-test (CTR / CVR A/B)
  b2b-budget    reverse-funnel: closed-won target -> leads -> budget

Stdlib only, except PyYAML for reading client files (pip install pyyaml).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"

ACCOUNT_KEY = {
    "meta_ads": "account_id",
    "google_ads": "customer_id",
    "linkedin_ads": "sponsored_account_id",
    "microsoft_ads": "account_id",
    "tiktok_ads": "advertiser_id",
    "pinterest_ads": "ad_account_id",
    "vibe_ctv": "advertiser_id",
}
MONEY_FIELDS = {"daily_budget", "lifetime_budget", "budget", "monthly_budget", "campaign_budget"}
BID_FIELDS = {"target_roas", "target_cpa", "bid_amount", "cost_cap", "bid_cap", "roas_goal"}
REQUIRED_CARD = ["id", "client", "platform", "account_id", "account_name", "category", "entity", "change",
                 "why", "risk", "rollback"]


# ----------------------------------------------------------------------------- io helpers
def load_yaml(path: str | Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:  # pragma: no cover
        sys.exit("PyYAML is required to read client files: pip install pyyaml")
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def norm_id(v) -> str:
    s = str(v or "").strip().lower()
    for prefix in ("act_", "urn:li:sponsoredaccount:"):
        s = s.removeprefix(prefix)
    return s.replace("-", "").replace(" ", "")


# ----------------------------------------------------------------------------- scaffold
def cmd_scaffold(a) -> int:
    out = Path(a.out) / a.slug
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()  # noqa: UP017
    subs = {"__SLUG__": a.slug, "__NAME__": a.name, "__MODEL__": a.model,
            "__TENANT__": str(a.tenant or "unknown"), "__DATE__": today}
    made = []
    for src, dst in (("client-account.yaml", "ads-account.yaml"), ("brand-playbook-template.md", "brand-playbook.md")):
        target = out / dst
        if target.exists() and not a.force:
            print(f"skip   {target} (exists; --force to overwrite)")
            continue
        text = (TEMPLATES / src).read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        if dst == "ads-account.yaml" and a.tenant:
            text = text.replace("foresite_tenant_id: null", f"foresite_tenant_id: {a.tenant}", 1)
        target.write_text(text, encoding="utf-8")
        made.append(target)
    log = out / "decisions.jsonl"
    if not log.exists():
        log.touch()
        made.append(log)
    for m in made:
        print(f"create {m}")
    return 0


# ----------------------------------------------------------------------------- guard
def guard_card(card: dict, client: dict) -> list[tuple[str, str]]:
    """Return [(PASS|FAIL|WARN, message)]."""
    res: list[tuple[str, str]] = []
    g = {**DEFAULT_GUARDRAILS, **(client.get("guardrails") or {})}

    missing = [k for k in REQUIRED_CARD if card.get(k) in (None, "", {})]
    res.append(("FAIL", f"card missing fields: {', '.join(missing)}") if missing else ("PASS", "card complete"))

    cl = client.get("client") or {}
    if cl.get("slug") and card.get("client") != cl.get("slug"):
        res.append(("FAIL", f"card client '{card.get('client')}' != client file '{cl.get('slug')}'"))

    plat = card.get("platform")
    pconf = (client.get("platforms") or {}).get(plat)
    if not pconf:
        res.append(("FAIL", f"platform '{plat}' not in client file"))
    else:
        key = ACCOUNT_KEY.get(plat, "account_id")
        want_id, want_name = pconf.get(key), pconf.get("account_name")
        if not want_id or not want_name:
            res.append(("FAIL", f"client file lacks {plat}.{key} / account_name — registry incomplete, no writes"))
        else:
            if norm_id(want_id) != norm_id(card.get("account_id")):
                res.append(("FAIL", f"account_id {card.get('account_id')} != registry {want_id} (WRONG ACCOUNT)"))
            else:
                res.append(("PASS", "account_id matches registry"))
            if str(want_name).strip().lower() != str(card.get("account_name", "")).strip().lower():
                res.append(("FAIL", f"account_name '{card.get('account_name')}' != registry '{want_name}'"))
            else:
                res.append(("PASS", "account_name matches registry"))
        if card.get("autonomy_level", 2) >= 2 and pconf.get("access") != "write":
            res.append(("WARN", f"{plat} access is '{pconf.get('access')}' — execution will need write access"))

    ent = card.get("entity") or {}
    tag = g.get("locked_name_tag")
    if tag and tag in str(ent.get("name", "")):
        res.append(("FAIL", f"entity is {tag} — never touched"))

    ch = card.get("change") or {}
    field = str(ch.get("field", ""))
    before, after = ch.get("before"), ch.get("after")
    if isinstance(before, (int, float)) and isinstance(after, (int, float)) and before > 0:
        step = (after - before) / before * 100
        if field in MONEY_FIELDS:
            lim_up, lim_dn = g["budget_step_up_max_pct"], g["budget_step_down_max_pct"]
            if step > lim_up:
                res.append(("FAIL", f"budget step +{step:.1f}% > {lim_up}% max"))
            elif step < -lim_dn:
                res.append(("FAIL", f"budget step {step:.1f}% < -{lim_dn}% max"))
            else:
                res.append(("PASS", f"budget step {step:+.1f}% within limits"))
        elif field in BID_FIELDS:
            lim = g["bid_target_step_max_pct"]
            res.append(("FAIL", f"bid/target step {step:+.1f}% > ±{lim}%") if abs(step) > lim
                       else ("PASS", f"bid/target step {step:+.1f}% within ±{lim}%"))

    hrs = card.get("hours_since_last_edit")
    if hrs is not None and field in MONEY_FIELDS and hrs < g["min_hours_between_budget_edits"]:
        res.append(("FAIL", f"last budget edit {hrs}h ago < {g['min_hours_between_budget_edits']}h"))

    conv = card.get("evidence_conversions")
    if conv is not None and card.get("category") in {"budget", "bid", "pause", "reallocation"} \
            and conv < g["min_conversions_for_decision"]:
        res.append(("WARN", f"only {conv} conversions behind this decision (< {g['min_conversions_for_decision']})"))

    cap = (client.get("budgets") or {}).get("monthly_cap_usd")
    proj = card.get("projected_month_spend_usd")
    if card.get("new_money"):
        res.append(("FAIL", "new money — escalation lane 1, needs Approver budget increase first"))
    elif cap and proj is not None and proj > cap:
        res.append(("FAIL", f"projected month spend ${proj:,.0f} > cap ${cap:,.0f} — this is NEW MONEY"))
    elif cap and proj is not None:
        res.append(("PASS", f"projected month spend ${proj:,.0f} within cap ${cap:,.0f}"))

    if not (client.get("approvals") or {}).get("approvers"):
        res.append(("FAIL", "client file has no approvers"))
    return res


DEFAULT_GUARDRAILS = {
    "budget_step_up_max_pct": 20,
    "budget_step_down_max_pct": 30,
    "min_hours_between_budget_edits": 72,
    "bid_target_step_max_pct": 15,
    "min_conversions_for_decision": 30,
    "locked_name_tag": "[LOCKED]",
}


def cmd_guard(a) -> int:
    card = json.loads(Path(a.card).read_text(encoding="utf-8"))
    client = load_yaml(a.client)
    res = guard_card(card, client)
    for status, msg in res:
        print(f"{status:4}  {msg}")
    failed = any(s == "FAIL" for s, _ in res)
    print("RESULT: FAIL — do not present for approval / do not execute" if failed else "RESULT: PASS")
    return 1 if failed else 0


# ----------------------------------------------------------------------------- log
def cmd_log(a) -> int:
    card = json.loads(Path(a.card).read_text(encoding="utf-8"))
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),  # noqa: UP017
             "status": a.status,
             "by": a.by, "channel": a.channel, "note": a.note, "card": card}
    path = Path(a.log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(",", ":")) + "\n")
    print(f"logged {card.get('id')} {a.status} -> {path}")
    return 0


# ----------------------------------------------------------------------------- math
def breakeven(margin: float, buffer: float = 0.0, aov: float | None = None) -> dict:
    if not 0 < margin <= 1:
        raise ValueError("margin must be a fraction in (0, 1], e.g. 0.35")
    be = 1 / margin
    out = {"break_even_roas": round(be, 2), "target_roas": round(be * (1 + buffer), 2)}
    if aov:
        out["break_even_cpa"] = round(aov * margin, 2)
        out["target_cpa"] = round(aov * margin / (1 + buffer), 2)
    return out


def month_pace(cap: float, spent: float, day: int, days_in_month: int) -> dict:
    elapsed = day / days_in_month
    pct = spent / cap if cap else 0.0
    remaining_days = days_in_month - day
    return {
        "mtd_pct_of_cap": round(pct * 100, 1),
        "month_elapsed_pct": round(elapsed * 100, 1),
        "projected_month_spend": round(spent / elapsed, 2) if elapsed else 0.0,
        "required_daily_to_hit_cap": round((cap - spent) / remaining_days, 2) if remaining_days > 0 else 0.0,
        "status": "OVER" if pct > elapsed * 1.1 else "UNDER" if pct < elapsed * 0.9 else "ON PACE",
    }


def intraday_projection(rows: list[dict], weekday: int, hour: int, so_far: float, n_days: int = 4) -> dict:
    """rows: {date: YYYY-MM-DD, hour: 0-23, value: hourly amount}. Pools the last n completed same-weekday days."""
    by_day: dict[str, dict[int, float]] = defaultdict(dict)
    for r in rows:
        by_day[r["date"]][int(r["hour"])] = float(r["value"])
    days = sorted(d for d in by_day if datetime.fromisoformat(d).weekday() == weekday)[-n_days:]
    if not days:
        raise ValueError("no history for that weekday")
    cum = sum(v for d in days for h, v in by_day[d].items() if h < hour)
    tot = sum(v for d in days for v in by_day[d].values())
    share = cum / tot if tot else 0.0
    return {"days_used": days, "share_of_day_by_hour": round(share, 4),
            "projected_finish": round(so_far / share, 2) if share else None}


def two_prop(a_conv: int, a_n: int, b_conv: int, b_n: int) -> dict:
    pa, pb = a_conv / a_n, b_conv / b_n
    p = (a_conv + b_conv) / (a_n + b_n)
    se = math.sqrt(p * (1 - p) * (1 / a_n + 1 / b_n))
    z = (pb - pa) / se if se else 0.0
    pval = math.erfc(abs(z) / math.sqrt(2))
    return {"rate_a": round(pa, 5), "rate_b": round(pb, 5), "lift_pct": round((pb / pa - 1) * 100, 1) if pa else None,
            "z": round(z, 3), "p_value": round(pval, 4), "significant_95": pval < 0.05}


def b2b_budget(won_target: float, deal_size: float, win_rate: float, sql_to_opp: float, mql_to_sql: float,
               lead_to_mql: float, cpl: float) -> dict:
    deals = won_target / deal_size
    opps = deals / win_rate
    sqls = opps / sql_to_opp
    mqls = sqls / mql_to_sql
    leads = mqls / lead_to_mql
    budget = leads * cpl
    return {"deals": math.ceil(deals), "opportunities": math.ceil(opps), "sqls": math.ceil(sqls),
            "mqls": math.ceil(mqls), "leads": math.ceil(leads), "budget": round(budget, 2),
            "cost_per_sql": round(budget / sqls, 2), "cost_per_opp": round(budget / opps, 2),
            "cac": round(budget / deals, 2), "pipeline_generated": round(opps * deal_size, 2)}


def _print(d: dict) -> int:
    print(json.dumps(d, indent=2))
    return 0


# ----------------------------------------------------------------------------- cli
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="adsctl", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scaffold")
    s.add_argument("--slug", required=True)
    s.add_argument("--name", required=True)
    s.add_argument("--model", choices=["b2c", "b2b"], required=True)
    s.add_argument("--tenant", type=int)
    s.add_argument("--out", default="clients")
    s.add_argument("--force", action="store_true")

    s = sub.add_parser("guard")
    s.add_argument("--card", required=True)
    s.add_argument("--client", required=True)

    s = sub.add_parser("log")
    s.add_argument("--card", required=True)
    s.add_argument("--log", required=True, help="clients/<slug>/decisions.jsonl")
    s.add_argument("--status", required=True,
                   choices=["proposed", "approved", "rejected", "expired", "superseded", "executing", "verified",
                            "failed", "drifted", "rolled_back", "held"])
    s.add_argument("--by", default="agent")
    s.add_argument("--channel", default="chat")
    s.add_argument("--note", default="")

    s = sub.add_parser("breakeven")
    s.add_argument("--margin", type=float, required=True, help="contribution margin fraction, e.g. 0.35")
    s.add_argument("--buffer", type=float, default=0.0, help="profit buffer over break-even, e.g. 0.25")
    s.add_argument("--aov", type=float)

    s = sub.add_parser("pace")
    s.add_argument("--cap", type=float, required=True)
    s.add_argument("--spent", type=float, required=True)
    s.add_argument("--day", type=int, required=True, help="completed days this month")
    s.add_argument("--days-in-month", type=int, required=True)

    s = sub.add_parser("pace-intraday")
    s.add_argument("--history", required=True, help="CSV with columns date,hour,value (hourly, not cumulative)")
    s.add_argument("--weekday", type=int, required=True, help="0=Mon … 6=Sun")
    s.add_argument("--hour", type=int, required=True, help="hours completed today (e.g. 10 at 10:00)")
    s.add_argument("--so-far", type=float, required=True)
    s.add_argument("--days", type=int, default=4)

    s = sub.add_parser("sig")
    for k in ("a-conv", "a-n", "b-conv", "b-n"):
        s.add_argument(f"--{k}", type=int, required=True)

    s = sub.add_parser("b2b-budget")
    s.add_argument("--won-target", type=float, required=True)
    s.add_argument("--deal-size", type=float, required=True)
    s.add_argument("--win-rate", type=float, required=True)
    s.add_argument("--sql-to-opp", type=float, required=True)
    s.add_argument("--mql-to-sql", type=float, required=True)
    s.add_argument("--lead-to-mql", type=float, required=True)
    s.add_argument("--cpl", type=float, required=True)

    a = p.parse_args(argv)
    if a.cmd == "scaffold":
        return cmd_scaffold(a)
    if a.cmd == "guard":
        return cmd_guard(a)
    if a.cmd == "log":
        return cmd_log(a)
    if a.cmd == "breakeven":
        return _print(breakeven(a.margin, a.buffer, a.aov))
    if a.cmd == "pace":
        return _print(month_pace(a.cap, a.spent, a.day, a.days_in_month))
    if a.cmd == "pace-intraday":
        with open(a.history, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return _print(intraday_projection(rows, a.weekday, a.hour, a.so_far, a.days))
    if a.cmd == "sig":
        return _print(two_prop(a.a_conv, a.a_n, a.b_conv, a.b_n))
    if a.cmd == "b2b-budget":
        return _print(b2b_budget(a.won_target, a.deal_size, a.win_rate, a.sql_to_opp, a.mql_to_sql,
                                 a.lead_to_mql, a.cpl))
    return 2


if __name__ == "__main__":
    sys.exit(main())
