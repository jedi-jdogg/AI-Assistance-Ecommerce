from datetime import date

from lindas_agent.forecast.revenue import daily_forecast, month_pace, month_target, twelve_month_targets
from lindas_agent.metrics.funnel import detect_bot_days, guardrail_alerts, summarize


def test_targets_chain_ten_percent(settings):
    ladder = twelve_month_targets(settings)
    assert ladder[0][0] == "2026-09"
    assert abs(ladder[0][1] - 1120196.91 * 1.1) < 1
    assert abs(ladder[-1][1] / ladder[0][1] - 1.1 ** 11) < 1e-6


def test_month_target_chains_from_actual_when_beaten(settings):
    actuals = {"2026-08": 1120196.91, "2026-09": 1500000.0}
    t_oct = month_target(settings, date(2026, 10, 1), actuals)
    assert abs(t_oct - 1500000.0 * 1.1) < 1


def test_pace(settings, sales_history):
    p = month_pace(sales_history, settings, today=date(2026, 9, 6))
    assert p.month == "2026-09"
    assert p.mtd_actual == 70000 * 6
    assert p.projected_month_end > p.mtd_actual
    assert p.status in ("ahead", "on_track", "behind")
    fc = daily_forecast(sales_history, 5, settings)
    assert len(fc) == 5 and all(v > 0 for _, v in fc)


def test_bot_detection(settings, funnel_history):
    bots = detect_bot_days(funnel_history, settings)
    days = {b.day for b in bots}
    assert date(2026, 8, 7) in days and date(2026, 7, 30) not in days
    s = summarize(funnel_history, settings, 30)
    assert s.cvr_engaged == 220 / 1000


def test_guardrails_quiet_on_healthy_data(settings, sales_history, funnel_history):
    alerts = guardrail_alerts(sales_history, funnel_history, settings)
    assert not [a for a in alerts if a.severity.value == "critical"]
