/**
 * auth.service.ts — Core authentication business logic.
 * Handles registration, login, token generation/refresh, and logout.
 */
import {
  Injectable,
  ConflictException,
  UnauthorizedException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcrypt';
import * as crypto from 'crypto';
import { UserEntity } from '../entities/user.entity';
import { RefreshTokenEntity } from '../entities/refresh-token.entity';
import { RegisterDto } from './dto/register.dto';
import { AuthResponseDto, UserProfileDto } from './dto/auth-response.dto';

@Injectable()
export class AuthService {
  private readonly refreshExpDays: number;

  constructor(
    @InjectRepository(UserEntity)
    private readonly userRepo: Repository<UserEntity>,
    @InjectRepository(RefreshTokenEntity)
    private readonly refreshRepo: Repository<RefreshTokenEntity>,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {
    this.refreshExpDays = parseInt(
      this.configService.get<string>('JWT_REFRESH_EXPIRATION', '7'),
      10,
    );
  }

  /** Register a new user account */
  async register(dto: RegisterDto): Promise<{ auth: AuthResponseDto; refreshToken: string }> {
    const existing = await this.userRepo.findOne({ where: { email: dto.email } });
    if (existing) {
      throw new ConflictException('Email already registered');
    }

    const passwordHash = await bcrypt.hash(dto.password, 12);
    const user = this.userRepo.create({
      email: dto.email,
      passwordHash,
      name: dto.name,
    });
    await this.userRepo.save(user);

    return this.generateAuthResponse(user);
  }

  /** Validate email + password for local strategy */
  async validateUser(email: string, password: string): Promise<UserEntity | null> {
    const user = await this.userRepo.findOne({ where: { email } });
    if (!user || !user.isActive) return null;

    const valid = await bcrypt.compare(password, user.passwordHash);
    return valid ? user : null;
  }

  /** Generate tokens after successful login */
  async login(user: UserEntity): Promise<{ auth: AuthResponseDto; refreshToken: string }> {
    return this.generateAuthResponse(user);
  }

  /** Rotate refresh token — validate old, issue new pair */
  async refreshTokens(oldToken: string): Promise<{ auth: AuthResponseDto; refreshToken: string }> {
    // SHA-256 hash allows direct DB lookup (no bcrypt iteration needed)
    const tokenHash = this.hashRefreshToken(oldToken);

    const stored = await this.refreshRepo.findOne({
      where: { tokenHash },
      relations: ['user'],
    });

    if (!stored || !stored.user || new Date() > stored.expiresAt) {
      // If expired or not found, clean up and reject
      if (stored) await this.refreshRepo.delete(stored.id);
      throw new UnauthorizedException('Invalid or expired refresh token');
    }

    // Delete old token (rotation)
    await this.refreshRepo.delete(stored.id);

    return this.generateAuthResponse(stored.user);
  }

  /** Logout — delete all refresh tokens for user */
  async logout(userId: string): Promise<void> {
    await this.refreshRepo.delete({ userId });
  }

  /** Get user profile by ID */
  async getProfile(userId: string): Promise<UserProfileDto> {
    const user = await this.userRepo.findOne({ where: { id: userId } });
    if (!user) throw new UnauthorizedException('User not found');
    return this.toUserProfile(user);
  }

  /** Clean up expired refresh tokens (call periodically) */
  async cleanExpiredTokens(): Promise<void> {
    await this.refreshRepo
      .createQueryBuilder()
      .delete()
      .where('expires_at < :now', { now: new Date() })
      .execute();
  }

  // ── Private helpers ──────────────────────────────────────────

  private async generateAuthResponse(
    user: UserEntity,
  ): Promise<{ auth: AuthResponseDto; refreshToken: string }> {
    const accessToken = this.generateAccessToken(user);
    const refreshToken = this.generateRefreshToken();

    // Store SHA-256 hashed refresh token in DB
    const tokenHash = this.hashRefreshToken(refreshToken);
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + this.refreshExpDays);

    await this.refreshRepo.save(
      this.refreshRepo.create({ tokenHash, userId: user.id, expiresAt }),
    );

    return {
      auth: { accessToken, user: this.toUserProfile(user) },
      refreshToken,
    };
  }

  private generateAccessToken(user: UserEntity): string {
    return this.jwtService.sign({
      sub: user.id,
      email: user.email,
      role: user.role,
    });
  }

  private generateRefreshToken(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  /** SHA-256 hash for refresh token (enables direct DB lookup) */
  private hashRefreshToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }

  private toUserProfile(user: UserEntity): UserProfileDto {
    return { id: user.id, email: user.email, name: user.name, role: user.role };
  }
}
