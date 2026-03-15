import { Test, TestingModule } from '@nestjs/testing';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { AnalyticsController } from './analytics.controller';
import { AnalyticsService } from './analytics.service';

describe('AnalyticsController', () => {
  let controller: AnalyticsController;
  const mockAnalyticsService = {
    getStockAnalysis: jest.fn(),
    getValuationMetrics: jest.fn(),
    getTechnicalIndicators: jest.fn(),
    batchAnalysis: jest.fn(),
    screenStocks: jest.fn(),
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      controllers: [AnalyticsController],
      providers: [
        { provide: AnalyticsService, useValue: mockAnalyticsService },
        { provide: CACHE_MANAGER, useValue: { get: jest.fn(), set: jest.fn() } },
      ],
    }).compile();

    controller = module.get<AnalyticsController>(AnalyticsController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('getStockAnalysis', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { recommendation: 'Buy', confidence: 72 };
      mockAnalyticsService.getStockAnalysis.mockResolvedValue(mockResult);

      const result = await controller.getStockAnalysis('aapl', {});
      expect(result).toEqual(mockResult);
      expect(mockAnalyticsService.getStockAnalysis).toHaveBeenCalledWith('AAPL', {});
    });
  });

  describe('getValuationMetrics', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { trailing_pe: 28.5, pb_ratio: 4.2 };
      mockAnalyticsService.getValuationMetrics.mockResolvedValue(mockResult);

      const result = await controller.getValuationMetrics('msft');
      expect(result).toEqual(mockResult);
      expect(mockAnalyticsService.getValuationMetrics).toHaveBeenCalledWith('MSFT');
    });
  });

  describe('getTechnicalIndicators', () => {
    it('should uppercase symbol and delegate to service', async () => {
      const mockResult = { rsi_14: 55.0, sma_20: 170.5 };
      mockAnalyticsService.getTechnicalIndicators.mockResolvedValue(mockResult);

      const result = await controller.getTechnicalIndicators('goog', { timeframe: '1w' });
      expect(result).toEqual(mockResult);
      expect(mockAnalyticsService.getTechnicalIndicators).toHaveBeenCalledWith('GOOG', { timeframe: '1w' });
    });
  });

  describe('batchAnalysis', () => {
    it('should delegate symbols to service', async () => {
      const mockResult = { analyses: [{ symbol: 'AAPL' }] };
      mockAnalyticsService.batchAnalysis.mockResolvedValue(mockResult);

      const result = await controller.batchAnalysis({ symbols: ['AAPL', 'MSFT'] });
      expect(result).toEqual(mockResult);
      expect(mockAnalyticsService.batchAnalysis).toHaveBeenCalledWith(['AAPL', 'MSFT']);
    });
  });

  describe('screenStocks', () => {
    it('should delegate screening criteria to service', async () => {
      const dto = { maxPe: 25, rsiOversold: true, limit: 10 };
      const mockResult = { stocks: [], total: 0 };
      mockAnalyticsService.screenStocks.mockResolvedValue(mockResult);

      const result = await controller.screenStocks(dto as any);
      expect(result).toEqual(mockResult);
      expect(mockAnalyticsService.screenStocks).toHaveBeenCalledWith(dto);
    });
  });
});
