# Phase 01 — Backend Auth Module

## Context Links

- [plan.md](./plan.md)
- [app.module.ts](../../gateway/src/app.module.ts)
- [database.module.ts](../../gateway/src/database/database.module.ts)
- [01-schema.sql](../../init-db/01-schema.sql)
- [watchlist.entity.ts](../../gateway/src/entities/watchlist.entity.ts) (reference for entity pattern)
- [main.ts](../../gateway/src/main.ts)

## Overview

- **Priority:** HIGH
- **Status:** pending
- **Description:** Create complete auth module — User/RefreshToken entities, Passport strategies, controller with register/login/refresh/logout endpoints, bcrypt hashing, JWT signing.

## Key Insights

- DB uses `synchronize: false` — schema managed by `init-db/01-schema.sql`. Must add SQL for users + refresh_tokens tables.
- Existing entities follow: `@Entity('table_name')` with `@PrimaryGeneratedColumn()`, snake_case column names, `@CreateDateColumn` / `@UpdateDateColumn`.
- Watchlist already references `user_id` as VARCHAR(36) — use UUID for user ID to stay compatible.
- CORS already has `credentials: true` and `Authorization` in allowedHeaders.
- Swagger is set up in main.ts — add `addBearerAuth()` to DocumentBuilder.

## Requirements

### Functional
- POST `/api/v1/auth/register` — create user, return tokens
- POST `/api/v1/auth/login` — validate credentials, return tokens
- POST `/api/v1/auth/refresh` — rotate refresh token via httpOnly cookie
- POST `/api/v1/auth/logout` — invalidate refresh token
- GET `/api/v1/auth/me` — return current user profile (requires JWT)

### Non-Functional
- Passwords hashed with bcrypt (12 rounds)
- Access token: 15min expiry, refresh token: 7 days
- Refresh token stored hashed in DB (not plaintext)
- Rate limiting on login/register (optional, defer to Phase 5 if needed)

## Architecture

```
AuthController
  |-> AuthService
       |-> UserRepository (TypeORM)
       |-> RefreshTokenRepository (TypeORM)
       |-> JwtService (@nestjs/jwt)
       |-> bcrypt (password hashing)

Strategies:
  LocalStrategy -> validates email+password -> returns User
  JwtStrategy -> validates access token -> returns { userId, email, role }
```

## Related Code Files

### Files to Create
- `gateway/src/auth/auth.module.ts` — Module wiring
- `gateway/src/auth/auth.service.ts` — Business logic (register, login, refresh, logout)
- `gateway/src/auth/auth.controller.ts` — REST endpoints
- `gateway/src/auth/dto/register.dto.ts` — RegisterDto (email, password, name)
- `gateway/src/auth/dto/login.dto.ts` — LoginDto (email, password)
- `gateway/src/auth/dto/auth-response.dto.ts` — AuthResponseDto (accessToken, user)
- `gateway/src/auth/strategies/jwt.strategy.ts` — PassportStrategy(Strategy) from passport-jwt
- `gateway/src/auth/strategies/local.strategy.ts` — PassportStrategy(Strategy) from passport-local
- `gateway/src/auth/guards/jwt-auth.guard.ts` — AuthGuard('jwt')
- `gateway/src/auth/guards/optional-jwt-auth.guard.ts` — Returns user if token present, null otherwise
- `gateway/src/entities/user.entity.ts` — User entity
- `gateway/src/entities/refresh-token.entity.ts` — RefreshToken entity

### Files to Modify
- `gateway/src/app.module.ts` — Import AuthModule
- `gateway/package.json` — Add auth dependencies
- `gateway/src/main.ts` — Add `.addBearerAuth()` to Swagger config
- `init-db/01-schema.sql` — Add users and refresh_tokens tables

## Implementation Steps

### 1. Add SQL schema for users and refresh_tokens

Append to `init-db/01-schema.sql`:

```sql
-- ============================================
-- USERS TABLE (authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);

-- ============================================
-- REFRESH TOKENS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens (token_hash);
```

### 2. Install dependencies

```bash
cd gateway && npm install @nestjs/passport @nestjs/jwt passport passport-jwt passport-local bcrypt
npm install -D @types/passport-jwt @types/passport-local @types/bcrypt
```

### 3. Create User entity (`gateway/src/entities/user.entity.ts`)

Fields: `id` (UUID, PK), `email` (unique), `passwordHash`, `name`, `role` (enum: user/admin), `isActive`, `createdAt`, `updatedAt`.
Follow existing entity pattern (snake_case column names, `@CreateDateColumn`).
Add `@OneToMany` relation to `WatchlistEntity` (watchlists.user_id links to users.id).

### 4. Create RefreshToken entity (`gateway/src/entities/refresh-token.entity.ts`)

Fields: `id` (serial PK), `tokenHash`, `userId` (UUID FK -> users), `expiresAt`, `createdAt`.
Add `@ManyToOne` relation to User.

### 5. Create DTOs

**RegisterDto**: email (IsEmail), password (MinLength(8), MaxLength(64)), name (IsString, MinLength(2))
**LoginDto**: email (IsEmail), password (IsString)
**AuthResponseDto**: accessToken (string), user ({ id, email, name, role })

### 6. Create AuthService (`gateway/src/auth/auth.service.ts`)

Methods:
- `register(dto: RegisterDto)` — check email uniqueness, hash password (bcrypt, 12 rounds), create user, generate tokens, return AuthResponseDto
- `validateUser(email, password)` — find user by email, compare bcrypt hash, return user or null
- `login(user: User)` — generate access+refresh tokens, store refresh hash in DB, set refresh cookie, return AuthResponseDto
- `refreshTokens(refreshToken: string)` — validate refresh token hash, check expiry, rotate (delete old, create new), return new access+refresh tokens
- `logout(userId: string)` — delete all refresh tokens for user
- `getProfile(userId: string)` — return user without passwordHash

Private helpers:
- `generateAccessToken(user)` — JwtService.sign({ sub: user.id, email, role }, { expiresIn: '15m' })
- `generateRefreshToken()` — crypto.randomBytes(32).toString('hex')
- `hashRefreshToken(token)` — bcrypt.hash(token, 10) (lighter rounds for refresh tokens)

### 7. Create Passport Strategies

**LocalStrategy**: usernameField = 'email'. Calls `authService.validateUser()`. Throws UnauthorizedException on failure.

**JwtStrategy**: Extracts token from `Authorization: Bearer`. Validates and returns `{ userId: payload.sub, email: payload.email, role: payload.role }`.
Uses `ConfigService` to get `JWT_SECRET`.

### 8. Create Guards

**JwtAuthGuard**: `@Injectable() extends AuthGuard('jwt')` — standard, rejects unauthenticated.
**OptionalJwtAuthGuard**: Override `handleRequest()` to return null instead of throwing when no token present.

### 9. Create AuthController (`gateway/src/auth/auth.controller.ts`)

- `@Post('register')` — body: RegisterDto, returns AuthResponseDto, sets refresh cookie
- `@Post('login') @UseGuards(AuthGuard('local'))` — body: LoginDto, returns AuthResponseDto, sets refresh cookie
- `@Post('refresh')` — reads refresh token from cookie, returns new tokens
- `@Post('logout') @UseGuards(JwtAuthGuard)` — clears refresh cookie, deletes DB tokens
- `@Get('me') @UseGuards(JwtAuthGuard)` — returns user profile

Cookie config for refresh token:
```typescript
response.cookie('refresh_token', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/api/v1/auth/refresh',
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
});
```

### 10. Create AuthModule

```typescript
@Module({
  imports: [
    PassportModule,
    JwtModule.registerAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.get<string>('JWT_SECRET'),
        signOptions: { expiresIn: config.get<string>('JWT_ACCESS_EXPIRATION', '15m') },
      }),
    }),
    TypeOrmModule.forFeature([UserEntity, RefreshTokenEntity]),
  ],
  controllers: [AuthController],
  providers: [AuthService, JwtStrategy, LocalStrategy],
  exports: [AuthService, JwtModule],
})
export class AuthModule {}
```

### 11. Wire into AppModule

Add `AuthModule` to imports array in `app.module.ts`.

### 12. Update Swagger config in main.ts

Add `.addBearerAuth()` to DocumentBuilder and `.addTag('auth', 'Authentication endpoints')`.

## Todo List

- [ ] Add users + refresh_tokens SQL to 01-schema.sql
- [ ] Install npm dependencies (@nestjs/passport, @nestjs/jwt, passport, passport-jwt, passport-local, bcrypt, types)
- [ ] Create user.entity.ts
- [ ] Create refresh-token.entity.ts
- [ ] Create register.dto.ts, login.dto.ts, auth-response.dto.ts
- [ ] Create auth.service.ts
- [ ] Create local.strategy.ts
- [ ] Create jwt.strategy.ts
- [ ] Create jwt-auth.guard.ts
- [ ] Create optional-jwt-auth.guard.ts
- [ ] Create auth.controller.ts
- [ ] Create auth.module.ts
- [ ] Add AuthModule to app.module.ts imports
- [ ] Add .addBearerAuth() to Swagger in main.ts
- [ ] Add JWT_SECRET, JWT_ACCESS_EXPIRATION, JWT_REFRESH_EXPIRATION to .env.example
- [ ] Verify `nest build` compiles without errors

## Success Criteria

- `POST /api/v1/auth/register` creates user, returns access token + sets httpOnly refresh cookie
- `POST /api/v1/auth/login` authenticates, returns access token + sets httpOnly refresh cookie
- `POST /api/v1/auth/refresh` rotates tokens
- `POST /api/v1/auth/logout` clears tokens
- `GET /api/v1/auth/me` returns user profile with valid JWT
- Passwords stored as bcrypt hashes (never plaintext)
- Swagger docs show auth endpoints with Bearer auth button
- `nest build` compiles clean

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| DB schema out of sync (synchronize: false) | Tables don't exist at runtime | Add SQL to 01-schema.sql; for running DB, execute migration manually |
| JWT_SECRET not set in env | App crashes or uses weak default | Fail fast in JwtStrategy if env var missing |
| Existing watchlists use VARCHAR(36) user_id | UUID mismatch | User.id is UUID — compatible with existing watchlist.user_id |
| bcrypt blocking event loop | Slow responses under load | bcrypt is async by default; 12 rounds is ~250ms, acceptable |

## Security Considerations

- Passwords: bcrypt with 12 salt rounds
- Refresh tokens: stored hashed in DB, transmitted only in httpOnly cookie
- Access tokens: short-lived (15min), no sensitive data in payload
- CORS: credentials already enabled, restrict origin in production
- Input validation: class-validator on all DTOs (whitelist: true, forbidNonWhitelisted: true)
- Email uniqueness enforced at DB level (UNIQUE constraint)

## Next Steps

- Phase 02: Apply guards to existing controllers
- After Phase 03: Migrate watchlist `X-User-Id` header to JWT-extracted userId
