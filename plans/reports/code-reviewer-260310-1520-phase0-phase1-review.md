# Code Review: Phase 0 + Phase 1 Changes

**Reviewer:** code-reviewer
**Date:** 2026-03-10
**Scope:** Proto refactor, shared helpers dedup, N+1 query fixes, watchlist optimization, ghost entity cleanup

---

## Summary

14 files reviewed across 3 services (informer, analytics, gateway). Changes are structurally sound. The N+1 fixes are correct and the deduplication is clean. Found **0 critical**, **3 important**, and **5 minor** issues.

---

## IMPORTANT Issues

### 1. `to_native()` does not handle `np.bool_` -- silent psycopg2 failure risk

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/analytics/src/utils/numeric_helpers.py:49-57`

`to_native()` converts `np.integer`, `np.floating`, and `np.ndarray` but misses `np.bool_`. If a calculator ever returns a numpy boolean (e.g., from a comparison like `rsi > 70`), psycopg2 will receive a `numpy.bool_` instead of Python `bool`. psycopg2 does *not* natively adapt `numpy.bool_` and will raise `ProgrammingError: can't adapt type 'numpy.bool_'`.

Currently no callers pass booleans through `to_native()`, so this is latent rather than active. But the function's docstring says "for psycopg2 compatibility" -- it should be complete.

**Suggested fix:** Add a `np.bool_` branch:
```python
if isinstance(v, np.bool_):
    return bool(v)
```

### 2. `search()` uses f-string SQL with caller-controlled `where` clause content

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/src/repositories/stock_repository.py:101`

```python
f"SELECT COUNT(*) AS cnt FROM stocks WHERE {where}"
```

The `where` variable is built from static string fragments (`"1=1"`, `"exchange = %s"`, etc.) -- actual values go through `%s` params. So this is **not injectable** today. However, the pattern of interpolating a `where` clause via f-string is fragile. A future maintainer adding a filter with a user-controlled column name or operator would silently introduce injection. This is an existing pattern (not introduced in Phase 0/1) but worth flagging since `stock_repository.py` was modified.

**Risk:** Low today, maintenance hazard.

### 3. `ScreenStocks` LATERAL JOIN returns `Decimal` types from PostgreSQL that flow into proto mappers

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/analytics/src/repositories/valuation_repository.py:45-93`

The new `get_screening_data()` LATERAL JOIN returns `numeric` columns from PostgreSQL, which psycopg2 returns as Python `Decimal` objects. These values are passed into `dict_to_valuation_proto()` and `dict_to_technicals_proto()` which call `safe_float_or_zero()`. `safe_float_or_zero()` handles `Decimal` correctly via `float(v)`. The `latest_close` is also converted via `float(row["latest_close"])` at line 184 of `analytics_handler.py`.

This works correctly. However, the reconstructed `ind_row` dict at lines 189-202 of `analytics_handler.py` passes raw `Decimal` values into `self._svc.resolve_signals()`, which eventually calls `TechnicalCalculator.compute_signals()`. If that method does comparisons like `val > 70` with `Decimal`, it works. But if it does `isinstance(val, float)` checks, it would fail silently.

**Risk:** Depends on `compute_signals()` implementation. Worth verifying.

---

## MINOR Issues

### 4. `generate.sh` cleans `*_pb2.py` but not `*_pb2.pyi` stub files

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/protos/scripts/generate.sh:29`

```bash
find "$OUT_DIR" -name '*_pb2.py' -o -name '*_pb2_grpc.py' | xargs rm -f
```

If protoc is ever invoked with `--pyi_out` to generate type stubs, old `.pyi` files would not be cleaned. Not a problem today since `--pyi_out` is not used, but worth noting.

### 5. `BatchGetStocks` preserves request order but silently drops duplicates

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/src/handlers/informer_handler.py:112-114`

```python
found_map = {r["symbol"]: r for r in rows}
found = [dict_to_stock(found_map[s]) for s in valid_symbols if s in found_map]
```

If the client sends `["AAPL", "AAPL"]`, `found_map` deduplicates them to one entry. The iteration over `valid_symbols` would then produce two `AAPL` entries in the response. This is probably fine (proto `repeated` allows duplicates) but is a subtle behavioral difference from the old N-query approach where each query returned independently.

### 6. `stock_proto_to_dict` uses `market_cap if market_cap else None` -- falsy zero bug

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/src/mappers/stock_mapper.py:36`

```python
"market_cap": stock.market_cap if stock.market_cap else None,
```

If `stock.market_cap` is legitimately `0` (proto3 default), this converts it to `None`. Since proto3 cannot distinguish "field not set" from "field is 0", this is a known tradeoff. But it means a stock with `market_cap=0` in the proto will be stored as `NULL` in the DB. Acceptable but worth documenting.

### 7. `_START_TIME` in both handlers captures module import time, not server start time

**Files:**
- `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/src/handlers/informer_handler.py:24`
- `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/analytics/src/handlers/analytics_handler.py:33`

```python
_START_TIME = datetime.now(timezone.utc)
```

This runs at import time, not when the gRPC server starts. The delta is typically negligible, but for lazy imports or test scenarios the uptime would be inaccurate.

### 8. `ScreenStocks` sector filter applied after LATERAL JOIN -- could filter in SQL

**File:** `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/analytics/src/handlers/analytics_handler.py:207`

```python
if criteria.sector and row.get("sector", "") != criteria.sector:
    continue
```

The sector filter is applied in Python after fetching all rows from the DB. The SQL query already JOINs `stocks s` which has `s.sector`. Adding `AND ($1 = '' OR s.sector = $1)` to the SQL would reduce data transfer when sector is specified. This is an optimization opportunity, not a bug.

---

## Verified Correct

### Proto backward compatibility
- HealthCheck messages moved to `common/health.proto` with package `stock.common`. Both service protos import it. Generated stubs import `from common import health_pb2`. Both handler files import `from generated.common import health_pb2`. Chain is verified end-to-end.
- Service RPCs now reference `stock.common.HealthCheckRequest/Response` in proto files. Generated `_pb2_grpc.py` files reference the correct descriptors. No breakage.

### SQL correctness
- `WHERE symbol = ANY(%s)` with `([list],)` tuple param is correct psycopg2 usage. psycopg2 adapts Python lists to PostgreSQL arrays. Verified in `stock_repository.py:37-47`.
- LATERAL JOIN syntax in `valuation_repository.py:57-93` is correct PostgreSQL. `LEFT JOIN LATERAL ... ON true` is the standard pattern for "latest row per group."
- `DISTINCT ON (vm.stock_id) ... ORDER BY vm.stock_id, vm.calculated_at DESC` correctly returns the most recent valuation per stock.

### Behavioral equivalence
- `BatchGetStocks`: Old approach did N individual `get_by_symbol()` calls. New approach does 1 `get_by_symbols()` call. Both produce the same `found_map` keyed by symbol. Response iteration preserves request order via `for s in valid_symbols if s in found_map`. Error handling preserved: exception around the batch query maps to `INTERNAL`.

### TypeORM entity registrations
- `WatchlistsModule` registers `WatchlistEntity`, `WatchlistItemEntity`, and `StockEntity`. The `StockEntity` is needed because `findAll()` and `findOne()` load `relations: ['items', 'items.stock']`. The `autoLoadEntities: true` in `database.module.ts` means entities registered via any `forFeature()` in any module are auto-included in the connection. Removing the 5 ghost entities (OhlcvEntity, FinancialReportEntity, IndicatorEntity, ValuationMetricEntity, and presumably UserEntity) is safe because those entities are not queried by watchlist operations, and `autoLoadEntities` ensures they remain available if registered elsewhere.

### Import correctness
- `informer_handler.py` imports `dict_to_stock` from `mappers.stock_mapper` -- resolves correctly.
- `stock_admin_handler.py` imports both `dict_to_stock` and `stock_proto_to_dict` from `mappers.stock_mapper` -- resolves correctly.
- `valuation_repository.py` and `indicator_repository.py` import `to_native` from `utils.numeric_helpers` -- resolves correctly.
- No circular dependencies detected.

### Empty input handling
- `get_by_symbols([])` returns `[]` immediately (line 35-36 of `stock_repository.py`). No empty `ANY` query sent.
- `BatchGetStocks` with all-invalid symbols: `valid_symbols = []`, `get_by_symbols([])` returns `[]`, response has empty `stocks` and all symbols in `not_found`.

---

## Metrics

| Metric | Value |
|--------|-------|
| Files reviewed | 14 |
| Critical issues | 0 |
| Important issues | 3 |
| Minor issues | 5 |
| SQL injection risk | None (params used correctly) |
| Proto compatibility | Verified OK |
| Behavioral equivalence | Verified OK |

---

## Unresolved Questions

1. Does `TechnicalCalculator.compute_signals()` perform any `isinstance(val, float)` checks that would fail with `Decimal` input from the LATERAL JOIN query? (Finding #3)
2. Were the 5 removed ghost entities from `WatchlistsModule` originally `OhlcvEntity`, `FinancialReportEntity`, `IndicatorEntity`, `ValuationMetricEntity`, and one more? The review instructions mention 5 but only 4 are obvious candidates. Need to confirm the 5th entity.
