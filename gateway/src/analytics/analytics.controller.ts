import { Controller, Get, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AnalyticsService } from './analytics.service';

/**
 * AnalyticsController — REST endpoints for technical analysis data.
 * Full implementation in Phase 6.
 */
@ApiTags('analytics')
@Controller('analytics')
export class AnalyticsController {
  constructor(private readonly analyticsService: AnalyticsService) {}

  @Get(':symbol/indicators')
  @ApiOperation({ summary: 'Get technical indicators for a symbol (placeholder)' })
  getIndicators(@Param('symbol') symbol: string) {
    return this.analyticsService.getIndicators(symbol);
  }
}
