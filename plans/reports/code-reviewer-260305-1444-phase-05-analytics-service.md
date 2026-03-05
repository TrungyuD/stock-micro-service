# Code Review: Phase 5 — Analytics Service Metrics Engine

**Reviewer:** code-reviewer | **Date:** 2026-03-05 | **Score: 8/10**

---

## Summary

Solid implementation of a gRPC analytics service with clean separation (repos, calculators, handler, scheduler). Math is mostly correct, schema/proto alignment is good, parameterized queries used throughout. Key issues: Bollinger Bands uses `ddof=1` (sample std) instead of population std, `_signals` dict missing from cached DB rows, handler exceeds 200-line limit, and screening filter logic has subtle truthy-value bugs with proto defaults.

---

## 1. Schema Alignment

**Status: PASS**

| Code Column | DB Column | Match |
|---|---|---|
| `indicators.rsi_14` | `rsi_14 DECIMAL(6,2)` | OK |
| `indicators.sma_20/50/200` | `sma_20/50/200 DECIMAL(12,4)` | OK |
| `indicators.ema_20/50` | `ema_20/50 DECIMAL(12,4)` | OK |
| `indicators.macd_line/signal/histogram` | `macd_line/signal/histogram DECIMAL(12,4)` | OK |
| `indicators.bb_upper/middle/lower` | `bb_upper/middle/lower DECIMAL(12,4)` | OK |
| `valuation_metrics.*` | All columns match | OK |
| UPSERT conflict keys | `(stock_id, time)` / `(stock_id, calculated_at)` | Matches UNIQUE constraints |

**No column name mismatches found.**

---

## 2. Proto Alignment

**Status: PASS with notes**

- All 7 RPCs implemented: `GetValuationMetrics`, `GetTechnicalIndicators`, `GetStockAnalysis`, `BatchAnalysis`, `ScreenStocks`, `TriggerCalculation`, `HealthCheck`
- Proto field mapping in `_dict_to_valuation_proto` and `_dict_to_technicals_proto` correctly maps to all proto fields
- `BollingerBands.band_width` and `percent_b` correctly computed in handler from stored values
- `RSI.signal`, `MovingAverages.trend_signal`, `MACDIndicator.signal` populated from `_signals` dict

**Issue [MEDIUM]:** When `_dict_to_technicals_proto` receives a cached DB row (from `_ind_repo.get_latest`), the `_signals` key is **not present** in the DB row — it's only added by `TechnicalCalculator.compute()`. This means cached rows will always produce `"Neutral"` for all signal fields.
- **Impact:** RPCs returning cached data show wrong signals until recalc.
- **Fix:** Recompute signals from the DB row when `_signals` is missing, or always recompute signals at proto-mapping time.

---

## 3. Math Correctness

### RSI (Wilder Smoothing) — CORRECT
- Seed: `avg_gain = mean(gains[:14])`, `avg_loss = mean(losses[:14])`
- Wilder smoothing: `avg = (avg * 13 + current) / 14`
- Handles `avg_loss == 0` → returns 100.0
- Rounds to 4 decimal places

### SMA — CORRECT
- `np.mean(closes[-N:])` for N = 20, 50, 200
- Correct slicing for most-recent window

### EMA — CORRECT
- Seed with SMA of first `period` values
- Multiplier `k = 2 / (period + 1)` — standard EMA (not Wilder's 1/N)
- Note: This is the **standard EMA**, appropriate for MACD and general use

### MACD (12/26/9) — CORRECT
- `MACD line = EMA12 - EMA26`
- `Signal = EMA9 of MACD line` (only valid after EMA26 stabilizes)
- `Histogram = MACD - Signal`
- `valid_start = 25` correctly identifies where EMA26 first produces valid output

### Bollinger Bands (20/2) — **ISSUE [LOW]**
- `np.std(window, ddof=1)` uses **sample std dev** (N-1 denominator)
- Traditional Bollinger Bands use **population std dev** (`ddof=0`)
- Difference is small (sqrt(20/19) = ~1.026x multiplier), but worth noting for purists
- **Recommendation:** Use `ddof=0` for strict BB compliance

### EPS Growth Rate (CAGR) — CORRECT
- `CAGR = (newest/oldest)^(1/years) - 1`
- Guards against negative/zero base EPS
- Requires >= 2 data points

### Valuation Scoring — REASONABLE
- Incremental weighted average approach works but produces **unequal weighting** depending on factor count. The first factor has weight 1/1, second gets 1/2, third 1/3, fourth 1/4.
- Effectively: PE~40%, PEG~27%, PB~20%, PS~13% — actually close to the stated weights (40/30/20/10)
- Accidental but reasonable behavior

---

## 4. Security (SQL Injection)

**Status: PASS**

- All queries use `%s` parameterized placeholders
- No string concatenation in SQL
- `SELECT *` used in a few places (indicator_repository, valuation_repository `get_latest`) — acceptable for internal service but ideally specify columns for forward compatibility

---

## 5. Error Handling & gRPC Status Codes

**Status: PASS**

| Scenario | Code | Correct |
|---|---|---|
| Missing/empty symbol | `INVALID_ARGUMENT` | YES |
| Symbol not found | `NOT_FOUND` | YES |
| Insufficient data | `NOT_FOUND` | YES (could argue `FAILED_PRECONDITION`) |
| Internal exception | `INTERNAL` | YES |
| Empty batch | Returns empty response | YES |

- All RPCs wrapped in try/except with `logger.exception`
- `HealthCheck` gracefully reports `NOT_SERVING` on DB failure

---

## 6. Thread Safety

**Status: PASS**

- `psycopg2.pool.ThreadedConnectionPool` — designed for multithreaded gRPC
- Context manager properly commits/rollbacks and always returns connection to pool
- `TechnicalCalculator` and `ValuationCalculator` are stateless — safe for concurrent use
- `TriggerCalculation` spawns daemon thread — safe, but no way to monitor/cancel running jobs
- APScheduler `BackgroundScheduler` uses its own thread pool — compatible

**Minor concern:** `TriggerCalculation` fire-and-forget has no dedup. Two rapid calls will both run full recalcs concurrently. Not a correctness issue (upsert is idempotent) but wastes resources.

---

## 7. Code Quality / DRY

### GOOD
- Calculator/repo/handler separation is clean
- `_safe_div`, `_f`, `_i` guard functions avoid repetitive null checks
- `_is_fresh_today` caching avoids unnecessary recomputation
- Consistent logging patterns
- Config via pydantic-settings is clean

### ISSUES

**[HIGH] analytics_handler.py is 581 lines — exceeds 200-line limit**
- Proto mapping helpers (`_dict_to_valuation_proto`, `_dict_to_technicals_proto`) ~80 lines
- Screening helpers (`_passes_*`, `_compute_match_score`, `_sort_screened`) ~55 lines
- Recommendation helpers (`_combine_recommendation`, `_build_rationale`) ~55 lines
- **Fix:** Extract into separate modules: `proto_mappers.py`, `screening_helpers.py`, `recommendation_helpers.py`

**[MEDIUM] `_signals` dict not persisted — cached path is broken**
- `TechnicalCalculator.compute()` attaches `_signals` to result dict
- `indicator_repository.upsert()` does NOT store `_signals` (no DB columns for it)
- When `_get_or_compute_technicals` returns cached row, `_signals` is missing
- All signal fields default to `"Neutral"`, `buy_signals=0`, `sell_signals=0`
- **Fix:** Either persist signals in DB, or recompute `_derive_signals()` at proto-mapping time from the stored indicator values

**[MEDIUM] Screening filter bug with proto default values**
- In `_passes_valuation_criteria`, conditions like `if c.min_pe and pe and pe < c.min_pe` rely on proto3 default of `0.0` being falsy
- This **works by accident** for proto3 (default `0.0` is falsy in Python), but it means clients CANNOT filter with `min_pe=0` intentionally
- `rsi_overbought` and `rsi_oversold` are `bool` defaults `False` — these work correctly

**[LOW] DRY violation: recalculation logic duplicated**
- `AnalyticsHandler._compute_and_persist_technicals()` duplicates `CalculationScheduler._recalculate_technicals()`
- Same for valuation
- **Fix:** Extract shared `compute_and_persist_*` functions or have scheduler use handler methods

**[LOW] Duplicate `_f()` helper**
- `valuation_calculator.py` defines `_f()` (returns `None` on failure)
- `analytics_handler.py` defines `_f()` (returns `0.0` on failure)
- Different semantics, same name — confusing. Rename handler's to `_f_or_zero()` or similar

**[LOW] `datetime` import in scheduler methods**
- `_recalculate_technicals` and `_recalculate_valuation` import `datetime` inside method body — move to top-level

---

## 8. Additional Observations

**[INFO] `forward_pe` is just a copy of `trailing_pe`**
- `valuation_calculator.py` line 62: `result["forward_pe"] = result["trailing_pe"]`
- Proto has `forward_pe` field; DB has `forward_pe` column
- Currently no forward EPS data source — acceptable placeholder, but should be documented or omitted from responses

**[INFO] EV/EBITDA approximation is very rough**
- EV = market_cap (ignores debt - cash)
- EBITDA = operating_income (ignores depreciation/amortization)
- Schema has `total_liabilities`, `total_assets` — could improve EV estimate with `market_cap + total_liabilities - (total_assets - total_liabilities)` if desired
- Acceptable for v1

**[INFO] Dividend yield / payout ratio always None**
- No dividend data in `financial_reports` table
- Both fields persist as NULL and return `0.0` via proto

**[INFO] `db_dsn` property returns dict, not a DSN string**
- Name suggests a string; returns kwargs dict. Minor naming nit.

---

## Defect Summary

| Severity | Count | Items |
|---|---|---|
| HIGH | 1 | Handler file exceeds 200 lines (581 lines) |
| MEDIUM | 2 | `_signals` missing on cached rows; screening filter edge case |
| LOW | 4 | DRY violations (recalc duplication, duplicate `_f`), Bollinger ddof, inline imports |
| INFO | 4 | forward_pe placeholder, EV/EBITDA approximation, dividend always None, dsn naming |

---

## Recommended Fixes (Priority Order)

1. **Split analytics_handler.py** into handler + `proto_mappers.py` + `screening_helpers.py` + `recommendation_helpers.py`
2. **Fix `_signals` on cached path** — recompute signals in `_dict_to_technicals_proto` when `_signals` key is absent, using the stored RSI/SMA/MACD values
3. **Extract shared recalculation logic** — create a shared module used by both handler and scheduler
4. **Rename duplicate `_f()`** in handler to `_f_or_zero()` for clarity
5. **Bollinger Bands**: change `ddof=1` to `ddof=0` for standard BB formula

---

## Unresolved Questions

1. Is `forward_pe` expected to diverge from `trailing_pe` in a future phase, or should it be omitted from responses until real forward EPS data is available?
2. Should `TriggerCalculation` deduplicate concurrent requests (e.g., via a lock or job queue)?
3. Will dividend data be added to the `financial_reports` schema, or should dividend_yield/payout_ratio be removed from the proto?
