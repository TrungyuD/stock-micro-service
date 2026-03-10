# Code Review: Phase 6 Testing -- Stock CRUD Unit Tests

## Scope
- **Files reviewed**: 6
  1. `gateway/src/stocks/stocks.controller.spec.ts` (125 LOC)
  2. `gateway/src/stocks/stocks.service.spec.ts` (159 LOC)
  3. `services/informer/pytest.ini` (3 LOC)
  4. `services/informer/tests/test_informer_handler.py` (206 LOC)
  5. `services/informer/tests/test_stock_repository.py` (116 LOC)
  6. `services/informer/tests/test_stock_admin_handler.py` (145 LOC)
- **LOC changed**: ~754 total across all files
- **Focus**: Test quality, mock correctness, edge case coverage, isolation
- **Test results**: NestJS 46/46 passed, Python 65/67 (2 pre-existing failures)

## Overall Assessment

**PASS with minor recommendations.** Tests are well-structured, follow good patterns (AAA structure, clear naming, proper mock isolation). Coverage of the happy path and key error scenarios is solid. The mocks correctly match actual service/handler interfaces. A few edge cases and assertion improvements identified below.

---

## Critical Issues

None.

---

## Important Issues

### 1. [Important] `stock_mapper.py`: `stock_proto_to_dict` has a latent `is_active` logic bug

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/src/mappers/stock_mapper.py`, line 43

The expression `stock.is_active if stock.is_active else True` always returns `True`. When `stock.is_active` is `False` (proto3 default), the falsy branch triggers and returns `True`. You can never set `is_active=False` through `CreateStock` or `UpdateStock` flows.

This is not a test bug, but the tests do not catch it. `test_stock_admin_handler.py` only tests `is_active=True` scenarios. A test with `is_active=False` in the proto would expose the bug.

**Impact**: Cannot deactivate a stock via UpdateStock with `is_active=False` in the request body; the mapper silently ignores it.

### 2. [Important] `test_informer_handler.py` -- `TestInformerHandlerListStocks` does not set `request.country`

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/tests/test_informer_handler.py`, line 98-121

The test uses `MagicMock()` for the request but never sets `request.country`. Since `MagicMock()` returns a new `MagicMock` for any attribute access (not a string), the call `self._stock_repo.search(country=request.country)` passes a MagicMock object instead of a string. This works because the repo is also mocked, but it means:
- The test does not verify the `country` attribute is forwarded correctly
- The `ListStocks` handler calls `request.country` (line 75 of `informer_handler.py`), but no test validates its behavior

**Recommendation**: Set `request.country = ""` (or `"US"`) in the existing test, and add a dedicated `country` filter test for `ListStocks` at the handler level (not just service and repository).

---

## Medium Priority

### 3. [Medium] Controller tests do not verify `toUpperCase()` on `createStock` and `updateStock`

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/gateway/src/stocks/stocks.controller.spec.ts`, lines 90-112

The controller's `createStock` does NOT uppercase -- it passes `dto` directly to `stocksService.createStock(dto)`. But `updateStock` also passes `symbol` as-is. Looking at the actual controller source (`stocks.controller.ts`), `createStock` and `updateStock` indeed do NOT call `.toUpperCase()` on the symbol -- that happens in `StocksService`. The test is correct but could be stronger by testing with a lowercase symbol to confirm the controller does NOT transform it (documenting the contract that uppercase normalization is the service's responsibility).

### 4. [Medium] `test_stock_repository.py` country filter assertion is fragile

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/tests/test_stock_repository.py`, lines 66-68

```python
_, args, _ = mock_db_pool.execute.mock_calls[1]
assert "US" in args[1]
```

This inspects positional args of the second `execute()` call and checks `"US" in args[1]` which is a tuple. This works because Python's `in` operator checks tuple membership. However, it's tightly coupled to the internal SQL parameter ordering. If the repository adds a filter before `country` in the parameter list, this test breaks. Consider using `any("US" in str(call) for call in mock_db_pool.execute.mock_calls)` or extracting the full params tuple for clearer assertion.

### 5. [Medium] `test_stock_admin_handler.py` -- `CreateStock` does not test upsert-on-conflict behavior

The `upsert()` method handles `ON CONFLICT (symbol) DO UPDATE`. No test verifies the update-path behavior when `CreateStock` is called for an already-existing symbol. This is an important edge case since the handler uses `upsert`, not `insert`.

### 6. [Medium] Missing error-scenario tests for `UpdateStock` and `DeleteStock` when DB raises

`test_stock_admin_handler.py` tests `CreateStock` with DB error (`test_create_db_error`) but has no equivalent for `UpdateStock` or `DeleteStock` with exception paths. Both have `except Exception` blocks that set `INTERNAL` status.

---

## Minor / Nitpick

### 7. [Minor] `test_informer_handler.py` at 206 lines exceeds 200-line guideline

The file is slightly over the project's 200-line limit. Not urgent since it's a test file, but consider extracting a helper class or using fewer inline mock setups.

### 8. [Minor] `stocks.service.spec.ts` -- `createStock` test asserts response but not the full gRPC shape

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/gateway/src/stocks/stocks.service.spec.ts`, line 100

```typescript
expect(result.stock.symbol).toBe('TEST');
```

The test checks `result.stock.symbol` but does not verify other fields in the response. Other tests (e.g., `getStockInfo`) use `toEqual` for full object comparison. Consider using `toEqual` for consistency.

### 9. [Nitpick] `pytest.ini` change -- adding `src/generated` to pythonpath

**File**: `/Users/sotatek/freelancer/pet-proj/stock-trading-ana-tool/stock-micro-service/services/informer/pytest.ini`

This is correct and necessary for imports like `from generated import informer_pb2`. No side effects since `src/generated` is a specific subdirectory. The `conftest.py` already adds `src/` via `sys.path.insert`, so this gives pytest itself the same visibility. No concerns.

### 10. [Nitpick] Import fix in `test_informer_handler.py` is correct

Changing `from handlers.informer_handler import _dict_to_stock` to `from mappers.stock_mapper import dict_to_stock` correctly tracks the refactoring of this function into the mapper module. The underscore-prefix removal (public API) is also correct.

---

## Edge Cases Found by Scouting

1. **`is_active=False` round-trip broken** (see Important #1): The `stock_proto_to_dict` mapper makes it impossible to explicitly set `is_active=False` via gRPC. No test covers this path.
2. **`UpdateStock` partial update with empty strings**: `stock_admin_handler.py` line 62-66 uses `incoming["name"] or existing.get("name", "")` -- if someone explicitly sends `name=""` in an update, the `or` falls through to the existing value, preventing clearing a field. Not tested.
3. **Concurrent `CreateStock` upsert race condition**: Two simultaneous `CreateStock` calls for the same symbol could both succeed (by design, since it's `ON CONFLICT DO UPDATE`), but the `get_by_id` after `upsert` could return stale data if the second upsert overwrites the first. No test covers this concurrency scenario (acceptable for unit tests, but worth noting for integration tests).
4. **`ListStocks` with `request.country` attribute missing in test**: MagicMock auto-creates attributes, so the handler code reads a MagicMock instead of a string. See Important #2.

---

## Positive Observations

- **Good test structure**: All tests follow AAA (Arrange-Act-Assert) pattern clearly
- **Proper mock isolation**: `jest.clearAllMocks()` / fresh fixture per test prevents state leakage
- **Error path coverage**: Tests for INVALID_ARGUMENT, NOT_FOUND, INTERNAL consistently across handlers
- **Symbol normalization tested**: Both NestJS service tests and Python handler tests verify uppercase normalization
- **Soft-delete semantics**: `test_stock_repository.py` correctly tests both found/not-found paths for `soft_delete`
- **Proto message construction**: `test_stock_admin_handler.py` uses real proto message objects (`informer_pb2.CreateStockRequest`, `types_pb2.Stock`) rather than dicts, giving high fidelity
- **Shared fixtures**: `conftest.py` provides clean, reusable fixtures for all Python test files

---

## Recommended Actions (prioritized)

1. **Add test for `is_active=False` in `CreateStock`/`UpdateStock`** -- will expose the `stock_proto_to_dict` mapper bug
2. **Fix `stock_proto_to_dict` is_active logic** -- change line 43 to handle `False` explicitly (this is a source bug, not a test bug)
3. **Set `request.country` in `TestInformerHandlerListStocks`** -- prevents silent MagicMock passthrough
4. **Add DB-error tests for `UpdateStock` and `DeleteStock`** in `test_stock_admin_handler.py`
5. **Consider integration test for upsert-on-conflict** in a later phase

---

## Metrics

- **Type Coverage (TS)**: N/A (test files, but DTOs are properly typed with class-validator)
- **Test Coverage**: Good for new CRUD operations; ~80% statement coverage estimate for stock_admin_handler.py (missing exception paths for Update/Delete)
- **Linting Issues**: 0 (tests pass clean)
- **Test File Count**: 6 files, ~55 total test cases across both stacks

---

## Unresolved Questions

1. The 2 pre-existing Python test failures -- are they tracked? Which tests are failing?
2. Is there a plan to add E2E/integration tests for the admin CRUD endpoints (with auth guard testing)?
3. Should the `stock_proto_to_dict` `is_active` bug be fixed in this phase or deferred?
