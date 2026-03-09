/**
 * stocks.service.ts — Proxies REST requests to the Informer gRPC service.
 * Injects the INFORMER_SERVICE client registered in GrpcClientModule.
 */
import { Injectable, OnModuleInit, Inject, Logger } from '@nestjs/common';
import { ClientGrpc } from '@nestjs/microservices';
import { lastValueFrom, Observable } from 'rxjs';
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
}

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

  /** Get single stock metadata by symbol */
  async getStockInfo(symbol: string) {
    return lastValueFrom(this.informerService.GetStockInfo({ symbol }));
  }

  /** List stocks with optional filters and pagination */
  async listStocks(query: ListStocksQueryDto) {
    const pageSize = query.limit ?? query.pageSize;
    return lastValueFrom(
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
    return lastValueFrom(this.informerService.BatchGetStocks({ symbols }));
  }

  /** Get OHLCV price history for a symbol */
  async getPriceHistory(symbol: string, query: GetPriceHistoryQueryDto) {
    return lastValueFrom(
      this.informerService.GetPriceHistory({
        symbol,
        interval: query.interval ?? '1d',
        start_date: query.startDate ?? '',
        end_date: query.endDate ?? '',
        limit: query.limit ?? 365,
      }),
    );
  }

  /** Get financial reports for a symbol */
  async getFinancialReports(symbol: string, query: GetFinancialReportsQueryDto) {
    return lastValueFrom(
      this.informerService.GetFinancialReports({
        symbol,
        report_type: query.reportType ?? '',
        years_back: query.yearsBack ?? 5,
      }),
    );
  }

  /** Check Informer service health */
  async healthCheck() {
    return lastValueFrom(this.informerService.HealthCheck({}));
  }

  /** Create a new stock */
  async createStock(dto: CreateStockDto) {
    return lastValueFrom(
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
    return lastValueFrom(
      this.informerService.UpdateStock({
        symbol: symbol.toUpperCase(),
        stock: {
          symbol: symbol.toUpperCase(),
          name: dto.name ?? '',
          sector: dto.sector ?? '',
          industry: dto.industry ?? '',
          exchange: dto.exchange ?? '',
          country: dto.country ?? '',
          currency: dto.currency ?? '',
          is_active: dto.isActive ?? true,
        },
      }),
    );
  }

  /** Soft-delete a stock */
  async deleteStock(symbol: string) {
    return lastValueFrom(
      this.informerService.DeleteStock({ symbol: symbol.toUpperCase() }),
    );
  }
}
