/**
 * jwt-auth.guard.ts — Guard requiring valid JWT access token.
 * Apply via @UseGuards(JwtAuthGuard) on protected endpoints.
 */
import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {}
