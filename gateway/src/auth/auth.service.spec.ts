/**
 * auth.service.spec.ts — Unit tests for AuthService.
 * Covers register, validateUser, login, refreshTokens, logout, getProfile, cleanExpiredTokens.
 */
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { ConflictException, UnauthorizedException } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';
import { AuthService } from './auth.service';
import { UserEntity } from '../entities/user.entity';
import { RefreshTokenEntity } from '../entities/refresh-token.entity';

// Mock bcrypt to avoid slow hashing in tests
jest.mock('bcrypt', () => ({
  hash: jest.fn().mockResolvedValue('hashed_password'),
  compare: jest.fn(),
}));

describe('AuthService', () => {
  let service: AuthService;

  const mockUserRepo = {
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
  };

  const mockRefreshRepo = {
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
    delete: jest.fn(),
    createQueryBuilder: jest.fn(),
  };

  const mockJwtService = {
    sign: jest.fn().mockReturnValue('mock_access_token'),
  };

  const mockConfigService = {
    get: jest.fn((key: string, fallback?: string) => {
      if (key === 'JWT_REFRESH_EXPIRATION') return '7';
      return fallback;
    }),
  };

  const mockUser: Partial<UserEntity> = {
    id: 'user-uuid-1',
    email: 'test@example.com',
    passwordHash: 'hashed_password',
    name: 'Test User',
    role: 'user',
    isActive: true,
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: getRepositoryToken(UserEntity), useValue: mockUserRepo },
        { provide: getRepositoryToken(RefreshTokenEntity), useValue: mockRefreshRepo },
        { provide: JwtService, useValue: mockJwtService },
        { provide: ConfigService, useValue: mockConfigService },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  // ── register ──────────────────────────────────────────
  describe('register', () => {
    const dto = { email: 'new@example.com', password: 'Password123', name: 'New User' };

    it('should register a new user and return auth response', async () => {
      mockUserRepo.findOne.mockResolvedValue(null);
      const createdUser = { ...mockUser, email: dto.email, name: dto.name };
      mockUserRepo.create.mockReturnValue(createdUser);
      mockUserRepo.save.mockResolvedValue(createdUser);
      mockRefreshRepo.create.mockReturnValue({});
      mockRefreshRepo.save.mockResolvedValue({});

      const result = await service.register(dto);

      expect(mockUserRepo.findOne).toHaveBeenCalledWith({ where: { email: dto.email } });
      expect(bcrypt.hash).toHaveBeenCalledWith(dto.password, 12);
      expect(result.auth.accessToken).toBe('mock_access_token');
      expect(result.auth.user.email).toBe(dto.email);
      expect(result.refreshToken).toBeDefined();
    });

    it('should throw ConflictException if email already registered', async () => {
      mockUserRepo.findOne.mockResolvedValue(mockUser);

      await expect(service.register(dto)).rejects.toThrow(ConflictException);
    });
  });

  // ── validateUser ──────────────────────────────────────
  describe('validateUser', () => {
    it('should return user when credentials are valid', async () => {
      mockUserRepo.findOne.mockResolvedValue(mockUser);
      (bcrypt.compare as jest.Mock).mockResolvedValue(true);

      const result = await service.validateUser('test@example.com', 'Password123');
      expect(result).toEqual(mockUser);
    });

    it('should return null when user not found', async () => {
      mockUserRepo.findOne.mockResolvedValue(null);

      const result = await service.validateUser('missing@example.com', 'pass');
      expect(result).toBeNull();
    });

    it('should return null when user is inactive', async () => {
      mockUserRepo.findOne.mockResolvedValue({ ...mockUser, isActive: false });

      const result = await service.validateUser('test@example.com', 'pass');
      expect(result).toBeNull();
    });

    it('should return null when password is invalid', async () => {
      mockUserRepo.findOne.mockResolvedValue(mockUser);
      (bcrypt.compare as jest.Mock).mockResolvedValue(false);

      const result = await service.validateUser('test@example.com', 'wrong');
      expect(result).toBeNull();
    });
  });

  // ── login ─────────────────────────────────────────────
  describe('login', () => {
    it('should generate tokens for a valid user', async () => {
      mockRefreshRepo.create.mockReturnValue({});
      mockRefreshRepo.save.mockResolvedValue({});

      const result = await service.login(mockUser as UserEntity);

      expect(result.auth.accessToken).toBe('mock_access_token');
      expect(result.auth.user.id).toBe(mockUser.id);
      expect(result.refreshToken).toBeDefined();
      expect(mockJwtService.sign).toHaveBeenCalledWith({
        sub: mockUser.id,
        email: mockUser.email,
        role: mockUser.role,
      });
    });
  });

  // ── refreshTokens ─────────────────────────────────────
  describe('refreshTokens', () => {
    const rawToken = 'raw_refresh_token_hex';
    const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');

    it('should rotate refresh token and return new auth response', async () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 1);

      mockRefreshRepo.findOne.mockResolvedValue({
        id: 1,
        tokenHash,
        user: mockUser,
        expiresAt: futureDate,
      });
      mockRefreshRepo.delete.mockResolvedValue({});
      mockRefreshRepo.create.mockReturnValue({});
      mockRefreshRepo.save.mockResolvedValue({});

      const result = await service.refreshTokens(rawToken);

      // Old token deleted
      expect(mockRefreshRepo.delete).toHaveBeenCalledWith(1);
      expect(result.auth.accessToken).toBe('mock_access_token');
      expect(result.refreshToken).toBeDefined();
    });

    it('should throw UnauthorizedException when token not found', async () => {
      mockRefreshRepo.findOne.mockResolvedValue(null);

      await expect(service.refreshTokens('invalid_token')).rejects.toThrow(
        UnauthorizedException,
      );
    });

    it('should throw UnauthorizedException when token is expired', async () => {
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 1);

      mockRefreshRepo.findOne.mockResolvedValue({
        id: 2,
        tokenHash,
        user: mockUser,
        expiresAt: pastDate,
      });
      mockRefreshRepo.delete.mockResolvedValue({});

      await expect(service.refreshTokens(rawToken)).rejects.toThrow(UnauthorizedException);
      // Expired token should be cleaned up
      expect(mockRefreshRepo.delete).toHaveBeenCalledWith(2);
    });
  });

  // ── logout ────────────────────────────────────────────
  describe('logout', () => {
    it('should delete all refresh tokens for the user', async () => {
      mockRefreshRepo.delete.mockResolvedValue({});

      await service.logout('user-uuid-1');

      expect(mockRefreshRepo.delete).toHaveBeenCalledWith({ userId: 'user-uuid-1' });
    });
  });

  // ── getProfile ────────────────────────────────────────
  describe('getProfile', () => {
    it('should return user profile DTO', async () => {
      mockUserRepo.findOne.mockResolvedValue(mockUser);

      const result = await service.getProfile('user-uuid-1');

      expect(result).toEqual({
        id: mockUser.id,
        email: mockUser.email,
        name: mockUser.name,
        role: mockUser.role,
      });
    });

    it('should throw UnauthorizedException when user not found', async () => {
      mockUserRepo.findOne.mockResolvedValue(null);

      await expect(service.getProfile('missing-uuid')).rejects.toThrow(UnauthorizedException);
    });
  });

  // ── cleanExpiredTokens ────────────────────────────────
  describe('cleanExpiredTokens', () => {
    it('should delete expired refresh tokens via query builder', async () => {
      const mockQb = {
        delete: jest.fn().mockReturnThis(),
        where: jest.fn().mockReturnThis(),
        execute: jest.fn().mockResolvedValue({ affected: 3 }),
      };
      mockRefreshRepo.createQueryBuilder.mockReturnValue(mockQb);

      await service.cleanExpiredTokens();

      expect(mockRefreshRepo.createQueryBuilder).toHaveBeenCalled();
      expect(mockQb.delete).toHaveBeenCalled();
      expect(mockQb.where).toHaveBeenCalledWith('expires_at < :now', { now: expect.any(Date) });
      expect(mockQb.execute).toHaveBeenCalled();
    });
  });
});
