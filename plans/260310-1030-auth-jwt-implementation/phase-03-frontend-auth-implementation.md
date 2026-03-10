# Phase 03 — Frontend Auth Implementation

## Context Links

- [plan.md](./plan.md)
- [Phase 01](./phase-01-backend-auth-module.md)
- [Phase 02](./phase-02-backend-route-protection.md)
- [api-client.ts](../../../stock-app/src/lib/api-client.ts)
- [login/page.tsx](../../../stock-app/src/app/(auth)/login/page.tsx)
- [providers.tsx](../../../stock-app/src/components/providers.tsx)
- [dashboard-header.tsx](../../../stock-app/src/components/layout/dashboard-header.tsx)
- [sidebar-store.ts](../../../stock-app/src/stores/sidebar-store.ts) (reference for Zustand pattern)
- [constants.ts](../../../stock-app/src/lib/constants.ts)

## Overview

- **Priority:** HIGH
- **Status:** pending
- **Description:** Create auth store (Zustand), wire up login/register forms, update API client to inject Bearer token, add Next.js middleware for route protection, add user dropdown in header.

## Key Insights

- Zustand v5 is already installed — use same pattern as `sidebar-store.ts` (create + persist middleware)
- API client is a thin fetch wrapper — need to inject `Authorization: Bearer` header
- Login page UI already exists (placeholder) — wire up form submission
- Next.js 16 App Router — use `middleware.ts` at `src/` root for route protection
- Providers wrap everything — add auth initialization there
- `credentials: 'include'` needed in fetch for httpOnly cookie (refresh token)

## Requirements

### Functional
- Login form: email + password, submit -> POST /auth/login, store access token, redirect to /
- Register form: name + email + password + confirm, submit -> POST /auth/register, store token, redirect to /
- Auto-redirect: unauthenticated users hitting protected routes -> /login
- Public routes (/, /stocks) never redirect
- Token refresh: on 401 response, silently call /auth/refresh, retry original request
- User menu: show user name in header, dropdown with logout
- Logout: call /auth/logout, clear store, redirect to /login

### Non-Functional
- No flash of protected content before redirect
- Graceful degradation if refresh fails (redirect to login)
- SSR-compatible (middleware runs on server)

## Architecture

```
Next.js Middleware (server-side)
  |-> Check for auth cookie/token existence
  |-> Redirect to /login for protected routes if unauthenticated
  |-> Pass through for public routes

Auth Store (Zustand, client-side)
  |-> accessToken (in memory, NOT persisted to localStorage)
  |-> user object (id, email, name, role)
  |-> isAuthenticated computed flag
  |-> login(), register(), logout(), refreshToken() actions

API Client
  |-> Intercept all requests, add Authorization header if token exists
  |-> On 401: attempt refresh, retry, or redirect to login
```

## Related Code Files

### Files to Create
- `stock-app/src/stores/auth-store.ts` — Zustand auth state + actions
- `stock-app/src/app/(auth)/register/page.tsx` — Register page
- `stock-app/src/middleware.ts` — Next.js middleware for route protection
- `stock-app/src/components/layout/user-menu.tsx` — User dropdown (name + logout)
- `stock-app/src/lib/auth-api.ts` — Auth-specific API functions (login, register, refresh, logout, me)

### Files to Modify
- `stock-app/src/lib/api-client.ts` — Add auth header injection + 401 refresh logic
- `stock-app/src/app/(auth)/login/page.tsx` — Wire up form submission
- `stock-app/src/components/providers.tsx` — Add auth hydration on mount
- `stock-app/src/components/layout/dashboard-header.tsx` — Add UserMenu component

## Implementation Steps

### 1. Create auth API functions (`stock-app/src/lib/auth-api.ts`)

```typescript
import { API_BASE_URL } from './constants';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthResponse {
  accessToken: string;
  user: AuthUser;
}

export async function loginApi(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include', // receive httpOnly cookie
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function registerApi(name: string, email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
    credentials: 'include',
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function refreshApi(): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Refresh failed');
  return res.json();
}

export async function logoutApi(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
}

export async function getMeApi(accessToken: string): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error('Not authenticated');
  return res.json();
}
```

### 2. Create auth store (`stock-app/src/stores/auth-store.ts`)

```typescript
import { create } from 'zustand';
import { loginApi, registerApi, refreshApi, logoutApi, type AuthUser } from '@/lib/auth-api';

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  setAuth: (accessToken: string, user: AuthUser) => void;
  clearAuth: () => void;
}
```

Key details:
- Do NOT use `persist` middleware — access token stays in memory only
- `refreshToken()` calls `/auth/refresh`, updates store, returns new access token or null
- `login()`/`register()` call API, then `setAuth()`
- `logout()` calls API, then `clearAuth()`
- `isAuthenticated` derived from `!!accessToken && !!user`

### 3. Update api-client.ts — Auth header + 401 retry

Modify `apiFetch` to:
1. Get access token from auth store
2. Add `Authorization: Bearer <token>` header if token exists
3. Add `credentials: 'include'` for cookie support
4. On 401 response: call `refreshToken()`, if successful retry original request once
5. If refresh also fails: call `clearAuth()`, redirect to `/login`

```typescript
import { useAuthStore } from '@/stores/auth-store';

// Inside apiFetch:
const token = useAuthStore.getState().accessToken;
if (token) {
  reqHeaders['Authorization'] = `Bearer ${token}`;
}
// ... fetch with credentials: 'include' ...
if (response.status === 401) {
  const newToken = await useAuthStore.getState().refreshToken();
  if (newToken) {
    // retry with new token
    reqHeaders['Authorization'] = `Bearer ${newToken}`;
    const retryResponse = await fetch(url, { ...opts, headers: reqHeaders });
    // handle retry response...
  } else {
    useAuthStore.getState().clearAuth();
    if (typeof window !== 'undefined') window.location.href = '/login';
  }
}
```

### 4. Wire up login page (`stock-app/src/app/(auth)/login/page.tsx`)

Convert to `"use client"` component. Add:
- State: email, password, error, isSubmitting
- `handleSubmit`: call `useAuthStore.login()`, on success `router.push('/')`, on error show message
- Link to `/register` page
- Remove "coming soon" text

### 5. Create register page (`stock-app/src/app/(auth)/register/page.tsx`)

Similar to login but with name, email, password, confirm password fields.
Use same glassmorphism Card design.
Validate password === confirm on client side.
On success, redirect to `/`.

### 6. Create Next.js middleware (`stock-app/src/middleware.ts`)

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_ROUTES = ['/', '/stocks', '/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (PUBLIC_ROUTES.some(route => pathname === route || pathname.startsWith('/_next'))) {
    return NextResponse.next();
  }

  // Check for refresh_token cookie (indicates user has session)
  const refreshToken = request.cookies.get('refresh_token');
  if (!refreshToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
```

Note: Middleware checks `refresh_token` cookie (httpOnly but visible to middleware).
This is server-side — prevents flash of protected content.

### 7. Add auth hydration in providers.tsx

On app mount, try to refresh the token to restore session:

```typescript
// Add useEffect that calls refreshToken on mount
useEffect(() => {
  useAuthStore.getState().refreshToken().catch(() => {
    // No valid session — user stays unauthenticated
  });
}, []);
```

### 8. Create UserMenu component (`stock-app/src/components/layout/user-menu.tsx`)

Dropdown with user avatar (initials), name, role badge, and logout button.
Use shadcn/ui `DropdownMenu`.
Show "Sign in" button if not authenticated.

### 9. Update dashboard-header.tsx

Import and render `<UserMenu />` in the header, between locale switcher and right edge.

## Todo List

- [ ] Create auth-api.ts with login, register, refresh, logout, me functions
- [ ] Create auth-store.ts (Zustand, no persist)
- [ ] Update api-client.ts with auth header injection + 401 retry
- [ ] Wire up login page form (convert to client component, add submit handler)
- [ ] Create register page with matching design
- [ ] Create middleware.ts for route protection
- [ ] Add auth hydration in providers.tsx
- [ ] Create user-menu.tsx component
- [ ] Update dashboard-header.tsx to include UserMenu
- [ ] Test: login flow end-to-end
- [ ] Test: register flow end-to-end
- [ ] Test: unauthenticated access to /watchlist redirects to /login
- [ ] Test: accessing /stocks works without login
- [ ] Test: 401 triggers silent refresh

## Success Criteria

- User can register, login, and see their name in header
- Unauthenticated users redirected to /login on protected routes
- Public routes (/, /stocks) always accessible
- Token refresh happens silently on 401
- Logout clears session and redirects to /login
- Login/register forms show validation errors
- No flash of protected content for unauthenticated users

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Middleware can't read httpOnly cookie | Route protection fails server-side | Next.js middleware CAN read cookies (just not JS on client) — verify refresh_token path allows middleware access |
| Token refresh race condition | Multiple 401s trigger multiple refresh calls | Add `isRefreshing` flag + queue pending requests |
| Zustand store not available in middleware | Can't check access token server-side | Use cookie-based check in middleware; access token check is client-side only |
| CORS blocks cookie on different port (dev) | Login works but cookie not set | Backend CORS already has `credentials: true`; ensure frontend uses `credentials: 'include'` |

## Security Considerations

- Access token in memory only — not in localStorage (XSS-safe)
- Refresh token in httpOnly cookie — not accessible to JS (XSS-safe)
- Cookie path restricted to `/api/v1/auth/refresh` — not sent with every request
- Middleware redirect includes `?redirect=` param for post-login return
- Password never stored on client

## Next Steps

- Phase 04: Write tests for auth flows
- Future: Add forgot password / reset password flow
