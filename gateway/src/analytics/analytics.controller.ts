/**
 * analytics.controller.ts — REST endpoints for stock analysis data.
 * Proxies to Analytics gRPC service via AnalyticsService.
 */
import { Controller, Get, Post, Param, Query, Body } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiParam, ApiResponse } from '@nestjs/swagger';
import { AnalyticsService } from './analytics.service';
import { GetTechnicalIndicatorsQueryDto } from './dto/get-technical-indicators-query.dto';
import { GetStockAnalysisQueryDto } from './dto/get-stock-analysis-query.dto';
import { BatchAnalysisDto } from './dto/batch-analysis.dto';
import { ScreenStocksDto } from './dto/screen-stocks.dto';

@ApiTags('analytics')
@Controller('analytics')
export class AnalyticsController {
  constructor(private readonly analyticsService: AnalyticsService) {}

  @Get(':symbol')
  @ApiOperation({ summary: 'Get combined stock analysis (valuation + technicals)' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Combined analysis with recommendation' })
  getStockAnalysis(
    @Param('symbol') symbol: string,
    @Query() query: GetStockAnalysisQueryDto,
  ) {
    return this.analyticsService.getStockAnalysis(symbol.toUpperCase(), query);
  }

  @Get(':symbol/valuation')
  @ApiOperation({ summary: 'Get valuation metrics (P/E, P/B, PEG, etc.)' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Valuation metrics' })
  getValuationMetrics(@Param('symbol') symbol: string) {
    return this.analyticsService.getValuationMetrics(symbol.toUpperCase());
  }

  @Get(':symbol/technicals')
  @ApiOperation({ summary: 'Get technical indicators (RSI, MACD, MAs, Bollinger)' })
  @ApiParam({ name: 'symbol', example: 'AAPL' })
  @ApiResponse({ status: 200, description: 'Technical indicator data' })
  getTechnicalIndicators(
    @Param('symbol') symbol: string,
    @Query() query: GetTechnicalIndicatorsQueryDto,
  ) {
    return this.analyticsService.getTechnicalIndicators(symbol.toUpperCase(), query);
  }

  @Post('batch')
  @ApiOperation({ summary: 'Batch analysis for multiple symbols (max 50)' })
  @ApiResponse({ status: 200, description: 'Analysis results for each symbol' })
  batchAnalysis(@Body() dto: BatchAnalysisDto) {
    return this.analyticsService.batchAnalysis(dto.symbols);
  }

  @Post('screen')
  @ApiOperation({ summary: 'Screen stocks by valuation/technical criteria' })
  @ApiResponse({ status: 200, description: 'Matching stocks with scores' })
  screenStocks(@Body() dto: ScreenStocksDto) {
    return this.analyticsService.screenStocks(dto);
  }
}
