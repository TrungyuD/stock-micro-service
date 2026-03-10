# Phase 02 — Backend Route Protection

## Context Links

- [plan.md](./plan.md)
- [Phase 01](./phase-01-backend-auth-module.md)
- [watchlists.controller.ts](../../gateway/src/watchlists/watchlists.controller.ts)
- [stocks.controller.ts](../../gateway/src/stocks/stocks.controller.ts)
- [analytics.controller.ts](../../gateway/src/analytics/analytics.controller.ts)

## Overview

- **Priority:** HIGH
- **Status:** pending
- **Description:** Apply JwtAuthGuard to protected endpoints, migrate watchlist controller from `X-User-Id` header to JWT-extracted userId, keep public endpoints open.

## Key Insights

- WatchlistsController currently reads `X-User-Id` header with `DEFAULT_USER_ID = 'anonymous'` fallback — must replace with `@Request() req` and `req.user.userId` from JWT
- Stocks controller: all GET endpoints should stay public. POST/PUT/DELETE (admin CRUD) should require auth + admin role.
- Analytics controller: GET endpoints for individual stock analysis stay public (read-only data). batch/screen endpoints can stay public too (no user data).
- Need a `@CurrentUser()` custom decorator for clean extraction of user from request.

## Requirements

### Functional
- Watchlist endpoints: require JWT auth, extract userId from token
- Stock CRUD (create/update/delete): require JWT + admin role
- Stock read endpoints: public
- Analytics endpoints: public (read-only market data)
- `GET /api/v1/auth/me`: already protected in Phase 01

### Non-Functional
- No breaking changes to public read endpoints
- Clean decorator-based auth (no manual header parsing)

## Architecture

```
Request -> JwtAuthGuard (rejects if no valid token)
        -> OptionalJwtAuthGuard (passes through, sets req.user or null)
        -> RolesGuard (checks req.user.role against @Roles() decorator)
        -> @CurrentUser() decorator extracts user from req
```

## Related Code Files

### Files to Create
- `gateway/src/auth/decorators/current-user.decorator.ts` — `@CurrentUser()` param decorator
- `gateway/src/auth/decorators/roles.decorator.ts` — `@Roles('admin')` metadata decorator
- `gateway/src/auth/guards/roles.guard.ts` — Checks user role against required roles
- `gateway/src/auth/decorators/public.decorator.ts` — `@Public()` decorator to skip auth

### Files to Modify
- `gateway/src/watchlists/watchlists.controller.ts` — Replace `X-User-Id` with JWT auth
- `gateway/src/stocks/stocks.controller.ts` — Add admin guard to CUD endpoints
- `gateway/src/watchlists/watchlists.module.ts` — May need to import AuthModule

## Implementation Steps

### 1. Create `@CurrentUser()` decorator

```typescript
// gateway/src/auth/decorators/current-user.decorator.ts
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const CurrentUser = createParamDecorator(
  (data: string | undefined, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user;
    return data ? user?.[data] : user;
  },
);
```

### 2. Create `@Roles()` decorator + RolesGuard

```typescript
// gateway/src/auth/decorators/roles.decorator.ts
import { SetMetadata } from '@nestjs/common';
export const ROLES_KEY = 'roles';
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);
```

```typescript
// gateway/src/auth/guards/roles.guard.ts
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ROLES_KEY } from '../decorators/roles.decorator';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!requiredRoles) return true;
    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.includes(user.role);
  }
}
```

### 3. Update WatchlistsController

Remove `X-User-Id` header usage. Apply `@UseGuards(JwtAuthGuard)` at controller level.
Replace `@Headers('x-user-id') userId?: string` with `@CurrentUser('userId') userId: string`.
Remove `DEFAULT_USER_ID` constant.

Before:
```typescript
@Get()
findAll(@Headers('x-user-id') userId?: string) {
  return this.watchlistsService.findAll(userId || DEFAULT_USER_ID);
}
```

After:
```typescript
@Get()
@UseGuards(JwtAuthGuard)
findAll(@CurrentUser('userId') userId: string) {
  return this.watchlistsService.findAll(userId);
}
```

Apply to all 6 watchlist endpoints.
Update Swagger annotations: remove `@ApiHeader` for X-User-Id, add `@ApiBearerAuth()`.

### 4. Update StocksController

Keep GET endpoints public (no guard).
Add `@UseGuards(JwtAuthGuard, RolesGuard) @Roles('admin') @ApiBearerAuth()` to:
- `@Post()` createStock
- `@Put(':symbol')` updateStock
- `@Delete(':symbol')` deleteStock

### 5. Analytics controller — no changes

All analytics endpoints are read-only market data, stay public.

### 6. Export new decorators and guards from auth module

Add `RolesGuard` to providers, export `CurrentUser`, `Roles` decorators.

## Todo List

- [ ] Create current-user.decorator.ts
- [ ] Create roles.decorator.ts
- [ ] Create roles.guard.ts
- [ ] Update WatchlistsController: remove X-User-Id, add JwtAuthGuard + @CurrentUser
- [ ] Update WatchlistsController Swagger: remove @ApiHeader, add @ApiBearerAuth
- [ ] Update StocksController: add admin auth to POST/PUT/DELETE
- [ ] Update StocksController Swagger: add @ApiBearerAuth to protected endpoints
- [ ] Verify `nest build` compiles clean
- [ ] Manual test: unauthenticated GET /stocks still works
- [ ] Manual test: unauthenticated POST /watchlists returns 401

## Success Criteria

- GET /stocks, GET /stocks/:symbol, GET /analytics/* — accessible without auth
- POST/PUT/DELETE /stocks — require JWT + admin role, return 401/403 otherwise
- All /watchlists endpoints — require JWT, return 401 without token
- Watchlists use JWT userId instead of X-User-Id header
- Swagger shows lock icon on protected endpoints

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking watchlist API for existing frontend | 500 errors until frontend updated | Phase 03 updates frontend simultaneously |
| Admin role not seeded | Can't test stock CRUD | Add admin user to 02-seed.sql or register + manually update role |
| Guard ordering | RolesGuard runs before JwtAuthGuard | Always list JwtAuthGuard first in @UseGuards() |

## Security Considerations

- Admin-only endpoints gated by role check (defense in depth)
- No user can access another user's watchlists (userId from JWT, not request body)
- Reflector-based role check prevents role escalation

## Next Steps

- Phase 03: Frontend auth implementation to consume these protected endpoints
