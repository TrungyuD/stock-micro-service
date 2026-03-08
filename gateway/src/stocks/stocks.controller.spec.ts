import { Test, TestingModule } from '@nestjs/testing';
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
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      controllers: [StocksController],
      providers: [
        { provide: StocksService, useValue: mockStocksService },
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
});
