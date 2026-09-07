"""Revenue forecasting and 10%-growth pacing.

Model (deliberately simple, explainable, and robust to the store's promo spikes):
  base_dow[d]  = median of the last 4 same-weekday values (28-day window)
  trend        = clip(mean(last 14d) / mean(prior 14d), 1-cap, 1+cap)
  forecast[t]  = base_dow[weekday(t)] * trend
Month-end projection = MTD actual + sum(forecast over remaining days).
Target for month M  = actual(M-1) * (1 + monthly_target_pct), chained from the baseline month.
"""
from __future__ import annotations

import calendar
import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from ..config import Settings
from ..models import DailySales


@dataclass
class Pace:
    month: str
    target: float
    mtd_actual: float
    projected_month_end: float
    days_elapsed: int
    days_in_month: int
    required_daily_rate: float      # to hit target from here
    forecast_daily_rate: float
    status: str                     # ahead | on_track | behind

    @property
    def gap(self) -> float:
        return self.projected_month_end - self.target


def month_target(settings: Settings, month: date, monthly_actuals: dict[str, float]) -> float:
    """Chain 10% from the baseline month. If the prior month beat its target, chain from the actual."""
    pct = float(settings.get("growth.monthly_target_pct", 0.10))
    base_month = str(settings.get("growth.baseline_month"))
    base_value = float(settings.get("growth.baseline_total_sales"))
    y, m = map(int, base_month.split("-"))
    cur = date(y, m, 1)
    target = base_value
    while cur < month.replace(day=1):
        prev_key = cur.strftime("%Y-%m")
        # next month's target grows from the larger of (prior target, prior actual)
        prior_actual = monthly_actuals.get(prev_key, 0.0)
        target = max(target, prior_actual) * (1 + pct)
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return target


def daily_forecast(history: list[DailySales], horizon_days: int, settings: Settings, metric: str = "total_sales") -> list[tuple[date, float]]:
    if not history:
        return []
    hist = sorted(history, key=lambda d: d.day)
    values = {d.day: getattr(d, metric) for d in hist}
    last_day = hist[-1].day
    dow_window = int(settings.get("forecast.dow_window_days", 28))
    short = int(settings.get("forecast.trend_short_days", 14))
    cap = float(settings.get("forecast.trend_cap", 0.25))

    recent = [values[d] for d in sorted(values) if d > last_day - timedelta(days=dow_window)]
    by_dow: dict[int, list[float]] = {}
    for d in sorted(values):
        if d > last_day - timedelta(days=dow_window):
            by_dow.setdefault(d.weekday(), []).append(values[d])
    overall = statistics.median(recent) if recent else 0.0
    base = {k: statistics.median(v) for k, v in by_dow.items()}

    last14 = [values[d] for d in sorted(values) if d > last_day - timedelta(days=short)]
    prev14 = [values[d] for d in sorted(values) if last_day - timedelta(days=2 * short) < d <= last_day - timedelta(days=short)]
    trend = 1.0
    if last14 and prev14 and statistics.mean(prev14) > 0:
        trend = statistics.mean(last14) / statistics.mean(prev14)
        trend = max(1 - cap, min(1 + cap, trend))

    out = []
    for i in range(1, horizon_days + 1):
        d = last_day + timedelta(days=i)
        out.append((d, base.get(d.weekday(), overall) * trend))
    return out


def month_pace(history: list[DailySales], settings: Settings, today: date | None = None) -> Pace:
    today = today or (max(h.day for h in history) if history else date.today())
    first = today.replace(day=1)
    dim = calendar.monthrange(today.year, today.month)[1]
    mtd = sum(h.total_sales for h in history if first <= h.day <= today)
    remaining = dim - today.day
    fc = daily_forecast(history, remaining, settings)
    projected = mtd + sum(v for _, v in fc)

    # monthly actuals for chaining targets
    monthly: dict[str, float] = {}
    for h in history:
        monthly[h.day.strftime("%Y-%m")] = monthly.get(h.day.strftime("%Y-%m"), 0.0) + h.total_sales
    target = month_target(settings, today, monthly)
    required = (target - mtd) / remaining if remaining > 0 else 0.0
    fc_rate = (sum(v for _, v in fc) / remaining) if remaining > 0 else 0.0
    ratio = projected / target if target else 1.0
    status = "ahead" if ratio >= 1.03 else ("on_track" if ratio >= 0.97 else "behind")
    return Pace(
        month=today.strftime("%Y-%m"), target=target, mtd_actual=mtd, projected_month_end=projected,
        days_elapsed=today.day, days_in_month=dim, required_daily_rate=required,
        forecast_daily_rate=fc_rate, status=status,
    )


def twelve_month_targets(settings: Settings) -> list[tuple[str, float]]:
    pct = float(settings.get("growth.monthly_target_pct", 0.10))
    base_month = str(settings.get("growth.baseline_month"))
    y, m = map(int, base_month.split("-"))
    cur = date(y, m, 1)
    val = float(settings.get("growth.baseline_total_sales"))
    out = []
    for _ in range(12):
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
        val *= 1 + pct
        out.append((cur.strftime("%Y-%m"), val))
    return out
