import { Test, TestingModule } from '@nestjs/testing';
import { of } from 'rxjs';
import { AnalyticsService } from './analytics.service';

describe('AnalyticsService', () => {
  let service: AnalyticsService;
  const mockGrpcService = {
    GetValuationMetrics: jest.fn(),
    GetTechnicalIndicators: jest.fn(),
    GetStockAnalysis: jest.fn(),
    BatchAnalysis: jest.fn(),
    ScreenStocks: jest.fn(),
    HealthCheck: jest.fn(),
  };

  const mockClient = {
    getService: jest.fn().mockReturnValue(mockGrpcService),
  };

  beforeEach(async () => {
    jest.clearAllMocks();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AnalyticsService,
        { provide: 'ANALYTICS_SERVICE', useValue: mockClient },
      ],
    }).compile();

    service = module.get<AnalyticsService>(AnalyticsService);
    service.onModuleInit();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('getValuationMetrics', () => {
    it('should call gRPC GetValuationMetrics', async () => {
      const mockResponse = { symbol: 'AAPL', trailing_pe: 25.5 };
      mockGrpcService.GetValuationMetrics.mockReturnValue(of(mockResponse));

      const result = await service.getValuationMetrics('AAPL');
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetValuationMetrics).toHaveBeenCalledWith({ symbol: 'AAPL' });
    });
  });

  describe('getTechnicalIndicators', () => {
    it('should call gRPC with timeframe defaults', async () => {
      const mockResponse = { symbol: 'AAPL', rsi_14: 55.0 };
      mockGrpcService.GetTechnicalIndicators.mockReturnValue(of(mockResponse));

      const result = await service.getTechnicalIndicators('AAPL', {});
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetTechnicalIndicators).toHaveBeenCalledWith({
        symbol: 'AAPL',
        timeframe: '1d',
      });
    });
  });

  describe('getStockAnalysis', () => {
    it('should call gRPC GetStockAnalysis', async () => {
      const mockResponse = { recommendation: 'Buy' };
      mockGrpcService.GetStockAnalysis.mockReturnValue(of(mockResponse));

      const result = await service.getStockAnalysis('AAPL', { includeRationale: true });
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.GetStockAnalysis).toHaveBeenCalledWith({
        symbol: 'AAPL',
        include_rationale: true,
      });
    });
  });

  describe('batchAnalysis', () => {
    it('should call gRPC BatchAnalysis', async () => {
      const mockResponse = { analyses: [] };
      mockGrpcService.BatchAnalysis.mockReturnValue(of(mockResponse));

      const result = await service.batchAnalysis(['AAPL', 'MSFT']);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('screenStocks', () => {
    it('should call gRPC ScreenStocks with criteria', async () => {
      const mockResponse = { stocks: [] };
      mockGrpcService.ScreenStocks.mockReturnValue(of(mockResponse));

      const result = await service.screenStocks({ maxPe: 25, limit: 10 });
      expect(result).toEqual(mockResponse);
      expect(mockGrpcService.ScreenStocks).toHaveBeenCalled();
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
