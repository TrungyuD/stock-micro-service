/**
 * stocks.service.ts — Proxies REST requests to the Informer gRPC service.
 * Injects the INFORMER_SERVICE client registered in GrpcClientModule.
 */
import { Injectable, OnModuleInit, Inject, Logger } from '@nestjs/common';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable, timeout } from 'rxjs';
import { ListStocksQueryDto } from './dto/list-stocks-query.dto';
import { GetPriceHistoryQueryDto } from './dto/get-price-history-query.dto';
import { GetFinancialReportsQueryDto } from './dto/get-financial-reports-query.dto';
import { CreateStockDto } from './dto/create-stock.dto';
import { UpdateStockDto } from './dto/update-stock.dto';

/** gRPC service interface matching informer.proto */
interface InformerGrpcService {
  GetStockInfo(req: { symbol: string }): Observable<any>;
  ListStocks(req: any): Observable<any>;
  BatchGetStocks(req: { symbols: string[] }): Observable<any>;
  GetPriceHistory(req: any): Observable<any>;
  GetFinancialReports(req: any): Observable<any>;
  CreateStock(req: { stock: any }): Observable<any>;
  UpdateStock(req: { symbol: string; stock: any }): Observable<any>;
  DeleteStock(req: { symbol: string }): Observable<any>;
  HealthCheck(req: Record<string, never>): Observable<any>;
  GetLivePrice(req: { symbols: string[] }): Observable<any>;
}

/** Default gRPC call timeout in ms */
const GRPC_TIMEOUT_MS = 10_000;

@Injectable()
export class StocksService implements OnModuleInit {
  private readonly logger = new Logger(StocksService.name);
  private informerService: InformerGrpcService;

  constructor(@Inject('INFORMER_SERVICE') private readonly client: ClientGrpc) {}

  onModuleInit() {
    this.informerService =
      this.client.getService<InformerGrpcService>('InformerService');
    this.logger.log('Informer gRPC client initialized');
  }

  /** Wraps an observable with timeout to prevent indefinite hangs */
  private call<T>(obs: Observable<T>, timeoutMs = GRPC_TIMEOUT_MS): Promise<T> {
    return lastValueFrom(obs.pipe(timeout(timeoutMs)));
  }

  /** Get single stock metadata by symbol */
  async getStockInfo(symbol: string) {
    return this.call(this.informerService.GetStockInfo({ symbol }));
  }

  /** List stocks with optional filters and pagination */
  async listStocks(query: ListStocksQueryDto) {
    const pageSize = query.limit ?? query.pageSize;
    return this.call(
      this.informerService.ListStocks({
        exchange: query.exchange ?? '',
        sector: query.sector ?? '',
        search: query.search ?? '',
        country: query.country ?? '',
        pagination: { page: query.page, page_size: pageSize },
      }),
    );
  }

  /** Batch-get multiple stocks by symbols (max 50) */
  async batchGetStocks(symbols: string[]) {
    const normalized = symbols.map((s) => s.trim().toUpperCase());
    return this.call(this.informerService.BatchGetStocks({ symbols: normalized }));
  }

  /** Get OHLCV price history for a symbol */
  async getPriceHistory(symbol: string, query: GetPriceHistoryQueryDto) {
    return this.call(
      this.informerService.GetPriceHistory({
        symbol,
        interval: query.interval ?? '1d',
        start_date: query.startDate ?? '',
        end_date: query.endDate ?? '',
        limit: query.limit ?? 365,
      }),
      15_000, // price history may be slow on first fetch
    );
  }

  /** Get financial reports for a symbol */
  async getFinancialReports(symbol: string, query: GetFinancialReportsQueryDto) {
    return this.call(
      this.informerService.GetFinancialReports({
        symbol,
        report_type: query.reportType ?? '',
        years_back: query.yearsBack ?? 5,
      }),
      15_000,
    );
  }

  /** Check Informer service health */
  async healthCheck() {
    return this.call(this.informerService.HealthCheck({}), 3_000);
  }

  /** Create a new stock */
  async createStock(dto: CreateStockDto) {
    return this.call(
      this.informerService.CreateStock({
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
    // Only send fields that were explicitly provided (partial update)
    const stock: Record<string, unknown> = { symbol: symbol.toUpperCase() };
    if (dto.name !== undefined) stock.name = dto.name;
    if (dto.sector !== undefined) stock.sector = dto.sector;
    if (dto.industry !== undefined) stock.industry = dto.industry;
    if (dto.exchange !== undefined) stock.exchange = dto.exchange;
    if (dto.country !== undefined) stock.country = dto.country;
    if (dto.currency !== undefined) stock.currency = dto.currency;
    if (dto.isActive !== undefined) stock.is_active = dto.isActive;

    return this.call(
      this.informerService.UpdateStock({
        symbol: symbol.toUpperCase(),
        stock,
      }),
    );
  }

  /** Soft-delete a stock */
  async deleteStock(symbol: string) {
    return this.call(
      this.informerService.DeleteStock({ symbol: symbol.toUpperCase() }),
    );
  }

  /** Get live prices for multiple symbols via Informer gRPC */
  async getLivePrice(symbols: string[]) {
    return this.call(this.informerService.GetLivePrice({ symbols }));
  }
}
