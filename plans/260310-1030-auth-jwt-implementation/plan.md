---
title: "JWT Authentication for Stock Trading App"
description: "Add email/password JWT auth with access+refresh tokens across NestJS backend and Next.js frontend"
status: pending
priority: P1
effort: 12h
branch: feat/auth-jwt
tags: [auth, jwt, nestjs, nextjs, security]
created: 2026-03-10
---

# JWT Authentication Implementation Plan

## Overview

Add email/password JWT authentication with access token (15min) + refresh token (7 days).
Public pages: Dashboard (/), Stocks (/stocks). Protected: Stock detail, Analytics, Watchlist, Admin, Settings.

## Architecture Decisions

- **Access token**: In-memory (Zustand), 15min TTL, sent via `Authorization: Bearer`
- **Refresh token**: httpOnly cookie, 7-day TTL, auto-refresh on 401
- **Backend**: NestJS PassportModule (passport-jwt + passport-local), bcrypt hashing
- **Frontend**: Next.js middleware for route protection, Zustand auth store
- **DB**: Schema-first (01-schema.sql) -- `users` and `refresh_tokens` tables added manually

## Phases

| # | Phase | Priority | Status | Effort | File |
|---|-------|----------|--------|--------|------|
| 1 | Backend Auth Module | HIGH | pending | 4h | [phase-01](./phase-01-backend-auth-module.md) |
| 2 | Backend Route Protection | HIGH | pending | 2h | [phase-02](./phase-02-backend-route-protection.md) |
| 3 | Frontend Auth Implementation | HIGH | pending | 4h | [phase-03](./phase-03-frontend-auth-implementation.md) |
| 4 | Testing | MEDIUM | pending | 2h | [phase-04](./phase-04-testing.md) |

## Dependencies

```
Phase 1 --> Phase 2 --> Phase 3 --> Phase 4
                    \-> Phase 3 (partial — login UI can start after Phase 1)
```

## Key Risks

- DB uses `synchronize: false` — must add SQL migration for users/refresh_tokens tables
- Watchlist controller uses `X-User-Id` header (MVP) — must migrate to JWT-extracted userId
- CORS `credentials: true` already set — good for httpOnly cookies

## Environment Variables (new)

```
JWT_SECRET=<random-64-char-string>
JWT_ACCESS_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d
```
