# Analytics Service — Phase 5 Implementation Report

**Agent:** fullstack-developer
**Date:** 2026-03-05

---

## Files Created

### Repositories (`src/repositories/`)
| File | Purpose |
|---|---|
| `stock_data_repository.py` | READ-ONLY access to `stocks`, `ohlcv`, `financial_reports` |
| `indicator_repository.py` | Read/write `indicators` table with upsert on `(stock_id, time)` |
| `valuation_repository.py` | Read/write `valuation_metrics` table; `get_all_latest()` uses DISTINCT ON for ScreenStocks |

### Calculators (`src/calculators/`)
| File | Purpose |
|---|---|
| `technical_calculator.py` | Pure-numpy RSI-14 (Wilder), SMA 20/50/200, EMA 20/50, MACD 12/26/9, Bollinger 20/2σ + signal derivation |
| `valuation_calculator.py` | PE, forward PE, PEG (EPS CAGR), P/B, P/S, EV/EBITDA (approx), dividend_yield placeholder, valuation_signal/score |

### Handler (`src/handlers/`)
| File | Purpose |
|---|---|
| `analytics_handler.py` | All 7 RPCs: GetValuationMetrics, GetTechnicalIndicators, GetStockAnalysis, BatchAnalysis, ScreenStocks, TriggerCalculation, HealthCheck |

### Scheduler (`src/scheduler/`)
| File | Purpose |
|---|---|
| `calculation_scheduler.py` | APScheduler cron Mon-Fri @ configurable hour (default 17:00 EST) recalculates all stocks |

### Infrastructure
| File | Change |
|---|---|
| `src/server.py` | Fully wired — DB pool, repos, calcs, handler, scheduler, graceful shutdown |
| `src/config.py` | Added `db_pool_min/max`, `enable_scheduler`, `calc_hour/calc_minute`, `db_dsn` property |
| `src/database.py` | Rewritten to full `DatabasePool` class matching Informer pattern (ThreadedConnectionPool + execute helper) |
| `requirements.txt` | Replaced pandas-ta with `numpy>=1.26`, `pandas>=2.0`, added `APScheduler==3.10.4`, `pytz` |
| `Dockerfile` | New — mirrors Informer Dockerfile; generates analytics proto stubs at build time |
| `.env.example` | Added `DB_POOL_MIN/MAX`, `ENABLE_SCHEDULER`, `CALC_HOUR/CALC_MINUTE` |

---

## Architecture Summary

```
gRPC request
    │
    ▼
AnalyticsHandler
    ├── get_or_compute_technicals()  →  TechnicalCalculator.compute(bars)  →  IndicatorRepository.upsert()
    ├── get_or_compute_valuation()   →  ValuationCalculator.compute(...)   →  ValuationRepository.upsert()
    └── cache check: _is_fresh_today() — skip recompute if same-day cached result exists

CalculationScheduler (BackgroundScheduler)
    └── recalculate_all() Mon-Fri @ 17:00 EST
```

## Technical Indicator Math
- **RSI-14:** Wilder's exponential smoothing (seed = SMA of first 14 deltas)
- **SMA:** numpy mean over sliding windows (20, 50, 200)
- **EMA:** custom `_ema()` with SMA seed + `k = 2/(n+1)` multiplier
- **MACD:** EMA12 − EMA26; Signal = EMA9 of MACD; Histogram = MACD − Signal
- **Bollinger:** SMA20 ± 2 × sample-stddev(20)

## Compile Results
All 10 source files: ✓ `py_compile` passed with no errors

---

## Unresolved Questions
1. **Dividend data** — `financial_reports` schema has no dividend column; `dividend_yield` and `payout_ratio` return `None` until a dividend field is added to the schema or sourced from the Informer.
2. **Forward EPS** — no separate forward_eps column; `forward_pe` uses trailing EPS as proxy.
3. **EV/EBITDA** — uses operating_income as EBITDA proxy and market_cap (price × shares) as EV proxy; does not account for debt/cash (not in schema).
4. **`_signals` dict persistence** — the `_signals` helper dict is computed at runtime and attached to the in-memory result; it is NOT stored in the DB. ScreenStocks technical filtering on cached `ind_row` from DB will not have `_signals` — the `_passes_technical_criteria` function handles this gracefully (returns True when `_signals` missing).
