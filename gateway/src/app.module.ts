/**
 * app.module.ts — Root module assembling all feature modules.
 * ConfigModule (global), DatabaseModule, GrpcClientModule, and feature modules.
 */
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { GrpcClientModule } from './grpc/grpc-client.module';
import { DatabaseModule } from './database/database.module';
import { StocksModule } from './stocks/stocks.module';
import { AnalyticsModule } from './analytics/analytics.module';
import { WatchlistsModule } from './watchlists/watchlists.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [
    // Load .env file globally across all modules
    ConfigModule.forRoot({ isGlobal: true, envFilePath: '.env' }),
    // PostgreSQL + TypeORM connection
    DatabaseModule,
    // gRPC client proxies for Informer and Analytics services
    GrpcClientModule,
    // Feature modules
    StocksModule,
    AnalyticsModule,
    WatchlistsModule,
    HealthModule,
  ],
})
export class AppModule {}
