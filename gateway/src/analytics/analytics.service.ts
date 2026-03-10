/**
 * analytics.service.ts — Proxies REST requests to the Analytics gRPC service.
 * Injects the ANALYTICS_SERVICE client registered in GrpcClientModule.
 */
import { Injectable, OnModuleInit, Inject, Logger } from '@nestjs/common';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable, timeout } from 'rxjs';
import { GetTechnicalIndicatorsQueryDto } from './dto/get-technical-indicators-query.dto';
import { GetStockAnalysisQueryDto } from './dto/get-stock-analysis-query.dto';
import { ScreenStocksDto } from './dto/screen-stocks.dto';

/** gRPC service interface matching analytics.proto */
interface AnalyticsGrpcService {
  GetValuationMetrics(req: { symbol: string }): Observable<any>;
  GetTechnicalIndicators(req: { symbol: string; timeframe: string }): Observable<any>;
  GetStockAnalysis(req: { symbol: string; include_rationale: boolean }): Observable<any>;
  BatchAnalysis(req: { symbols: string[] }): Observable<any>;
  ScreenStocks(req: any): Observable<any>;
  HealthCheck(req: Record<string, never>): Observable<any>;
}

/** Default gRPC call timeout in ms */
const GRPC_TIMEOUT_MS = 10_000;

@Injectable()
export class AnalyticsService implements OnModuleInit {
  private readonly logger = new Logger(AnalyticsService.name);
  private analyticsService: AnalyticsGrpcService;

  constructor(@Inject('ANALYTICS_SERVICE') private readonly client: ClientGrpc) {}

  onModuleInit() {
    this.analyticsService =
      this.client.getService<AnalyticsGrpcService>('AnalyticsService');
    this.logger.log('Analytics gRPC client initialized');
  }

  /** Wraps an observable with timeout to prevent indefinite hangs */
  private call<T>(obs: Observable<T>, timeoutMs = GRPC_TIMEOUT_MS): Promise<T> {
    return lastValueFrom(obs.pipe(timeout(timeoutMs)));
  }

  /** Get valuation metrics (P/E, P/B, PEG, etc.) */
  async getValuationMetrics(symbol: string) {
    return this.call(this.analyticsService.GetValuationMetrics({ symbol }));
  }

  /** Get technical indicators (RSI, MACD, Bollinger, MAs) */
  async getTechnicalIndicators(symbol: string, query: GetTechnicalIndicatorsQueryDto) {
    return this.call(
      this.analyticsService.GetTechnicalIndicators({
        symbol,
        timeframe: query.timeframe ?? '1d',
      }),
    );
  }

  /** Get combined stock analysis (valuation + technicals + recommendation) */
  async getStockAnalysis(symbol: string, query: GetStockAnalysisQueryDto) {
    return this.call(
      this.analyticsService.GetStockAnalysis({
        symbol,
        include_rationale: query.includeRationale ?? false,
      }),
    );
  }

  /** Batch analysis for multiple symbols */
  async batchAnalysis(symbols: string[]) {
    return this.call(this.analyticsService.BatchAnalysis({ symbols }), 15_000);
  }

  /** Screen stocks by criteria */
  async screenStocks(dto: ScreenStocksDto) {
    return this.call(
      this.analyticsService.ScreenStocks({
        criteria: {
          min_pe: dto.minPe ?? 0,
          max_pe: dto.maxPe ?? 0,
          min_peg: dto.minPeg ?? 0,
          max_peg: dto.maxPeg ?? 0,
          min_dividend_yield: dto.minDividendYield ?? 0,
          max_dividend_yield: dto.maxDividendYield ?? 0,
          rsi_oversold: dto.rsiOversold ?? false,
          rsi_overbought: dto.rsiOverbought ?? false,
          trend_direction: dto.trendDirection ?? '',
          sector: dto.sector ?? '',
        },
        limit: dto.limit ?? 20,
        sort_by: dto.sortBy ?? '',
      }),
      15_000, // screening scans all stocks
    );
  }

  /** Check Analytics service health */
  async healthCheck() {
    return this.call(this.analyticsService.HealthCheck({}), 3_000);
  }
}
