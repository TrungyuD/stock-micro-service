# Phase 04 — Testing

## Context Links

- [plan.md](./plan.md)
- [Phase 01](./phase-01-backend-auth-module.md)
- [Phase 02](./phase-02-backend-route-protection.md)
- [Phase 03](./phase-03-frontend-auth-implementation.md)
- [gateway/package.json](../../gateway/package.json) — jest config
- [stock-app/package.json](../../../stock-app/package.json) — vitest config

## Overview

- **Priority:** MEDIUM
- **Status:** pending
- **Description:** Write backend e2e tests for auth endpoints and route protection, frontend integration tests for auth flows.

## Key Insights

- Backend: Jest with `@nestjs/testing`, supertest for HTTP tests. e2e config at `gateway/test/jest-e2e.json`.
- Frontend: Vitest with jsdom. Already configured in stock-app.
- Backend tests need a test database or mocked TypeORM repositories.
- Focus on critical auth paths — don't over-test (YAGNI).

## Requirements

### Functional
- Backend: Test register, login, refresh, logout, protected routes, public routes
- Frontend: Test auth store actions, api-client 401 retry, middleware redirect logic

### Non-Functional
- Tests must not require running database (use mocks for unit tests)
- e2e tests can use test database if available
- No flaky tests (avoid timing-dependent assertions)

## Related Code Files

### Files to Create
- `gateway/src/auth/auth.service.spec.ts` — Unit tests for AuthService
- `gateway/src/auth/auth.controller.spec.ts` — Unit tests for AuthController
- `gateway/test/auth.e2e-spec.ts` — e2e tests for auth endpoints
- `stock-app/src/stores/__tests__/auth-store.test.ts` — Auth store tests
- `stock-app/src/lib/__tests__/api-client.test.ts` — API client 401 retry tests

## Implementation Steps

### 1. Backend Unit Tests — AuthService (`auth.service.spec.ts`)

Test cases:
- `register()`: creates user with hashed password, returns tokens
- `register()`: throws ConflictException for duplicate email
- `validateUser()`: returns user for correct credentials
- `validateUser()`: returns null for wrong password
- `validateUser()`: returns null for non-existent email
- `login()`: generates access + refresh tokens
- `refreshTokens()`: validates and rotates refresh token
- `refreshTokens()`: throws on expired/invalid token
- `logout()`: deletes all refresh tokens for user

Mock: TypeORM repositories, JwtService, bcrypt.

### 2. Backend Unit Tests — AuthController (`auth.controller.spec.ts`)

Test cases:
- POST /register: calls service, sets cookie, returns 201
- POST /login: calls service via LocalGuard, sets cookie, returns 200
- POST /refresh: reads cookie, calls service, returns new tokens
- POST /logout: clears cookie, returns 200
- GET /me: returns user from JWT, returns 200

Mock: AuthService.

### 3. Backend e2e Tests (`test/auth.e2e-spec.ts`)

Full integration tests using `@nestjs/testing` + supertest:

```typescript
describe('Auth (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();
    app = moduleFixture.createNestApplication();
    // Apply same config as main.ts (prefix, pipes, etc.)
    await app.init();
  });

  it('POST /auth/register — creates user and returns tokens', ...);
  it('POST /auth/register — rejects duplicate email', ...);
  it('POST /auth/login — returns tokens for valid credentials', ...);
  it('POST /auth/login — returns 401 for invalid password', ...);
  it('POST /auth/refresh — rotates tokens', ...);
  it('POST /auth/logout — invalidates session', ...);
  it('GET /auth/me — returns profile with valid token', ...);
  it('GET /auth/me — returns 401 without token', ...);
  it('GET /watchlists — returns 401 without token', ...);
  it('GET /stocks — accessible without token', ...);
  it('POST /stocks — returns 401 without token', ...);
  it('POST /stocks — returns 403 for non-admin', ...);
});
```

### 4. Frontend Unit Tests — Auth Store (`auth-store.test.ts`)

Test cases:
- `login()`: calls API, updates store with token + user
- `login()`: sets error on API failure
- `register()`: calls API, updates store
- `logout()`: calls API, clears store
- `refreshToken()`: updates access token
- `refreshToken()`: clears auth on failure
- `clearAuth()`: resets all state

Mock: auth-api functions with vi.mock.

### 5. Frontend Unit Tests — API Client (`api-client.test.ts`)

Test cases:
- Adds Authorization header when token present
- Does not add header when no token
- On 401: attempts refresh, retries request
- On 401 + refresh failure: clears auth, no retry

Mock: global fetch, auth store.

## Todo List

- [ ] Create auth.service.spec.ts with unit tests
- [ ] Create auth.controller.spec.ts with unit tests
- [ ] Create auth.e2e-spec.ts with integration tests
- [ ] Create auth-store.test.ts with store tests
- [ ] Create api-client.test.ts with 401 retry tests
- [ ] Run `cd gateway && npm test` — all pass
- [ ] Run `cd stock-app && npm test` — all pass
- [ ] Run `cd gateway && npm run test:e2e` — all pass (if test DB available)

## Success Criteria

- All unit tests pass: `npm test` in both gateway and stock-app
- e2e tests cover: register, login, refresh, logout, protected route 401, public route 200
- No skipped or mocked-away tests for critical auth logic
- Code coverage on auth module > 80%

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| e2e tests need running DB | CI pipeline fails | Use in-memory SQLite or mock repositories for CI; real DB for local e2e |
| Test isolation | Leaked state between tests | Use `beforeEach` cleanup, separate test user per test |
| bcrypt slow in tests | Test suite takes minutes | Use low salt rounds (4) in test environment |

## Security Considerations

- Test credentials must not be real / production values
- Test database should be isolated (never share with dev/prod)
- Do not log tokens in test output

## Next Steps

- After all tests pass, auth feature is complete and ready for code review
- Future: Add rate limiting tests, password complexity tests
