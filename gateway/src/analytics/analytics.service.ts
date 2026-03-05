import { Injectable } from '@nestjs/common';

/**
 * AnalyticsService — placeholder service for technical indicators.
 * Will be wired to Analytics gRPC client in Phase 6.
 */
@Injectable()
export class AnalyticsService {
  getIndicators(symbol: string) {
    return { symbol, message: 'AnalyticsService placeholder — Phase 6 implementation pending' };
  }
}
