import { Test, TestingModule } from '@nestjs/testing';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { StocksController } from './stocks.controller';
import { StocksService } from './stocks.service';

describe('StocksController', () => {
  let controller: StocksController;
  const mockStocksService = {
    listStocks: jest.fn(),
    batchGetStocks: jest.fn(),
    getStockInfo: jest.fn(),
    getPriceHistory: jest.fn(),
    getFinancialReports: jest.fn(),
    createStock: jest.fn(),
    updateStock: jest.fn(),
    deleteStock: jest.fn(),
  };

  const mockCacheManager = { get: jest.fn(), set: jest.fn(), clear: jest.fn() };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      controllers: [StocksController],
      providers: [
        { provide: StocksService, useValue: mockStocksService },
        { provide: CACHE_MANAGER, useValue: mockCacheManager },
      ],
    }).compile();

    controller = module.get<StocksController>(StocksController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('findAll', () => {
    it('should delegate to stocksService.listStocks', async () => {
      const mockResult = { stocks: [], pagination: { total_count: 0 } };
      mockStocksService.listStocks.mockResolvedValue(mockResult);

      const result = await controller.findAll({ page: 1, pageSize: 20 });
      expect(result).toEqual(mockResult);
      expect(mockStocksService.listStocks).toHaveBeenCalledWith({ page: 1, pageSize: 20 });
    });
  });

  describe('batchGetStocks', () => {
    it('should delegate to stocksService.batchGetStocks', async () => {
      const mockResult = { stocks: [], not_found: [] };
      mockStocksService.batchGetStocks.mockResolvedValue(mockResult);

      const result = await controller.batchGetStocks({ symbols: ['AAPL'] });
      expect(result).toEqual(mockResult);
      expect(mockStocksService.batchGetStocks).toHaveBeenCalledWith(['AAPL']);
    });
  });

  describe('findOne', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { stock: { symbol: 'AAPL' } };
      mockStocksService.getStockInfo.mockResolvedValue(mockResult);

      const result = await controller.findOne('aapl');
      expect(result).toEqual(mockResult);
      expect(mockStocksService.getStockInfo).toHaveBeenCalledWith('AAPL');
    });
  });

  describe('getPriceHistory', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { candles: [] };
      mockStocksService.getPriceHistory.mockResolvedValue(mockResult);

      const result = await controller.getPriceHistory('msft', {});
      expect(result).toEqual(mockResult);
      expect(mockStocksService.getPriceHistory).toHaveBeenCalledWith('MSFT', {});
    });
  });

  describe('getFinancialReports', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { reports: [] };
      mockStocksService.getFinancialReports.mockResolvedValue(mockResult);

      const result = await controller.getFinancialReports('goog', {});
      expect(result).toEqual(mockResult);
      expect(mockStocksService.getFinancialReports).toHaveBeenCalledWith('GOOG', {});
    });
  });

  describe('createStock', () => {
    it('should delegate to service and invalidate cache', async () => {
      const dto = { symbol: 'TEST', name: 'Test Inc.' };
      const mockResult = { stock: { symbol: 'TEST', name: 'Test Inc.' } };
      mockStocksService.createStock.mockResolvedValue(mockResult);

      const result = await controller.createStock(dto as any);
      expect(result).toEqual(mockResult);
      expect(mockStocksService.createStock).toHaveBeenCalledWith(dto);
      expect(mockCacheManager.clear).toHaveBeenCalled();
    });
  });

  describe('updateStock', () => {
    it('should delegate to service and invalidate cache', async () => {
      const dto = { name: 'Updated Name' };
      const mockResult = { stock: { symbol: 'AAPL', name: 'Updated Name' } };
      mockStocksService.updateStock.mockResolvedValue(mockResult);

      const result = await controller.updateStock('AAPL', dto as any);
      expect(result).toEqual(mockResult);
      expect(mockStocksService.updateStock).toHaveBeenCalledWith('AAPL', dto);
      expect(mockCacheManager.clear).toHaveBeenCalled();
    });
  });

  describe('deleteStock', () => {
    it('should delegate to service and invalidate cache', async () => {
      const mockResult = { success: true, message: 'Stock AAPL deactivated' };
      mockStocksService.deleteStock.mockResolvedValue(mockResult);

      const result = await controller.deleteStock('AAPL');
      expect(result).toEqual(mockResult);
      expect(mockStocksService.deleteStock).toHaveBeenCalledWith('AAPL');
      expect(mockCacheManager.clear).toHaveBeenCalled();
    });
  });
});
