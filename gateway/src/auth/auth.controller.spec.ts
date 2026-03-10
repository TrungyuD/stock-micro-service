/**
 * auth.controller.spec.ts — Unit tests for AuthController.
 * Covers register, login, refresh, logout, me endpoints + cookie handling.
 */
import { Test, TestingModule } from '@nestjs/testing';
import { HttpStatus } from '@nestjs/common';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';

describe('AuthController', () => {
  let controller: AuthController;

  const mockAuthService = {
    register: jest.fn(),
    login: jest.fn(),
    refreshTokens: jest.fn(),
    logout: jest.fn(),
    getProfile: jest.fn(),
  };

  const mockUser = {
    id: 'user-uuid-1',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user',
  };

  const mockAuthResponse = {
    auth: { accessToken: 'mock_token', user: mockUser },
    refreshToken: 'raw_refresh_hex',
  };

  /** Create a fake Express Response with cookie/clearCookie/status/json */
  const createMockResponse = () => ({
    cookie: jest.fn(),
    clearCookie: jest.fn(),
    status: jest.fn().mockReturnThis(),
    json: jest.fn(),
  });

  /** Create a fake Express Request with optional cookies and user */
  const createMockRequest = (overrides: Record<string, any> = {}) => ({
    cookies: {},
    user: undefined,
    ...overrides,
  });

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      controllers: [AuthController],
      providers: [{ provide: AuthService, useValue: mockAuthService }],
    }).compile();

    controller = module.get<AuthController>(AuthController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  // ── register ──────────────────────────────────────────
  describe('register', () => {
    const dto = { email: 'new@example.com', password: 'Password123', name: 'New User' };

    it('should register user, set refresh cookie, and return auth response', async () => {
      mockAuthService.register.mockResolvedValue(mockAuthResponse);
      const res = createMockResponse();

      const result = await controller.register(dto, res as any);

      expect(mockAuthService.register).toHaveBeenCalledWith(dto);
      expect(res.cookie).toHaveBeenCalledWith(
        'refresh_token',
        'raw_refresh_hex',
        expect.objectContaining({ httpOnly: true, path: '/api/v1/auth' }),
      );
      expect(result).toEqual(mockAuthResponse.auth);
    });
  });

  // ── login ─────────────────────────────────────────────
  describe('login', () => {
    it('should login user, set refresh cookie, and return auth response', async () => {
      mockAuthService.login.mockResolvedValue(mockAuthResponse);
      const req = createMockRequest({ user: mockUser });
      const res = createMockResponse();

      const result = await controller.login({ email: '', password: '' }, req as any, res as any);

      expect(mockAuthService.login).toHaveBeenCalledWith(mockUser);
      expect(res.cookie).toHaveBeenCalledWith(
        'refresh_token',
        'raw_refresh_hex',
        expect.objectContaining({ httpOnly: true }),
      );
      expect(result).toEqual(mockAuthResponse.auth);
    });
  });

  // ── refresh ───────────────────────────────────────────
  describe('refresh', () => {
    it('should refresh tokens when cookie is present', async () => {
      mockAuthService.refreshTokens.mockResolvedValue(mockAuthResponse);
      const req = createMockRequest({ cookies: { refresh_token: 'old_token' } });
      const res = createMockResponse();

      const result = await controller.refresh(req as any, res as any);

      expect(mockAuthService.refreshTokens).toHaveBeenCalledWith('old_token');
      expect(res.cookie).toHaveBeenCalledWith(
        'refresh_token',
        'raw_refresh_hex',
        expect.objectContaining({ httpOnly: true }),
      );
      expect(result).toEqual(mockAuthResponse.auth);
    });

    it('should return 401 when no refresh cookie', async () => {
      const req = createMockRequest({ cookies: {} });
      const res = createMockResponse();

      await controller.refresh(req as any, res as any);

      expect(res.status).toHaveBeenCalledWith(HttpStatus.UNAUTHORIZED);
      expect(res.json).toHaveBeenCalledWith({ message: 'No refresh token' });
      expect(mockAuthService.refreshTokens).not.toHaveBeenCalled();
    });
  });

  // ── logout ────────────────────────────────────────────
  describe('logout', () => {
    it('should logout user, clear refresh cookie', async () => {
      mockAuthService.logout.mockResolvedValue(undefined);
      const req = createMockRequest({ user: { userId: 'user-uuid-1' } });
      const res = createMockResponse();

      const result = await controller.logout(req as any, res as any);

      expect(mockAuthService.logout).toHaveBeenCalledWith('user-uuid-1');
      expect(res.clearCookie).toHaveBeenCalledWith(
        'refresh_token',
        expect.objectContaining({ maxAge: 0 }),
      );
      expect(result).toEqual({ message: 'Logged out' });
    });
  });

  // ── me ────────────────────────────────────────────────
  describe('me', () => {
    it('should return user profile', async () => {
      mockAuthService.getProfile.mockResolvedValue(mockUser);
      const req = createMockRequest({ user: { userId: 'user-uuid-1' } });

      const result = await controller.me(req as any);

      expect(mockAuthService.getProfile).toHaveBeenCalledWith('user-uuid-1');
      expect(result).toEqual(mockUser);
    });
  });
});
