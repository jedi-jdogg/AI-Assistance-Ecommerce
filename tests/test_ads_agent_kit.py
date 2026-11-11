"""Tests for the Foresite Ads Agent kit: guardrail checks, math helpers, and built-skill sync."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "ads-agent-kit"

spec = importlib.util.spec_from_file_location("adsctl", KIT / "shared" / "scripts" / "adsctl.py")
adsctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adsctl)

CLIENT = {
    "client": {"slug": "lindas"},
    "platforms": {"meta_ads": {"account_id": "act_864074647303601", "account_name": "Linda's Electric Quilters",
                               "access": "write"}},
    "budgets": {"monthly_cap_usd": 15000},
    "approvals": {"approvers": [{"name": "Owner"}]},
}


@pytest.fixture
def card():
    return json.loads((KIT / "examples" / "card-budget-increase.json").read_text())


def statuses(res):
    return [s for s, _ in res]


def test_example_card_passes(card):
    res = adsctl.guard_card(card, CLIENT)
    assert "FAIL" not in statuses(res), res


def test_wrong_account_fails(card):
    card["account_id"] = "act_111"
    res = adsctl.guard_card(card, CLIENT)
    assert any(s == "FAIL" and "WRONG ACCOUNT" in m for s, m in res)


def test_account_name_mismatch_fails(card):
    card["account_name"] = "Some Other Brand"
    assert "FAIL" in statuses(adsctl.guard_card(card, CLIENT))


def test_budget_step_too_large_fails(card):
    card["change"]["after"] = 600.0  # +50%
    res = adsctl.guard_card(card, CLIENT)
    assert any(s == "FAIL" and "budget step" in m for s, m in res)


def test_client_override_tightens_step(card):
    client = copy.deepcopy(CLIENT)
    client["guardrails"] = {"budget_step_up_max_pct": 10}
    assert "FAIL" in statuses(adsctl.guard_card(card, client))


def test_new_money_over_cap_fails(card):
    card["projected_month_spend_usd"] = 16000
    res = adsctl.guard_card(card, CLIENT)
    assert any(s == "FAIL" and "NEW MONEY" in m for s, m in res)


def test_locked_entity_fails(card):
    card["entity"]["name"] = "[LOCKED] Brand Search"
    assert "FAIL" in statuses(adsctl.guard_card(card, CLIENT))


def test_recent_edit_fails(card):
    card["hours_since_last_edit"] = 24
    assert "FAIL" in statuses(adsctl.guard_card(card, CLIENT))


def test_incomplete_registry_blocks_writes(card):
    client = copy.deepcopy(CLIENT)
    client["platforms"]["meta_ads"]["account_name"] = ""
    res = adsctl.guard_card(card, client)
    assert any(s == "FAIL" and "registry incomplete" in m for s, m in res)


def test_google_ids_normalize():
    assert adsctl.norm_id("191-524-4603") == adsctl.norm_id("1915244603")
    assert adsctl.norm_id("act_864074647303601") == "864074647303601"


def test_breakeven():
    r = adsctl.breakeven(0.35, 0.25, 120)
    assert r["break_even_roas"] == 2.86 and r["target_roas"] == 3.57 and r["break_even_cpa"] == 42.0


def test_breakeven_rejects_percent_input():
    with pytest.raises(ValueError):
        adsctl.breakeven(35)


def test_month_pace():
    r = adsctl.month_pace(30000, 15000, 10, 30)
    assert r["status"] == "OVER" and r["projected_month_spend"] == 45000


def test_intraday_projection_pools_same_weekday():
    rows = []
    for d in ("2026-10-14", "2026-10-21", "2026-10-28", "2026-11-04"):  # Wednesdays
        for h in range(24):
            rows.append({"date": d, "hour": h, "value": 100})
    rows.append({"date": "2026-11-05", "hour": 0, "value": 99999})  # Thursday, ignored
    r = adsctl.intraday_projection(rows, weekday=2, hour=12, so_far=1200)
    assert r["share_of_day_by_hour"] == 0.5 and r["projected_finish"] == 2400
    assert len(r["days_used"]) == 4


def test_two_prop_significance():
    assert adsctl.two_prop(100, 10000, 150, 10000)["significant_95"]
    assert not adsctl.two_prop(100, 10000, 105, 10000)["significant_95"]


def test_b2b_budget_reverse_funnel():
    r = adsctl.b2b_budget(500000, 25000, 0.25, 0.5, 0.4, 0.3, 150)
    assert r["deals"] == 20 and r["opportunities"] == 80 and r["sqls"] == 160
    assert r["budget"] == pytest.approx(200000.0) and r["cost_per_sql"] == pytest.approx(1250.0)


def test_built_skills_in_sync():
    out = subprocess.run([sys.executable, str(KIT / "build.py"), "--check"], capture_output=True, text=True,
                         check=False)
    assert out.returncode == 0, out.stdout


def test_skill_frontmatter():
    for model in ("b2c", "b2b"):
        text = (ROOT / ".claude" / "skills" / f"foresite-ads-{model}" / "SKILL.md").read_text()
        assert text.startswith("---\nname: foresite-ads-" + model + "\ndescription: ")
