/**
 * app.module.ts — Root module assembling all feature modules.
 * ConfigModule (global), DatabaseModule, GrpcClientModule,
 * CacheConfigModule, ThrottlerModule, and feature modules.
 */
import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { GrpcClientModule } from './grpc/grpc-client.module';
import { DatabaseModule } from './database/database.module';
import { CacheConfigModule } from './cache/cache-config.module';
import { StocksModule } from './stocks/stocks.module';
import { AnalyticsModule } from './analytics/analytics.module';
import { WatchlistsModule } from './watchlists/watchlists.module';
import { HealthModule } from './health/health.module';
import { AuthModule } from './auth/auth.module';

@Module({
  imports: [
    // Load .env file globally across all modules
    ConfigModule.forRoot({ isGlobal: true, envFilePath: '.env' }),
    // PostgreSQL + TypeORM connection
    DatabaseModule,
    // Redis cache (falls back to in-memory if Redis unavailable)
    CacheConfigModule,
    // Rate limiting: 100 requests per 60 seconds per IP
    ThrottlerModule.forRoot([{ ttl: 60_000, limit: 100 }]),
    // gRPC client proxies for Informer and Analytics services
    GrpcClientModule,
    // Feature modules
    AuthModule,
    StocksModule,
    AnalyticsModule,
    WatchlistsModule,
    HealthModule,
  ],
  providers: [
    // Apply rate limiting globally
    { provide: APP_GUARD, useClass: ThrottlerGuard },
  ],
})
export class AppModule {}
