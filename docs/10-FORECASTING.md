# Revenue forecasting and pacing

## Daily model
forecast(day) = median(same weekday, last 4 weeks) × trend, trend = mean(last 14d) ÷ mean(prior 14d) clipped to ±25%.
Medians make the model robust to promo spikes (Sep 3: $88K vs typical $35K) and to the bot-driven days.

## Month projection
Projected = MTD actual + Σ forecast(remaining days). Status: ahead ≥ 103%, on track 97–103%, behind < 97%.
Required daily rate = (target − MTD) ÷ days left, printed next to the forecast rate so the gap is obvious.

## Targets
Target(M) = max(target(M−1), actual(M−1)) × 1.10 chained from Aug-2026 ($1,120,197). See `01-GROWTH-PLAN-10PCT.md`.

## Known limitations and next steps
- No holiday calendar yet: add promo/holiday multipliers (Black Friday week ≈ 2–3×, Christmas week ≈ 0.6×).
- No product-level forecast: purchasing uses simple velocity; move to weekly seasonal indices per category.
- Use last year's same-month ratio as a sanity check (Sep→Oct 2025 was +21%, Oct→Nov +22%, Nov→Dec −30%).
