# Phase 2 Implementation Report — Error Handling & Resilience

**Date:** 2026-03-10 15:35 | **Branch:** main

## Phase 2.1: gRPC Call Timeouts

**Problem:** All `lastValueFrom()` calls had no deadline — if a Python service hangs, the gateway hangs indefinitely.

**Fix:** Added private `call<T>()` wrapper in both service classes with RxJS `timeout()` pipe.

| Endpoint type | Timeout |
|---------------|---------|
| Health checks | 3s |
| Standard queries | 10s (default) |
| Heavy queries (price history, financials, screening, batch analysis) | 15s |

**Files:**
- `gateway/src/stocks/stocks.service.ts` — 9 methods now use `this.call()`
- `gateway/src/analytics/analytics.service.ts` — 6 methods now use `this.call()`

---

## Phase 2.2: DB Connection Retry on Startup

**Problem:** `db_pool.initialize()` called bare — if Postgres isn't ready, service crashes on boot.

**Fix:** Wrapped with `retry_with_backoff(max_retries=5, backoff_factor=2.0)`. Delay: 2s → 4s → 8s → 16s → 32s (total ~62s window).

**Files:**
- `services/informer/src/server.py` — added import + retry wrapper
- `services/analytics/src/server.py` — added import + retry wrapper
- `services/analytics/src/utils/retry.py` — **NEW** (copy from informer, identical implementation)

---

## Phase 2.3: DTO Validation Hardening

| DTO | Field | Before | After |
|-----|-------|--------|-------|
| `CreateStockDto` | `symbol` | `@IsString @MaxLength(10)` | `@IsNotEmpty @Matches(/^[A-Z0-9.]{1,10}$/)` |
| `CreateStockDto` | `name` | `@IsString @MaxLength(255)` | Added `@IsNotEmpty` |
| `BatchGetStocksDto` | `symbols[]` | `@IsString({each})` | Added `@Matches(/^[A-Za-z0-9.]{1,10}$/, {each})` |
| `GetPriceHistoryQueryDto` | `interval` | `@IsString` | `@IsIn(['1d','1wk','1mo'])` |
| `GetPriceHistoryQueryDto` | `startDate/endDate` | `@IsString` | `@Matches(/^\d{4}-\d{2}-\d{2}$/)` |
| `GetTechnicalIndicatorsQueryDto` | `timeframe` | `@IsString` | `@IsIn(['1d','1wk'])` |
| `ScreenStocksDto` | `trendDirection` | `@IsString` | `@IsIn(['Bullish','Bearish'])` |
| `ScreenStocksDto` | `sortBy` | `@IsString` | `@IsIn(['valuation_score','match_score','current_price'])` |

**Files:**
- `gateway/src/stocks/dto/create-stock.dto.ts`
- `gateway/src/stocks/dto/batch-get-stocks.dto.ts`
- `gateway/src/stocks/dto/get-price-history-query.dto.ts`
- `gateway/src/analytics/dto/screen-stocks.dto.ts`
- `gateway/src/analytics/dto/get-technical-indicators-query.dto.ts`

---

## Verification
- Gateway TypeScript build: `tsc --noEmit` passes clean

## Unresolved (Not in Scope)
- CORS `origin: true` → env-based restriction (needs prod deploy context)
- Rate limiting (`@nestjs/throttler`) — not yet planned
- DB password required in production — config guard deferred
