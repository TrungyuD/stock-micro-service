/**
 * roles.guard.spec.ts — Unit tests for RolesGuard.
 * Covers: no roles metadata (allow all), matching role, mismatched role, missing user.
 */
import { ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { RolesGuard } from './roles.guard';

describe('RolesGuard', () => {
  let guard: RolesGuard;
  let reflector: Reflector;

  /** Build a minimal ExecutionContext mock with the given request user */
  const createContext = (user?: Record<string, any>): ExecutionContext =>
    ({
      getHandler: jest.fn(),
      getClass: jest.fn(),
      switchToHttp: () => ({
        getRequest: () => ({ user }),
      }),
    }) as unknown as ExecutionContext;

  beforeEach(() => {
    reflector = new Reflector();
    guard = new RolesGuard(reflector);
  });

  it('should allow access when no @Roles() metadata is set', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(undefined);

    expect(guard.canActivate(createContext({ role: 'user' }))).toBe(true);
  });

  it('should allow access when user role matches required role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(['admin']);

    expect(guard.canActivate(createContext({ role: 'admin' }))).toBe(true);
  });

  it('should deny access when user role does not match', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(['admin']);

    expect(guard.canActivate(createContext({ role: 'user' }))).toBe(false);
  });

  it('should deny access when user is undefined', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(['admin']);

    expect(guard.canActivate(createContext(undefined))).toBe(false);
  });

  it('should allow access when user role is in multiple required roles', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(['admin', 'moderator']);

    expect(guard.canActivate(createContext({ role: 'moderator' }))).toBe(true);
  });
});
