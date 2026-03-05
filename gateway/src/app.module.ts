import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { GrpcClientModule } from './grpc/grpc-client.module';
import { StocksModule } from './stocks/stocks.module';
import { AnalyticsModule } from './analytics/analytics.module';
import { DatabaseModule } from './database/database.module';

@Module({
  imports: [
    // Load .env file globally across all modules
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    // PostgreSQL + TypeORM connection (reads credentials from ConfigService)
    DatabaseModule,
    // Global gRPC client proxies for Informer and Analytics services
    GrpcClientModule,
    // Feature modules
    StocksModule,
    AnalyticsModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}

