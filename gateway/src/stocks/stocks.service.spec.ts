import { Test, TestingModule } from '@nestjs/testing';
import { of } from 'rxjs';
import { StocksService } from './stocks.service';

describe('StocksService', () => {
  let service: StocksService;
  const mockGrpcService = {
    GetStockInfo: jest.fn(),
    ListStocks: jest.fn(),
    BatchGetStocks: jest.fn(),
    GetPriceHistory: jest.fn(),
    GetFinancialReports: jest.fn(),
    HealthCheck: jest.fn(),
  };

  const mockClient = {
    getService: jest.fn().mockReturnValue(mockGrpcService),
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        StocksService,
        { provide: 'INFORMER_SERVICE', useValue: mockClient },
      ],
    }).compile();

    service = module.get<StocksService>(StocksService);
    service.onModuleInit();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('getStockInfo', () => {
    it('should call gRPC GetStockInfo with symbol', async () => {
      const mockResponse = { stock: { symbol: 'AAPL', name: 'Apple Inc.' } };
      mockGrpcService.GetStockInfo.mockReturnValue(of(mockResponse));

      const result = await service.getStockInfo('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetStockInfo).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('listStocks', () => {
    it('should call gRPC ListStocks with query params', async () => {
      const mockResponse = { stocks: [], pagination: { total_count: 0 } };
      mockGrpcService.ListStocks.mockReturnValue(of(mockResponse));

      const result = await service.listStocks({ page: 1, pageSize: 20 });
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.ListStocks).toHaveBeenCalledWith({
        exchange: '',
        sector: '',
        search: '',
        pagination: { page: 1, page_size: 20 },
      });
    });
  });

  describe('batchGetStocks', () => {
    it('should call gRPC BatchGetStocks with symbols', async () => {
      const mockResponse = { stocks: [], not_found: [] };
      mockGrpcService.BatchGetStocks.mockReturnValue(of(mockResponse));

      const result = await service.batchGetStocks(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.BatchGetStocks).toHaveBeenCalledWith({
        symbols: ['AAPL', 'MSFT'],
      });
    });
  });

  describe('getPriceHistory', () => {
    it('should call gRPC GetPriceHistory with defaults', async () => {
      const mockResponse = { symbol: 'AAPL', candles: [] };
      mockGrpcService.GetPriceHistory.mockReturnValue(of(mockResponse));

      const result = await service.getPriceHistory('AAPL', {});
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetPriceHistory).toHaveBeenCalledWith({
        symbol: 'AAPL',
        interval: '1d',
        start_date: '',
        end_date: '',
        limit: 365,
      });
    });
  });

  describe('healthCheck', () => {
    it('should call gRPC HealthCheck', async () => {
      const mockResponse = { status: 'SERVING' };
      mockGrpcService.HealthCheck.mockReturnValue(of(mockResponse));

      const result = await service.healthCheck();
      expect(result).toEqual(mockResponse);
    });
  });
});
