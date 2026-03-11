import { Test, TestingModule } from '@nestjs/testing';
import { of } from 'rxjs';
import { StocksService } from './stocks.service';

describe('StocksService', () => {
  let service: StocksService;

  // Mock for StockService (metadata CRUD + search)
  const mockStockGrpcService = {
    GetStock: jest.fn(),
    ListStocks: jest.fn(),
    SearchStocks: jest.fn(),
    GetStocksByIds: jest.fn(),
    CreateStock: jest.fn(),
    UpdateStock: jest.fn(),
    DeleteStock: jest.fn(),
    TriggerDataCollection: jest.fn(),
  };

  // Mock for PriceService (latest prices + OHLCV)
  const mockPriceGrpcService = {
    GetLatestPrice: jest.fn(),
    GetLatestPrices: jest.fn(),
    GetOHLCV: jest.fn(),
  };

  // Mock for FinancialService (income, balance sheet, cash flow, reports)
  const mockFinancialGrpcService = {
    GetIncomeStatement: jest.fn(),
    GetBalanceSheet: jest.fn(),
    GetCashFlow: jest.fn(),
    GetFinancialSummary: jest.fn(),
    GetFinancialReports: jest.fn(),
  };

  const mockClient = {
    getService: jest.fn().mockImplementation((name: string) => {
      if (name === 'StockService') return mockStockGrpcService;
      if (name === 'PriceService') return mockPriceGrpcService;
      if (name === 'FinancialService') return mockFinancialGrpcService;
      return {};
    }),
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

  it('should initialize all three gRPC services on module init', () => {
    expect(mockClient.getService).toHaveBeenCalledWith('StockService');
    expect(mockClient.getService).toHaveBeenCalledWith('PriceService');
    expect(mockClient.getService).toHaveBeenCalledWith('FinancialService');
  });

  describe('getStockInfo', () => {
    it('should call StockService.GetStock with symbol', async () => {
      const mockResponse = { stock: { symbol: 'AAPL', name: 'Apple Inc.' } };
      mockStockGrpcService.GetStock.mockReturnValue(of(mockResponse));

      const result = await service.getStockInfo('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockStockGrpcService.GetStock).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('listStocks', () => {
    it('should call StockService.ListStocks with query params', async () => {
      const mockResponse = { stocks: [], pagination: { total_count: 0 } };
      mockStockGrpcService.ListStocks.mockReturnValue(of(mockResponse));

      const result = await service.listStocks({ page: 1, pageSize: 20 });
      expect(result).toEqual(mockResponse);
      expect(mockStockGrpcService.ListStocks).toHaveBeenCalledWith({
        exchange: '',
        sector: '',
        search: '',
        country: '',
        pagination: { page: 1, page_size: 20 },
      });
    });

    it('should pass country filter', async () => {
      const mockResponse = { stocks: [], pagination: { total_count: 0 } };
      mockStockGrpcService.ListStocks.mockReturnValue(of(mockResponse));

      await service.listStocks({ country: 'VN', page: 1, pageSize: 20 });
      expect(mockStockGrpcService.ListStocks).toHaveBeenCalledWith(
        expect.objectContaining({ country: 'VN' }),
      );
    });
  });

  describe('searchStocks', () => {
    it('should call StockService.SearchStocks with query and limit', async () => {
      const mockResponse = { stocks: [] };
      mockStockGrpcService.SearchStocks.mockReturnValue(of(mockResponse));

      const result = await service.searchStocks('apple', 10);
      expect(result).toEqual(mockResponse);
      expect(mockStockGrpcService.SearchStocks).toHaveBeenCalledWith({ query: 'apple', limit: 10 });
    });
  });

  describe('batchGetStocks', () => {
    it('should normalize symbols and call SearchStocks', async () => {
      const mockResponse = { stocks: [] };
      mockStockGrpcService.SearchStocks.mockReturnValue(of(mockResponse));

      const result = await service.batchGetStocks(['aapl', ' msft ']);
      expect(result).toEqual(mockResponse);
      expect(mockStockGrpcService.SearchStocks).toHaveBeenCalledWith(
        expect.objectContaining({ limit: 2 }),
      );
    });
  });

  describe('createStock', () => {
    it('should call StockService.CreateStock with uppercase symbol', async () => {
      const mockResponse = { stock: { symbol: 'TEST', name: 'Test Inc.' } };
      mockStockGrpcService.CreateStock.mockReturnValue(of(mockResponse));

      const result = await service.createStock({ symbol: 'test', name: 'Test Inc.' });
      expect(result.stock.symbol).toBe('TEST');
      expect(mockStockGrpcService.CreateStock).toHaveBeenCalledWith({
        stock: expect.objectContaining({ symbol: 'TEST', name: 'Test Inc.' }),
      });
    });
  });

  describe('updateStock', () => {
    it('should call StockService.UpdateStock with symbol and partial fields', async () => {
      const mockResponse = { stock: { symbol: 'AAPL', name: 'Updated' } };
      mockStockGrpcService.UpdateStock.mockReturnValue(of(mockResponse));

      const result = await service.updateStock('aapl', { name: 'Updated' });
      expect(result.stock.name).toBe('Updated');
      expect(mockStockGrpcService.UpdateStock).toHaveBeenCalledWith({
        symbol: 'AAPL',
        stock: expect.objectContaining({ symbol: 'AAPL', name: 'Updated' }),
      });
    });
  });

  describe('deleteStock', () => {
    it('should call StockService.DeleteStock and return success', async () => {
      const mockResponse = { success: true, message: 'Stock AAPL deactivated' };
      mockStockGrpcService.DeleteStock.mockReturnValue(of(mockResponse));

      const result = await service.deleteStock('aapl');
      expect(result.success).toBe(true);
      expect(mockStockGrpcService.DeleteStock).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('getPriceHistory', () => {
    it('should call PriceService.GetOHLCV with defaults', async () => {
      const mockResponse = { symbol: 'AAPL', candles: [] };
      mockPriceGrpcService.GetOHLCV.mockReturnValue(of(mockResponse));

      const result = await service.getPriceHistory('AAPL', {});
      expect(result).toEqual(mockResponse);
      expect(mockPriceGrpcService.GetOHLCV).toHaveBeenCalledWith({
        symbol: 'AAPL',
        interval: '1d',
        start_date: '',
        end_date: '',
        limit: 365,
      });
    });
  });

  describe('getLatestPrice', () => {
    it('should call PriceService.GetLatestPrice with symbol', async () => {
      const mockResponse = { symbol: 'AAPL', last_price: 175.5 };
      mockPriceGrpcService.GetLatestPrice.mockReturnValue(of(mockResponse));

      const result = await service.getLatestPrice('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockPriceGrpcService.GetLatestPrice).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('getLatestPrices', () => {
    it('should call PriceService.GetLatestPrices with symbols array', async () => {
      const mockResponse = { prices: [{ symbol: 'AAPL', last_price: 175.5 }], failed: [] };
      mockPriceGrpcService.GetLatestPrices.mockReturnValue(of(mockResponse));

      const result = await service.getLatestPrices(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
      expect(mockPriceGrpcService.GetLatestPrices).toHaveBeenCalledWith({ symbols: ['AAPL', 'MSFT'] });
    });
  });

  describe('getFinancialReports', () => {
    it('should call FinancialService.GetFinancialReports with defaults', async () => {
      const mockResponse = { reports: [] };
      mockFinancialGrpcService.GetFinancialReports.mockReturnValue(of(mockResponse));

      const result = await service.getFinancialReports('AAPL', {});
      expect(result).toEqual(mockResponse);
      expect(mockFinancialGrpcService.GetFinancialReports).toHaveBeenCalledWith({
        symbol: 'AAPL',
        report_type: '',
        years_back: 5,
      });
    });
  });

  describe('getFinancialSummary', () => {
    it('should call FinancialService.GetFinancialSummary', async () => {
      const mockResponse = { summary: { symbol: 'AAPL', revenue: 1000000 } };
      mockFinancialGrpcService.GetFinancialSummary.mockReturnValue(of(mockResponse));

      const result = await service.getFinancialSummary('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockFinancialGrpcService.GetFinancialSummary).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('getIncomeStatement', () => {
    it('should call FinancialService.GetIncomeStatement with defaults', async () => {
      const mockResponse = { symbol: 'AAPL', statements: [] };
      mockFinancialGrpcService.GetIncomeStatement.mockReturnValue(of(mockResponse));

      const result = await service.getIncomeStatement('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockFinancialGrpcService.GetIncomeStatement).toHaveBeenCalledWith({
        symbol: 'AAPL',
        period: 'annual',
        years_back: 5,
      });
    });
  });
});
