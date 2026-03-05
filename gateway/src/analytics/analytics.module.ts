import { Module } from '@nestjs/common';
import { AnalyticsController } from './analytics.controller';
import { AnalyticsService } from './analytics.service';

/**
 * AnalyticsModule — handles REST endpoints for technical indicators and valuation metrics.
 * Delegates to Python Analytics gRPC service via GrpcClientModule (global).
 */
@Module({
  controllers: [AnalyticsController],
  providers: [AnalyticsService],
})
export class AnalyticsModule {}
