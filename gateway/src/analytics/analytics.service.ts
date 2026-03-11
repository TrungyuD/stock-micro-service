/**
 * analytics.service.ts — Proxies REST requests to Analytics gRPC services.
 * Injects the ANALYTICS_SERVICE client registered in GrpcClientModule.
 * Uses four gRPC services from the v1 proto split:
 *   - TechnicalAnalysisService: RSI, MACD, Bollinger, MAs
 *   - FundamentalAnalysisService: valuation metrics + combined analysis
 *   - ScreeningService: stock screening, batch analysis, preset screens
 *   - ScoringService: composite scores + recommendations
 */
import { Injectable, OnModuleInit, Inject, Logger } from '@nestjs/common';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable, timeout } from 'rxjs';
import { GetTechnicalIndicatorsQueryDto } from './dto/get-technical-indicators-query.dto';
import { GetStockAnalysisQueryDto } from './dto/get-stock-analysis-query.dto';
import { ScreenStocksDto } from './dto/screen-stocks.dto';

/** gRPC service interface matching analyzer/v1/technical.proto */
interface TechnicalGrpcService {
  GetTechnicalIndicators(req: { symbol: string; timeframe: string }): Observable<any>;
  GetMultipleIndicators(req: { symbol: string; indicator_names: string[]; timeframe: string }): Observable<any>;
  GetIndicatorBatch(req: { symbols: string[]; timeframe: string }): Observable<any>;
}

/** gRPC service interface matching analyzer/v1/fundamental.proto */
interface FundamentalGrpcService {
  GetValuationMetrics(req: { symbol: string }): Observable<any>;
  GetStockAnalysis(req: { symbol: string; include_rationale: boolean }): Observable<any>;
  CompareStocks(req: { symbols: string[] }): Observable<any>;
}

/** gRPC service interface matching analyzer/v1/screening.proto */
interface ScreeningGrpcService {
  ScreenStocks(req: any): Observable<any>;
  BatchAnalysis(req: { symbols: string[] }): Observable<any>;
  GetPresetScreens(req: Record<string, never>): Observable<any>;
  TriggerCalculation(req: any): Observable<any>;
}

/** gRPC service interface matching analyzer/v1/scoring.proto */
interface ScoringGrpcService {
  GetScore(req: { symbol: string; strategy?: string }): Observable<any>;
  GetBatchScores(req: { symbols: string[]; strategy?: string }): Observable<any>;
  GetRecommendation(req: { symbol: string }): Observable<any>;
}

/** Default gRPC call timeout in ms */
const GRPC_TIMEOUT_MS = 10_000;

@Injectable()
export class AnalyticsService implements OnModuleInit {
  private readonly logger = new Logger(AnalyticsService.name);
  private technicalService: TechnicalGrpcService;
  private fundamentalService: FundamentalGrpcService;
  private screeningService: ScreeningGrpcService;
  private scoringService: ScoringGrpcService;

  constructor(@Inject('ANALYTICS_SERVICE') private readonly client: ClientGrpc) {}

  onModuleInit() {
    this.technicalService = this.client.getService<TechnicalGrpcService>('TechnicalAnalysisService');
    this.fundamentalService = this.client.getService<FundamentalGrpcService>('FundamentalAnalysisService');
    this.screeningService = this.client.getService<ScreeningGrpcService>('ScreeningService');
    this.scoringService = this.client.getService<ScoringGrpcService>('ScoringService');
    this.logger.log('Analytics gRPC services initialized (Technical, Fundamental, Screening, Scoring)');
  }

  /** Wraps an observable with timeout to prevent indefinite hangs */
  private call<T>(obs: Observable<T>, timeoutMs = GRPC_TIMEOUT_MS): Promise<T> {
    return lastValueFrom(obs.pipe(timeout(timeoutMs)));
  }

  // --- Fundamental Analysis ---

  /** Get valuation metrics (P/E, P/B, PEG, etc.) */
  async getValuationMetrics(symbol: string) {
    return this.call(this.fundamentalService.GetValuationMetrics({ symbol }));
  }

  /** Get combined stock analysis (valuation + technicals + recommendation) */
  async getStockAnalysis(symbol: string, query: GetStockAnalysisQueryDto) {
    return this.call(
      this.fundamentalService.GetStockAnalysis({
        symbol,
        include_rationale: query.includeRationale ?? false,
      }),
      15_000,
    );
  }

  /** Compare multiple stocks side-by-side (max 10) */
  async compareStocks(symbols: string[]) {
    return this.call(this.fundamentalService.CompareStocks({ symbols }), 30_000);
  }

  // --- Technical Analysis ---

  /** Get technical indicators (RSI, MACD, Bollinger, MAs) */
  async getTechnicalIndicators(symbol: string, query: GetTechnicalIndicatorsQueryDto) {
    return this.call(
      this.technicalService.GetTechnicalIndicators({
        symbol,
        timeframe: query.timeframe ?? '1d',
      }),
    );
  }

  /** Get specific indicators by name for a symbol */
  async getMultipleIndicators(symbol: string, indicatorNames: string[], timeframe = '1d') {
    return this.call(
      this.technicalService.GetMultipleIndicators({
        symbol,
        indicator_names: indicatorNames,
        timeframe,
      }),
    );
  }

  /** Batch get indicators for multiple symbols (max 20) */
  async getIndicatorBatch(symbols: string[], timeframe = '1d') {
    return this.call(
      this.technicalService.GetIndicatorBatch({ symbols, timeframe }),
      30_000,
    );
  }

  // --- Screening ---

  /** Screen stocks by valuation/technical criteria */
  async screenStocks(dto: ScreenStocksDto) {
    return this.call(
      this.screeningService.ScreenStocks({
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
      30_000,
    );
  }

  /** Batch analysis for multiple symbols (max 50) */
  async batchAnalysis(symbols: string[]) {
    return this.call(this.screeningService.BatchAnalysis({ symbols }), 60_000);
  }

  /** Get preset screening templates */
  async getPresetScreens() {
    return this.call(this.screeningService.GetPresetScreens({}), 3_000);
  }

  // --- Scoring ---

  /** Get composite score for a single symbol */
  async getScore(symbol: string, strategy?: string) {
    return this.call(this.scoringService.GetScore({ symbol, strategy }));
  }

  /** Batch scores for multiple symbols (max 50) */
  async getBatchScores(symbols: string[], strategy?: string) {
    return this.call(this.scoringService.GetBatchScores({ symbols, strategy }), 30_000);
  }

  /** Get buy/hold/sell recommendation for a symbol */
  async getRecommendation(symbol: string) {
    return this.call(this.scoringService.GetRecommendation({ symbol }), 15_000);
  }
}
