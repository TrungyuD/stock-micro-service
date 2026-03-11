/**
 * stocks.service.ts — Proxies REST requests to Informer gRPC services.
 * Injects the INFORMER_SERVICE client registered in GrpcClientModule.
 * Uses three gRPC services from the v1 proto split:
 *   - StockService: metadata CRUD + search
 *   - PriceService: latest prices + OHLCV history
 *   - FinancialService: income, balance sheet, cash flow, financial reports
 */
import { Injectable, OnModuleInit, Inject, Logger } from '@nestjs/common';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable, timeout } from 'rxjs';
import { ListStocksQueryDto } from './dto/list-stocks-query.dto';
import { GetPriceHistoryQueryDto } from './dto/get-price-history-query.dto';
import { GetFinancialReportsQueryDto } from './dto/get-financial-reports-query.dto';
import { CreateStockDto } from './dto/create-stock.dto';
import { UpdateStockDto } from './dto/update-stock.dto';

/** gRPC service interfaces matching informer/v1/stock.proto */
interface StockGrpcService {
  GetStock(req: { symbol: string }): Observable<any>;
  ListStocks(req: any): Observable<any>;
  SearchStocks(req: { query: string; limit: number }): Observable<any>;
  GetStocksByIds(req: { ids: number[] }): Observable<any>;
  CreateStock(req: { stock: any }): Observable<any>;
  UpdateStock(req: { symbol: string; stock: any }): Observable<any>;
  DeleteStock(req: { symbol: string }): Observable<any>;
  TriggerDataCollection(req: any): Observable<any>;
}

/** gRPC service interfaces matching informer/v1/price.proto */
interface PriceGrpcService {
  GetLatestPrice(req: { symbol: string }): Observable<any>;
  GetLatestPrices(req: { symbols: string[] }): Observable<any>;
  GetOHLCV(req: any): Observable<any>;
  /** Server-side streaming: continuous price updates at the given interval */
  StreamPrices(req: { symbols: string[]; interval_ms: number }): Observable<any>;
}

/** gRPC service interfaces matching informer/v1/financial.proto */
interface FinancialGrpcService {
  GetIncomeStatement(req: any): Observable<any>;
  GetBalanceSheet(req: any): Observable<any>;
  GetCashFlow(req: any): Observable<any>;
  GetFinancialSummary(req: { symbol: string }): Observable<any>;
  GetFinancialReports(req: any): Observable<any>;
}

/** Default gRPC call timeout in ms */
const GRPC_TIMEOUT_MS = 10_000;

@Injectable()
export class StocksService implements OnModuleInit {
  private readonly logger = new Logger(StocksService.name);
  private stockService: StockGrpcService;
  private priceService: PriceGrpcService;
  private financialService: FinancialGrpcService;

  constructor(@Inject('INFORMER_SERVICE') private readonly client: ClientGrpc) {}

  onModuleInit() {
    this.stockService = this.client.getService<StockGrpcService>('StockService');
    this.priceService = this.client.getService<PriceGrpcService>('PriceService');
    this.financialService = this.client.getService<FinancialGrpcService>('FinancialService');
    this.logger.log('Informer gRPC services initialized (Stock, Price, Financial)');
  }

  /** Wraps an observable with timeout to prevent indefinite hangs */
  private call<T>(obs: Observable<T>, timeoutMs = GRPC_TIMEOUT_MS): Promise<T> {
    return lastValueFrom(obs.pipe(timeout(timeoutMs)));
  }

  /** Get single stock metadata by symbol */
  async getStockInfo(symbol: string) {
    return this.call(this.stockService.GetStock({ symbol }));
  }

  /** List stocks with optional filters and pagination */
  async listStocks(query: ListStocksQueryDto) {
    const pageSize = query.limit ?? query.pageSize;
    return this.call(
      this.stockService.ListStocks({
        exchange: query.exchange ?? '',
        sector: query.sector ?? '',
        search: query.search ?? '',
        country: query.country ?? '',
        pagination: { page: query.page, page_size: pageSize },
      }),
    );
  }

  /** Search stocks by name/symbol substring */
  async searchStocks(query: string, limit = 20) {
    return this.call(this.stockService.SearchStocks({ query, limit }));
  }

  /** Batch-get multiple stocks by symbols (max 50) — kept for backward compat with controller */
  async batchGetStocks(symbols: string[]) {
    const normalized = symbols.map((s) => s.trim().toUpperCase());
    // New proto uses SearchStocks for symbol-based lookup; fall back to search per symbol
    return this.call(
      this.stockService.SearchStocks({ query: normalized.join(','), limit: normalized.length }),
    );
  }

  /** Get OHLCV price history for a symbol */
  async getPriceHistory(symbol: string, query: GetPriceHistoryQueryDto) {
    return this.call(
      this.priceService.GetOHLCV({
        symbol,
        interval: query.interval ?? '1d',
        start_date: query.startDate ?? '',
        end_date: query.endDate ?? '',
        limit: query.limit ?? 365,
      }),
      15_000,
    );
  }

  /** Get financial reports for a symbol (backward-compat monolithic endpoint) */
  async getFinancialReports(symbol: string, query: GetFinancialReportsQueryDto) {
    return this.call(
      this.financialService.GetFinancialReports({
        symbol,
        report_type: query.reportType ?? '',
        years_back: query.yearsBack ?? 5,
      }),
      15_000,
    );
  }

  /** Create a new stock */
  async createStock(dto: CreateStockDto) {
    return this.call(
      this.stockService.CreateStock({
        stock: {
          symbol: dto.symbol?.toUpperCase(),
          name: dto.name,
          sector: dto.sector ?? '',
          industry: dto.industry ?? '',
          exchange: dto.exchange ?? '',
          country: dto.country ?? 'US',
          currency: dto.currency ?? 'USD',
          is_active: dto.isActive ?? true,
        },
      }),
    );
  }

  /** Update an existing stock */
  async updateStock(symbol: string, dto: UpdateStockDto) {
    const stock: Record<string, unknown> = { symbol: symbol.toUpperCase() };
    if (dto.name !== undefined) stock.name = dto.name;
    if (dto.sector !== undefined) stock.sector = dto.sector;
    if (dto.industry !== undefined) stock.industry = dto.industry;
    if (dto.exchange !== undefined) stock.exchange = dto.exchange;
    if (dto.country !== undefined) stock.country = dto.country;
    if (dto.currency !== undefined) stock.currency = dto.currency;
    if (dto.isActive !== undefined) stock.is_active = dto.isActive;

    return this.call(
      this.stockService.UpdateStock({ symbol: symbol.toUpperCase(), stock }),
    );
  }

  /** Soft-delete a stock */
  async deleteStock(symbol: string) {
    return this.call(
      this.stockService.DeleteStock({ symbol: symbol.toUpperCase() }),
    );
  }

  /** Get latest price snapshot for a single symbol */
  async getLatestPrice(symbol: string) {
    return this.call(this.priceService.GetLatestPrice({ symbol }));
  }

  /** Get latest prices for multiple symbols (used by price poller) */
  async getLatestPrices(symbols: string[]) {
    return this.call(this.priceService.GetLatestPrices({ symbols }));
  }

  /** Server-side streaming: continuous price updates (returns Observable, no timeout) */
  streamPrices(symbols: string[], intervalMs = 15000): Observable<any> {
    return this.priceService.StreamPrices({ symbols, interval_ms: intervalMs });
  }

  /** Get income statement data */
  async getIncomeStatement(symbol: string, period = 'annual', yearsBack = 5) {
    return this.call(
      this.financialService.GetIncomeStatement({ symbol, period, years_back: yearsBack }),
      15_000,
    );
  }

  /** Get balance sheet data */
  async getBalanceSheet(symbol: string, period = 'annual', yearsBack = 5) {
    return this.call(
      this.financialService.GetBalanceSheet({ symbol, period, years_back: yearsBack }),
      15_000,
    );
  }

  /** Get cash flow statement data */
  async getCashFlow(symbol: string, period = 'annual', yearsBack = 5) {
    return this.call(
      this.financialService.GetCashFlow({ symbol, period, years_back: yearsBack }),
      15_000,
    );
  }

  /** Get combined financial summary (key metrics) */
  async getFinancialSummary(symbol: string) {
    return this.call(this.financialService.GetFinancialSummary({ symbol }), 15_000);
  }
}
