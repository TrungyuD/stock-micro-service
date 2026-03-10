# Code Review: Phase 2 -- Error Handling & Resilience

## Scope
- **Files reviewed**: 12 (10 changed + 2 scouted: grpc-exception.filter.ts, main.ts)
- **LOC**: ~550
- **Focus**: gRPC timeout wrapper, DB retry logic, DTO validation hardening

## Overall Assessment

Phase 2 is structurally sound. The `call()` wrapper, retry decorator, and DTO tightening are reasonable additions. However, there is one **critical** issue with timeout error propagation through the exception filter, one **important** breaking-change risk from inconsistent symbol casing rules, and several medium-priority items around DRY violations and retry safety.

---

## CRITICAL

### 1. RxJS `TimeoutError` leaks as HTTP 500 with misleading gRPC error metadata

**Files**: `gateway/src/stocks/stocks.service.ts:44-46`, `gateway/src/analytics/analytics.service.ts:39-41`, `gateway/src/common/filters/grpc-exception.filter.ts:57`

**Problem**: When `timeout(ms)` fires, RxJS throws a `TimeoutError` (not a gRPC error). This error has no `.code`, no `.status`, no `.details` property. The `GrpcExceptionFilter` falls through to `const grpcCode = exception?.code ?? exception?.status ?? 2` which resolves to `2` (gRPC UNKNOWN), mapping to HTTP 500.

The client receives:
```json
{"statusCode": 500, "message": "Timeout has occurred", "timestamp": "..."}
```

This is wrong. A timeout on a downstream gRPC call should return **HTTP 504 Gateway Timeout**, not 500. The current filter has no branch for non-gRPC, non-HttpException errors. `TimeoutError` is neither, so it gets misclassified as gRPC code 2.

**Impact**: Monitoring dashboards will conflate real server errors (500) with timeout events. Clients cannot distinguish "service is down" from "service is slow." Retry logic on frontends that only retries on 504 will not trigger.

**Fix**: Add a `TimeoutError` check in `GrpcExceptionFilter.catch()` before the gRPC fallback branch:
```typescript
import { TimeoutError } from 'rxjs';
// ...
if (exception instanceof TimeoutError) {
  response.status(HttpStatus.GATEWAY_TIMEOUT).json({
    statusCode: HttpStatus.GATEWAY_TIMEOUT,
    message: 'Upstream service did not respond in time',
    timestamp: new Date().toISOString(),
  });
  return;
}
```

---

## IMPORTANT

### 2. Inconsistent symbol casing between create-stock and batch-get-stocks DTOs -- breaking change

**Files**: `gateway/src/stocks/dto/create-stock.dto.ts:11` vs `gateway/src/stocks/dto/batch-get-stocks.dto.ts:14`

**Problem**: `CreateStockDto.symbol` requires uppercase only: `/^[A-Z0-9.]{1,10}$/`. `BatchGetStocksDto.symbols` allows mixed case: `/^[A-Za-z0-9.]{1,10}$/`. This is inconsistent. If a frontend sends `"aapl"` to batch-get, it passes validation but then hits the gRPC service which may or may not normalize. Meanwhile the same `"aapl"` on create-stock gets rejected at the DTO layer.

Also, `stocks.service.ts:108` does `dto.symbol?.toUpperCase()` -- the optional chaining `?.` is wrong here because `symbol` is required (`@IsNotEmpty`). It will never be null/undefined after validation. More importantly, if the plan is to normalize to uppercase in the service layer, then the DTO regex should allow lowercase too (like batch-get does) so validation does not reject before normalization gets a chance.

**Impact**: Frontends currently sending lowercase symbols (common in many ticker APIs) will get 400 errors on create but succeed on batch-get. This is a breaking change if existing clients use lowercase.

**Fix**: Either (a) use the same case-insensitive regex `/^[A-Za-z0-9.]{1,10}$/` everywhere and normalize with `.toUpperCase()` in the service layer, or (b) use the strict uppercase regex everywhere and document the contract. Pick one, but be consistent.

### 3. DB retry on partial initialization -- pool leak risk

**Files**: `services/informer/src/server.py:47-51`, `services/analytics/src/server.py:48-52`, `services/informer/src/database.py:26-46`

**Problem**: `DatabasePool.initialize()` first creates a `ThreadedConnectionPool` (line 28-32), then does a health-check query (line 34-38). If the pool creates successfully but the health-check fails, `self._pool` is already set to the new pool object. On retry, `initialize()` is called again, which creates *another* `ThreadedConnectionPool` without closing the first one. The old pool's connections are leaked.

**Impact**: Each retry after a partial `initialize()` leaks `db_pool_min` connections. With 5 retries that is potentially 5 leaked pools. In practice this may be benign if the DB is truly unreachable (connections fail immediately), but if the issue is intermittent (e.g., health-check times out due to slow startup), real connections get leaked.

**Fix**: Add cleanup at the start of `initialize()`:
```python
def initialize(self) -> None:
    if self._pool is not None:
        try:
            self._pool.closeall()
        except Exception:
            pass
    self._pool = pool.ThreadedConnectionPool(...)
```

### 4. Date regex validates format but not semantics

**File**: `gateway/src/stocks/dto/get-price-history-query.dto.ts:15,20`

**Problem**: The regex `/^\d{4}-\d{2}-\d{2}$/` accepts `9999-99-99`, `2025-13-32`, `2025-02-30`. These are syntactically valid per the regex but semantically invalid dates. If the downstream Python service uses `datetime.strptime()` or similar, it will reject these with an opaque gRPC error rather than a clean 400.

**Impact**: Users get confusing error messages for invalid dates. Not a crash, but a poor UX.

**Fix**: Use `@IsDateString()` from class-validator (validates ISO 8601) or add a custom validator that checks `new Date(value)` is valid.

### 5. No jitter in retry backoff

**File**: `services/analytics/src/utils/retry.py:41`, `services/informer/src/utils/retry.py:46`

**Problem**: The delay is deterministic: `backoff_factor ** (attempt + 1)`. With 5 retries and factor 2.0 the schedule is 2s, 4s, 8s, 16s, 32s. If multiple instances start simultaneously and the DB is briefly unreachable, they all retry at the exact same moments -- thundering herd.

**Impact**: Under container orchestration (Kubernetes, Docker Compose) where multiple replicas start together, this amplifies DB connection storms.

**Fix**: Add jitter: `wait = (backoff_factor ** (attempt + 1)) * (0.5 + random.random())`.

---

## MINOR

### 6. `call()` method is copy-pasted across two services -- DRY violation

**Files**: `gateway/src/stocks/stocks.service.ts:44-46`, `gateway/src/analytics/analytics.service.ts:39-41`

**Problem**: Identical 3-line method duplicated. If timeout handling changes (e.g., adding `catchError`, retry logic, logging), both must be updated.

**Fix**: Extract to a shared utility:
```typescript
// common/grpc/grpc-call.util.ts
export function grpcCall<T>(obs: Observable<T>, timeoutMs = 10_000): Promise<T> {
  return lastValueFrom(obs.pipe(timeout(timeoutMs)));
}
```

### 7. `retry.py` duplicated across informer and analytics services

**Files**: `services/informer/src/utils/retry.py`, `services/analytics/src/utils/retry.py`

**Problem**: Identical files (except one has an `Example::` docstring block). If one is patched the other must be manually synced.

**Fix**: Extract to a shared package (`services/shared/retry.py`) or accept the duplication given these are separate deployables. Acceptable trade-off for a monorepo, but note it.

### 8. `createStock` uses optional chaining on required field

**File**: `gateway/src/stocks/stocks.service.ts:108`

**Problem**: `dto.symbol?.toUpperCase()` -- the `?.` is unnecessary because `symbol` is `@IsNotEmpty()` and `@IsString()`. After `ValidationPipe` passes, `symbol` is guaranteed to be a non-empty string. The `?.` suggests the developer was unsure if validation runs before the service, or it was a defensive copy-paste.

**Fix**: Remove `?.` to `dto.symbol.toUpperCase()`. Cleaner, no false safety.

### 9. `updateStock` defaults `is_active` to `true` when not provided

**File**: `gateway/src/stocks/stocks.service.ts:134`

**Problem**: `dto.isActive ?? true` means if a client sends an update without `isActive`, the stock is always set to active. If the stock was previously deactivated, an unrelated update (e.g., changing sector) will silently reactivate it.

**Fix**: Either omit `is_active` from the payload when `dto.isActive` is undefined, or default to the existing value. This depends on how the gRPC service handles absent fields (protobuf default for bool is `false`, not `true`).

### 10. Magic numbers for timeouts

**Files**: `gateway/src/stocks/stocks.service.ts:82,94`, `gateway/src/analytics/analytics.service.ts:70,92`

**Problem**: `15_000` and `3_000` are inline magic numbers. The default is a named constant (`GRPC_TIMEOUT_MS = 10_000`), but the overrides are not.

**Fix**: Define named constants: `GRPC_HEALTH_TIMEOUT_MS = 3_000`, `GRPC_HEAVY_TIMEOUT_MS = 15_000`.

---

## Edge Cases Found by Scouting

1. **RxJS `timeout()` does NOT cancel the underlying gRPC call.** It unsubscribes from the observable, but the gRPC request may still complete server-side. If the server performs a write (e.g., `CreateStock`), the client sees a timeout error but the write succeeds -- no idempotency guard.

2. **`lastValueFrom` on empty observable throws `EmptyError`**, not `TimeoutError`. If a gRPC call returns an empty stream (no messages before completion), `lastValueFrom` throws `EmptyError`. This is also not handled by the exception filter and would produce HTTP 500 with `"no elements in sequence"`.

3. **`enableImplicitConversion: true` in `main.ts:37`** means query string values like `limit=20` are auto-converted from string to number. This is correct for `@IsInt()` fields but can cause surprising behavior: `"true"` becomes `true` for `@IsBoolean()` fields in query params. For body DTOs this is fine (JSON parsing handles types). Just noting the interaction.

---

## Summary of Actions (prioritized)

| # | Severity | Action |
|---|----------|--------|
| 1 | CRITICAL | Handle `TimeoutError` in `GrpcExceptionFilter` -- return 504, not 500 |
| 2 | IMPORTANT | Unify symbol casing regex across DTOs (pick case-insensitive + normalize, or strict uppercase everywhere) |
| 3 | IMPORTANT | Guard `DatabasePool.initialize()` against leaked pools on retry |
| 4 | IMPORTANT | Validate date semantics, not just format |
| 5 | IMPORTANT | Add jitter to retry backoff |
| 6 | MINOR | Extract `call()` to shared utility |
| 7 | MINOR | Acknowledge or consolidate duplicated `retry.py` |
| 8 | MINOR | Remove unnecessary optional chaining on `dto.symbol` |
| 9 | MINOR | Fix `isActive` default in `updateStock` |
| 10 | MINOR | Name timeout magic numbers |

---

## Unresolved Questions

1. Does the gRPC server-side enforce idempotency on `CreateStock`? If not, the timeout-but-write-succeeds scenario (edge case #1) can cause duplicate stocks.
2. What is the protobuf default for `is_active` in the stock message? If `false`, then `dto.isActive ?? true` in `updateStock` fights the proto default.
3. Should `EmptyError` from `lastValueFrom` be handled generically in the filter, or should `call()` use `lastValueFrom(obs, { defaultValue: null })`?
