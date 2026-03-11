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
    CreateStock: jest.fn(),
    UpdateStock: jest.fn(),
    DeleteStock: jest.fn(),
    HealthCheck: jest.fn(),
    GetLivePrice: jest.fn(),
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
        country: '',
        pagination: { page: 1, page_size: 20 },
      });
    });
  });

  describe('batchGetStocks', () => {
    it('should normalize symbols to uppercase and call gRPC', async () => {
      const mockResponse = { stocks: [], not_found: [] };
      mockGrpcService.BatchGetStocks.mockReturnValue(of(mockResponse));

      const result = await service.batchGetStocks(['aapl', ' msft ']);
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.BatchGetStocks).toHaveBeenCalledWith({
        symbols: ['AAPL', 'MSFT'],
      });
    });
  });

  describe('listStocks with country', () => {
    it('should pass country filter to gRPC ListStocks', async () => {
      const mockResponse = { stocks: [], pagination: { total_count: 0 } };
      mockGrpcService.ListStocks.mockReturnValue(of(mockResponse));

      await service.listStocks({ country: 'VN', page: 1, pageSize: 20 });
      expect(mockGrpcService.ListStocks).toHaveBeenCalledWith(
        expect.objectContaining({ country: 'VN' }),
      );
    });
  });

  describe('createStock', () => {
    it('should call gRPC CreateStock with stock payload', async () => {
      const mockResponse = { stock: { symbol: 'TEST', name: 'Test Inc.' } };
      mockGrpcService.CreateStock.mockReturnValue(of(mockResponse));

      const result = await service.createStock({ symbol: 'test', name: 'Test Inc.' });
      expect(result.stock.symbol).toBe('TEST');
      expect(mockGrpcService.CreateStock).toHaveBeenCalledWith({
        stock: expect.objectContaining({ symbol: 'TEST', name: 'Test Inc.' }),
      });
    });
  });

  describe('updateStock', () => {
    it('should call gRPC UpdateStock with symbol and partial fields', async () => {
      const mockResponse = { stock: { symbol: 'AAPL', name: 'Updated' } };
      mockGrpcService.UpdateStock.mockReturnValue(of(mockResponse));

      const result = await service.updateStock('aapl', { name: 'Updated' });
      expect(result.stock.name).toBe('Updated');
      expect(mockGrpcService.UpdateStock).toHaveBeenCalledWith({
        symbol: 'AAPL',
        stock: expect.objectContaining({ symbol: 'AAPL', name: 'Updated' }),
      });
    });
  });

  describe('deleteStock', () => {
    it('should call gRPC DeleteStock and return success', async () => {
      const mockResponse = { success: true, message: 'Stock AAPL deactivated' };
      mockGrpcService.DeleteStock.mockReturnValue(of(mockResponse));

      const result = await service.deleteStock('aapl');
      expect(result.success).toBe(true);
      expect(mockGrpcService.DeleteStock).toHaveBeenCalledWith({ symbol: 'AAPL' });
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

  describe('getLivePrice', () => {
    it('should call gRPC GetLivePrice with symbols array', async () => {
      const mockResponse = { prices: [{ symbol: 'AAPL', last_price: 175.5 }] };
      mockGrpcService.GetLivePrice.mockReturnValue(of(mockResponse));

      const result = await service.getLivePrice(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetLivePrice).toHaveBeenCalledWith({ symbols: ['AAPL', 'MSFT'] });
    });
  });
});
